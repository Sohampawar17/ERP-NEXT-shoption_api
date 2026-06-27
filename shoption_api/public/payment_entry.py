import frappe
from frappe.utils import flt

def update_sales_order_from_payment(doc, method):
    """
    Update Sales Order payment status
    whenever Payment Entry is submitted or cancelled
    """

    for ref in doc.references:
        if ref.reference_doctype != "Sales Order":
            continue

        so = frappe.get_doc("Sales Order", ref.reference_name)

        advance_paid = flt(so.advance_paid)

        # Prefer rounded_total if available
        total_amount = (
            flt(so.rounded_total)
            if flt(so.rounded_total) > 0
            else flt(so.grand_total)
        )

        # ✅ tolerance to avoid float precision issue
        tolerance = 1

        if advance_paid <= tolerance:
            status = "Unpaid"
        elif advance_paid + tolerance < total_amount:
            status = "Partially Paid"
        else:
            status = "Fully Paid"

        # Avoid unnecessary DB update
        if so.custom_payment_status == status:
            continue

        frappe.db.set_value(
            "Sales Order",
            so.name,
            "custom_payment_status",
            status,
            update_modified=False
        )
