import frappe
from frappe.utils import get_url
import json
from urllib.parse import quote
from frappe import _
from frappe.integrations.utils import make_post_request
from frappe_whatsapp.utils import get_whatsapp_account

DEFAULT_APP_LINK = "https://www.shoption.in/app"
DEFAULT_GBRU_LINK = "https://gbru.shoption.in/"
DELIVERY_STATUS_DELIVERED = "delivered"
DEFAULT_TEMPLATE_HEADER_IMAGE = "/files/full_payment_received_img.jpeg"
TEMPLATE_HEADER_IMAGE_MAP = {
    "farmer_registration_msg": "/files/farmer_registration_msg.png",
    "dealer_registration_msg": "/files/dealer_registration_msg.png",
    "order_confirm_scheduled": "/files/standard_order_placement.png",
    "order_placed_cod": "/files/standard_order_placement.png",
    "order_confirm_cod": "/files/standard_order_placement.png",
    "full_payment_done": "/files/full_payment_recieved.png",
    "full_payment_recieved": "/files/full_payment_recieved.png",
    "booking_payment_cod": "/files/booking_payment_recieved_cod.png",
    "booking_payment_recieved_cod": "/files/booking_payment_recieved_cod.png",
    "invoice_generated_hindi": "/files/invoice_generated_scheduled_order.png",
    "invoice_generated_scheduled": "/files/invoice_generated_scheduled_order.png",
    "invoice_generated_scheduled_order": "/files/invoice_generated_scheduled_order.png",
    "invoice_generated_cod": "/files/invoice_generated_cod_order.png",
    "order_delivered_for_dealers": "/files/order_delivered_for_dealer.jpeg",
    "order_delivered_for_dealer": "/files/order_delivered_for_dealer.jpeg",
    "order_delivered_for_farmer": "/files/order_delivered_for_farmer.jpeg",
    "order_dispatched_": "/files/order_dispatched_for_both.png",
    "order_dispatched_scheduled_and_cod": "/files/order_dispatched_for_both.png",
    "order_dispatched_for_both": "/files/order_dispatched_for_both.png",
    "order_delivered_for_kisan_":"/files/order_delivered_for_farmer.jpeg",
    "order_placed_": "/files/standard_order_placement.png",
    "standard_order_placement_": "/files/standard_order_placement.png",
    "mobile_auto_installation": "/files/mobile_auto_installation.jpeg",
    "mobile_auto_promotion": "/files/mobile_auto_promotion.jpeg",
    "seeders_promotion": "/files/seeder_promotion.jpeg",
    "seeder_installation": "/files/seeder_installation.jpeg",
    "solar_camera_installation": "/files/solar_camera_installation.jpeg",
    "solar_camera_promotion": "/files/solar_camera_promotion.jpeg",
    "toofan_spray_pump_installation": "/files/toofan_spray_pump_installation.jpeg",
    "toofan_spray_pump_promotion": "/files/toofan_spray_pump_promotion.jpeg"
}

# Warrior App templates (as per integration guide)
WARRIOR_TEMPLATE_DEALER_REGISTRATION = "dealer_registration_msg"
WARRIOR_TEMPLATE_FARMER_REGISTRATION = "farmer_registration_msg"
WARRIOR_TEMPLATE_FULL_PAYMENT = "full_payment_recieved"
WARRIOR_TEMPLATE_BOOKING_PAYMENT_COD = "booking_payment_recieved_cod"
WARRIOR_TEMPLATE_ORDER_CONFIRM_SCHEDULED = "order_confirm_scheduled"
WARRIOR_TEMPLATE_ORDER_CONFIRM_COD = "order_confirm_cod"
WARRIOR_TEMPLATE_ORDER_PLACED = WARRIOR_TEMPLATE_ORDER_CONFIRM_SCHEDULED
WARRIOR_TEMPLATE_ORDER_DISPATCHED = "order_dispatched_for_both"
WARRIOR_TEMPLATE_INVOICE_GENERATED_SCHEDULED = "invoice_generated_scheduled_order"
WARRIOR_TEMPLATE_INVOICE_GENERATED_COD = "invoice_generated_cod"
WARRIOR_TEMPLATE_INVOICE_GENERATED = WARRIOR_TEMPLATE_INVOICE_GENERATED_SCHEDULED
WARRIOR_TEMPLATE_DELIVERED_KISAN = "order_delivered_for_farmer"
WARRIOR_TEMPLATE_DELIVERED_DEALER = "order_delivered_for_dealer"

# Shoption App templates (as per integration guide)
SHOPTION_TEMPLATE_B2B_PAYMENT_DONE = "b2b_txn_payment_done"
SHOPTION_TEMPLATE_B2B_PAYMENT_FAILED = "b2b_txn_payment"
PAYMENT_TOLERANCE = 1


# Canonical template key -> actual Meta template name configured in WhatsApp Templates
TEMPLATE_ACTUAL_NAME_MAP = {
    "dealer_registration_msg": "dealer_registration_msg",
    "farmer_registration_msg":"farmer_registration_msg",
    "full_payment_received": "full_payment_done",
    "order_placed_": "order_placed_scheduled_delivery",
    "order_dispatched_": "order_dispatched_scheduled_and_cod",
    "invoice_generated_hindi": "invoice_generated_scheduled",
    "order_delivered_for_kisan_": "order_delivered_for_farmer",
    "order_delivered_for_dealers": "order_delivered_for_dealer",
    "b2b_txn_ordered": "b2b_txn_ordered",
    "b2b_txn_payment_done": "b2b_txn_payment_done",
    "b2b_txn_payment": "b2b_txn_payment",
    "order_confirm_scheduled": "order_confirm_scheduled",
    "full_payment_recieved": "full_payment_recieved",
    "invoice_generated_scheduled_order": "invoice_generated_scheduled_order",
    "order_confirm_cod": "order_confirm_cod",
    "booking_payment_recieved_cod": "booking_payment_recieved_cod",
    "invoice_generated_cod": "invoice_generated_cod",
    "order_dispatched_for_both": "order_dispatched_for_both",
    "order_placed_scheduled_delivery": "order_placed_scheduled_delivery",
    "full_payment_done": "full_payment_done",
    "invoice_generated_scheduled": "invoice_generated_scheduled",
    "order_placed_cod": "order_placed_cod",
    "booking_payment_cod": "booking_payment_cod",
    "invoice_generated_cod": "invoice_generated_cod",
    "order_dispatched_scheduled_and_cod": "order_dispatched_scheduled_and_cod",
    "standard_order_placement_": "standard_order_placement_",
    "seeders_campaign_lead": "seeders_campaign_lead",
    "solar_camera_campaign_lead": "solar_camera_campaign_lead",
    "mobile_auto_campaign_lead": "mobile_auto_campaign_lead",
    "spray_pump_campaign_lead": "spray_pump_campaign_lead",
    "order_delivered_for_farmer": "order_delivered_for_farmer",
    "order_delivered_for_dealer": "order_delivered_for_dealer",
    "seeders_promotion": "seeders_promotion",
    "solar_camera_promotion": "solar_camera_promotion",
    "mobile_auto_promotion": "mobile_auto_promotion",
    "toofan_spray_pump_promotion": "toofan_spray_pump_promotion",
    "seeder_installation": "seeder_installation",
    "mobile_auto_installation": "mobile_auto_installation",
    "solar_camera_installation": "solar_camera_installation",
    "toofan_spray_pump_installation": "toofan_spray_pump_installation",
}
TEMPLATE_LANGUAGE_FALLBACK_MAP = {
    "b2b_txn_payment": "en",
    "b2b_txn_payment_done": "en_GB",
    "booking_payment_cod": "en_US",
    "booking_payment_recieved_cod": "hi",
    "full_payment_done": "en_US",
    "full_payment_recieved": "hi",
    "invoice_generated_cod": "en_US",
    "invoice_generated_cod": "hi",
    "invoice_generated_scheduled": "en_US",
    "invoice_generated_scheduled_order": "hi",
    "order_delivered_for_dealer": "hi",
    "order_delivered_for_farmer": "hi",
    "order_dispatched_scheduled_and_cod": "hi",
    "order_dispatched_for_both": "hi",
    "order_confirm_cod": "hi",
    "order_confirm_scheduled": "hi",
    "order_placed_cod": "en_US",
    "order_placed_scheduled_delivery": "hi",
    "standard_order_placement_": "hi",
    "seeders_campaign_lead": "hi",
    "solar_camera_campaign_lead": "hi",
    "mobile_auto_campaign_lead": "hi",
    "spray_pump_campaign_lead": "hi",
        "seeders_promotion": "hi",
    "solar_camera_promotion": "hi",
    "mobile_auto_promotion": "hi",
    "toofan_spray_pump_promotion": "hi",
}

TEMPLATE_NAMED_BODY_PARAMETER_MAP = {
    "full_payment_done": ["Name", "Order_ID", "Order_Amount", "Amount", "App_Link"],
    "order_dispatched_scheduled_and_cod": [
        "Name",
        "Order_ID",
        "Invoice_ID",
        "Invoice_Amount",
        "Transporter_Name",
        "Tracking_Link",
    ],
    "order_placed_cod": ["Name", "Order_ID", "Order_Amount", "Booking_Amount", "Pending_Amount"],
    "order_placed_scheduled_delivery": ["Order_ID", "Order_Amount"],
}


def _normalize_phone(phone):
    if not phone:
        return None
    digits = "".join(ch for ch in str(phone) if ch.isdigit())
    if not digits:
        return None
    if digits.startswith("91") and len(digits) >= 12:
        return digits
    if len(digits) == 10:
        return f"91{digits}"
    return digits


def _find_template_docname(template_name):
    actual_name = TEMPLATE_ACTUAL_NAME_MAP.get(template_name, template_name)

    name = frappe.db.get_value("WhatsApp Templates", {"actual_name": actual_name}, "name")
    if name:
        return name

    name = frappe.db.get_value("WhatsApp Templates", {"template_name": actual_name}, "name")
    if name:
        return name

    name = frappe.db.get_value("WhatsApp Templates", {"template_name": template_name}, "name")
    if name:
        return name
    return frappe.db.get_value("WhatsApp Templates", {"actual_name": template_name}, "name")


def _get_template_account(template_doc):
    if template_doc and template_doc.whatsapp_account:
        return frappe.get_doc("WhatsApp Account", template_doc.whatsapp_account)
    return get_whatsapp_account(account_type="outgoing")


def _build_template_payload(template_name, template_doc, to_phone, payload, button_payload=None):
    payload = payload or {}
    actual_name = TEMPLATE_ACTUAL_NAME_MAP.get(template_name, template_name)
    language_code = (
        template_doc.language_code
        if template_doc and template_doc.language_code
        else TEMPLATE_LANGUAGE_FALLBACK_MAP.get(template_name, "en")
    )
    data = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "template",
        "template": {
            "name": actual_name,
            "language": {"code": language_code},
            "components": [],
        },
    }
    named_parameters = TEMPLATE_NAMED_BODY_PARAMETER_MAP.get(actual_name)
    if named_parameters:
        parameters = []
        for parameter_name in named_parameters:
            value = payload.get(parameter_name)
            if value is not None:
                parameters.append(
                    {
                        "type": "text",
                        "parameter_name": parameter_name,
                        "text": str(value),
                    }
                )
        if parameters:
            data["template"]["components"].append({"type": "body", "parameters": parameters})
    elif payload:
        values = list(payload.values())
        data["template"]["components"].append(
            {"type": "body", "parameters": [{"type": "text", "text": str(v)} for v in values]}
        )

    header_url = None
    header_type = ((template_doc.header_type if template_doc else "image") or "").lower()
    if template_doc and header_type != "image":
        header_url = None
    elif template_doc and template_doc.sample:
        header_url = template_doc.sample
    else:
        header_url = TEMPLATE_HEADER_IMAGE_MAP.get(template_name, DEFAULT_TEMPLATE_HEADER_IMAGE)

    if header_url:
        if not str(header_url).startswith("http"):
            header_url = f"{get_url()}{header_url}"
        data["template"]["components"].append(
            {
                "type": "header",
                "parameters": [{"type": "image", "image": {"link": header_url}}],
            }
        )

    for button in button_payload or []:
        data["template"]["components"].append(
            {
                "type": "button",
                "sub_type": button.get("sub_type", "url"),
                "index": str(button.get("index", 0)),
                "parameters": [{"type": "text", "text": str(button.get("text", ""))}],
            }
        )

    return data

def _send_via_template(template_name, phone, payload, dedupe_key, force=False, button_payload=None):
    if not phone:
        frappe.log_error("WA Debug: Missing phone", f"template={template_name}, dedupe={dedupe_key}")
        return

    if not force and not _send_once(dedupe_key):
        frappe.log_error("WA Debug: Deduped", f"template={template_name}, dedupe={dedupe_key}")
        return

    try:
        normalized_phone = _normalize_phone(phone)
        if not normalized_phone:
            frappe.log_error("WA Debug: Phone normalize failed", f"template={template_name}, phone={phone}")
            return
        template_doc = None
        template_docname = _find_template_docname(template_name)
        if template_docname:
            template_doc = frappe.get_doc("WhatsApp Templates", template_docname)
        else:
            frappe.log_error(
                "WA Debug: Template doc missing",
                f"template={template_name}, to={normalized_phone}, dedupe={dedupe_key}",
            )

        whatsapp_account = _get_template_account(template_doc)
        if not whatsapp_account:
            frappe.throw(_("Please set a default outgoing WhatsApp Account"))

        data = _build_template_payload(template_name, template_doc, normalized_phone, payload, button_payload)
        token = whatsapp_account.get_password("token")
        headers = {"authorization": f"Bearer {token}", "content-type": "application/json"}
        frappe.log_error(
            "WA Debug: Sending Meta",
            f"template={template_name}, to={normalized_phone}, payload={json.dumps(data)}",
        )
        response = make_post_request(
            f"{whatsapp_account.url.strip()}/{whatsapp_account.version}/{whatsapp_account.phone_id}/messages",
            headers=headers,
            data=json.dumps(data),
        )
        frappe.log_error(
            "WA Debug: Meta send success",
            f"template={template_name}, to={normalized_phone}, response={json.dumps(response)}",
        )
        parameters = None
        if data["template"]["components"]:
            for comp in data["template"]["components"]:
                if comp.get("type") == "body":
                    parameters = [param["text"] for param in comp["parameters"]]
                    parameters = frappe.json.dumps(parameters, default=str)
                    break

        frappe.get_doc(
            {
                "doctype": "WhatsApp Message",
                "type": "Outgoing",
                "message": str(data["template"]),
                "to": normalized_phone,
                "message_type": "Template",
                "message_id": response["messages"][0]["id"],
                "content_type": (((template_doc.header_type if template_doc else "image") or "image")).lower(),
                "use_template": 1,
                "template": (template_doc.name if template_doc else None),
                "template_parameters": parameters,
                "whatsapp_account": whatsapp_account.name,
            }
        ).save(ignore_permissions=True)

        frappe.get_doc(
            {
                "doctype": "WhatsApp Notification Log",
                "template": (template_doc.name if template_doc else template_name),
                "meta_data": frappe.flags.integration_request.json() if frappe.flags.integration_request else response,
            }
        ).insert(ignore_permissions=True)
    except Exception as e:
        error_message = str(e)
        if frappe.flags.integration_request:
            api_error = frappe.flags.integration_request.json().get("error", {})
            if api_error:
                error_message = api_error.get("Error", api_error.get("message", error_message))

        frappe.log_error(
            title=f"WhatsApp Template Send Failed: {template_name}",
            message=frappe.get_traceback(),
        )
        frappe.get_doc(
            {
                "doctype": "WhatsApp Notification Log",
                "template": template_name,
                "meta_data": {"error": error_message},
            }
        ).insert(ignore_permissions=True)

def _is_dealer(customer):
    group = (frappe.db.get_value("Customer", customer, "customer_group") or "").lower()
    return "dealer" in group


def _is_farmer(customer):
    group = (frappe.db.get_value("Customer", customer, "customer_group") or "").lower()
    return "farmer" in group or "kisan" in group


def _customer_name(customer):
    return frappe.db.get_value("Customer", customer, "customer_name") or customer


def _sales_order_payment_values(order_id, booking_amount=None):
    order_amount, order_booking_amount, advance_paid = frappe.db.get_value(
        "Sales Order",
        order_id,
        ["rounded_total", "custom_pay_on_proceed_order", "advance_paid"],
    ) or (0, 0, 0)
    order_amount = round(float(order_amount or frappe.db.get_value("Sales Order", order_id, "grand_total") or 0), 2)
    paid_amount = round(float(order_booking_amount or 0), 2)
    if not paid_amount and booking_amount is not None:
        paid_amount = round(float(booking_amount or 0), 2)
    pending_amount = round(max(order_amount - paid_amount, 0), 2)
    return order_amount, paid_amount, pending_amount


def _sales_order_paid_amount(order_id, payment_amount=None):
    advance_paid = round(float(frappe.db.get_value("Sales Order", order_id, "advance_paid") or 0), 2)
    if payment_amount is not None:
        advance_paid = round(max(advance_paid, float(payment_amount or 0)), 2)
    return advance_paid


def _tracking_url(value=None):
    return _safe_url(value or DEFAULT_GBRU_LINK)


def _safe_url(url):
    if not url:
        return url
    return quote(str(url), safe="/:?&=%#")


def _normalize_text(value):
    return (value or "").strip().lower()


def _is_cod_sales_order(order):
    if not order:
        return False

    payment_type = (
        getattr(order, "custom_payment_type", None)
        if not isinstance(order, str)
        else frappe.db.get_value("Sales Order", order, "custom_payment_type")
    )
    return (payment_type or "").strip().lower() == "cash on delivery"


def _get_sales_invoice_print_format():
    print_format = "Standard"
    default_print_format = frappe.db.get_value(
        "Property Setter",
        filters={"doc_type": "Sales Invoice", "property": "default_print_format"},
        fieldname="value",
    )
    if default_print_format:
        print_format = default_print_format
    return print_format


def _customer_phone(customer):
    fields = [
        "mobile_no",
        "custom_whatsapp_number",
        "custom_mobile_no",
        "custom_phone",
    ]
    for field in fields:
        v = frappe.db.get_value("Customer", customer, field)
        if v:
            return v

    contact = frappe.db.get_value(
        "Dynamic Link", {"link_doctype": "Customer", "link_name": customer, "parenttype": "Contact"}, "parent"
    )
    if contact:
        return frappe.db.get_value("Contact", contact, "mobile_no") or frappe.db.get_value("Contact", contact, "phone")
    return None


def _send_once(key):
    cache = frappe.cache()
    if cache.get_value(key):
        return False
    cache.set_value(key, 1, expires_in_sec=86400)
    return True


def _send_warrior_payment_success(phone, customer_name, order_id, order_amount, amount, pending_amount, dedupe_seed, is_cod=False):
    template_name = WARRIOR_TEMPLATE_BOOKING_PAYMENT_COD if is_cod else WARRIOR_TEMPLATE_FULL_PAYMENT
    payload = (
        {
            "Order_ID": order_id,
            "Order_Amount": order_amount,
            "Booking_Amount": amount,
            "Pending_Amount": pending_amount,
        }
        if is_cod
        else {
            "Order_ID": order_id,
            "Order_Amount": order_amount,
            "Amount": amount,
            "App_Link": DEFAULT_APP_LINK,
        }
    )
    _send_via_template(
        template_name,
        phone,
        payload,
        f"wa:{template_name}:{dedupe_seed}",
    )

def _send_warrior_order_placed(phone, customer_name, order_id, order_amount, booking_amount, pending_amount, dedupe_seed, is_cod=False):
    template_name = WARRIOR_TEMPLATE_ORDER_CONFIRM_COD if is_cod else WARRIOR_TEMPLATE_ORDER_CONFIRM_SCHEDULED
    payload = (
        {
            "Order_ID": order_id,
            "Order_Amount": order_amount,
            "Booking_Amount": booking_amount,
            "Pending_Amount": pending_amount,
        }
        if is_cod
        else {"Order_ID": order_id, "Order_Amount": order_amount}
    )
    _send_via_template(
        template_name,
        phone,
        payload,
        f"wa:{template_name}:{dedupe_seed}",
    )


def _send_shoption_payment_success(phone, customer_name, order_id, txn_id, amount, dedupe_seed):
    _send_via_template(
        SHOPTION_TEMPLATE_B2B_PAYMENT_DONE,
        phone,
        {
            "customer_name": customer_name,
            "order_id": order_id,
            "txn_id": txn_id,
            "amount": amount,
        },
        f"wa:b2b_payment_done:{dedupe_seed}",
    )


def _send_shoption_payment_failed(phone, customer_name, order_id, amount, dedupe_seed):
    _send_via_template(
        SHOPTION_TEMPLATE_B2B_PAYMENT_FAILED,
        phone,
        {"customer_name": customer_name, "order_id": order_id, "amount": amount},
        f"wa:b2b_payment_failed:{dedupe_seed}",
    )


def _send_warrior_dispatch(phone, transport, transporter_mobile, dispatch_receipt_url, invoice_id, order_id, customer_name="-", invoice_amount="-"):
    _send_via_template(
        WARRIOR_TEMPLATE_ORDER_DISPATCHED,
        phone,
        {
            "Order_ID": order_id,
            "Invoice_ID": invoice_id,
            "Invoice_Amount": invoice_amount,
            "Transporter_Name": transport,
            "Tracking_Link": _tracking_url(dispatch_receipt_url),
        },
        f"wa:dispatch:{order_id}:{invoice_id}",
    )


def _send_warrior_delivered_farmer(phone, order_id, invoice_id, invoice_amount, source_key=None):
    dedupe_tail = source_key or invoice_id or order_id
    _send_via_template(
        WARRIOR_TEMPLATE_DELIVERED_KISAN,
        phone,
        {
            "order_id": order_id,
            "invoice_id": invoice_id,
            "invoice_amount": invoice_amount,
            "app_url": DEFAULT_APP_LINK,
        },
        f"wa:delivered:farmer:{order_id}:{dedupe_tail}",
    )


def _send_warrior_delivered_dealer(phone, order_id, invoice_id, invoice_amount, source_key=None):
    dedupe_tail = source_key or invoice_id or order_id
    _send_via_template(
        WARRIOR_TEMPLATE_DELIVERED_DEALER,
        phone,
        {
            "order_id": order_id,
            "invoice_id": invoice_id,
            "invoice_amount": invoice_amount,
            "app_url": DEFAULT_APP_LINK,
        },
        f"wa:delivered:dealer:{order_id}:{dedupe_tail}",
    )


def _send_warrior_invoice_generated(
    phone,
    customer_name,
    invoice_id,
    invoice_amount,
    order_amount,
    order_id,
    invoice_path,
    booking_amount=0,
    pending_amount=0,
    is_cod=False,
):
    template_name = (
        WARRIOR_TEMPLATE_INVOICE_GENERATED_COD if is_cod else WARRIOR_TEMPLATE_INVOICE_GENERATED_SCHEDULED
    )
    payload = (
        {
            "Order_ID": order_id,
            "Order_Amount": order_amount,
            "Booking_Amount": booking_amount,
            "Invoice_ID": invoice_id,
            "Invoice_Amount": invoice_amount,
            "Pending_Amount": pending_amount,
            "Invoice_Link": invoice_path or DEFAULT_GBRU_LINK,
        }
        if is_cod
        else {
            "Order_ID": order_id,
            "Order_Amount": order_amount,
            "Invoice_ID": invoice_id,
            "Invoice_Amount": invoice_amount,
            "Invoice_Link": invoice_path or DEFAULT_GBRU_LINK,
        }
    )
    _send_via_template(
        template_name,
        phone,
        payload,
        f"wa:{template_name}:{invoice_id}",
    )

def _get_sales_order_customer_by_invoice(sales_invoice):
    order_id = frappe.db.get_value("Sales Invoice Item", {"parent": sales_invoice}, "sales_order")
    if not order_id:
        return None, None
    customer = frappe.db.get_value("Sales Order", order_id, "customer")
    return order_id, customer


def _get_payment_entry_sales_orders(doc):
    sales_orders = {}
    for ref in (getattr(doc, "references", None) or []):
        reference_doctype = getattr(ref, "reference_doctype", None)
        reference_name = getattr(ref, "reference_name", None)
        if not reference_doctype or not reference_name:
            continue

        order_id = None
        if reference_doctype == "Sales Order":
            order_id = reference_name
        elif reference_doctype == "Sales Invoice":
            order_id = frappe.db.get_value("Sales Invoice Item", {"parent": reference_name}, "sales_order")

        if not order_id:
            continue

        allocated = float(getattr(ref, "allocated_amount", 0) or 0)
        sales_orders[order_id] = sales_orders.get(order_id, 0) + allocated

    return sales_orders


def handle_dealer_registration(doc, method=None):
    if doc.docstatus != 1:
        return

    customer = doc.name
    phone = _normalize_phone(doc.mobile_number)
    if not phone:
        return

    _send_via_template(
        WARRIOR_TEMPLATE_DEALER_REGISTRATION,
        phone,
        {"app_url": DEFAULT_APP_LINK},
        f"wa:dealer_registration:{customer}",
        force=True,
    )

def handle_farmers_registration(doc, method=None):
    if doc.docstatus != 1:
        return

    customer = doc.name
    phone = doc.mobile_number
    if not phone:
        return

    _send_via_template(
        WARRIOR_TEMPLATE_FARMER_REGISTRATION,
        phone,
        {},
        f"wa:farmer_registration:{customer}",
        force=True,
    )


def handle_payment_entry_whatsapp(doc, method=None):
    if getattr(doc, "docstatus", 0) != 1:
        return
    if getattr(doc, "party_type", None) != "Customer":
        return

    sales_orders = _get_payment_entry_sales_orders(doc)
    if not sales_orders:
        return

    txn_id = getattr(doc, "reference_no", None) or doc.name

    for order_id, paid_amount in sales_orders.items():
        customer = frappe.db.get_value("Sales Order", order_id, "customer")
        if not customer:
            continue

        phone = _customer_phone(customer)
        if not phone:
            continue

        order_amount, booking_amount, pending_amount = _sales_order_payment_values(order_id)
        total_paid = _sales_order_paid_amount(order_id, paid_amount)
        is_fully_paid = total_paid >= (order_amount - PAYMENT_TOLERANCE)
        is_cod = _is_cod_sales_order(order_id)
        customer_name = _customer_name(customer)

        if is_cod:
            _send_warrior_payment_success(
                phone,
                customer_name,
                order_id,
                order_amount,
                booking_amount,
                pending_amount,
                doc.name,
                is_cod=True,
            )
        elif is_fully_paid:
            _send_warrior_payment_success(
                phone,
                customer_name,
                order_id,
                order_amount,
                paid_amount,
                pending_amount,
                doc.name,
            )
            _send_shoption_payment_success(
                phone,
                customer_name,
                order_id,
                txn_id,
                paid_amount,
                doc.name,
            )
        # Partial-payment WhatsApp success notification is intentionally disabled for now.


def handle_order_placed(doc,method):
    if doc.docstatus != 1:
        return

    customer = doc.customer
    phone = doc.contact_mobile or _customer_phone(customer)
    if not phone:
        return

    order_id = doc.name
    order_amount, booking_amount, pending_amount = _sales_order_payment_values(order_id)
    customer_name = _customer_name(customer)
    _send_warrior_order_placed(
        phone,
        customer_name,
        order_id,
        order_amount,
        booking_amount,
        pending_amount,
        order_id,
        is_cod=_is_cod_sales_order(doc),
    )

def handle_payu_transaction(doc, method=None):
    if getattr(doc, "status", None) not in {"Success", "Failed"}:
        return

    order_id=frappe.db.get_value("Payment Gateway Transaction", {"txn_id":doc.txnid}, "order_id")
    so_customer = frappe.db.get_value("Sales Order", order_id, "customer")
    if not so_customer:
        return

    phone =doc.phone or  _customer_phone(so_customer)
    if not phone:
        return

    amount = float(doc.amount or 0)
    order_amount = float(frappe.db.get_value("Sales Order", order_id, "grand_total") or amount)
    customer_name = _customer_name(so_customer)

    if doc.status == "Failed":
        _send_shoption_payment_failed(phone, customer_name, order_id, order_amount, doc.name)

def handle_rupifi_webhook_log(doc, method=None):
    if not getattr(doc, "order_id", None):
        return

    so_customer = frappe.db.get_value("Sales Order", doc.order_id, "customer")
    if not so_customer:
        return

    phone = _customer_phone(so_customer)
    if not phone:
        return

    order_id = doc.order_id
    amount = float(doc.amount_value or 0)
    order_amount = float(frappe.db.get_value("Sales Order", order_id, "grand_total") or amount)
    customer_name = _customer_name(so_customer)

    if doc.status and doc.status != "CAPTURED":
        _send_shoption_payment_failed(phone, customer_name, order_id, order_amount, doc.name)


def handle_sales_order_dispatch_delivery(doc, method=None):
    if doc.docstatus != 1:
        return

    old_doc = doc.get_doc_before_save()

    lr_fields = ["custom_lr_number", "lr_number", "custom_lorry_receipt_no"]
    track_fields = ["custom_tracking_id", "tracking_id", "custom_tracking_number"]
    transport_fields = ["custom_transport_name", "transporter_name", "custom_transporter"]

    def first_val(fields):
        for f in fields:
            if getattr(doc, f, None):
                return getattr(doc, f)
        return None

    def old_val(fields):
        if not old_doc:
            return None
        for f in fields:
            if getattr(old_doc, f, None):
                return getattr(old_doc, f)
        return None

    lr = first_val(lr_fields)
    tracking = first_val(track_fields) or "-"
    transport = first_val(transport_fields) or "-"
    old_lr = old_val(lr_fields)

    customer = doc.customer
    phone = _customer_phone(customer)
    if not phone:
        return

    if lr and lr != old_lr:
        invoice_id = frappe.db.get_value("Sales Invoice Item", {"sales_order": doc.name}, "parent") or "-"
        invoice_amount = frappe.db.get_value("Sales Invoice", invoice_id, "grand_total") if invoice_id != "-" else "-"
        _send_warrior_dispatch(
            phone,
            transport,
            lr,
            tracking,
            invoice_id,
            doc.name,
            customer_name=_customer_name(customer),
            invoice_amount=invoice_amount,
        )

    delivery_status = (getattr(doc, "delivery_status", "") or "").lower()
    old_delivery_status = ((getattr(old_doc, "delivery_status", "") if old_doc else "") or "").lower()

    if delivery_status == DELIVERY_STATUS_DELIVERED and old_delivery_status != DELIVERY_STATUS_DELIVERED:
        invoice_id = frappe.db.get_value("Sales Invoice Item", {"sales_order": doc.name}, "parent") or "-"
        invoice_amount = frappe.db.get_value("Sales Invoice", invoice_id, "grand_total") if invoice_id != "-" else "-"

        if _is_farmer(customer):
            _send_warrior_delivered_farmer(phone, doc.name, invoice_id, invoice_amount)

        if _is_dealer(customer):
            _send_warrior_delivered_dealer(phone, doc.name, invoice_id, invoice_amount)


def handle_invoice_generated(doc, method=None):
    if doc.docstatus != 1:
        return
    if getattr(doc, "is_return", 0) or getattr(doc, "return_against", None):
        return

    customer = doc.customer
    phone = _customer_phone(customer)
    if not phone:
        return

    print_format = quote(_get_sales_invoice_print_format())
    invoice_pdf = (
        f"{get_url()}/api/method/frappe.utils.print_format.download_pdf"
        f"?doctype=Sales%20Invoice&name={doc.name}&format={print_format}&no_letterhead=0"
    )
    order_id = frappe.db.get_value("Sales Invoice Item", {"parent": doc.name}, "sales_order") or "-"
    order_amount = frappe.db.get_value("Sales Order", order_id, "grand_total") or "-"
    booking_amount, pending_amount = 0, 0
    if order_id != "-":
        _, booking_amount, pending_amount = _sales_order_payment_values(order_id)
    _send_warrior_invoice_generated(
        phone=phone,
        customer_name=_customer_name(customer),
        invoice_id=doc.name,
        invoice_amount=doc.grand_total or 0,
        order_amount=order_amount,
        order_id=order_id,
        invoice_path=invoice_pdf,
        booking_amount=booking_amount,
        pending_amount=pending_amount,
        is_cod=_is_cod_sales_order(order_id),
    )


def handle_indian_post_tracking_dispatch(doc, method=None):
    # Indian Post dispatch WhatsApp is sent only after the Sales Invoice
    # reaches custom_dispatch_status = "Dispatched".
    return


def handle_sales_invoice_dispatched_whatsapp(doc, method=None):
    if getattr(doc, "docstatus", 0) != 1:
        return
    if _normalize_text(getattr(doc, "custom_dispatch_status", None)) != "dispatched":
        return
    if _normalize_text(getattr(doc, "transporter_name", None)) != "indian post":
        return

    customer = getattr(doc, "customer", None)
    if not customer or not _is_farmer(customer):
        return

    order_id = frappe.db.get_value("Sales Invoice Item", {"parent": doc.name}, "sales_order")
    if not order_id:
        return

    tracking_log = frappe.db.get_all(
        "Indian Post Tracking Log",
        filters={
            "reference_type": "Sales Invoice",
            "reference_name": doc.name,
            "is_cancelled": 0,
        },
        fields=["name", "transporter", "transporter_name"],
        order_by="creation desc",
        limit=1,
    )
    if not tracking_log:
        return

    phone = _customer_phone(customer)
    if not phone:
        return

    log = tracking_log[0]
    dispatch_receipt_url = (
        f"{get_url()}/printview?doctype=Indian%20Post%20Tracking%20Log"
        f"&name={quote(log.name)}&format={quote('Standard')}&no_letterhead=0"
    )
    invoice_amount = round(float(getattr(doc, "rounded_total", None) or getattr(doc, "grand_total", 0) or 0), 2)
    _send_warrior_dispatch(
        phone,
        log.get("transporter_name") or log.get("transporter") or "Indian Post",
        "-",
        dispatch_receipt_url,
        doc.name,
        order_id,
        customer_name=_customer_name(customer),
        invoice_amount=invoice_amount,
    )


def handle_upload_lr_main_dispatch(doc, method=None):
    if getattr(doc, "docstatus", 0) != 1:
        return

    order_id = getattr(doc, "sales_order", None)
    customer = None
    if order_id:
        customer = frappe.db.get_value("Sales Order", order_id, "customer")
    if not customer and getattr(doc, "sales_invoice", None):
        order_id, customer = _get_sales_order_customer_by_invoice(doc.sales_invoice)

    if not order_id or not customer:
        return

    phone = _customer_phone(customer)
    if not phone:
        return

    transport = getattr(doc, "transporter_name", None) or "-"
    transporter_mobile = frappe.db.get_value("Supplier", getattr(doc, "transporter", None), "mobile_no") or "-"
    dispatch_receipt_url = None
    if getattr(doc, "lr_copy", None):
        dispatch_receipt_url = doc.lr_copy if str(doc.lr_copy).startswith("http") else f"{get_url()}{doc.lr_copy}"
        dispatch_receipt_url = _safe_url(dispatch_receipt_url)
    if not dispatch_receipt_url:
        dispatch_receipt_url = f"{get_url()}/app/upload-lr-main/{quote(doc.name)}"
    invoice_id = getattr(doc, "sales_invoice", None) or "-"
    invoice_amount = frappe.db.get_value("Sales Invoice", invoice_id, "grand_total") if invoice_id != "-" else "-"
    _send_warrior_dispatch(
        phone,
        transport,
        transporter_mobile,
        dispatch_receipt_url,
        invoice_id,
        order_id,
        customer_name=_customer_name(customer),
        invoice_amount=invoice_amount,
    )


def handle_shipment_delivered(doc, method=None):
    frappe.log_error("WA Debug: Shipment trigger entered", f"shipment={doc.name}, docstatus={getattr(doc, 'docstatus', None)}")
    if getattr(doc, "docstatus", 0) != 1:
        frappe.log_error("WA Debug: Shipment skipped", f"reason=docstatus_not_submitted, shipment={doc.name}")
        return

    sales_invoice = getattr(doc, "custom_sales_invoice", None)
    if not sales_invoice:
        frappe.log_error("WA Debug: Shipment skipped", f"reason=missing_custom_sales_invoice, shipment={doc.name}")
        return

    order_id, customer = _get_sales_order_customer_by_invoice(sales_invoice)
    if not order_id or not customer:
        frappe.log_error(
            "WA Debug: Shipment skipped",
            f"reason=missing_order_or_customer, shipment={doc.name}, sales_invoice={sales_invoice}, order_id={order_id}, customer={customer}",
        )
        return

    phone = _customer_phone(customer)
    if not phone:
        frappe.log_error(
            "WA Debug: Shipment skipped",
            f"reason=missing_phone, shipment={doc.name}, customer={customer}, sales_invoice={sales_invoice}",
        )
        return

    invoice_id = sales_invoice
    invoice_amount = frappe.db.get_value("Sales Invoice", invoice_id, "grand_total") or "-"
    frappe.log_error(
        "WA Debug: Shipment resolved",
        f"shipment={doc.name}, sales_invoice={sales_invoice}, order_id={order_id}, customer={customer}, phone={phone}",
    )
    if _is_farmer(customer):
        _send_warrior_delivered_farmer(phone, order_id, invoice_id, invoice_amount, source_key=f"shipment:{doc.name}")
    if _is_dealer(customer):
        _send_warrior_delivered_dealer(phone, order_id, invoice_id, invoice_amount, source_key=f"shipment:{doc.name}")
