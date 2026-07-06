import base64
from urllib.parse import parse_qs
import frappe
from frappe.utils import get_datetime_str
import hashlib

def decode_token(token):
    decoded = base64.b64decode(token).decode()
    return {k: v[0] for k, v in parse_qs(decoded).items()}

def payu_log(stage, step, title, data=None):
    frappe.log_error(
        title=f"[PAYU][{stage}][STEP-{step}] {title}",
        message=frappe.as_json(data) if data else ""
    )
@frappe.whitelist(allow_guest=True)
def start_payu_payment():
    import base64, urllib.parse, uuid

    try:
        payu_log("START", "01", "Request Received", frappe.form_dict)

        token = frappe.form_dict.get("token")
        if not token:
            payu_log("START", "02", "Token Missing")
            frappe.throw("Token missing")

        decoded = base64.b64decode(token).decode("utf-8")
        raw_data = dict(urllib.parse.parse_qsl(decoded))
        data = {k.strip().lower(): v.strip() for k, v in raw_data.items()}

        payu_log("START", "03", "Token Decoded", data)

        settings = frappe.get_single("PayU Settings")

        key = settings.merchant_key.strip()
        salt = settings.salt.strip()
        payu_url = settings.payu_url

        txnid = f"TXN{uuid.uuid4().hex[:10]}"

        amount = float(data.get("amount", 0))
        gst_percent = float(data.get("gst_percent", 18))

        gst_amount = round((amount * gst_percent) / 100, 2)
        total_amount = round(amount + gst_amount, 2)

        productinfo = data.get("productinfo")
        firstname = data.get("firstname")
        email = data.get("email")
        phone = data.get("phone")
        order_id = data.get("order_id")

        payu_log("START", "04", "Amount Calculated", {
            "base": amount,
            "gst_percent": gst_percent,
            "gst": gst_amount,
            "total": total_amount
        })

        hashh = generate_payu_hash(
            key=key,
            txnid=txnid,
            amount=total_amount,
            productinfo=productinfo,
            firstname=firstname,
            email=email,
            salt=salt,
            udf1=order_id
        )


        payu_log("START", "05", "Hash Generated", {
            "txnid": txnid,
            "hash": hashh
        })

        doc = frappe.get_doc({
            "doctype": "PayU Transaction",
            "txnid": txnid,
            "order_id": order_id,
            "amount": total_amount,
            "base_amount": amount,
            "gst_amount": gst_amount,
            "status": "Initiated",
            "productinfo": productinfo,
            "firstname": firstname,
            "email": email,
            "phone": phone
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        payu_log("START", "06", "Transaction Saved", doc.name)

        html = f"""
        <html>
        <body onload="document.forms['payuForm'].submit()">
            <form name="payuForm" method="post" action="{payu_url}">
                <input type="hidden" name="key" value="{key}">
                <input type="hidden" name="txnid" value="{txnid}">
                <input type="hidden" name="amount" value="{total_amount}">
                <input type="hidden" name="productinfo" value="{productinfo}">
                <input type="hidden" name="firstname" value="{firstname}">
                <input type="hidden" name="email" value="{email}">
                <input type="hidden" name="phone" value="{phone}">
                <input type="hidden" name="surl" value="{settings.payu_success_url}">
                <input type="hidden" name="furl" value="{settings.payu_failure_url}">
                <input type="hidden" name="hash" value="{hashh}">
                <input type="hidden" name="udf1" value="{order_id}">
                <input type="hidden" name="service_provider" value="payu_paisa">
            </form>
        </body>
        </html>
        """

        payu_log("START", "07", "Redirecting To PayU")

        return {"html": html}

    except Exception:
        payu_log("START", "99", "Exception", frappe.get_traceback())
        frappe.throw("Unable to initiate payment")

def generate_payu_hash(
    key,
    txnid,
    amount,
    productinfo,
    firstname,
    email,
    salt,
    udf1="",
    udf2="",
    udf3="",
    udf4="",
    udf5=""
):
    hash_string = (
        f"{key}|{txnid}|{amount}|{productinfo}|"
        f"{firstname}|{email}|{udf1}|{udf2}|{udf3}|{udf4}|{udf5}"
        f"||||||{salt}"
    )

    return hashlib.sha512(hash_string.encode("utf-8")).hexdigest().lower()


def verify_payu_response_hash(response):
    settings = frappe.get_single("PayU Settings")
    salt = settings.salt.strip()

    status = response.get("status")
    email = response.get("email")
    firstname = response.get("firstname")
    productinfo = response.get("productinfo")
    amount = response.get("amount")
    txnid = response.get("txnid")
    udf1 = response.get("udf1")
    received_hash = response.get("hash", "").lower()

    hash_string = (
        f"{salt}|{status}||||||||{udf1}|{email}|"
        f"{firstname}|{productinfo}|{amount}|{txnid}|{settings.merchant_key}"
    )

    calculated_hash = hashlib.sha512(hash_string.encode()).hexdigest().lower()

    payu_log("HASH", "01", "Response Hash Compare", {
        "calculated": calculated_hash,
        "received": received_hash,
        "string": hash_string
    })

    return calculated_hash == received_hash

@frappe.whitelist(allow_guest=True)
def payu_success():
    try:
        response = frappe.form_dict or {}

        payu_log("SUCCESS", "01", "Callback Received", response)

        if not verify_payu_response_hash(response):
            payu_log("SUCCESS", "02", "Hash Failed", response)
            return "<h2>Invalid Transaction</h2>"

        txnid = response.get("txnid")

        txn_name = frappe.get_value("PayU Transaction", {"txnid": txnid}, "name")
        if not txn_name:
            payu_log("SUCCESS", "03", "Transaction Not Found", txnid)
            return "<h2>Transaction Not Found</h2>"

        doc = frappe.get_doc("PayU Transaction", txn_name)
        doc.status = "Success"
        doc.payu_response = frappe.as_json(response)
        doc.save(ignore_permissions=True)
        frappe.db.commit()

        payu_log("SUCCESS", "04", "Payment Marked Success", txn_name)

        return "<h2>Payment Successful</h2>"

    except Exception:
        payu_log("SUCCESS", "99", "Exception", frappe.get_traceback())
        return "<h2>Error Occurred</h2>"

@frappe.whitelist(allow_guest=True)
def payu_failure():
    response = frappe.form_dict or {}

    payu_log("FAILURE", "01", "Failure Callback", response)

    txnid = response.get("txnid")
    error = response.get("error_Message") or response.get("error")

    txn_name = frappe.get_value("PayU Transaction", {"txnid": txnid}, "name")
    if txn_name:
        doc = frappe.get_doc("PayU Transaction", txn_name)
        doc.status = "Failed"
        doc.error_message = error
        doc.payu_response = frappe.as_json(response)
        doc.save(ignore_permissions=True)
        frappe.db.commit()

        payu_log("FAILURE", "02", "Transaction Marked Failed", txn_name)

    return "<h2>Payment Failed</h2>"


@frappe.whitelist(allow_guest=True)
def payu_webhook_success():
    import hashlib
    data = frappe.form_dict

    txnid = data.get("txnid")
    txn = frappe.get_doc("PayU Transaction", {"txnid": txnid})
    settings = frappe.get_single("PayU Settings")
    key = settings.merchant_key
    salt = settings.salt

    # 🔐 Skip hash for EasyPay
    if data.get("udf1") != "Easypay":
        salt = frappe.conf.payu_salt
        secret = frappe.conf.payu_webhook_secret

        hash_string = (
            f"{salt}|{data['status']}||||||"
            f"{data.get('udf5')}|{data.get('udf4')}|"
            f"{data.get('udf3')}|{data.get('udf2')}|"
            f"{data.get('udf1')}|{data['email']}|"
            f"{data['firstname']}|{data['productinfo']}|"
            f"{data['amount']}|{txnid}|{secret}"
        )

        # if hashlib.sha512(hash_string.encode()).hexdigest().lower() != data.get("hash"):
        #     frappe.throw("Webhook Hash Invalid")

    # 🧾 Save webhook payload
    frappe.get_doc({
        "doctype": "PayU Webhook Log",
        "txnid": txnid,
        "payload": frappe.as_json(data),
        "status": "Success"
    }).insert(ignore_permissions=True)

    # ✅ CREATE PAYMENT ENTRY (MOST IMPORTANT)
    create_payment_entry(txn)

    return "OK"


def create_payment_entry(txn):
    existing_pe = frappe.db.get_value(
        "Payment Entry",
        {
            "reference_no": txn.txnid,
            "docstatus": ["!=", 2],
        },
        "name",
    )
    if existing_pe:
        return existing_pe

    so = frappe.get_doc("Sales Order", txn.sales_order)

    pe = frappe.new_doc("Payment Entry")
    pe.payment_type = "Receive"
    pe.party_type = "Customer"
    pe.party = so.customer
    pe.company = so.company
    pe.paid_amount = txn.amount
    pe.received_amount = txn.amount
    pe.reference_no = txn.txnid
    pe.append("references", {
        "reference_doctype": "Sales Order",
        "reference_name": so.name,
        "allocated_amount": txn.amount
    })
    pe.insert(ignore_permissions=True)
    pe.submit()
    return pe.name



# new payment entries

import frappe
import json
from frappe.utils import now

@frappe.whitelist(allow_guest=True)
def save_transaction():
    """
    Save Payment Gateway Transaction details.
    Accepts raw JSON in POST request body.
    """
    try:
        # Get raw JSON from request body
        frappe.set_user("Administrator")
        raw_data = frappe.local.request.get_data(as_text=True)
        data = json.loads(raw_data)
        frappe.log_error(message=frappe.as_json(data), title="Save Transaction Payload")
        # Create Doc
        doc = frappe.get_doc({
            "doctype": "Payment Gateway Transaction",
            "txn_id": data.get("txn_id"),
            "productinfo": data.get("product_info"),
            "firstname": data.get("first_name"),
            "email": data.get("email"),
            "amount": data.get("amount"),
            "phone": data.get("phone"),
            "userid": data.get("userid"),
            "order_id": data.get("orderid"),
            "callbackurl": data.get("callbackurl"),
            "request_token": data.get("request_token"),
            "request_decodedtoken": data.get("request_decodedToken"),
            "request_cleanedtoken": data.get("request_cleanedToken"),
            "request_hashstring": data.get("request_hashString"),
            "request_hash": data.get("request_hash"),
            "created_at": now()
        })

        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        return {"status": "success", "message": "Transaction saved", "txn_id": data.get("txn_id")}

    except Exception as e:
        frappe.log_error(message=str(e), title="Save Transaction Error")
        return {"status": "error", "message": str(e)}

@frappe.whitelist(allow_guest=True)
def update_transaction():
    """
    Update Payment Gateway Transaction using txn_id.
    Accepts raw JSON payload.
    """

    try:
        # -----------------------------
        # Read RAW JSON
        # -----------------------------
        
        raw_data = frappe.local.request.get_data(as_text=True)
        data = json.loads(raw_data)
        frappe.log_error(message=frappe.as_json(data), title="Update Transaction Payload")
        txn_id = data.get("txnid")
        status = data.get("status")  # Success / Failed

        if not txn_id:
            frappe.throw("txnid is required")
        frappe.set_user("Administrator")
        # -----------------------------
        # Find existing transaction
        # -----------------------------
        docname = frappe.db.get_value(
            "Payment Gateway Transaction",
            {"txn_id": txn_id},
            "name"
        )

        if not docname:
            frappe.throw(f"Transaction not found for txn_id: {txn_id}")

        doc = frappe.get_doc("Payment Gateway Transaction", docname)

        # -----------------------------
        # Update core fields
        # -----------------------------
        doc.status = status
        doc.amount = data.get("amount")
        doc.statusupdateddate = now()

        # -----------------------------
        # Update Response fields
        # -----------------------------
        doc.response_payu_txnid = txn_id
        doc.response_payu_hash = data.get("hash")
        doc.response_mihpayid = data.get("mihpayid")
        doc.response_mode = data.get("mode")
        doc.response_unmappedstatus = data.get("unmappedstatus")
        doc.response_key = data.get("key")
        doc.response_discount = data.get("discount")
        doc.response_net_amount_debit = data.get("net_amount_debit")
        doc.response_addedon = data.get("addedon")

        doc.response_field1 = data.get("field1")
        doc.response_field2 = data.get("field2")
        doc.response_field3 = data.get("field3")
        doc.response_field4 = data.get("field4")
        doc.response_field5 = data.get("field5")
        doc.response_field6 = data.get("field6")
        doc.response_field7 = data.get("field7")
        doc.response_field8 = data.get("field8")
        doc.response_field9 = data.get("field9")

        doc.response_payment_source = data.get("payment_source")
        doc.response_pg_type = data.get("PG_TYPE")
        doc.response_bank_ref_num = data.get("bank_ref_num")
        doc.response_bankcode = data.get("bankcode")
        doc.response_error = data.get("error")
        doc.response_error_message = data.get("error_Message")
        doc.response_splitinfo = data.get("splitInfo")

        # -----------------------------
        # PayU echo data
        # -----------------------------
        doc.response_payu_productinfo = data.get("productinfo")
        doc.response_payu_firstname = data.get("firstname")
        doc.response_payu_email = data.get("email")
        doc.response_payu_phone = data.get("phone")

        # -----------------------------
        # Save
        # -----------------------------
        doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Transaction updated successfully",
            "txnid": txn_id,
            "payment_status": status
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Update Transaction Error")
        return {
            "status": "error",
            "message": str(e)
        }


@frappe.whitelist(allow_guest=True)
def get_callback_url():
    """
    Fetch Callback URL and Order ID using txn_id
    """

    txn_id = frappe.form_dict.get("txnid")

    if not txn_id:
        frappe.throw("txnid is required")

    data = frappe.db.get_value(
        "Payment Gateway Transaction",
        {"txn_id": txn_id},
        ["callbackurl", "order_id"],
        as_dict=True
    )

    if not data:
        frappe.throw(f"No transaction found for txn_id: {txn_id}")

    return {
        "status": "success",
        "txnid": txn_id,
        "callbackurl": data.callbackurl,
        "order_id": data.order_id
    }


@frappe.whitelist(allow_guest=True)
def get_transaction_details():
    """
    Fetch Product Info, First Name, Email using txn_id
    """

    txn_id = frappe.form_dict.get("txnid")

    if not txn_id:
        frappe.throw("txnid is required")

    data = frappe.db.get_value(
        "Payment Gateway Transaction",
        {"txn_id": txn_id},
        ["productinfo", "firstname", "email"],
        as_dict=True
    )

    if not data:
        frappe.throw(f"No transaction found for txn_id: {txn_id}")

    return {
        "status": "success",
        "txnid": txn_id,
        "productinfo": data.productinfo,
        "firstname": data.firstname,
        "email": data.email
    }
import frappe
from frappe.utils import now
from shoption_api.shoption_test_api.doctype.payment_webhook_log.payment_webhook_log import (
    upsert_payment_webhook_log,
)

@frappe.whitelist(allow_guest=True)
def payu_response_webhook():
    """
    Save PayU webhook response into PayU Response DocType
    """
    payu_response_name = None
    txnid = ""
    payment_status = None
    raw_payload = None
    data = {}
    try:
        # PayU sends form-urlencoded data
        data = frappe.form_dict.copy()
        txnid = (data.get("txnid") or "").strip()
        status = (data.get("status") or "").strip()

        if not txnid:
            frappe.throw("txnid missing")

        frappe.set_user("Administrator")

        payment_status = "Success" if status.lower() == "success" else "Failed"
        raw_payload = frappe.as_json(data)
        # -----------------------------
        # Skip duplicate transaction completely
        # -----------------------------
        payu_response_name = frappe.db.get_value("PayU Response", {"txnid": txnid}, "name")
        if payu_response_name:
            return {
                "status": "duplicate",
                "payment_status": payment_status,
                "txnid": txnid,
                "mihpayid": data.get("mihpayid"),
                "message": "Duplicate transaction received. Existing PayU Response was not updated.",
            }

        doc = frappe.new_doc("PayU Response")

        doc.mihpayid = data.get("mihpayid")
        doc.mode = data.get("mode")
        doc.status = payment_status
        doc.key = data.get("key")
        doc.txnid = txnid
        doc.amount = data.get("amount")
        doc.addedon = data.get("addedon")
        doc.productinfo = data.get("productinfo")
        doc.firstname = data.get("firstname")
        doc.lastname = data.get("lastname")
        doc.address1 = data.get("address1")
        doc.address2 = data.get("address2")
        doc.city = data.get("city")
        doc.state = data.get("state")
        doc.country = data.get("country")
        doc.zipcode = data.get("zipcode")
        doc.email = data.get("email")
        doc.phone = data.get("phone")

        # UDFs
        doc.udf1 = data.get("udf1")
        doc.udf2 = data.get("udf2")
        doc.udf3 = data.get("udf3")
        doc.udf4 = data.get("udf4")
        doc.udf5 = data.get("udf5")

        # Extra fields
        doc.paymentsource = data.get("payment_source")
        doc.pgtype = data.get("PG_TYPE")
        doc.error = data.get("error")
        doc.errormessage = data.get("error_Message")
        doc.netamountdebit = data.get("net_amount_debit")
        doc.discount = data.get("discount")
        doc.bankrefno = data.get("bank_ref_num")
        doc.bankcode = data.get("bankcode")

        # Optional fields
        doc.unmappedstatus = data.get("unmappedstatus")
        doc.hash = data.get("hash")
        doc.cardtoken = data.get("card_token")
        doc.cardno = data.get("cardnum")

        doc.lastupdated_at = now()

        doc.insert(ignore_permissions=True)
        payu_response_name = doc.name
        payment_entry = frappe.db.get_value(
            "Payment Entry",
            {
                "reference_no": txnid,
                "docstatus": ["!=", 2],
            },
            "name",
        )

        upsert_payment_webhook_log(
            provider="PayU",
            transaction_reference=txnid,
            external_payment_id=data.get("mihpayid"),
            payload=raw_payload,
            status=payment_status,
            source_doctype="PayU Response",
            source_name=payu_response_name,
            processed=1,
            processed_on=now(),
            error_message=None,
            payment_entry=payment_entry,
        )
        frappe.db.commit()

        return {
            "status": "saved",
            "payment_status": payment_status,
            "txnid": txnid,
            "mihpayid": data.get("mihpayid")
        }

    except Exception:
        # Rollback any partial transaction
        frappe.db.rollback()
        upsert_payment_webhook_log(
            provider="PayU",
            transaction_reference=txnid,
            external_payment_id=data.get("mihpayid"),
            payload=raw_payload,
            status=payment_status,
            source_doctype="PayU Response",
            processed=0,
            error_message=frappe.get_traceback(),
        )
        frappe.db.commit()

        # Log full traceback for debugging
        frappe.log_error(
            title="PayU Webhook Error",
            message=frappe.get_traceback()
        )

        # PayU expects HTTP 200, so return a safe response
        return {
            "status": "error",
            "message": "Webhook processing failed"
        }

from shoption_api.erp_api.common import api_response


@frappe.whitelist()
def view_paymentlinks(order_id=None):
    
    if not order_id:
        return api_response( False,"order_id is required", [])

    # NOTE: change doctype/fieldnames if your DocType differs
    rows = frappe.get_all(
        "Payment Link",
        filters={"order_id": str(order_id)},
        fields=[
            "order_id",
            "customer_id",
            "transactionid",
            "transactionamount",
            "linkexpirydate",
            "linkcreated_at",
            "linkcreatedby",
            "linkremark",
            "linkurl",
            "payment_link_status as current_status"
        ],
        order_by="creation desc",
    )
    for i in rows:
        i["current_status"] = 4 if i["linkexpirydate"] and get_datetime_str(i["linkexpirydate"]) < get_datetime_str(now()) else i["current_status"]
    # Match response shape in doc :contentReference[oaicite:1]{index=1}
    return api_response(True,"Data Fetched Successfully", rows or [])
     


# -----------------------------
# 2) Generate Transaction Id
# API: Paymentlinks/Generate/Transactionid
# -----------------------------
import uuid
import random
from frappe.utils import now_datetime, get_system_timezone
from frappe.utils.data import convert_utc_to_timezone

def make_transaction_id(order_id):
    prefix = order_id or random.randint(10000, 99999)
    dt_utc = now_datetime()
    dt_local = convert_utc_to_timezone(dt_utc, get_system_timezone())
    date_part = dt_local.strftime("%Y%m%d")   # 8
    time_part = dt_local.strftime("%H%M%S")   # 6
    short_uuid = uuid.uuid4().hex[:12].upper()  # 12 chars
    return f"{prefix}_{date_part}{time_part}_{short_uuid}"


@frappe.whitelist()
def get_transactionid(order_id=None):
    
    if not order_id:
        return {"status": False, "message": "order_id is required", "data": []}

    txn = make_transaction_id(order_id)

    # Match response shape in doc :contentReference[oaicite:2]{index=2}
    return api_response(True,"Data Fetched Successfully",{"transaction_id":txn or ""})


# -----------------------------
# 3) Save Payment Link
# API: Paymentlinks/Save/Paymentlinks
# -----------------------------
@frappe.whitelist()
def save_paymentlinks(
    order_id=None,
    customer_id=None,
    transactionid=None,
    transactionamount=None,
    linkexpirydate=None,
    linkcreated_at=None,
    linkcreatedby=None,
    linkremark=None,
    linkurl=None
):

    # Basic validations (as per request in doc :contentReference[oaicite:3]{index=3})
    if not order_id:
        return api_response(False, "order_id is required", [])
    if not transactionid:
        return api_response(False, "transactionid is required", [])
    try:
        
        # Upsert by transactionid (prevents duplicates)
        existing = frappe.db.get_value("Payment Link", {"transactionid": transactionid}, "name")

        if existing:
            pl = frappe.get_doc("Payment Link", existing)
        else:
            pl = frappe.new_doc("Payment Link")

        pl.order_id = str(order_id)
        pl.customer_id = str(customer_id)
        pl.transactionid = str(transactionid)
        pl.transactionamount = float(transactionamount)
        pl.linkexpirydate = linkexpirydate
        pl.linkcreated_at = linkcreated_at
        pl.linkcreatedby = str(linkcreatedby) if linkcreatedby is not None else None
        pl.linkremark = linkremark
        pl.linkurl = linkurl

        pl.insert(ignore_permissions=True)
        frappe.db.commit()

        return api_response(True, "Data Saved Successfully", [])
            
    except Exception:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Paymentlinks Save API failed")
        return api_response(False, "Failed to save payment link", [])
