# Copyright (c) 2025, Abhishek and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RaiseaComplaint(Document):


	def before_insert(self):
		self.raised_by = frappe.session.user
		
	def before_save(self):
		# Set resolved details
		if self.status == "Resolved" and not self.resolved_by:
			self.resolved_by = frappe.session.user
			self.resolved_on = frappe.utils.now()

import frappe
from frappe.utils import flt
from frappe.utils.data import escape_html

def r2(x):
    return round(flt(x or 0), 2)

def _badge_colors(status: str):
    s = (status or "").lower()
    if "cancel" in s or "closed" in s:
        return "#FFE5E5", "#B00020"
    if "paid" in s or "completed" in s or "delivered" in s:
        return "#E7F7EE", "#0F7B43"
    if "overdue" in s or "unpaid" in s:
        return "#FFF4E5", "#9A5A00"
    return "#EEF2FF", "#243B8A"

def _field_exists(doctype, fieldname):
    return frappe.get_meta(doctype).has_field(fieldname)

@frappe.whitelist()
def get_order_details_html(order_id):
    """
    ONLY Sales Order
    - Header: 1 query
    - Item totals: 1 query
    - Payments (SO + invoices of this SO): 1 query
    Total DB calls: 3
    """
    if not order_id:
        return {"html": ""}

    doctype = "Sales Order"
    tbl = "`tabSales Order`"

    # ✅ custom fieldnames (change if yours are different)
    payment_status_field = "custom_payment_status"
    dispatch_status_field = "custom_dispatch_status"

    # -----------------------------------------
    # 1) Header query (dynamic select)
    # -----------------------------------------
    base_fields = [
        "name",
        "customer",
        "customer_name",
        "customer_group",
        "status",
        "transaction_date",
        "delivery_date",
        "net_total",
        "total_taxes_and_charges",
        "grand_total",
    ]

    if _field_exists(doctype, payment_status_field):
        base_fields.append(payment_status_field)
    if _field_exists(doctype, dispatch_status_field):
        base_fields.append(dispatch_status_field)

    select_cols = ", ".join([f"`{f}`" for f in base_fields])

    so_rows = frappe.db.sql(
        f"""
        SELECT {select_cols}
        FROM {tbl}
        WHERE name = %s AND docstatus != 2
        LIMIT 1
        """,
        (order_id,),
        as_dict=True,
    )

    if not so_rows:
        return {"html": ""}

    so = so_rows[0]

    order_no = so.get("name")
    customer = so.get("customer") or ""
    customer_name = so.get("customer_name") or ""
    customer_group = so.get("customer_group") or ""
    status = so.get("status") or ""
    posting_date = so.get("transaction_date") or ""
    delivery_date = so.get("delivery_date") or ""

    payment_status = so.get(payment_status_field) if payment_status_field in so else ""
    dispatch_status = so.get(dispatch_status_field) if dispatch_status_field in so else ""

    net_total = r2(so.get("net_total"))
    taxes_and_charges = r2(so.get("total_taxes_and_charges"))
    grand_total = r2(so.get("grand_total"))

    # -----------------------------------------
    # 2) Items totals (count + qty)
    # -----------------------------------------
    item_totals = frappe.db.sql(
        """
        SELECT
            COUNT(*) AS total_items,
            SUM(qty) AS total_qty
        FROM `tabSales Order Item`
        WHERE parent = %s
        """,
        (order_no,),
        as_dict=True,
    )[0]

    total_items = int(item_totals.get("total_items") or 0)
    total_qty = r2(item_totals.get("total_qty") or 0)

    # -----------------------------------------
    # 3) Payments summary (SO + payments of invoices made from this SO)
    # -----------------------------------------
    pay = frappe.db.sql(
        """
        SELECT
            SUM(t.amount)       AS received,
            MAX(t.posting_date) AS last_payment_date
        FROM (
            -- Payments directly against Sales Order
            SELECT
                per.allocated_amount AS amount,
                pe.posting_date      AS posting_date
            FROM `tabPayment Entry Reference` per
            JOIN `tabPayment Entry` pe
              ON pe.name = per.parent
             AND pe.docstatus = 1
             AND pe.party_type = 'Customer'
            WHERE per.reference_doctype = 'Sales Order'
              AND per.reference_name = %(so)s

            UNION ALL

            -- Payments against Sales Invoices created from this Sales Order
            SELECT
                per.allocated_amount AS amount,
                pe.posting_date      AS posting_date
            FROM `tabSales Invoice Item` sii
            JOIN `tabSales Invoice` si
              ON si.name = sii.parent
             AND si.docstatus = 1
            JOIN `tabPayment Entry Reference` per
              ON per.reference_doctype = 'Sales Invoice'
             AND per.reference_name = si.name
            JOIN `tabPayment Entry` pe
              ON pe.name = per.parent
             AND pe.docstatus = 1
             AND pe.party_type = 'Customer'
            WHERE sii.sales_order = %(so)s
        ) t
        """,
        {"so": order_no},
        as_dict=True,
    )[0]

    received = r2(pay.get("received") or 0)
    last_payment_date = pay.get("last_payment_date")
    pending = r2(max(grand_total - received, 0))

    badge_bg, badge_fg = _badge_colors(status)

    def esc(x):
        return escape_html(str(x or ""))

    html = f"""
    <div style="border:1px solid #e6e6e6;border-radius:12px;padding:14px;background:#fff;">

        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px;">
            <div>
                <div style="font-size:16px;font-weight:800;">{esc(order_no)}</div>
            </div>

            <div style="padding:6px 10px;border-radius:999px;background:{badge_bg};color:{badge_fg};
                        font-weight:800;font-size:12px;white-space:nowrap;">
                {esc(status)}
            </div>
        </div>

        <!-- Customer row -->
        <div style="display:flex;justify-content:space-between;gap:10px;margin-top:10px;
                    border:1px solid #eee;background:#fafafa;border-radius:10px;padding:10px;">
            <div style="font-size:13px;"><b>Customer:</b> {esc(customer_name or customer)}</div>
            <div style="font-size:13px;"><b>Group:</b> {esc(customer_group) or "-"}</div>
        </div>

        <!-- Date row -->
        <div style="display:flex;justify-content:space-between;gap:10px;margin-top:10px;
                    border:1px solid #eee;background:#fafafa;border-radius:10px;padding:10px;">
            <div style="font-size:13px;"><b>Date:</b> {esc(posting_date) or "-"}</div>
            <div style="font-size:13px;"><b>Delivery Date:</b> {esc(delivery_date) or "-"}</div>
        </div>

        <!-- Payment + Dispatch -->
        <div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:12px;">
            <div style="background:#fafafa;border:1px solid #eee;border-radius:10px;padding:10px;">
                <div style="font-size:12px;color:#666;">Payment Status</div>
                <div style="font-size:14px;font-weight:800;">{esc(payment_status) or "-"}</div>
            </div>
            <div style="background:#fafafa;border:1px solid #eee;border-radius:10px;padding:10px;">
                <div style="font-size:12px;color:#666;">Dispatch Status</div>
                <div style="font-size:14px;font-weight:800;">{esc(dispatch_status) or "-"}</div>
            </div>
        </div>

        <!-- Totals -->
        <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:12px;">
            <div style="background:#fafafa;border:1px solid #eee;border-radius:10px;padding:10px;">
                <div style="font-size:12px;color:#666;">Total Items</div>
                <div style="font-size:14px;font-weight:800;">{total_items}</div>
            </div>
            <div style="background:#fafafa;border:1px solid #eee;border-radius:10px;padding:10px;">
                <div style="font-size:12px;color:#666;">Total Qty</div>
                <div style="font-size:14px;font-weight:800;">{total_qty}</div>
            </div>
            <div style="background:#fafafa;border:1px solid #eee;border-radius:10px;padding:10px;">
                <div style="font-size:12px;color:#666;">Net Total</div>
                <div style="font-size:14px;font-weight:800;">₹ {net_total:,.2f}</div>
            </div>
        </div>

        <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:10px;">
            <div style="background:#fafafa;border:1px solid #eee;border-radius:10px;padding:10px;">
                <div style="font-size:12px;color:#666;">Taxes & Charges</div>
                <div style="font-size:14px;font-weight:800;">₹ {taxes_and_charges:,.2f}</div>
            </div>
            <div style="background:#fafafa;border:1px solid #eee;border-radius:10px;padding:10px;">
                <div style="font-size:12px;color:#666;">Grand Total</div>
                <div style="font-size:14px;font-weight:800;">₹ {grand_total:,.2f}</div>
            </div>
            <div style="background:#fafafa;border:1px solid #eee;border-radius:10px;padding:10px;">
                <div style="font-size:12px;color:#666;">Payments (Received)</div>
                <div style="font-size:14px;font-weight:800;">₹ {received:,.2f}</div>
            </div>
        </div>

        <div style="margin-top:10px;background:#fff7ed;border:1px solid #fed7aa;border-radius:10px;padding:10px;">
            <div style="font-size:12px;color:#9a3412;">Pending</div>
            <div style="font-size:14px;font-weight:900;color:#9a3412;">₹ {pending:,.2f}</div>
        </div>

    </div>
    """

    return {
        "html": html,
        "totals": {
            "total_items": total_items,
            "total_qty": total_qty,
            "net_total": net_total,
            "taxes_and_charges": taxes_and_charges,
            "grand_total": grand_total,
            "received": received,
            "pending": pending,
            "payment_status": payment_status,
            "dispatch_status": dispatch_status,
            "last_payment_date": last_payment_date,
        },
    }