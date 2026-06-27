# import frappe
# from shoption_api.erp_api.common import api_auth, require_post, api_response
# from frappe.utils import getdate, nowdate

# @frappe.whitelist(allow_guest=True)
# def get_dealer_dealerships(dealer_id):
#     api_auth()
#     require_post()
#     frappe.set_user("Administrator")

#     if not dealer_id:
#         return api_response(False, "dealer_id is required")

#     today = getdate(nowdate())

#     records = frappe.get_all(
#         "Apply Dealership",
#         filters={"dealer_id": dealer_id},
#         fields=[
#             "name",
#             "dealership_type",
#             "delership_plan",
#             "approval_status",
#             "valid_to"
#         ],
#         order_by="creation desc"
#     )

#     data = []

#     for row in records:

#         # ---------------------------
#         # Remaining Days
#         # ---------------------------
#         remaining_days = None
#         if row.valid_to:
#             remaining_days = (getdate(row.valid_to) - today).days

#         # ---------------------------
#         # Status Badge (Flutter)
#         # ---------------------------
#         is_active = row.approval_status == "Override"

#         data.append({
#             "docname": row.name,
#             "dealership_type": row.dealership_type,
#             "plan_name": row.delership_plan,   # already name
#             "approval_status": row.approval_status,
#             "valid_to": row.valid_to,
#             "remaining_days": remaining_days,
#             "status_label": "Active" if is_active else "Pending For Review"
#         })

#     return api_response(True, "Dealer dealerships fetched", data)


# updated 
import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response
from frappe.utils import getdate, nowdate

@frappe.whitelist(allow_guest=True)
def get_dealer_dealerships(dealer_id):
    api_auth()
    require_post()
    frappe.set_user("Administrator")

    if not dealer_id:
        return api_response(False, "dealer_id is required")

    today = getdate(nowdate())

    records = frappe.get_all(
        "Apply Dealership",
        filters={"dealer_id": dealer_id,"docstatus":["!=",2]},
        fields=[
            "name",
            "dealership_type",
            "dealership_plan_name as delership_plan",
            "approval_status",
            "valid_to",
            "plan_deposit_amount",
            "first_order_value"
        ],
        order_by="creation desc"
    )

    data = []

    for row in records:

        # ---------------------------
        # Remaining Days
        # ---------------------------
        remaining_days = None
        if row.valid_to:
            remaining_days = (getdate(row.valid_to) - today).days

        # ---------------------------
        # STATUS LABEL LOGIC (3 STATES)
        # ---------------------------
        if row.approval_status == "Pending for Review":
            status_label = "Pending for Review"

        elif row.approval_status == "Active":
            status_label = "Active"

        else:
            # Pending for Activation, Pending for Approval, Override (before Active)
            status_label = "Pending for Activation"

        data.append({
            "docname": row.name,
            "dealership_type": row.dealership_type,
            "plan_name": row.delership_plan,
            "approval_status": row.approval_status,
            "valid_to": row.valid_to,
            "remaining_days": remaining_days,
            "status_label": status_label,
            "first_order_value" : row.first_order_value,
            "plan_deposit_amount" : row.plan_deposit_amount
        })

    return api_response(True, "Dealer dealerships fetched", data)
