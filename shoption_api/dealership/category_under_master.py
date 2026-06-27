import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response

@frappe.whitelist(allow_guest=True)
def get_dealership_category_list(dealership_type=None):

    api_auth()
    require_post()

    if not dealership_type:
        return api_response(False, "dealership_type is required")

    # Mapping dealership type to category filter
    category_filter_map = {
        "Gbru Consumable Dealership": "Consumable",
        "Gbru KSK Dealership": "KSK",
        "Gbru Machinery Dealership": "Machinery"
    }

    category_filter = category_filter_map.get(dealership_type)

    if not category_filter:
        return api_response(False, "Invalid dealership_type")

    # Fetch Dealership Category records
    records = frappe.get_all(
        "Dealership Category",
        filters={
            "dealership_category_name": ["like", f"%{category_filter}%"]
        },
        fields=[
            "name as id",
            "dealership_category_name",
            "brand",
            "category",
            "sub_category"
        ],
        order_by="creation desc"
    )

    return api_response(
        True,
        "Dealership categories fetched successfully",
        {
            "dealership_type": dealership_type,
            "total": len(records),
            "data": records
        }
    )
