import frappe
from frappe.utils import flt, getdate, nowdate
# from warrior.public.sales_order import _get_paid_amount_for_sales_order

def update_payment_status(doc, method=None):
    """
    Update payment status based on paid amount with ₹1 tolerance
    """

    tolerance = 1  # ₹1 tolerance
    paid_amount = flt(doc.advance_paid)
    # paid_amount = flt(_get_paid_amount_for_sales_order(doc.name)) or 0
    grand_total = flt(doc.rounded_total or doc.grand_total or 0)

    pending_amount = round(grand_total - paid_amount, 2)

    if paid_amount <= 0:
        status = "Unpaid"
    elif pending_amount <= tolerance:
        status = "Fully Paid"
    else:
        status = "Partially Paid"

    # Avoid recursion
    if doc.custom_payment_status != status:
        frappe.db.set_value(
            "Sales Order",
            doc.name,
            "custom_payment_status",
            status,
            update_modified=False
        )