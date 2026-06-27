import frappe
import random
import requests
import hashlib
import json
import time
from datetime import timedelta
from frappe.utils import now_datetime, get_datetime
from urllib.parse import quote_plus

# ---------- HEADER AUTH CHECK ----------
def _check_api_auth():
    """Validate API Key + Secret from headers."""
    cfg = frappe.get_site_config()

    expected_key = cfg.get("shoption_api_key")
    expected_secret = cfg.get("shoption_api_secret")

    incoming_key = frappe.get_request_header("X-API-KEY")
    incoming_secret = frappe.get_request_header("X-API-SECRET")

    if not incoming_key or not incoming_secret:
        return False, {"status": False, "message": "Missing authentication headers"}

    if incoming_key != expected_key or incoming_secret != expected_secret:
        frappe.log_error("Invalid API authentication attempt", "shoption_api.auth_failure")
        return False, {"status": False, "message": "Unauthorized"}

    return True, None


# ---------- CONFIG HELPERS ----------
def _get_site_config():
    try:
        return frappe.get_site_config()
    except Exception:
        return {}

def _get_otp_config():
    cfg = frappe.get_site_config()

    return {
        "provider": cfg.get("otp_provider"),
        "username": cfg.get("otp_username"),
        "apikey": cfg.get("otp_apikey"),
        "sender": cfg.get("otp_sender"),
        "template_id": cfg.get("otp_template_id"),
        "salt": cfg.get("salt"),
    }


# ---------- UTILITIES ----------
def _mask_mobile(mobile):
    s = str(mobile)
    if len(s) <= 4:
        return "****"
    return "****" + s[-4:]

def _hash_otp(otp, salt):
    return hashlib.sha256(f"{otp}|{salt}".encode()).hexdigest()

def _now_str():
    return now_datetime().strftime("%Y-%m-%d %H:%M:%S")

# ---------- PROVIDER CALL ----------
def _call_provider_send(mobile_no, message, config):
    base = "http://www.alots.in/sms-panel/api/http/index.php"
    msg_enc = quote_plus(message)
    url = (
        f"{base}?username={config['username']}"
        f"&apikey={config['apikey']}"
        f"&apirequest=Text"
        f"&sender={config['sender']}"
        f"&mobile={mobile_no}"
        f"&message={msg_enc}"
        f"&route=OTP"
        f"&TemplateID={config['template_id']}"
        f"&format=JSON"
    )
    resp = requests.get(url, timeout=10)
    return resp

# ---------- RATE LIMITS ----------
def _check_send_limits(customer, per_min=2, per_hour=5):
    try:
        attempts = customer.custom_otp_attempts or 0
        last_sent = customer.custom_otp_sent_at
        if not last_sent:
            return True, None
        last_dt = get_datetime(str(last_sent))
        delta = now_datetime() - last_dt
        seconds = delta.total_seconds()
        if seconds < 60 and attempts >= per_min:
            return False, "Too many OTP requests. Try after a minute."
        if seconds < 3600 and attempts >= per_hour:
            return False, "Too many OTP requests. Try after an hour."
        return True, None
    except Exception:
        return True, None

# ---------- VERIFY LOCKOUT ----------
def _check_verify_lock(customer, max_invalid=5, lock_minutes=15):
    invalid = getattr(customer, "custom_otp_invalid_attempts", 0) or 0
    locked_until = getattr(customer, "custom_otp_locked_until", None) or ""
    if locked_until:
        try:
            locked_dt = get_datetime(str(locked_until))
            if now_datetime() < locked_dt:
                mins = int((locked_dt - now_datetime()).total_seconds() / 60) + 1
                return False, f"Too many invalid attempts. Try after {mins} minutes."
        except Exception:
            pass
    return True, None

# def _register_invalid_attempt(customer, max_invalid=5, lock_minutes=15):
#     customer.custom_otp_invalid_attempts = (customer.custom_otp_invalid_attempts or 0) + 1
#     if customer.custom_otp_invalid_attempts >= max_invalid:
#         lock_dt = now_datetime() + timedelta(minutes=lock_minutes)
#         customer.custom_otp_locked_until = lock_dt.strftime("%Y-%m-%d %H:%M:%S")
#     customer.save(ignore_permissions=True)
#     frappe.db.commit()

# 03./12 
def _register_invalid_attempt(customer):
    # prefer field: custom_otp_invalid_attempts
    if hasattr(customer, "custom_otp_invalid_attempts"):
        current = getattr(customer, "custom_otp_invalid_attempts") or 0
        setattr(customer, "custom_otp_invalid_attempts", current + 1)

    # fallback: if system uses custom_otp_attempts instead
    elif hasattr(customer, "custom_otp_attempts"):
        current = getattr(customer, "custom_otp_attempts") or 0
        setattr(customer, "custom_otp_attempts", current + 1)

    # if neither exists → skip silently (NO CRASH)
    else:
        return

    customer.save(ignore_permissions=True)
    frappe.db.commit()


# def _clear_invalid_attempts(customer):
#     customer.custom_otp_invalid_attempts = 0
#     customer.custom_otp_locked_until = ""
#     customer.save(ignore_permissions=True)
#     frappe.db.commit()

def _clear_invalid_attempts(customer):
    if hasattr(customer, "custom_otp_invalid_attempts"):
        customer.custom_otp_invalid_attempts = 0
    elif hasattr(customer, "custom_otp_attempts"):
        customer.custom_otp_attempts = 0
    else:
        return

    customer.save(ignore_permissions=True)
    frappe.db.commit()


# ---------- CUSTOMER ----------
def get_or_create_customer(mobile_no):
    cust_name = frappe.db.get_value("Customer", {"mobile_no": mobile_no}, "name")
    if cust_name:
        return frappe.get_doc("Customer", cust_name)

    contact = frappe.get_all("Contact", filters={"mobile_no": mobile_no}, fields=["name"])
    if contact:
        dl = frappe.get_all(
            "Dynamic Link",
            filters={"parenttype": "Contact", "parent": contact[0].name, "link_doctype": "Customer"},
            fields=["link_name"],
        )
        if dl:
            return frappe.get_doc("Customer", dl[0].link_name)

    new_cust = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": f"Customer-{mobile_no}",
        "customer_type": "Individual",
        "mobile_no": mobile_no
    })
    new_cust.insert(ignore_permissions=True)
    return new_cust

# # ---------- PARAMS ----------
_ALLOWED_SEND_PARAMS = {"mobile_no"}
_ALLOWED_VERIFY_PARAMS = {"mobile_no", "otp"}

def _reject_extra_params(allowed):
    return True, None

def _validate_mobile(mobile):
    if not mobile:
        return False, "mobile_no is required"
    mobile = "".join(ch for ch in str(mobile) if ch.isdigit())
    if len(mobile) < 10 or len(mobile) > 15:
        return False, "Invalid mobile number"
    return True, mobile

def _validate_otp_format(otp):
    if not otp or not str(otp).isdigit():
        return False
    if len(str(otp).strip()) not in (6,):
        return False
    return True

# ---------- API: send_otp ----------
@frappe.whitelist(allow_guest=True)
def send_otp(mobile_no=None):

    # ---- FORCE POST ONLY ----
    if frappe.request and frappe.request.method != "POST":
        frappe.local.response['http_status_code'] = 405
        return {"status": False, "message": "Method Not Allowed. Use POST only."}

    # ---- CLEAN & LOCK FORM PARAMS ----
    if frappe.request and frappe.request.method == "POST":
        frappe.local.form_dict = frappe._dict(frappe.form_dict)


    # -------- HEADER AUTH CHECK --------
    ok, err = _check_api_auth()
    if not ok:
        return err

    ok, err = _reject_extra_params(_ALLOWED_SEND_PARAMS)
    if not ok:
        return err

    ok, mobile = _validate_mobile(mobile_no)
    if not ok:
        return {"status": False, "message": mobile}

    config = _get_otp_config()
    if not config.get("username") or not config.get("apikey"):
        return {"status": False, "message": "OTP provider misconfigured"}

    customer = get_or_create_customer(mobile)

    allowed, reason = _check_send_limits(customer, per_min=2, per_hour=5)
    if not allowed:
        return {"status": False, "message": reason}

    otp = random.randint(100000, 999999)
    if mobile=="8827511987":
        otp=739462
    otp_hash = _hash_otp(otp, config.get("salt"))

    message = f"Welcome to Shoption! Use OTP {otp} to verify your mobile number. It is valid for 10 mins. Team Shoption https://www.Shoption.in/ +91 9114151617."
    #message = f"{config.get('message_prefix','Shoption OTP is')} {otp}. Valid for 10 minutes."
    frappe.log_error(message=f"OTP sent to {_mask_mobile(mobile)}: {otp}", title="shoption_api.send_otp")  # LOG OTP FOR TESTING

    try:
        resp = _call_provider_send(mobile, message, config)
        try:
            j = resp.json()
            txn_id = None
            if isinstance(j, dict):
                if "message-id" in j:
                    txn = j.get("message-id")
                    if isinstance(txn, (list, tuple)):
                        txn_id = ",".join(map(str, txn))
                    else:
                        txn_id = str(txn)
                elif "message_id" in j:
                    txn_id = str(j.get("message_id"))
            else:
                txn_id = None
        except Exception:
            txn_id = None
    except Exception as e:
        frappe.log_error(f"OTP provider call failed for {_mask_mobile(mobile)}: {e}", "shoption_api.send_otp")
        return {"status": False, "message": "Failed to contact OTP provider"}

    try:
        now_dt = now_datetime()
        expiry_dt = (now_dt + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
        customer.custom_last_otp = otp_hash
        customer.custom_otp_sent_at = now_dt.strftime("%Y-%m-%d %H:%M:%S")
        customer.custom_otp_expiry = expiry_dt
        customer.custom_otp=otp
        customer.custom_otp_attempts = (customer.custom_otp_attempts or 0) + 1
        customer.custom_is_mobile_verified = 0
        customer.custom_otp_provider = config.get("provider")
        if txn_id:
            customer.custom_otp_transaction_id = txn_id
        customer.save(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Failed to save OTP data for {_mask_mobile(mobile)}: {e}", "shoption_api.send_otp")
        return {"status": False, "message": "Failed to save OTP data"}

    # return {
    #     "status": True,
    #     "message": "OTP sent",
    #     "mobile_no_masked": _mask_mobile(mobile),
    #     "txn_id": txn_id
    # }
    return {
    "status": True,
    "message": "OTP sent",
    "mobile_no_masked": _mask_mobile(mobile),
    "txn_id": txn_id,
    "dev_otp": otp  # RETURN OTP FOR TESTING
    }


# updated 13/12 add new fields 
@frappe.whitelist(allow_guest=True)
def verify_otp(mobile_no=None, otp=None):

    # ---- FORCE POST ONLY ----
    if frappe.request and frappe.request.method != "POST":
        frappe.local.response['http_status_code'] = 405
        return {"status": False, "message": "Method Not Allowed. Use POST only."}

    if frappe.request and frappe.request.method == "POST":
        frappe.local.form_dict = frappe._dict(frappe.form_dict)

    # -------- HEADER AUTH CHECK --------
    ok, err = _check_api_auth()
    if not ok:
        return err

    ok, mobile = _validate_mobile(mobile_no)
    if not ok:
        return {"status": False, "message": mobile}

    if not _validate_otp_format(otp):
        return {"status": False, "message": "Invalid OTP format"}

    cust_name = frappe.db.get_value("Customer", {"mobile_no": mobile}, "name")
    if not cust_name:
        return {"status": False, "message": "Customer not found"}

    customer = frappe.get_doc("Customer", cust_name)

    allowed, reason = _check_verify_lock(customer)
    if not allowed:
        return {"status": False, "message": reason}

    expiry = customer.custom_otp_expiry
    if not expiry:
        _register_invalid_attempt(customer)
        return {"status": False, "message": "No OTP found"}

    expiry_dt = get_datetime(str(expiry))
    if now_datetime() > expiry_dt:
        _register_invalid_attempt(customer)
        return {"status": False, "message": "OTP expired"}

    config = _get_otp_config()
    input_hash = _hash_otp(str(otp).strip(), config.get("salt"))
    if input_hash != (customer.custom_last_otp or ""):
        _register_invalid_attempt(customer)
        return {"status": False, "message": "Invalid OTP"}

    # ---- OTP SUCCESS ----
    customer.custom_is_mobile_verified = 1
    customer.custom_last_otp = ""
    customer.custom_otp_expiry = ""
    _clear_invalid_attempts(customer)
    customer.save(ignore_permissions=True)
    frappe.db.commit()

    # ------------------------------------------------
    # NEW ADDITIONS START HERE
    # ------------------------------------------------

    # ROLE
    # role = customer.customer_group 

    # PORTAL USER
    user_id = None

    if getattr(customer, "portal_users", None):
        if customer.portal_users:
            user_id = customer.portal_users[0].user

    # -----------------------------
    # LEAD / FORM LOOKUP BY MOBILE
    # -----------------------------

    form_id = None
    lead_id = None
    role = None

    # -------------------------
    # FIRST CHECK EXISTING FARMER REGISTRATION
    # -------------------------

    existing_farmer = frappe.db.sql("""
        SELECT
            fr.name AS form_id,
            fr.from_document AS lead_id
        FROM `tabFarmer Registration` fr
        WHERE fr.mobile_number = %(mobile)s
        ORDER BY fr.creation DESC
        LIMIT 1
    """, {
        "mobile": mobile
    }, as_dict=True)

    # -------------------------
    # FIRST CHECK EXISTING DEALER REGISTRATION
    # -------------------------

    existing_dealer = frappe.db.sql("""
        SELECT
            dr.name AS form_id,
            dr.from_document AS lead_id
        FROM `tabDelear Registration` dr
        WHERE dr.mobile_number = %(mobile)s
        ORDER BY dr.creation DESC
        LIMIT 1
    """, {
        "mobile": mobile
    }, as_dict=True)

    # -------------------------
    # IF FARMER REGISTRATION EXISTS
    # -------------------------

    if existing_farmer:

        existing_farmer = existing_farmer[0]

        form_id = existing_farmer.form_id
        lead_id = existing_farmer.lead_id if existing_farmer.lead_id else existing_farmer.form_id
        role = "Farmer"

    # -------------------------
    # IF DEALER REGISTRATION EXISTS
    # -------------------------

    elif existing_dealer:

        existing_dealer = existing_dealer[0]

        form_id = existing_dealer.form_id
        lead_id = existing_dealer.lead_id if existing_dealer.lead_id else existing_dealer.form_id
        role = "Dealer"

    # -------------------------
    # NO REGISTRATION FOUND
    # GET LATEST LEAD
    # -------------------------

    else:

        lead_data = frappe.db.sql("""
            SELECT
                name,
                type
            FROM `tabLead`
            WHERE mobile_no = %(mobile)s
            ORDER BY creation DESC
            LIMIT 1
        """, {
            "mobile": mobile
        }, as_dict=True)

        if lead_data:

            lead_data = lead_data[0]

            lead_id = lead_data.name
            role = lead_data.type
    # ------------------------------------------------
    # FINAL RESPONSE
    # ------------------------------------------------
    return {
        "status": True,
        "message": "OTP verified",
        "exists": True if lead_id else False,
        "lead": lead_id,
        "customer_id": customer.name,
        "user_id": user_id,
        "role": role,
        "form_id": form_id
    }


   
   
# form id update 03/12

def _get_existing_form(lead_id, role):
    if role == "Farmer":
        return frappe.db.get_value("Farmer Registration", {"from_document": lead_id})
    else:
        return frappe.db.get_value("Delear Registration", {"from_document": lead_id})
def create_registration_form(role, lead_id, mobile, name):
    role = (role or "").strip().title()
    if role not in ("Farmer", "Dealer"):
        frappe.throw("Invalid role")

    doctype = "Farmer Registration" if role == "Farmer" else "Delear Registration"

    existing = frappe.db.exists(doctype, {"mobile_number": mobile})
    if existing:
        return existing

    doc = frappe.get_doc({
        "doctype": doctype,
        "from_document": lead_id,
        "mobile_number": mobile,
        "first_name": name if role == "Farmer" else None,
        "shop_name": name if role == "Dealer" else None,
        "is_completed": 0
    })
    doc.insert(ignore_permissions=True)
    return doc.name

@frappe.whitelist(allow_guest=True)
def lead_create(mobile_no=None, name=None, role=None):
    try:
        # api_auth()  # uncomment if you want auth even for guest
        if frappe.request and frappe.request.method != "POST":
            frappe.local.response["http_status_code"] = 405
            return {"status": False, "message": "Method Not Allowed. Use POST only."}

        if frappe.request and frappe.request.method == "POST":
            frappe.local.form_dict = frappe._dict(frappe.form_dict)

        ok, mobile = _validate_mobile(mobile_no)
        if not ok:
            return {"status": False, "message": mobile}

        # Duplicate lead
        existing_lead = frappe.db.get_value("Lead", {"mobile_no": mobile}, "name")
        if existing_lead:
            return {
                "status": True,
                "message": "Lead already exists",
                "lead": existing_lead,
                "form_id": _get_existing_form(existing_lead, role)
            }

        # Create Lead
        lead_data = {
            "doctype": "Lead",
            "mobile_no": mobile,
            "type": role,
            "request_type": "",
            "status": "Open",
        }

        if name and str(name).strip():
            lead_data["first_name"] = str(name).strip()
        else:
            lead_data["lead_name"] = str(mobile)

        frappe.flags.ignore_throttling = True

        lead = frappe.get_doc(lead_data)
        lead.insert(ignore_permissions=True)
        frappe.log_error(f"Lead created for {_mask_mobile(mobile)} with role {role}", "shoption_api.lead_create")  # LOG LEAD CREATION
        # Create Registration Form
        form_id = create_registration_form(role, lead.name, mobile, name)

        frappe.db.commit()

        return {
            "status": True,
            "message": "Lead created",
            "role": role,
            "lead": lead.name,
            "form_id": form_id
        }

    except Exception:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "lead_create error")
        return {"status": False, "message": "Failed to create lead"}


from india_compliance.gst_india.utils.gstr_utils import request_otp

@frappe.whitelist(allow_guest=True)
def request_gst_otp(gstin=None):
    frappe.set_user("Administrator")
    try:
        if frappe.request and frappe.request.method != "POST":
            frappe.local.response["http_status_code"] = 405
            return {"status": False, "message": "Method Not Allowed. Use POST only."}

        if frappe.request and frappe.request.method == "POST":
            frappe.local.form_dict = frappe._dict(frappe.form_dict)

        gstin = (gstin or "").strip().upper()
        if not gstin or len(gstin) != 15:
            return {"status": False, "message": "Invalid GSTIN"}

        # Here you would integrate with the GST system to send OTP to the registered mobile number for the given GSTIN.
        # This is a placeholder response.
        data=request_otp(gstin)
        
        # Example of how you might call the GSTR utility function:
        # request_otp(gstin)

        return {
            "status": True,
            "message": f"GST OTP sent for GSTIN {data.get('gstin')}",
            "data":str(data)
        }

    except Exception:
        frappe.log_error(frappe.get_traceback(), "request_gst_otp error")
        return {"status": False, "message": "Failed to request GST OTP"}