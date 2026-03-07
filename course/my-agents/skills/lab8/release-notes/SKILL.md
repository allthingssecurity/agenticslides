---
name: release-notes
description: Build structured release notes from raw engineering changes for developers and stakeholders.
---

# Release Notes Skill

## When To Use
- User asks to summarize product or engineering changes.
- User provides a changelog, commit list, or sprint summary.

## Workflow
1. Group changes into categories: Features, Fixes, Improvements, Breaking Changes.
2. For each item, keep wording user-facing and outcome-oriented.
3. Add migration notes for any behavior changes.
4. Add a short "What to test" checklist.

## Output Template
- Version and date
- Highlights (2-4 bullets)
- Detailed changes by category
- Migration/rollback notes
- QA checklist

## Quality Rules
- Prefer impact language ("users can now...") over implementation detail.
- Mark uncertain items with "Needs verification".
