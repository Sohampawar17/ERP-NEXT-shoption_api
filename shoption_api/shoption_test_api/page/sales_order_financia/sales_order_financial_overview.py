import frappe
from frappe import _
from frappe.utils import flt
DISPATCH_STATUS_INVOICED = "Invoiced"
DISPATCH_STATUS_PRINT_STICKERS = "Print Stickers"
DISPATCH_STATUS_PACKING_OK = "Packing OK"
DISPATCH_STATUS_OUTWARD = "Outward"
DISPATCH_STATUS_UPLOAD_LR = "Upload LR Main"
DISPATCH_STATUS_DISPATCHED = "Dispatched"
DISPATCH_STATUS_DELIVERED = "Delivered"

def _normalize_text(value):
    return (value or "").strip().lower()


def _is_sticker_based_invoice(invoice_row):
    return (
        _normalize_text(invoice_row.get("customer_group")) == "farmer"
        and _normalize_text(invoice_row.get("transporter_name")) == "indian post"
    )


def _get_dealer_shop_name(customer):
    if not customer:
        return ""
    cust = frappe.db.get_value(
        "Customer",
        customer,
        ["customer_group", "custom_document_value", "customer_name"],
        as_dict=True,
    )
    if not cust:
        return ""
    if (cust.customer_group or "").strip().lower() != "dealer":
        return ""
    if not cust.custom_document_value:
        return cust.customer_name or ""
    shop_name = frappe.db.get_value(
        "Dealer Registration",
        cust.custom_document_value,
        "shop_name",
    )
    return shop_name or (cust.customer_name or "")


@frappe.whitelist()
def get_sales_order_financial_data(sales_order):
    if not sales_order:
        frappe.throw(_("Sales Order is required"))

    if not frappe.db.exists("Sales Order", sales_order):
        frappe.throw(_("Sales Order {0} not found").format(frappe.bold(sales_order)))

    so = frappe.db.get_value(
        "Sales Order",
        sales_order,
        [
            "name",
            "transaction_date",
            "delivery_date",
            "customer",
            "customer_name",
            "grand_total",
            "rounded_total",
            "advance_paid",
            "per_billed",
            "per_delivered",
            "status",
            "currency",
            "company",
            "custom_dispatch_status",
            "custom_payment_type",
            "custom_coupon_code_for_discount",
            "discount_amount",
            "custom_coupon_discount_amount",
        ],
        as_dict=True,
    )

    customer_group = None
    territory = None
    if so.customer:
        customer_group, territory = frappe.db.get_value(
            "Customer", so.customer, ["customer_group", "territory"]
        ) or (None, None)
    so.customer_group = customer_group
    so.territory = territory
    so.shop_name = _get_dealer_shop_name(so.customer) if (so.customer_group or "").strip().lower() == "dealer" else ""

    items = frappe.db.sql(
        """
        SELECT
            soi.name AS sales_order_item,
            soi.item_code,
            soi.item_name,
            soi.description,
            soi.qty,
            soi.delivered_qty,
            soi.uom,
            soi.rate,
            soi.amount,
            soi.delivery_date,
            soi.item_tax_template,
            soi.gst_hsn_code
        FROM `tabSales Order Item` soi
        WHERE soi.parent = %(sales_order)s
        ORDER BY soi.idx ASC
        """,
        {"sales_order": sales_order},
        as_dict=True,
    )

    advance_payments = frappe.db.sql(
        """
        SELECT
            pe.name AS payment_entry,
            'Payment Entry' AS payment_source,
            pe.posting_date,
            pe.party,
            pe.mode_of_payment,
            pe.paid_from,
            pe.paid_to,
            per.allocated_amount,
            pe.received_amount,
            pe.reference_no,
            pe.remarks AS remark
        FROM `tabPayment Entry Reference` per
        INNER JOIN `tabPayment Entry` pe ON pe.name = per.parent
        WHERE per.reference_doctype = 'Sales Order'
            AND per.reference_name = %(sales_order)s
            AND pe.docstatus = 1
            AND pe.payment_type = 'Receive'
        ORDER BY pe.posting_date DESC, pe.creation DESC
        """,
        {"sales_order": sales_order},
        as_dict=True,
    )

    # Include Journal Entries used for order-to-order adjustment as advance.
    adjusted_je_advance = frappe.db.sql(
        """
        SELECT
            je.name AS payment_entry,
            'Journal Entry' AS payment_source,
            je.posting_date,
            '' AS party,
            je.mode_of_payment,
            '' AS paid_from,
            '' AS paid_to,
            jea.credit AS allocated_amount,
            jea.credit AS received_amount,
            '' AS reference_no,
            je.remark AS remark
        FROM `tabJournal Entry` je
        INNER JOIN `tabJournal Entry Account` jea ON je.name = jea.parent
        WHERE je.docstatus = 1
            AND jea.reference_type = 'Sales Order'
            AND jea.reference_name = %(sales_order)s
            AND IFNULL(jea.is_advance, 'No') = 'Yes'
            AND LOWER(IFNULL(je.mode_of_payment, '')) = 'adjusted from one order to another'
        ORDER BY je.posting_date DESC, je.creation DESC
        """,
        {"sales_order": sales_order},
        as_dict=True,
    )
    advance_payments.extend(adjusted_je_advance)

    # Fallback for custom_sales_order-linked PE where explicit SO reference row may be absent.
    pe_custom_so_only = frappe.db.sql(
        """
        SELECT
            pe.name AS payment_entry,
            'Payment Entry' AS payment_source,
            pe.posting_date,
            pe.party,
            pe.mode_of_payment,
            pe.paid_from,
            pe.paid_to,
            IFNULL(pe.received_amount, pe.paid_amount) AS allocated_amount,
            pe.received_amount,
            pe.reference_no,
            pe.reference_date
        FROM `tabPayment Entry` pe
        WHERE pe.custom_sales_order = %(sales_order)s
            AND pe.docstatus = 1
            AND pe.payment_type = 'Receive'
            AND pe.name NOT IN (
                SELECT DISTINCT per.parent
                FROM `tabPayment Entry Reference` per
                WHERE per.reference_doctype = 'Sales Order'
                    AND per.reference_name = %(sales_order)s
            )
        ORDER BY pe.posting_date DESC, pe.creation DESC
        """,
        {"sales_order": sales_order},
        as_dict=True,
    )
    advance_payments.extend(pe_custom_so_only)

    invoices = frappe.db.sql(
        """
        SELECT DISTINCT
            si.name AS invoice,
            si.posting_date,
            si.customer,
            si.customer_name,
            si.grand_total,
            si.rounded_total,
            si.outstanding_amount,
            si.status,
            si.currency,
            si.custom_dispatch_status,
            si.customer_group,
            si.transporter_name,
             CASE
        WHEN IFNULL(si.custom_is_van_invoice, 0) = 1 THEN 'Yes'
        ELSE 'No'
    END AS is_van_invoice
        FROM `tabSales Invoice Item` sii
        INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE sii.sales_order = %(sales_order)s
            AND si.docstatus = 1
        ORDER BY si.posting_date DESC, si.creation DESC
        """,
        {"sales_order": sales_order},
        as_dict=True,
    )

    invoice_names = [row.invoice for row in invoices]

    pko_map = {}
    lr_map = {}
    shipment_map = {}
    sticker_count_map = {}

    if invoice_names:
        if frappe.db.exists("DocType", "Packing OK Slip"):
            pko_rows = frappe.get_all(
                "Packing OK Slip",
                filters={"sales_invoice": ["in", invoice_names], "docstatus": 1},
                fields=["name", "sales_invoice", "no_of_boxes"],
                order_by="creation desc",
            )
            for row in pko_rows:
                if row.sales_invoice and row.sales_invoice not in pko_map:
                    pko_map[row.sales_invoice] = row

        if frappe.db.exists("DocType", "Upload LR Main"):
            lr_rows = frappe.get_all(
                "Upload LR Main",
                filters={"sales_invoice": ["in", invoice_names], "docstatus": ["!=", 2]},
                fields=["name", "sales_invoice"],
                order_by="creation desc",
            )
            for row in lr_rows:
                if row.sales_invoice and row.sales_invoice not in lr_map:
                    lr_map[row.sales_invoice] = row

        if frappe.db.exists("DocType", "Shipment"):
            shipment_rows = frappe.get_all(
                "Shipment",
                filters={"custom_sales_invoice": ["in", invoice_names], "docstatus": ["!=", 2]},
                fields=["name", "custom_sales_invoice"],
                order_by="creation desc",
            )
            for row in shipment_rows:
                if row.custom_sales_invoice and row.custom_sales_invoice not in shipment_map:
                    shipment_map[row.custom_sales_invoice] = row

        if frappe.db.exists("DocType", "Indian Post Tracking Log"):
            sticker_rows = frappe.db.sql(
                """
                SELECT
                    reference_name AS invoice,
                    COUNT(name) AS sticker_logs_count
                FROM `tabIndian Post Tracking Log`
                WHERE reference_type = 'Sales Invoice'
                    AND reference_name IN %(invoice_names)s
                    AND IFNULL(is_cancelled, 0) = 0
                    AND docstatus != 2
                GROUP BY reference_name
                """,
                {"invoice_names": tuple(invoice_names)},
                as_dict=True,
            )
            sticker_count_map = {d.invoice: flt(d.sticker_logs_count) for d in sticker_rows}

    for invoice in invoices:
        inv_name = invoice.get("invoice")
        is_sticker_based = _is_sticker_based_invoice(invoice)
        pko = pko_map.get(inv_name)
        lr = lr_map.get(inv_name)
        shipment = shipment_map.get(inv_name)

        sticker_logs_count = int(sticker_count_map.get(inv_name, 0))
        if is_sticker_based:
            sticker_print_status = "Done" if sticker_logs_count > 0 else "Pending"
        else:
            sticker_print_status = "Not Required"
        dispatch_status = invoice.get("custom_dispatch_status")

        if dispatch_status == DISPATCH_STATUS_INVOICED:
            pending_stage = "Invoiced - Pending Dispatch"

        elif dispatch_status == DISPATCH_STATUS_PRINT_STICKERS:
            pending_stage = "Waiting for Sticker Printing Completion"

        elif dispatch_status == DISPATCH_STATUS_PACKING_OK:
            pending_stage = "Waiting for Packing Ok"

        elif dispatch_status == DISPATCH_STATUS_OUTWARD:
            pending_stage = "Waiting for Outward"

        elif dispatch_status == DISPATCH_STATUS_UPLOAD_LR:
            pending_stage = "Waiting to be Upload LR Main"

        elif dispatch_status == DISPATCH_STATUS_DISPATCHED:
            pending_stage = "Waiting for Delivery Confirmation"

        elif dispatch_status == DISPATCH_STATUS_DELIVERED:
            pending_stage = "Completed"

        else:
            pending_stage = dispatch_status

        invoice["pending_stage"] = pending_stage
        invoice["is_sticker_based"] = is_sticker_based
        invoice["sticker_logs_count"] = sticker_logs_count
        invoice["sticker_print_status"] = sticker_print_status
        invoice["packing_ok_slip"] = pko.name if pko else ""
        invoice["packing_ok_boxes"] = flt(pko.no_of_boxes) if pko else 0
        invoice["lr_number"] = lr.name if lr else ""
        invoice["shipment"] = shipment.name if shipment else ""

    invoice_payments = []
    if invoice_names:
        invoice_payments = frappe.db.sql(
            """
            SELECT
                per.reference_name AS invoice,
                pe.name AS payment_entry,
                'Payment Entry' AS payment_source,
                pe.posting_date,
                pe.party,
                pe.mode_of_payment,
                pe.paid_from,
                pe.paid_to,
                per.allocated_amount,
                pe.received_amount,
                pe.reference_no,
                pe.reference_date
            FROM `tabPayment Entry Reference` per
            INNER JOIN `tabPayment Entry` pe ON pe.name = per.parent
            WHERE per.reference_doctype = 'Sales Invoice'
                AND per.reference_name IN %(invoice_names)s
                AND pe.docstatus = 1
                AND pe.payment_type = 'Receive'
            ORDER BY pe.posting_date DESC, pe.creation DESC
            """,
            {"invoice_names": tuple(invoice_names)},
            as_dict=True,
        )

        # Include Journal Entries that are directly referenced against Sales Invoices.
        je_invoice_payments = frappe.db.sql(
            """
            SELECT
                jea.reference_name AS invoice,
                je.name AS payment_entry,
                'Journal Entry' AS payment_source,
                je.posting_date,
                '' AS party,
                je.mode_of_payment,
                '' AS paid_from,
                '' AS paid_to,
                jea.credit AS allocated_amount,
                jea.credit AS received_amount,
                '' AS reference_no,
                je.posting_date AS reference_date
            FROM `tabJournal Entry` je
            INNER JOIN `tabJournal Entry Account` jea ON je.name = jea.parent
            WHERE je.docstatus = 1
                AND jea.reference_type = 'Sales Invoice'
                AND jea.reference_name IN %(invoice_names)s
                AND jea.credit > 0
            ORDER BY je.posting_date DESC, je.creation DESC
            """,
            {"invoice_names": tuple(invoice_names)},
            as_dict=True,
        )
        invoice_payments.extend(je_invoice_payments)

        # Include Sales Order advances allocated at invoice level.
        so_advance_allocations = frappe.db.sql(
            """
            SELECT
                sia.parent AS invoice,
                sia.reference_name AS payment_entry,
                'Sales Order Advance Allocation' AS payment_source,
                si.posting_date,
                '' AS party,
                'Advance Allocated' AS mode_of_payment,
                '' AS paid_from,
                '' AS paid_to,
                sia.allocated_amount AS allocated_amount,
                sia.allocated_amount AS received_amount,
                '' AS reference_no,
                si.posting_date AS reference_date
            FROM `tabSales Invoice Advance` sia
            INNER JOIN `tabSales Invoice` si ON si.name = sia.parent
            WHERE sia.parent IN %(invoice_names)s
                AND sia.reference_type = 'Sales Order'
                AND IFNULL(sia.allocated_amount, 0) > 0
            ORDER BY si.posting_date DESC, sia.creation DESC
            """,
            {"invoice_names": tuple(invoice_names)},
            as_dict=True,
        )
        invoice_payments.extend(so_advance_allocations)

    so_advance_paid_total = sum(flt(d.allocated_amount or 0) for d in advance_payments)

    refund_requests = []
    refund_credit_notes = []
    if frappe.db.exists("DocType", "Refund Request"):
        refund_requests = frappe.get_all(
            "Refund Request",
            filters={
                "order_doctype": "Sales Order",
                "order_id": sales_order,
                "docstatus": ["!=", 2],
            },
            fields=[
                "name",
                "created_on",
                "requested_refund_amount",
                "paid_amount",
                "refund_mode",
                "workflow_state",
                "journal_entry",
                "target_order",
                "paid_on",
                "customer",
                "customer_name",
            ],
            order_by="creation desc",
        )

        je_names = [r.journal_entry for r in refund_requests if r.get("journal_entry")]
        je_map = {}
        if je_names:
            je_rows = frappe.get_all(
                "Journal Entry",
                filters={"name": ["in", je_names], "docstatus": ["!=", 2]},
                fields=["name", "posting_date", "company", "voucher_type", "remark", "user_remark", "docstatus"],
            )
            je_map = {j.name: j for j in je_rows}

        for rr in refund_requests:
            je = je_map.get(rr.get("journal_entry"))
            je_amount = 0
            if je:
                je_amount = flt(
                    frappe.db.sql(
                        """
                        SELECT SUM(credit_in_account_currency)
                        FROM `tabJournal Entry Account`
                        WHERE parent = %s
                            AND reference_type = 'Sales Order'
                            AND reference_name = %s
                        """,
                        (je.name, sales_order),
                    )[0][0]
                    or 0
                )

    # Include Sales Return / Credit Note only when it is against related Sales Invoices.
    if invoice_names:
        sales_return_rows = frappe.db.sql(
            """
            SELECT
                si.name AS sales_return_invoice,
                si.posting_date,
                si.return_against,
                si.rounded_total,
                si.grand_total,
                si.company,
                si.status,
                si.docstatus
            FROM `tabSales Invoice` si
            WHERE si.is_return = 1
                AND si.docstatus != 2
                AND si.return_against IN %(invoice_names)s
            ORDER BY si.posting_date DESC, si.creation DESC
            """,
            {"invoice_names": tuple(invoice_names)},
            as_dict=True,
        )
        for sr in sales_return_rows:
            refund_credit_notes.append(
                {
                    "entry_type": "Sales Return",
                    "refund_request": "",
                    "journal_entry": "",
                    "sales_return_invoice": sr.sales_return_invoice,
                    "against_sales_invoice": sr.return_against or "",
                    "posting_date": sr.posting_date,
                    "amount": flt(sr.rounded_total or sr.grand_total or 0),
                    "voucher_type": "Credit Note",
                    "company": sr.company,
                    "remark": f"Return Against: {sr.return_against or ''}".strip(),
                    "status": "Submitted" if sr.docstatus == 1 else "Draft",
                }
            )

    totals = {
        "sales_order_total": so.rounded_total or so.grand_total or 0,
        "sales_order_advance_paid": so.advance_paid,
        "invoice_total": sum((d.rounded_total or d.grand_total or 0) for d in invoices),
        "invoice_outstanding_total": sum((d.outstanding_amount or 0) for d in invoices),
        "invoice_payment_allocated_total": sum((d.allocated_amount or 0) for d in invoice_payments),
    }

    return {
        "sales_order": so,
        "totals": totals,
        "items": items,
        "advance_payments": advance_payments,
        "invoices": invoices,
        "invoice_payments": invoice_payments,
        "refund_requests": refund_requests,
        "refund_credit_notes": refund_credit_notes,
    }
