import frappe


UTR_SOURCE_CONFIG = (
    {
        "doctype": "Bank Transfer Request",
        "fieldname": "utr_number",
        "status_condition": "docstatus != 2 AND IFNULL(status, '') NOT IN ('Rejected', 'Cancelled')",
    },
    {
        "doctype": "Deposit Amount Payment Approal",
        "fieldname": "utr__check_no",
        "status_condition": "docstatus != 2",
    },
    {
        "doctype": "Van Payment Reconciliation",
        "fieldname": "utr_no",
        "status_condition": "docstatus != 2",
    },
)


def normalize_utr(value):
    return (value or "").strip()


def get_duplicate_utr_record(utr_number, current_doctype=None, current_name=None):
    normalized_utr = normalize_utr(utr_number)
    if not normalized_utr:
        return None

    for config in UTR_SOURCE_CONFIG:
        duplicate = frappe.db.sql(
            f"""
            SELECT %s AS doctype_name, name
            FROM `tab{config["doctype"]}`
            WHERE {config["status_condition"]}
              AND TRIM(IFNULL({config["fieldname"]}, '')) = %s
              AND (%s != %s OR %s IS NULL OR name != %s)
            LIMIT 1
            """,
            (
                config["doctype"],
                normalized_utr,
                current_doctype,
                config["doctype"],
                current_name,
                current_name,
            ),
            as_dict=True,
        )
        if duplicate:
            return duplicate[0]

    return None


def validate_unique_utr_number(utr_number, current_doctype=None, current_name=None):
    duplicate = get_duplicate_utr_record(
        utr_number=utr_number,
        current_doctype=current_doctype,
        current_name=current_name,
    )
    if not duplicate:
        return

    frappe.throw(
        "UTR Number already exists in {0}: {1}".format(
            duplicate.doctype_name,
            duplicate.name,
        )
    )
