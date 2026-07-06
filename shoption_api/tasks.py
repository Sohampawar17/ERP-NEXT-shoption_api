import hashlib

import frappe


ALERT_CACHE_KEY = "shoption_api:duplicate_payment_reference_alert_hash"


def check_duplicate_payment_references():
    duplicate_groups = []
    duplicate_groups.extend(
        _get_duplicate_groups(
            doctype="PayU Response",
            reference_field="txnid",
            label="PayU Response",
        )
    )
    duplicate_groups.extend(
        _get_duplicate_groups(
            doctype="Rupifi Webhook Log",
            reference_field="merchant_payment_ref_id",
            label="Rupifi Webhook Log",
        )
    )
    duplicate_groups.extend(
        _get_duplicate_groups(
            doctype="Payment Entry",
            reference_field="reference_no",
            label="Payment Entry",
            extra_condition="AND docstatus != 2",
        )
    )

    if not duplicate_groups:
        frappe.cache().delete_value(ALERT_CACHE_KEY, shared=True)
        return []

    recipients = _get_duplicate_alert_users()
    if not recipients:
        frappe.logger().warning(
            "Duplicate payment references found, but no alert users are configured in Payu Setting."
        )
        return duplicate_groups

    message = _build_alert_message(duplicate_groups)
    alert_hash = hashlib.sha256(message.encode("utf-8")).hexdigest()
    previous_hash = frappe.cache().get_value(ALERT_CACHE_KEY, shared=True)
    if previous_hash == alert_hash:
        return duplicate_groups

    for user in recipients:
        notification = frappe.new_doc("Notification Log")
        notification.for_user = user
        notification.type = "Alert"
        notification.subject = f"Duplicate payment references found ({len(duplicate_groups)} issues)"
        notification.email_content = message
        notification.insert(ignore_permissions=True)

    frappe.cache().set_value(
        ALERT_CACHE_KEY,
        alert_hash,
        shared=True,
        expires_in_sec=60 * 60 * 24 * 30,
    )
    return duplicate_groups


def _get_duplicate_groups(doctype, reference_field, label, extra_condition=""):
    rows = frappe.db.sql(
        f"""
        SELECT
            {reference_field} AS reference_no,
            COUNT(*) AS duplicate_count,
            GROUP_CONCAT(name ORDER BY modified DESC SEPARATOR ', ') AS document_names
        FROM `tab{doctype}`
        WHERE COALESCE(TRIM({reference_field}), '') != ''
            {extra_condition}
        GROUP BY {reference_field}
        HAVING COUNT(*) > 1
        ORDER BY COUNT(*) DESC, {reference_field} ASC
        """,
        as_dict=True,
    ) or []

    for row in rows:
        row["doctype"] = doctype
        row["label"] = label

    return rows


def _get_duplicate_alert_users():
    users = []
    for fieldname in ("duplicate_alert_user_1", "duplicate_alert_user_2"):
        user = frappe.db.get_single_value("Payu Setting", fieldname)
        if not user or user in users:
            continue

        enabled = frappe.db.get_value("User", user, "enabled")
        if enabled:
            users.append(user)

    return users


def _build_alert_message(duplicate_groups):
    lines = ["Duplicate payment references were found:"]

    for row in duplicate_groups:
        lines.append(
            "{label}: reference `{reference_no}` appears {duplicate_count} times in {document_names}".format(
                label=row.get("label") or row.get("doctype") or "",
                reference_no=row.reference_no,
                duplicate_count=int(row.duplicate_count or 0),
                document_names=row.document_names,
            )
        )

    return "\n".join(lines)
