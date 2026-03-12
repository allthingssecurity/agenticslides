"""
SAP Tools + Shared Config for the Durable Agent Demo
=====================================================
Simulated SAP systems (MM, FI/CO, BP) used by both
sap_step1_process.py and sap_step2_recover.py.
"""

import json
import random

from langchain_core.tools import tool


THREAD_ID = "sap-po-session-1"
STORE_NAME = "agentstore"

SAP_SYSTEM_PROMPT = """You are an SAP Procurement Agent that helps process purchase requests.

You have access to these SAP systems:
- **SAP MM** (Materials Management): Check materials, stock levels, create POs
- **SAP FI/CO** (Finance/Controlling): Check budgets by cost center
- **SAP BP** (Business Partner): Check vendor status and details

## Your Workflow for Purchase Requests:
1. Check the vendor status (is vendor active?)
2. Check material details and current stock
3. Check budget availability for the cost center
4. If everything checks out, create the purchase order
5. Summarize: what was ordered, from whom, PO number, approval status

## Important:
- Always verify vendor is ACTIVE before ordering
- Always check budget BEFORE creating PO
- Flag any issues: low stock, over-budget, inactive vendor
- Be specific with SAP document numbers
"""


@tool
def sap_check_vendor(vendor_id: str) -> str:
    """Check vendor status and details in SAP S/4HANA.

    Args:
        vendor_id: SAP vendor number (e.g. "V-10001")
    """
    vendors = {
        "V-10001": {
            "name": "Acme Industrial Supplies",
            "status": "ACTIVE",
            "payment_terms": "Net 30",
            "currency": "EUR",
            "country": "DE",
            "credit_rating": "A+",
            "ytd_spend": "€2.4M",
        },
        "V-10002": {
            "name": "Global Tech Components",
            "status": "ACTIVE",
            "payment_terms": "Net 45",
            "currency": "USD",
            "country": "US",
            "credit_rating": "A",
            "ytd_spend": "$890K",
        },
    }
    v = vendors.get(vendor_id)
    if v:
        return json.dumps(v, indent=2)
    return f"Error: Vendor {vendor_id} not found in SAP"


@tool
def sap_check_material(material_id: str) -> str:
    """Look up material/product details and stock in SAP MM.

    Args:
        material_id: SAP material number (e.g. "MAT-5001")
    """
    materials = {
        "MAT-5001": {
            "description": "Industrial Servo Motor 500W",
            "plant": "Plant 1000 (Munich)",
            "stock": 12,
            "unit": "EA",
            "price": "€1,250.00",
            "mrp_type": "PD (MRP)",
            "lead_time_days": 14,
            "last_po": "PO-4500012345",
        },
        "MAT-5002": {
            "description": "Hydraulic Valve Assembly HV-200",
            "plant": "Plant 1000 (Munich)",
            "stock": 3,
            "unit": "EA",
            "price": "€680.00",
            "mrp_type": "PD (MRP)",
            "lead_time_days": 21,
            "last_po": "PO-4500012200",
        },
        "MAT-5003": {
            "description": "PLC Controller Module X7",
            "plant": "Plant 2000 (Berlin)",
            "stock": 0,
            "unit": "EA",
            "price": "€3,400.00",
            "mrp_type": "PD (MRP)",
            "lead_time_days": 28,
            "last_po": "PO-4500011990",
        },
    }
    m = materials.get(material_id)
    if m:
        return json.dumps(m, indent=2)
    return f"Error: Material {material_id} not found in SAP"


@tool
def sap_create_purchase_order(
    vendor_id: str, material_id: str, quantity: int, notes: str = ""
) -> str:
    """Create a purchase order in SAP MM.

    Args:
        vendor_id: SAP vendor number
        material_id: SAP material number
        quantity: Order quantity
        notes: Optional notes for the PO
    """
    po_number = f"PO-450001{random.randint(3000, 9999)}"
    return json.dumps({
        "status": "CREATED",
        "po_number": po_number,
        "vendor": vendor_id,
        "material": material_id,
        "quantity": quantity,
        "notes": notes,
        "approval_status": "PENDING_APPROVAL",
        "message": f"Purchase order {po_number} created. Pending manager approval.",
    }, indent=2)


@tool
def sap_check_budget(cost_center: str, amount: float) -> str:
    """Check available budget for a cost center in SAP CO.

    Args:
        cost_center: SAP cost center (e.g. "CC-4100")
        amount: Amount to check against budget
    """
    budgets = {
        "CC-4100": {"name": "Manufacturing Ops", "budget": 500000, "spent": 320000, "currency": "EUR"},
        "CC-4200": {"name": "R&D Engineering", "budget": 750000, "spent": 680000, "currency": "EUR"},
    }
    b = budgets.get(cost_center)
    if not b:
        return f"Error: Cost center {cost_center} not found"
    available = b["budget"] - b["spent"]
    sufficient = "YES" if amount <= available else "NO — OVER BUDGET"
    return json.dumps({
        "cost_center": cost_center,
        "name": b["name"],
        "total_budget": f"€{b['budget']:,.0f}",
        "spent_ytd": f"€{b['spent']:,.0f}",
        "available": f"€{available:,.0f}",
        "requested": f"€{amount:,.0f}",
        "sufficient": sufficient,
    }, indent=2)


SAP_TOOLS = [sap_check_vendor, sap_check_material, sap_create_purchase_order, sap_check_budget]
