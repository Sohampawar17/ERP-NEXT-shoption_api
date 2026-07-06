import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now

_MISSING = object()


def build_unique_key(provider, transaction_reference):
	provider = (provider or "").strip().upper()
	transaction_reference = (transaction_reference or "").strip()
	return f"{provider}::{transaction_reference}" if provider and transaction_reference else None


class PaymentWebhookLog(Document):
	def validate(self):
		if not self.received_on:
			self.received_on = now()
		self.last_updated_on = now()
		self.unique_key = build_unique_key(self.provider, self.transaction_reference)


def upsert_payment_webhook_log(
	provider,
	transaction_reference,
	payload=_MISSING,
	status=_MISSING,
	source_doctype=_MISSING,
	source_name=_MISSING,
	external_payment_id=_MISSING,
	processed=_MISSING,
	processed_on=_MISSING,
	error_message=_MISSING,
	payment_entry=_MISSING,
):
	unique_key = build_unique_key(provider, transaction_reference)
	if not unique_key:
		return None

	log_name = frappe.db.get_value("Payment Webhook Log", {"unique_key": unique_key}, "name")
	doc = frappe.get_doc("Payment Webhook Log", log_name) if log_name else frappe.new_doc("Payment Webhook Log")

	doc.provider = (provider or "").strip()
	doc.transaction_reference = (transaction_reference or "").strip()
	doc.unique_key = unique_key

	if payload is not _MISSING:
		doc.payload = payload
	if status is not _MISSING:
		doc.status = status
	if source_doctype is not _MISSING:
		doc.source_doctype = source_doctype
	if source_name is not _MISSING:
		doc.source_name = source_name
	if external_payment_id is not _MISSING:
		doc.external_payment_id = external_payment_id
	if processed is not _MISSING:
		doc.processed = processed
	if processed_on is not _MISSING:
		doc.processed_on = processed_on
	if error_message is not _MISSING:
		doc.error_message = error_message
	if payment_entry is not _MISSING:
		doc.payment_entry = payment_entry

	if log_name:
		doc.save(ignore_permissions=True)
	else:
		doc.insert(ignore_permissions=True)

	return doc.name


def get_payment_webhook_log(provider, transaction_reference):
	unique_key = build_unique_key(provider, transaction_reference)
	if not unique_key:
		return None

	log_name = frappe.db.get_value("Payment Webhook Log", {"unique_key": unique_key}, "name")
	return frappe.get_doc("Payment Webhook Log", log_name) if log_name else None


def validate_duplicate_payment_entry_reference(doc, method=None):
	reference_no = (doc.reference_no or "").strip()
	if not reference_no:
		return

	is_webhook_reference = bool(
		frappe.db.exists("PayU Response", {"txnid": reference_no})
		or frappe.db.exists("Rupifi Webhook Log", {"merchant_payment_ref_id": reference_no})
		or frappe.db.exists("Rupifi Webhook Log", {"payment_id": reference_no})
	)
	if not is_webhook_reference:
		return

	existing_pe = frappe.db.get_value(
		"Payment Entry",
		{
			"name": ["!=", doc.name],
			"reference_no": reference_no,
			"docstatus": ["!=", 2],
		},
		"name",
	)
	if existing_pe:
		frappe.throw(
			_(
				"Payment Entry {0} already exists for webhook reference no {1}."
			).format(existing_pe, reference_no)
		)
