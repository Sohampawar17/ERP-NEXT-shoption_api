import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response
from frappe.utils import get_url


@frappe.whitelist(allow_guest=True)
def get_dealership_plans(dealership_category_name=None, page=1, page_size=20):
    api_auth()
    require_post()
    frappe.set_user("Administrator")

    # -------------------------------
    # Validation
    # -------------------------------
    if not dealership_category_name:
        return api_response(False, "dealership_category_name is required")

    # Safe pagination convert
    try:
        page = int(page)
        page_size = int(page_size)
    except:
        page, page_size = 1, 20

    start = (page - 1) * page_size

    try:
        # -------------------------------
        # Fetch Plans
        # -------------------------------
        plans = frappe.get_list(
            "Dealership Plan",
            filters={"dealership_category_name": dealership_category_name},
            fields=["name", "dealership_category_name", "dealership_plan_name",
                    "plan_description", "plan_logo",
                    "plan_type", "deposite_amount", "plan_coverage",
                    "first_order_value", "annual_target"],
            limit_start=start,
            limit_page_length=page_size,
            order_by="creation desc"
        )

        final_output = []

        for p in plans:
            plan_doc = frappe.get_doc("Dealership Plan", p["name"])

            # -------------------------------
            # Child table safe extraction
            # -------------------------------
            child_rows = []
            for row in plan_doc.get("dealership_plan_range", []):
                child_rows.append({
                    # "no": getattr(row, "no", None),
                    "notation": getattr(row, "notation", None),
                    "value": getattr(row, "value", None),
                    # "in_percentage": getattr(row, "in_percentage", None)
                    "in_percentage": getattr(row, "in__percentage", None)
                })

            # -------------------------------
            # Build full plan response
            # -------------------------------
            final_output.append({
                "dealership_plan_id": p.get("name"),
                "dealership_category_name": p.get("dealership_category_name"),
                "dealership_plan_name": p.get("dealership_plan_name"),
                "plan_description": p.get("plan_description"),
                # "plan_logo": p.get("plan_logo"),
                "plan_logo": get_url(p.get("plan_logo")) if p.get("plan_logo") else None,
                "plan_type": p.get("plan_type"),
                "deposite_amount": p.get("deposite_amount"),
                "plan_coverage": p.get("plan_coverage"),
                "first_order_value": p.get("first_order_value"),
                "annual_target": p.get("annual_target"),
                "dealership_plan_range": child_rows     # always list, even empty
            })

        # -------------------------------
        # Pagination summary
        # -------------------------------
        total = frappe.db.count("Dealership Plan",
            filters={"dealership_category_name": dealership_category_name}
        )

        total_pages = (total + page_size - 1) // page_size

        return api_response(True, "Dealership plans fetched", {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "data": final_output
        })

    except Exception as e:
        # ALWAYS return safe null response — no server error for missing fields
        return api_response(False, f"Error: {str(e)}", {"data": []})
