import frappe
import wrapt
from bs4 import BeautifulSoup
from frappe.utils import cstr
from collections import defaultdict
import json
from frappe.utils import (
    formatdate,
    nowdate,
    add_months,
    get_first_day,
    getdate,
    now,
    get_datetime
)
from shoption_api.cart.app_utils import generate_key


def gen_response(status, message, data=[]):
    frappe.response["http_status_code"] = status
    if status == 500:
        frappe.response["message"] = BeautifulSoup(str(message)).get_text()
    else:
        frappe.response["message"] = message
    frappe.response["data"] = data

def validate_method(methods):
    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        if frappe.local.request.method not in methods:
            return gen_response(500, "Invalid Request Method")
        return wrapped(*args, **kwargs)

    return wrapper

@frappe.whitelist(allow_guest=True)
def get_user_details(customer_id=None):
    # =====================================================
    # BASIC VALIDATION
    # =====================================================
    if not customer_id:
        return {
            "success": False,
            "message": "Customer ID is mandatory."
        }

    # =====================================================
    # FETCH USER DETAILS
    # =====================================================
    user_details = frappe.db.get_value(
        "User",
        {"username": customer_id},
        ["name", "mobile_no"],
        as_dict=True
    )

    if not user_details:
        return {
            "success": False,
            "message": "User not found."
        }

    # =====================================================
    # GENERATE API KEY / SECRET
    # =====================================================
    key_details = generate_key(user_details.name)

    # =====================================================
    # SUCCESS RESPONSE
    # =====================================================
    return {
        "success": True,
        "user": user_details.name,
        "mobile_no": user_details.mobile_no or "",
        "key_details": key_details
    }


@frappe.whitelist()
@validate_method(["GET"])
def get_customer_gmv(merchant_customer_ref_id):
    try:
        # --------------------------------------------------
        # Debug: Log headers & body
        # --------------------------------------------------
        headers = dict(frappe.local.request.headers)
        body = frappe.local.form_dict if hasattr(frappe.local, "form_dict") else {}

        # --------------------------------------------------
        # Validation
        # --------------------------------------------------
        if not merchant_customer_ref_id:
            return {
                "success": False,
                "message": "merchant_customer_ref_id is required"
            }

        # --------------------------------------------------
        # Date range: last 6 months (including current)
        # --------------------------------------------------
        to_date = nowdate()
        from_date = get_first_day(add_months(to_date, -5))

        # --------------------------------------------------
        # Fetch User
        # --------------------------------------------------
        user_details = frappe.db.get_value(
            "User",
            {"username": merchant_customer_ref_id},
            ["name", "mobile_no"],
            as_dict=True
        )

        if not user_details:
            return {
                "success": False,
                "message": "User not found"
            }

        # --------------------------------------------------
        # Fetch Customer via Portal User
        # --------------------------------------------------
        customer_id = frappe.db.get_value(
            "Portal User",
            {"user": user_details.name},
            "parent"
        )

        if not customer_id:
            return {
                "success": False,
                "message": "Customer not linked"
            }

        customer = frappe.db.get_value(
            "Customer",
            customer_id,
            ["name", "mobile_no"],
            as_dict=True
        )

        if not customer:
            return {
                "success": False,
                "message": "Customer not found"
            }

        # --------------------------------------------------
        # Fetch successful Payment Entries
        # --------------------------------------------------
        payment_entries = frappe.db.get_all(
            "Payment Entry",
            filters={
                "party_type": "Customer",
                "party": merchant_customer_ref_id,
                "docstatus": 1,
                "posting_date": ["between", [from_date, to_date]]
            },
            fields=["name", "posting_date", "received_amount", "paid_amount"]
        )

        # --------------------------------------------------
        # Prepare month list (ALWAYS 6 months)
        # --------------------------------------------------
        months = []
        current = get_first_day(from_date)
        end = get_first_day(to_date)

        while current <= end:
            months.append(formatdate(current, "MMM-yyyy"))
            current = add_months(current, 1)

        # --------------------------------------------------
        # GMV aggregation
        # --------------------------------------------------
        gmv_map = defaultdict(float)
        order_map = defaultdict(set)
        transaction_dates = []

        if payment_entries:
            pe_names = [pe.name for pe in payment_entries]

            references = frappe.db.get_all(
                "Payment Entry Reference",
                filters={
                    "parent": ["in", pe_names],
                    "reference_doctype": "Sales Order"
                },
                fields=["parent", "reference_name"]
            )

            pe_date_map = {pe.name: pe.posting_date for pe in payment_entries}

            for pe in payment_entries:
                month_year = formatdate(pe.posting_date, "MMM-yyyy")
                amount = pe.received_amount or pe.paid_amount or 0
                gmv_map[month_year] += amount
                transaction_dates.append(pe.posting_date)

            for ref in references:
                pe_date = pe_date_map.get(ref.parent)
                if not pe_date:
                    continue

                month_year = formatdate(pe_date, "MMM-yyyy")
                order_map[month_year].add(ref.reference_name)

        # --------------------------------------------------
        # Anchor date
        # --------------------------------------------------
        start_date_with_anchor = (
            getdate(min(transaction_dates)).strftime("%Y-%m-%d")
            if transaction_dates else from_date
        )

        # --------------------------------------------------
        # Final GMV response (FIXED 6 months)
        # --------------------------------------------------
        gmv_data = [
            {
                "month_year": month,
                "value": round(gmv_map.get(month, 0), 2),
                "count": len(order_map.get(month, set()))
            }
            for month in months
        ]

        # --------------------------------------------------
        # Response
        # --------------------------------------------------
        return {
            "success": True,
            "data": [
                {
                    "merchant_customer_ref_id": merchant_customer_ref_id,
                    "phone": customer.mobile_no,
                    "start_date_with_anchor": start_date_with_anchor,
                    "gmv_data": gmv_data
                }
            ]
        }

    except Exception:
        headers = dict(frappe.local.request.headers)
        body = frappe.local.form_dict if hasattr(frappe.local, "form_dict") else {}

        frappe.log_error(
            message=frappe.get_traceback() +
                    "\n\nRequest Headers:\n" + json.dumps(headers, indent=4) +
                    "\n\nRequest Body:\n" + json.dumps(body, indent=4),
            title="get_customer_gmv error"
        )

        return {
            "success": False,
            "message": "Unable to fetch GMV data"
        }


@frappe.whitelist()
@validate_method(["POST"])
def save_lead_callback():
    try:
        # --------------------------------------------------
        # Read raw JSON body
        # --------------------------------------------------
        data = frappe.form_dict

        merchant_customer_ref_id = data.get("merchant_customer_ref_id")
        application_status = data.get("application_status")
        status_message = data.get("status_message")
        # --------------------------------------------------
        # Basic validation
        # --------------------------------------------------
        if not merchant_customer_ref_id:
            return {
                "success": False,
                "message": "merchant_customer_ref_id is required"
            }

        if not application_status:
            return {
                "success": False,
                "message": "application_status is required"
            }

        # --------------------------------------------------
        # Create Lead Callback document
        # --------------------------------------------------
        doc = frappe.get_doc({
            "doctype": "Lead Callback",
            "merchant_customer_ref_id": str(merchant_customer_ref_id),
            "application_status": application_status,
            "status_message": status_message,
            "received_at": now()
        })

        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        # --------------------------------------------------
        # Strict response
        # --------------------------------------------------
        return {
            "success": True
        }

    except Exception:
        frappe.log_error(frappe.get_traceback(), "save_lead_callback error")
        return {
            "success": False,
            "message": "Failed to save lead callback"
        }


@frappe.whitelist()
@validate_method(["POST"])
def save_payment_initiation():
    """
    Save Rupifi Payment Initiation in Rupifi Webhook Log
    """

    try:
        # --------------------------------------------------
        # Read JSON body from POST
        # --------------------------------------------------
        data = frappe.form_dict

        order_id = data.get("order_id")
        customer_id = data.get("customer_id")
        merchant_payment_ref_id = data.get("merchant_payment_ref_id")
        raw_json = data.get("raw_json")

        # --------------------------------------------------
        # Validation
        # --------------------------------------------------
        if not order_id:
            return {"success": False, "message": "order_id is required"}
        if not customer_id:
            return {"success": False, "message": "customer_id is required"}
        if not merchant_payment_ref_id:
            return {"success": False, "message": "merchant_payment_ref_id is required"}
        if not raw_json:
            return {"success": False, "message": "raw_json is required"}

        # --------------------------------------------------
        # If raw_json is already a dict, convert to pretty string
        # --------------------------------------------------
        if isinstance(raw_json, dict):
            raw_json_str = json.dumps(raw_json, indent=2)
        else:
            # fallback if someone sends a string
            raw_json_str = str(raw_json)

        # --------------------------------------------------
        # Create Rupifi Webhook Log
        # --------------------------------------------------
        doc = frappe.get_doc({
            "doctype": "Rupifi Webhook Log",
            "order_id":order_id,
            "customer_id": customer_id,
            "merchant_payment_ref_id": merchant_payment_ref_id,
            "raw_json": raw_json_str,
            "created_at": now(),
            "last_updated_at": now()
        })

        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        return {"success": True}

    except Exception:
        frappe.log_error(message=frappe.get_traceback(), title="save_payment_initiation error")
        return {"success": False, "message": "Failed to save payment initiation"}
    

@frappe.whitelist()
@validate_method(["POST"])
def update_payment_webhook():
	try:
		data = frappe.form_dict or {}

		merchant_payment_ref_id = data.get("merchant_payment_ref_id")
		if not merchant_payment_ref_id:
			return {
				"success": False,
				"message": "merchant_payment_ref_id is required"
			}

		# Fetch existing webhook log
		doc = frappe.get_doc(
			"Rupifi Webhook Log",
			{"merchant_payment_ref_id": merchant_payment_ref_id}
		)

		# --------------------------
		# Top-level fields
		# --------------------------
		if "payment_id" in data:
			doc.payment_id = data.get("payment_id")

		if "status" in data:
			doc.status = data.get("status")

		if "auto_capture" in data:
			doc.auto_capture = data.get("auto_capture")

		if data.get("payment_date"):
			doc.paymentdate = get_datetime(data.get("payment_date"))

		if "redirect_url" in data:
			doc.redirect_url = data.get("redirect_url")

		if "redirect_confirm_url" in data:
			doc.redirect_confirm_url = data.get("redirect_confirm_url")

		if "redirect_cancel_url" in data:
			doc.redirect_cancel_url = data.get("redirect_cancel_url")

		if "callback_url" in data:
			doc.callback_url = data.get("callback_url")

		if "payment_url" in data:
			doc.paymenturl = data.get("payment_url")

		# --------------------------
		# Amount
		# --------------------------
		amount = data.get("amount") or {}
		if "value" in amount:
			doc.amount_value = amount.get("value")
		if "formatted_value" in amount:
			doc.amount_formatted_value = amount.get("formatted_value")
		if "currency" in amount:
			doc.currency = amount.get("currency")

		# --------------------------
		# Uncaptured Amount
		# --------------------------
		uncaptured = data.get("uncaptured_amount") or {}
		if "value" in uncaptured:
			doc.uncaptured_amount_value = uncaptured.get("value")
		if "formatted_value" in uncaptured:
			doc.uncaptured_amount_formatted_value = uncaptured.get("formatted_value")

		# --------------------------
		# Merchant / Account fields
		# --------------------------
		if "merchant_customer_ref_id" in data:
			doc.merchant_customer_ref_id = data.get("merchant_customer_ref_id")

		if "account_id" in data:
			doc.account_id = data.get("account_id")

		# --------------------------
		# Raw JSON storage
		# --------------------------
		if "raw_json" in data:
			# Ensure raw_json is stored as string
			if isinstance(data.get("raw_json"), (dict, list)):
				doc.raw_json = json.dumps(data.get("raw_json"))
			else:
				doc.raw_json = data.get("raw_json")

		doc.save(ignore_permissions=True)
		frappe.db.commit()

		return {
			"success": True,
			"message": "Payment webhook updated successfully",
			"docname": doc.name
		}

	except frappe.DoesNotExistError:
		return {
			"success": False,
			"message": "Webhook record not found"
		}

	except Exception:
		frappe.log_error(
			message=frappe.get_traceback(),
			title="update_payment_webhook error"
		)
		return {
			"success": False,
			"message": "Internal server error"
		}

@frappe.whitelist(allow_guest=True)
@validate_method(["GET"])
def get_order_by_payment_ref(merchant_payment_ref_id):
    try:
        if not merchant_payment_ref_id:
            return {
                "success": False,
                "message": "merchant_payment_ref_id is required"
            }
        order_id=frappe.db.get_value(
			"Rupifi Webhook Log",
			{"merchant_payment_ref_id": merchant_payment_ref_id},
                  "order_id"
		)
        return {
			"success": True,
			"order_id": order_id
		}
    except Exception:
        frappe.log_error(
            message=frappe.get_traceback(),
            title="update_payment_webhook error"
        )
        return {
            "success": False,
            "message": "Internal server error"
        }


@frappe.whitelist()
@validate_method(["GET"])
def get_token():
        try:
            tokens=frappe.get_all("Partner Authentication",filters={"is_active":1},fields=[      
            "partner_id",
            "partner_name",
            "token",
            "token_Type"
            ])
            return {
			"success": True,
 "message": "Data Fetched Successfully",
             "data":tokens
             		}
        
        except frappe.DoesNotExistError:
            return {
                "success": False,
                "message": "No partner records found"
            }

        except frappe.PermissionError:
            return {
                "success": False,
                "message": "You do not have permission to access partner data"
            }

        except Exception:
            frappe.log_error(
                message=frappe.get_traceback(),
                title="update_payment_webhook error"
            )
            return {
                "success": False,
                "message": "Internal server error"
            }