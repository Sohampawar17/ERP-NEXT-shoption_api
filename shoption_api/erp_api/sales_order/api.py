# import frappe
# from frappe.model.document import Document
# from frappe.utils import add_days

# class PurchaseOrder(Document):

#     @frappe.whitelist()
#     def update_payment_term_dates(self):
#         pi_date = self.custom_pi_date
#         lr_date = self.custom_lr_date

#         if not self.payment_schedule:
#             return

#         for row in self.payment_schedule:

#             if row.payment_term == "Some 10% Against PI" and pi_date:
#                 row.due_date = pi_date

#             elif row.payment_term == "Some 10% Against Dispatch LR" and lr_date:
#                 row.due_date = lr_date

#             elif row.payment_term == "Some 10% Against GRN" and lr_date:
#                 row.due_date = add_days(lr_date, 1)

#             elif row.payment_term == "Some 60% Credit Of Days" and lr_date:
#                 row.due_date = add_days(lr_date, 2)

#         # validation bypass (same pattern as dealership)
#         self.flags.ignore_validate = True


import frappe
from frappe.utils import add_days
from frappe.model.document import Document

@frappe.whitelist()
def update_po_payment_term_dates(purchase_order):
    """
    Update Payment Schedule dates based on PI Date & LR Date
    """

    po = frappe.get_doc("Purchase Order", purchase_order)

    pi_date = po.custom_pi_date
    lr_date = po.custom_lr_date

    if not po.payment_schedule:
        return

    for row in po.payment_schedule:

        # 10% Against PI
        if row.payment_term == "Some 10% Against PI" and pi_date:
            row.due_date = pi_date

        # 10% Against Dispatch LR
        elif row.payment_term == "Some 10% Against Dispatch LR" and lr_date:
            row.due_date = lr_date

        # 10% Against GRN (LR + 1)
        elif row.payment_term == "Some 10% Against GRN" and lr_date:
            row.due_date = add_days(lr_date, 1)

        # 60% Credit Of Days (LR + 2)
        elif row.payment_term == "Some 60% Credit Of Days" and lr_date:
            row.due_date = add_days(lr_date, 2)

    # same pattern as dealership
    po.flags.ignore_validate = True
    po.save(ignore_permissions=True)

    return {
        "status": "success",
        "message": "Payment term dates updated successfully"
    }
