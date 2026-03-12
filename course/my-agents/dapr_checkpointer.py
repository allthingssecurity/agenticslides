"""
DaprCheckpointSaver — BaseCheckpointSaver backed by Dapr State Store
====================================================================
A drop-in replacement for LangGraph's InMemorySaver that stores all
checkpoint data (messages, tool call history, channel values) in a Dapr
State Store (Redis, Postgres, Cosmos DB, etc.).

This is a direct port of InMemorySaver — same logic, different storage
backend.  When the Dapr sidecar is unavailable (no ``dapr`` package or
connection failure), it falls back to an in-memory dict so you can
develop without running Dapr.

Usage:
    from dapr_checkpointer import DaprCheckpointSaver

    checkpointer = DaprCheckpointSaver(store_name="agentstore")
    agent = create_deep_agent(
        model="openai:gpt-4o-mini",
        tools=[web_search],
        system_prompt="...",
        checkpointer=checkpointer,
    )
    # LangGraph state now persists in Redis/Postgres/Cosmos via Dapr
"""

from __future__ import annotations

import base64
import json
import logging
import random
from collections.abc import AsyncIterator, Iterator, Sequence
from typing import Any

from langchain_core.runnables import RunnableConfig

from langgraph.checkpoint.base import (
    WRITES_IDX_MAP,
    BaseCheckpointSaver,
    ChannelVersions,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    get_checkpoint_id,
    get_checkpoint_metadata,
)

logger = logging.getLogger(__name__)


# ─── Serialization bridge ─────────────────────────────────
# serde.dumps_typed() returns (type_str, bytes).
# Dapr State Store values are JSON strings.
# Bridge: {"type": type_str, "data": base64(bytes)}


def _encode_typed(typed_pair: tuple[str, bytes]) -> dict[str, str]:
    """Encode a (type_str, bytes) pair into a JSON-safe dict."""
    type_str, raw = typed_pair
    return {"type": type_str, "data": base64.b64encode(raw).decode("ascii")}


def _decode_typed(d: dict[str, str]) -> tuple[str, bytes]:
    """Decode a JSON dict back into a (type_str, bytes) pair."""
    return (d["type"], base64.b64decode(d["data"]))


# ═══════════════════════════════════════════════════════════
# DaprCheckpointSaver
# ═══════════════════════════════════════════════════════════


class DaprCheckpointSaver(BaseCheckpointSaver[str]):
    """A BaseCheckpointSaver backed by Dapr State Store.

    Direct port of ``InMemorySaver``.  Three data structures are mapped
    to Dapr State Store keys:

    ========================  ===================================
    InMemorySaver structure   Dapr key pattern
    ========================  ===================================
    storage[t][ns][cpid]      ``cp:{tid}:{ns}:{cpid}``
    blobs[(t,ns,ch,ver)]      ``blob:{tid}:{ns}:{ch}:{ver}``
    writes[(t,ns,cpid)][...]  ``writes:{tid}:{ns}:{cpid}``
    ========================  ===================================

    An index at ``idx:{tid}:{ns}`` tracks checkpoint IDs (sorted) for
    listing since Dapr has no "list keys by prefix" API.

    Args:
        store_name: Dapr component name (default ``"agentstore"``).
    """

    def __init__(self, store_name: str = "agentstore") -> None:
        super().__init__()
        self.store_name = store_name
        self._client: Any = None
        self._simulate = True

        # Try to connect to Dapr
        try:
            from dapr.clients import DaprClient

            client = DaprClient()
            # Quick health check — try to read a non-existent key
            client.get_state(store_name, "__health__")
            self._client = client
            self._simulate = False
            logger.info("DaprCheckpointSaver: connected to Dapr sidecar")
            print(f"  \033[92m[DAPR]\033[0m Connected to Dapr State Store '{store_name}' (Redis)")
        except ImportError:
            logger.info(
                "DaprCheckpointSaver: dapr package not installed — "
                "using in-memory fallback"
            )
            print(f"  \033[93m[DAPR]\033[0m dapr package not installed — using in-memory fallback")
        except Exception as exc:
            logger.info(
                "DaprCheckpointSaver: Dapr sidecar unavailable (%s) — "
                "using in-memory fallback",
                exc,
            )
            print(f"  \033[93m[DAPR]\033[0m Sidecar unavailable — using in-memory fallback")

        # In-memory fallback
        self._mem: dict[str, str] = {}

    # ─── low-level state store ops ────────────────────────

    def _save(self, key: str, value: Any) -> None:
        """Save a JSON-serializable value."""
        data = json.dumps(value)
        if self._simulate:
            self._mem[key] = data
        else:
            self._client.save_state(self.store_name, key, data)

    def _load(self, key: str) -> Any | None:
        """Load a value, returning None if not found."""
        if self._simulate:
            raw = self._mem.get(key)
        else:
            resp = self._client.get_state(self.store_name, key)
            raw = resp.data.decode("utf-8") if resp.data else None
        if raw:
            return json.loads(raw)
        return None

    def _delete(self, key: str) -> None:
        if self._simulate:
            self._mem.pop(key, None)
        else:
            self._client.delete_state(self.store_name, key)

    def _keys_with_prefix(self, prefix: str) -> list[str]:
        """Return all keys matching a prefix (simulation only helper)."""
        if self._simulate:
            return [k for k in self._mem if k.startswith(prefix)]
        # With real Dapr, we rely on indices rather than scanning
        return []

    # ─── index management ─────────────────────────────────
    # Index key: idx:{thread_id}:{checkpoint_ns}
    # Value: {"ids": ["cpid1", "cpid2", ...]}  (sorted ascending)

    def _idx_key(self, thread_id: str, checkpoint_ns: str) -> str:
        return f"idx:{thread_id}:{checkpoint_ns}"

    def _read_index(self, thread_id: str, checkpoint_ns: str) -> list[str]:
        data = self._load(self._idx_key(thread_id, checkpoint_ns))
        if data and "ids" in data:
            return data["ids"]
        return []

    def _append_index(
        self, thread_id: str, checkpoint_ns: str, checkpoint_id: str
    ) -> None:
        ids = self._read_index(thread_id, checkpoint_ns)
        if checkpoint_id not in ids:
            ids.append(checkpoint_id)
            ids.sort()
        self._save(self._idx_key(thread_id, checkpoint_ns), {"ids": ids})

    def _delete_index(self, thread_id: str, checkpoint_ns: str) -> None:
        self._delete(self._idx_key(thread_id, checkpoint_ns))

    # ─── namespace index ──────────────────────────────────
    # Tracks which checkpoint_ns values exist for a thread_id.
    # Key: ns_idx:{thread_id}  Value: {"namespaces": [...]}

    def _ns_idx_key(self, thread_id: str) -> str:
        return f"ns_idx:{thread_id}"

    def _read_ns_index(self, thread_id: str) -> list[str]:
        data = self._load(self._ns_idx_key(thread_id))
        if data and "namespaces" in data:
            return data["namespaces"]
        return []

    def _add_ns(self, thread_id: str, checkpoint_ns: str) -> None:
        nss = self._read_ns_index(thread_id)
        if checkpoint_ns not in nss:
            nss.append(checkpoint_ns)
            nss.sort()
            self._save(self._ns_idx_key(thread_id), {"namespaces": nss})

    # ─── key builders ─────────────────────────────────────

    @staticmethod
    def _cp_key(
        thread_id: str, checkpoint_ns: str, checkpoint_id: str
    ) -> str:
        return f"cp:{thread_id}:{checkpoint_ns}:{checkpoint_id}"

    @staticmethod
    def _blob_key(
        thread_id: str, checkpoint_ns: str, channel: str, version: str
    ) -> str:
        return f"blob:{thread_id}:{checkpoint_ns}:{channel}:{version}"

    @staticmethod
    def _writes_key(
        thread_id: str, checkpoint_ns: str, checkpoint_id: str
    ) -> str:
        return f"writes:{thread_id}:{checkpoint_ns}:{checkpoint_id}"

    # ─── helpers ──────────────────────────────────────────

    def _load_blobs(
        self,
        thread_id: str,
        checkpoint_ns: str,
        versions: ChannelVersions,
    ) -> dict[str, Any]:
        """Load and deserialize channel values from blob keys."""
        channel_values: dict[str, Any] = {}
        for channel, version in versions.items():
            key = self._blob_key(thread_id, checkpoint_ns, channel, str(version))
            data = self._load(key)
            if data is not None:
                typed = _decode_typed(data)
                if typed[0] != "empty":
                    channel_values[channel] = self.serde.loads_typed(typed)
        return channel_values

    def _load_writes(
        self, thread_id: str, checkpoint_ns: str, checkpoint_id: str
    ) -> list[tuple[str, str, tuple[str, bytes], str]]:
        """Load pending writes for a checkpoint."""
        data = self._load(
            self._writes_key(thread_id, checkpoint_ns, checkpoint_id)
        )
        if not data:
            return []
        # data is a dict keyed by "task_id:write_idx"
        # each value is [task_id, channel, encoded_typed, task_path]
        result = []
        for _inner_key, entry in data.items():
            task_id, channel, encoded, task_path = entry
            typed = _decode_typed(encoded)
            result.append((task_id, channel, typed, task_path))
        return result

    # ═══════════════════════════════════════════════════════
    # BaseCheckpointSaver interface
    # ═══════════════════════════════════════════════════════

    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        """Get a checkpoint tuple from Dapr State Store."""
        thread_id: str = config["configurable"]["thread_id"]
        checkpoint_ns: str = config["configurable"].get("checkpoint_ns", "")

        if checkpoint_id := get_checkpoint_id(config):
            # Specific checkpoint requested
            saved = self._load(
                self._cp_key(thread_id, checkpoint_ns, checkpoint_id)
            )
            if saved is None:
                return None

            checkpoint_encoded = _decode_typed(saved["checkpoint"])
            metadata_encoded = _decode_typed(saved["metadata"])
            parent_checkpoint_id = saved.get("parent_checkpoint_id")

            raw_writes = self._load_writes(
                thread_id, checkpoint_ns, checkpoint_id
            )
            checkpoint_: Checkpoint = self.serde.loads_typed(checkpoint_encoded)

            return CheckpointTuple(
                config=config,
                checkpoint={
                    **checkpoint_,
                    "channel_values": self._load_blobs(
                        thread_id,
                        checkpoint_ns,
                        checkpoint_["channel_versions"],
                    ),
                },
                metadata=self.serde.loads_typed(metadata_encoded),
                pending_writes=[
                    (tid, ch, self.serde.loads_typed(v))
                    for tid, ch, v, _ in raw_writes
                ],
                parent_config=(
                    {
                        "configurable": {
                            "thread_id": thread_id,
                            "checkpoint_ns": checkpoint_ns,
                            "checkpoint_id": parent_checkpoint_id,
                        }
                    }
                    if parent_checkpoint_id
                    else None
                ),
            )
        else:
            # Latest checkpoint
            ids = self._read_index(thread_id, checkpoint_ns)
            if not ids:
                return None
            checkpoint_id = ids[-1]  # sorted ascending, last = max

            saved = self._load(
                self._cp_key(thread_id, checkpoint_ns, checkpoint_id)
            )
            if saved is None:
                return None

            checkpoint_encoded = _decode_typed(saved["checkpoint"])
            metadata_encoded = _decode_typed(saved["metadata"])
            parent_checkpoint_id = saved.get("parent_checkpoint_id")

            raw_writes = self._load_writes(
                thread_id, checkpoint_ns, checkpoint_id
            )
            checkpoint_ = self.serde.loads_typed(checkpoint_encoded)

            return CheckpointTuple(
                config={
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": checkpoint_ns,
                        "checkpoint_id": checkpoint_id,
                    }
                },
                checkpoint={
                    **checkpoint_,
                    "channel_values": self._load_blobs(
                        thread_id,
                        checkpoint_ns,
                        checkpoint_["channel_versions"],
                    ),
                },
                metadata=self.serde.loads_typed(metadata_encoded),
                pending_writes=[
                    (tid, ch, self.serde.loads_typed(v))
                    for tid, ch, v, _ in raw_writes
                ],
                parent_config=(
                    {
                        "configurable": {
                            "thread_id": thread_id,
                            "checkpoint_ns": checkpoint_ns,
                            "checkpoint_id": parent_checkpoint_id,
                        }
                    }
                    if parent_checkpoint_id
                    else None
                ),
            )

    def list(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> Iterator[CheckpointTuple]:
        """List checkpoints from Dapr State Store."""
        # Determine thread_ids to iterate
        if config:
            thread_ids = [config["configurable"]["thread_id"]]
        else:
            # Without config, we'd need a global thread index.
            # For simulation mode, derive from keys; otherwise return empty.
            if self._simulate:
                prefixes = set()
                for k in self._mem:
                    if k.startswith("ns_idx:"):
                        prefixes.add(k[len("ns_idx:") :])
                thread_ids = sorted(prefixes)
            else:
                return

        config_checkpoint_ns = (
            config["configurable"].get("checkpoint_ns") if config else None
        )
        config_checkpoint_id = get_checkpoint_id(config) if config else None

        for thread_id in thread_ids:
            namespaces = self._read_ns_index(thread_id)
            if not namespaces:
                namespaces = [""]

            for checkpoint_ns in namespaces:
                if (
                    config_checkpoint_ns is not None
                    and checkpoint_ns != config_checkpoint_ns
                ):
                    continue

                ids = self._read_index(thread_id, checkpoint_ns)

                # Iterate descending (newest first)
                for checkpoint_id in reversed(ids):
                    # Filter by checkpoint_id from config
                    if (
                        config_checkpoint_id
                        and checkpoint_id != config_checkpoint_id
                    ):
                        continue

                    # Filter by before
                    if before:
                        before_id = get_checkpoint_id(before)
                        if before_id and checkpoint_id >= before_id:
                            continue

                    saved = self._load(
                        self._cp_key(thread_id, checkpoint_ns, checkpoint_id)
                    )
                    if saved is None:
                        continue

                    checkpoint_encoded = _decode_typed(saved["checkpoint"])
                    metadata_encoded = _decode_typed(saved["metadata"])
                    parent_checkpoint_id = saved.get("parent_checkpoint_id")

                    metadata = self.serde.loads_typed(metadata_encoded)

                    # Filter by metadata
                    if filter and not all(
                        query_value == metadata.get(query_key)
                        for query_key, query_value in filter.items()
                    ):
                        continue

                    # Limit
                    if limit is not None and limit <= 0:
                        break
                    elif limit is not None:
                        limit -= 1

                    raw_writes = self._load_writes(
                        thread_id, checkpoint_ns, checkpoint_id
                    )
                    checkpoint_: Checkpoint = self.serde.loads_typed(
                        checkpoint_encoded
                    )

                    yield CheckpointTuple(
                        config={
                            "configurable": {
                                "thread_id": thread_id,
                                "checkpoint_ns": checkpoint_ns,
                                "checkpoint_id": checkpoint_id,
                            }
                        },
                        checkpoint={
                            **checkpoint_,
                            "channel_values": self._load_blobs(
                                thread_id,
                                checkpoint_ns,
                                checkpoint_["channel_versions"],
                            ),
                        },
                        metadata=metadata,
                        parent_config=(
                            {
                                "configurable": {
                                    "thread_id": thread_id,
                                    "checkpoint_ns": checkpoint_ns,
                                    "checkpoint_id": parent_checkpoint_id,
                                }
                            }
                            if parent_checkpoint_id
                            else None
                        ),
                        pending_writes=[
                            (tid, ch, self.serde.loads_typed(v))
                            for tid, ch, v, _ in raw_writes
                        ],
                    )

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Save a checkpoint to Dapr State Store."""
        c = checkpoint.copy()
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"]["checkpoint_ns"]
        values: dict[str, Any] = c.pop("channel_values")  # type: ignore[misc]

        # Store blobs for each channel version
        for k, v in new_versions.items():
            blob_data: tuple[str, bytes]
            if k in values:
                blob_data = self.serde.dumps_typed(values[k])
            else:
                blob_data = ("empty", b"")
            self._save(
                self._blob_key(thread_id, checkpoint_ns, k, str(v)),
                _encode_typed(blob_data),
            )

        # Store checkpoint + metadata
        parent_checkpoint_id = config["configurable"].get("checkpoint_id")
        self._save(
            self._cp_key(thread_id, checkpoint_ns, checkpoint["id"]),
            {
                "checkpoint": _encode_typed(self.serde.dumps_typed(c)),
                "metadata": _encode_typed(
                    self.serde.dumps_typed(
                        get_checkpoint_metadata(config, metadata)
                    )
                ),
                "parent_checkpoint_id": parent_checkpoint_id,
            },
        )

        # Update indices
        self._append_index(thread_id, checkpoint_ns, checkpoint["id"])
        self._add_ns(thread_id, checkpoint_ns)

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint["id"],
            }
        }

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """Save pending writes to Dapr State Store."""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = config["configurable"]["checkpoint_id"]

        writes_key = self._writes_key(thread_id, checkpoint_ns, checkpoint_id)

        # Read-modify-write: load existing writes dict
        existing = self._load(writes_key) or {}

        for idx, (channel, value) in enumerate(writes):
            inner_key = f"{task_id}:{WRITES_IDX_MAP.get(channel, idx)}"

            # Idempotency: skip if non-negative index already exists
            write_idx = WRITES_IDX_MAP.get(channel, idx)
            if write_idx >= 0 and inner_key in existing:
                continue

            existing[inner_key] = [
                task_id,
                channel,
                _encode_typed(self.serde.dumps_typed(value)),
                task_path,
            ]

        self._save(writes_key, existing)

    def delete_thread(self, thread_id: str) -> None:
        """Delete all checkpoints, writes, and blobs for a thread."""
        namespaces = self._read_ns_index(thread_id)
        if not namespaces:
            namespaces = [""]

        for checkpoint_ns in namespaces:
            ids = self._read_index(thread_id, checkpoint_ns)
            for checkpoint_id in ids:
                # Delete checkpoint
                self._delete(
                    self._cp_key(thread_id, checkpoint_ns, checkpoint_id)
                )
                # Delete writes
                self._delete(
                    self._writes_key(thread_id, checkpoint_ns, checkpoint_id)
                )
                # Load checkpoint to find blob versions to delete
                # (Already deleted, but we stored the versions in the checkpoint)

            # Delete blob keys — scan in simulation, skip in production
            # (In production, blobs are orphaned and can be garbage-collected)
            if self._simulate:
                prefix = f"blob:{thread_id}:{checkpoint_ns}:"
                for key in self._keys_with_prefix(prefix):
                    self._delete(key)

            # Delete index
            self._delete_index(thread_id, checkpoint_ns)

        # Delete namespace index
        self._delete(self._ns_idx_key(thread_id))

    def get_next_version(self, current: str | None, channel: None) -> str:
        """Generate next version string — same as InMemorySaver."""
        if current is None:
            current_v = 0
        elif isinstance(current, int):
            current_v = current
        else:
            current_v = int(current.split(".")[0])
        next_v = current_v + 1
        next_h = random.random()
        return f"{next_v:032}.{next_h:016}"

    # ─── async variants (delegate to sync, same as InMemorySaver) ──

    async def aget_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        return self.get_tuple(config)

    async def alist(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[CheckpointTuple]:
        for item in self.list(config, filter=filter, before=before, limit=limit):
            yield item

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        return self.put(config, checkpoint, metadata, new_versions)

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        return self.put_writes(config, writes, task_id, task_path)

    async def adelete_thread(self, thread_id: str) -> None:
        return self.delete_thread(thread_id)
