
# # working 
# import frappe
# from frappe.utils.file_manager import save_file
# from shoption_api.erp_api.common import api_auth, require_post, api_response

# @frappe.whitelist(allow_guest=True)
# def apply_dealership(
#     dealership_type=None,
#     dealership_plan=None,
#     dealer_id=None,

#     country=None,
#     state=None,
#     district=None,
#     pincode=None,
#     address=None,
#     shop_name=None,

#     machinery=None,
#     ksk=None,
#     consumable=None,
#     other=None,

#     shop_opening_year=None,
#     employee_number=None,
#     have_godown=None,

#     gst_number=None,
#     primary_bank_name=None,

#     name1=None,
#     mobile_number=None,
#     whatsapp=None,
#     pan=None,
#     dob=None,

#     token_yantra=None,
#     mulching=None,
#     tarapaulin=None,
#     tools=None,
#     drip=None,
#     kitkat=None,
#     capacitor=None,
#     motor_pump=None,
#     pipes=None,
#     starters=None,
#     cables_wires=None,
#     spray_pumps=None,
#     ropes=None,

#     tehsils=None,           # list / json / comma-separated
#     marketplaces=None,     # list / json / comma-separated

#     shop_name_as_gst=None,
#     authorized_person_name=None,
#     place=None,
#     date=None
# ):
#     api_auth()
#     require_post()
#     frappe.set_user("Administrator")
#     frappe.flags.ignore_throttling = True

#     # Create Apply Dealership document
#     doc = frappe.new_doc("Apply Dealership")

#     # Simple field mapping (no cleaning)
#     doc.dealership_type = dealership_type
#     doc.dealership_plan = dealership_plan
#     doc.dealer_id = dealer_id

#     doc.country = country
#     doc.state = state
#     doc.district = district
#     doc.pincode = pincode
#     doc.address = address
#     doc.shop_name = shop_name

#     doc.machinery = machinery
#     doc.ksk = ksk
#     doc.consumable = consumable
#     doc.other = other

#     doc.shop_opening_year = shop_opening_year
#     doc.employee_number = employee_number
#     doc.have_godown = have_godown

#     doc.gst_number = gst_number
#     doc.primary_bank_name = primary_bank_name

#     doc.name1 = name1
#     doc.mobile_number = mobile_number
#     doc.whatsapp = whatsapp
#     doc.pan = pan
#     doc.dob = dob

#     doc.token_yantra = token_yantra
#     doc.mulching = mulching
#     doc.tarapaulin = tarapaulin
#     doc.tools = tools
#     doc.drip = drip
#     doc.kitkat = kitkat
#     doc.capacitor = capacitor
#     doc.motor_pump = motor_pump
#     doc.pipes = pipes
#     doc.starters = starters
#     doc.cables_wires = cables_wires
#     doc.spray_pumps = spray_pumps
#     doc.ropes = ropes

#     doc.shop_name_as_gst = shop_name_as_gst
#     doc.authorized_person_name = authorized_person_name
#     doc.place = place
#     doc.date = date

#     # Insert before attachments
#     doc.insert(ignore_permissions=True)

#     # Child table: Tehsils
#     if tehsils:
#         if isinstance(tehsils, str):
#             value = tehsils.strip()
#             if value.startswith("["):
#                 tehsils = frappe.parse_json(value)
#             else:
#                 tehsils = [t.strip() for t in value.split(",") if t.strip()]

#         for t in tehsils:
#             doc.append("tehsil", {"tehsil": t})

#     # Child table: Marketplaces
#     if marketplaces:
#         if isinstance(marketplaces, str):
#             value = marketplaces.strip()
#             if value.startswith("["):
#                 marketplaces = frappe.parse_json(value)
#             else:
#                 marketplaces = [m.strip() for m in value.split(",") if m.strip()]

#         for m in marketplaces:
#             doc.append("marketplaces", {"marketplace": m})

#     # File upload helper
#     def save_file_field(fieldname):
#         uploaded = frappe.request.files.get(fieldname)
#         if uploaded:
#             saved = save_file(
#                 uploaded.filename,
#                 uploaded.read(),
#                 "Apply Dealership",
#                 doc.name,
#                 is_private=False
#             )
#             return saved.file_url
#         return None

#     doc.gst_certificate = save_file_field("gst_certificate") or doc.gst_certificate
#     doc.owner_pan = save_file_field("owner_pan") or doc.owner_pan
#     doc.passport_photo = save_file_field("passport_photo") or doc.passport_photo
#     doc.address_proof = save_file_field("address_proof") or doc.address_proof
#     doc.owner_aadhar = save_file_field("owner_aadhar") or doc.owner_aadhar
#     doc.shop_photograph = save_file_field("shop_photograph") or doc.shop_photograph

#     # Final save (draft)
#     doc.save(ignore_permissions=True)
#     frappe.db.commit()

#     return api_response(
#         True,
#         "Apply Dealership created successfully",
#         {
#             "docname": doc.name,
#             "state": doc.state,
#             "district": doc.district,
#             "tehsils": tehsils or [],
#             "marketplaces": marketplaces or [],
#             "status": doc.docstatus
#         }
#     )

import frappe
from frappe.utils.file_manager import save_file
from shoption_api.erp_api.common import api_auth, require_post, api_response

@frappe.whitelist(allow_guest=True)
def apply_dealership(
    dealership_type=None,
    delership_plan=None,
    dealer_id=None,

    state=None,
    district=None,
    
    
    country=None,
    state_=None,
    district_=None,
    tehsil_=None,
    marketplace=None,
    pincode=None,
    address=None,
    
    shop_name=None,
    machinery=None,
    ksk=None,
    consumable=None,
    other=None,
    other_data=None,

    shop_opening_year=None,
    employee_number=None,
    have_godown=None,
    godown_size=None,

    gst_number=None,
    primary_bank_name=None,
    last_year_turnover=None,

    name1=None,
    mobile_number=None,
    whatsapp=None,
    pan=None,
    dob=None,

    token_yantra=None,
    mulching=None,
    tarapaulin=None,
    tools=None,
    drip=None,
    kitkat=None,
    capacitor=None,
    motor_pump=None,
    pipe=None,
    starters=None,
    cables_wires=None,
    spray_pump=None,
    rope=None,
    tehsils=None,           # list / json / comma-separated
    marketplaces=None,     # list / json / comma-separated

    shop_name_as_gst=None,
    authorized_person_name=None,
    place=None,
    date=None
):
    api_auth()
    require_post()
    frappe.set_user("Administrator")
    frappe.flags.ignore_throttling = True

    # ------------------------------------------------
    # Validation: one dealer + one dealership type only
    # ------------------------------------------------
    if dealer_id and dealership_type:
        existing = frappe.db.exists(
            "Apply Dealership",
            {
                "dealer_id": dealer_id,
                "dealership_type": dealership_type,
                "docstatus":["!=",2]
            }
        )
        if existing:
            return api_response(
                False,
                "Application already exists for this dealer and dealership type"
            )

    # ------------------------------------------------
    # Create Apply Dealership document
    # ------------------------------------------------
    doc = frappe.new_doc("Apply Dealership")
    doc.docstatus = 0

    # ------------------------------------------------
    # Simple field mapping (no cleaning)
    # ------------------------------------------------
    doc.dealership_type = dealership_type
    doc.delership_plan = delership_plan
    doc.dealer_id = dealer_id

    doc.country = country
    doc.state = state
    doc.district = district
    
    doc.state_ = state_
    doc.district_ = district_
    doc.tehsil_ = tehsil_
    doc.marketplace = marketplace
    
    doc.pincode = pincode
    doc.address = address
    
    doc.shop_name = shop_name
    doc.machinery = machinery
    doc.ksk = ksk
    doc.consumable = consumable
    doc.other = other
    doc.other_data = other_data

    doc.shop_opening_year = shop_opening_year
    doc.employee_number = employee_number
    doc.have_godown = have_godown
    doc.godown_size = godown_size

    doc.gst_number = gst_number
    doc.primary_bank_name = primary_bank_name
    doc.last_year_turnover = last_year_turnover

    doc.name1 = name1
    doc.mobile_number = mobile_number
    doc.whatsapp = whatsapp
    doc.pan = pan
    doc.dob = dob

    doc.token_yantra = token_yantra
    doc.mulching = mulching
    doc.tarapaulin = tarapaulin
    doc.tools = tools
    doc.drip = drip
    doc.kitkat = kitkat
    doc.capacitor = capacitor
    doc.motor_pump = motor_pump
    doc.pipe = pipe
    doc.starters = starters
    doc.cables_wires = cables_wires
    doc.spray_pump = spray_pump
    doc.rope = rope

    doc.shop_name_as_gst = shop_name_as_gst
    doc.authorized_person_name = authorized_person_name
    doc.place = place
    doc.date = date

    # ------------------------------------------------
    # Insert before attachments
    # ------------------------------------------------
    doc.insert(ignore_permissions=True)

    # ------------------------------------------------
    # Child table: Tehsils
    # ------------------------------------------------
    if tehsils:
        if isinstance(tehsils, str):
            value = tehsils.strip()
            if value.startswith("["):
                tehsils = frappe.parse_json(value)
            else:
                tehsils = [t.strip() for t in value.split(",") if t.strip()]

        for t in tehsils:
            doc.append("tehsil", {"tehsil": t})

    # ------------------------------------------------
    # Child table: Marketplaces
    # ------------------------------------------------
    if marketplaces:
        if isinstance(marketplaces, str):
            value = marketplaces.strip()
            if value.startswith("["):
                marketplaces = frappe.parse_json(value)
            else:
                marketplaces = [m.strip() for m in value.split(",") if m.strip()]

        for m in marketplaces:
            doc.append("marketplaces", {"marketplace": m})

    # ------------------------------------------------
    # File upload helper
    # ------------------------------------------------
    def save_file_field(fieldname):
        uploaded = frappe.request.files.get(fieldname)
        if uploaded:
            saved = save_file(
                uploaded.filename,
                uploaded.read(),
                "Apply Dealership",
                doc.name,
                # is_private=False
                is_private=0  # 🔥 mandatory for Attach field
            )
            return saved.file_url
        return None

    doc.gst_certificate = save_file_field("gst_certificate") or doc.gst_certificate
    doc.owner_pan = save_file_field("owner_pan") or doc.owner_pan
    doc.passport_photo = save_file_field("passport_photo") or doc.passport_photo
    doc.address_proof = save_file_field("address_proof") or doc.address_proof
    doc.owner_aadhar = save_file_field("owner_aadhar") or doc.owner_aadhar
    doc.shop_photograph = save_file_field("shop_photograph") or doc.shop_photograph

    # ------------------------------------------------
    # Final save (still draft)
    # ------------------------------------------------
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return api_response(
        True,
        "Apply Dealership created successfully",
        {
            "docname": doc.name,
            "dealership_type": doc.dealership_type,
            "delership_plan": doc.delership_plan,
            "dealer_id": doc.dealer_id,
            "state": doc.state,
            "district": doc.district,
            
            "tehsils": tehsils or [],
            "marketplaces": marketplaces or [],
            
            "country": doc.country,
            "state_": doc.state_,
            "district_": doc.district_,
            "tehsil_": doc.tehsil_,
            "marketplace": doc.marketplace,
            "pincode": doc.pincode,
            "address": doc.address,
            "shop_name": doc.shop_name,
            "machinery": doc.machinery,
            "ksk": doc.ksk,
            "consumable": doc.consumable,
            "other": doc.other,
            "other_data": doc.other_data,
            "shop_opening_year": doc.shop_opening_year,
            "employee_number": doc.employee_number,
            "have_godown": doc.have_godown,
            "godown_size": doc.godown_size,
            "gst_number": doc.gst_number,
            "primary_bank_name": doc.primary_bank_name,
            "last_year_turnover": doc.last_year_turnover,
            "owner_name": doc.name1,
            "mobile_number": doc.mobile_number,
            "whatsapp": doc.whatsapp,
            "pan": doc.pan,
            "dob": doc.dob,
            
            "gst_certificate": doc.gst_certificate,
            "owner_pan": doc.owner_pan,
            "passport_photo": doc.passport_photo,
            "address_proof": doc.address_proof,
            "owner_aadhar": doc.owner_aadhar,
            "shop_photograph": doc.shop_photograph,
            
            
            "shop_name_as_gst": doc.shop_name_as_gst,
            "authorized_person_name": doc.authorized_person_name,
            "place": doc.place,
            "date": doc.date,
            
            "status": doc.docstatus
        }
    )

@frappe.whitelist(allow_guest=True)
def set_review_period(
    docname,
    valid_from,
    valid_to
):
    api_auth()
    require_post()
    frappe.set_user("Administrator")

    doc = frappe.get_doc("Apply Dealership", docname)

    if doc.docstatus != 0:
        return api_response(False, "Only draft documents can be updated")

    doc.valid_from = valid_from
    doc.valid_to = valid_to

    # FIRST STATUS CHANGE
    doc.approval_status = "Pending for Activation"
    doc.form_status = "Dealership Deposit"

    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return api_response(True, "Review period set successfully", {
        "docname": doc.name,
        "approval_status": doc.approval_status,
        "valid_from": doc.valid_from,
        "valid_to": doc.valid_to,
        "form_status" : doc.form_status
    })


@frappe.whitelist(allow_guest=True)
def submit_deposit_details(
    docname,
    deposit_amount,
    utr_check_no,
    # current_date=None
):
    api_auth()
    require_post()
    frappe.set_user("Administrator")

    doc = frappe.get_doc("Apply Dealership", docname)

    if doc.approval_status != "Pending for Activation":
        return api_response(False, "Invalid state for deposit submission")

    uploaded = frappe.request.files.get("slip_attach")
    if uploaded:
        saved = save_file(
            uploaded.filename,
            uploaded.read(),
            "Apply Dealership",
            doc.name,
            is_private=False
        )
        doc.slip_attach = saved.file_url

    doc.deposit_amount = float(deposit_amount)
    doc.utr_check_no = utr_check_no
    doc.current_date =  frappe.utils.now_datetime()

    # SECOND STATUS CHANGE
    doc.approval_status = "Pending for Approval"
    frappe.log_error(message=str(doc.as_dict()),title="Docs deposit submit")
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return api_response(True, "Deposit submitted successfully", {
        "docname": doc.name,
        "approval_status": doc.approval_status,
        "deposit_amount": doc.deposit_amount,
        "utr_check_no": doc.utr_check_no,
        "current_date": doc.current_date,
        "form_status" : doc.form_status
    })

# @frappe.whitelist(allow_guest=True)
# def submit_deposit_details(
#     docname,
#     deposit_amount,
#     utr_check_no,
# ):
#     try:
#         api_auth()
#         require_post()

#         # Force system user (only if really required)
#         frappe.set_user("Administrator")

#         # Fetch document
#         doc = frappe.get_doc("Apply Dealership", docname)

#         # Validate state
#         if doc.approval_status != "Pending for Activation":
#             return api_response(False, "Invalid state for deposit submission")

#         # Handle file upload
#         uploaded = frappe.request.files.get("slip_attach")
#         if uploaded:
#             saved = save_file(
#                 uploaded.filename,
#                 uploaded.read(),
#                 "Apply Dealership",
#                 doc.name,
#                 is_private=False
#             )
#             doc.slip_attach = saved.file_url

#         # Update fields
#         doc.deposit_amount = deposit_amount
#         doc.utr_check_no = utr_check_no
#         doc.current_date = frappe.utils.now_datetime()

#         # Status change
#         doc.approval_status = "Pending for Approval"

#         # Save
#         doc.save(ignore_permissions=True)
#         frappe.db.commit()

#         return api_response(True, "Deposit submitted successfully", {
#             "docname": doc.name,
#             "approval_status": doc.approval_status,
#             "deposit_amount": doc.deposit_amount,
#             "utr_check_no": doc.utr_check_no,
#             "current_date": doc.current_date,
#             "form_status": doc.form_status
#         })

#     except frappe.DoesNotExistError:
#         frappe.log_error(
#             frappe.get_traceback(),
#             "submit_deposit_details: Document Not Found"
#         )
#         return api_response(False, "Apply Dealership document not found")

#     except frappe.PermissionError:
#         frappe.log_error(
#             frappe.get_traceback(),
#             "submit_deposit_details: Permission Error"
#         )
#         return api_response(False, "Permission denied")

#     except Exception as e:
#         frappe.log_error(
#             message=frappe.get_traceback(),
#             title="submit_deposit_details: Unexpected Error"
#         )
#         return api_response(False, "Something went wrong while submitting deposit")


# @frappe.whitelist(allow_guest=True)
# def check_approval_amount(docname, approved_amount=None, approval_date=None):
#     api_auth()
#     require_post()
#     frappe.set_user("Administrator")

#     doc = frappe.get_doc("Apply Dealership", docname)

#     if doc.approval_status != "Pending for Approval":
#         return api_response(False, "Invalid state for approval check")

#     plan_amount = float(doc.plan_deposit_amount or 0)
#     deposit_amount = float(doc.deposit_amount or 0)

#     # ------------------------------------------------
#     #  EDGE CASE HANDLING
#     # ------------------------------------------------
#     if approved_amount is not None and str(approved_amount).strip() != "":
#         # API value has priority
#         approved_amount = float(approved_amount)
#         doc.approved_amount = approved_amount
#         doc.approval_date = frappe.utils.now_datetime()
#     else:
#         # Fallback to already saved value
#         approved_amount = float(doc.approved_amount or 0)

#     # ------------------------------------------------
#     # FINAL CHECK
#     # ------------------------------------------------
#     next_step = (deposit_amount + approved_amount) >= plan_amount

#     doc.save(ignore_permissions=True)
#     frappe.db.commit()

#     return api_response(True, "Approval amount checked", {
#         "approval_status": doc.approval_status,
#         "next": next_step,
#         "approved_amount": approved_amount,
#         "deposit_amount": deposit_amount,
#         "plan_deposit_amount": plan_amount,
#         "current_date": frappe.utils.now_datetime(),
#         "approval_date": doc.approval_date
#     })



@frappe.whitelist(allow_guest=True)
def check_approval_amount(docname, approved_amount=None, approval_date=None):
    api_auth()
    require_post()
    frappe.set_user("Administrator")

    doc = frappe.get_doc("Apply Dealership", docname)

    # if doc.approval_status != "Pending for Approval":
    #     return api_response(False, "Invalid state for approval check")

    plan_amount = float(doc.plan_deposit_amount or 0)
    deposit_amount = float(doc.deposit_amount or 0)
    utr_check_no = doc.utr_check_no

    # ------------------------------------------------
    #  EDGE CASE HANDLING
    # ------------------------------------------------
    if approved_amount is not None and str(approved_amount).strip() != "":
        # API value has priority
        approved_amount = float(approved_amount)
        doc.approved_amount = approved_amount
        doc.approval_date = frappe.utils.now_datetime()
    else:
        # Fallback to already saved value
        approved_amount = float(doc.approved_amount or 0)

    # ------------------------------------------------
    # FINAL CHECK
    # ------------------------------------------------
    # next_step = (deposit_amount + approved_amount) >= plan_amount
    if(doc.override):
        next_step = True
    else:
        next_step = approved_amount == plan_amount
        
    if(next_step):
        doc.form_status = "First Order"
    
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return api_response(True, "Approval amount checked", {
        "approval_status": doc.approval_status,
        "next": next_step,
        "approved_amount": approved_amount,
        "deposit_amount": deposit_amount,
        "plan_deposit_amount": plan_amount,
        "utr_check_no" : utr_check_no,
        "current_date": doc.current_date,
        "approval_date": doc.approval_date,
        "form_status" : doc.form_status
    })



@frappe.whitelist(allow_guest=True)
def map_sales_order2(docname, sales_order):

    api_auth()
    require_post()
    frappe.set_user("Administrator")

    # -----------------------------
    # 1️⃣ FETCH APPLY DEALERSHIP
    # -----------------------------
    doc = frappe.get_doc("Apply Dealership", docname)

    if doc.approval_status != "Pending for Approval":
        return api_response(False, "Invalid state for sales order mapping")

    mobile_no = doc.mobile_number
    if not mobile_no:
        return api_response(False, "Mobile number not found in Apply Dealership")

    # -----------------------------
    # 2️⃣ CUSTOMER VALIDATION
    # -----------------------------
    customer_name = frappe.db.get_value(
        "Customer",
        {"mobile_no": mobile_no},
        "name"
    )

    if not customer_name:
        return api_response(False, "Customer not found for this dealer")

    # -----------------------------
    # 3️⃣ SALES ORDER VALIDATION
    # -----------------------------
    so_data = frappe.db.get_value(
        "Sales Order",
        sales_order,
        ["name", "customer", "custom_payment_status"],
        as_dict=True
    )

    if not so_data:
        return api_response(False, "Sales order not found", {
            "sales_order": sales_order
        })

    if so_data.customer != customer_name:
        return api_response(
            False,
            "Sales order does not belong to this dealer",
            {
                "sales_order_customer": so_data.customer,
                "expected_customer": customer_name
            }
        )

    if so_data.custom_payment_status != "Fully Paid":
        return api_response(
            False,
            "Sales order is not fully paid. Only fully paid orders are allowed.",
            {
                "sales_order": sales_order,
                "billing_status": so_data.custom_payment_status
            }
        )

    # -----------------------------
    # 4️⃣ FETCH SALES ORDER ITEMS (LEAN)
    # -----------------------------
    so_items = frappe.get_all(
        "Sales Order Item",
        filters={"parent": sales_order},
        fields=["item_code", "amount"]
    )

    if not so_items:
        return api_response(False, "Sales order has no items")

    # -----------------------------
    # 5️⃣ FETCH ALLOWED ITEM CODES
    # -----------------------------
    allowed_item_codes = set(
        get_allowed_item_codes_by_dealership(doc.dealership_type)
    )

    valid_items = []
    invalid_items = []
    calculated_amount = 0.0

    for row in so_items:
        code = row.item_code.strip()

        if code in allowed_item_codes:
            valid_items.append(code)
            calculated_amount += float(row.amount or 0)
        else:
            invalid_items.append(code)

    # -----------------------------
    # 6️⃣ STOP IF NO VALID ITEMS
    # -----------------------------
    if not valid_items:
        return api_response(
            False,
            "Sales order has no valid items for this dealership plan",
            {
                "sales_order": sales_order,
                "valid_items": [],
                "invalid_items": invalid_items
            }
        )

    # -----------------------------
    # 7️⃣ FIRST ORDER VALUE
    # -----------------------------
    first_order_value = 0.0
    if doc.delership_plan:
        first_order_value = float(
            frappe.db.get_value(
                "Dealership Plan",
                doc.delership_plan,
                "first_order_value"
            ) or 0
        )

    # -----------------------------
    # 8️⃣ MAP SALES ORDER
    # -----------------------------
    existing_row = next(
        (r for r in doc.dealership_sales_order if r.sales_order == sales_order),
        None
    )

    if existing_row:
        existing_row.order_amount = calculated_amount
    else:
        doc.append("dealership_sales_order", {
            "sales_order": sales_order,
            "order_amount": calculated_amount
        })

    # -----------------------------
    # 9️⃣ TOTAL ORDER AMOUNT
    # -----------------------------
    total_order_amount = sum(
        float(r.order_amount or 0)
        for r in doc.dealership_sales_order
    )

    doc.order_amount = total_order_amount
    doc.total_paid_order_amount = total_order_amount

    # -----------------------------
    # 🔟 STATUS DECISION
    # -----------------------------
    if doc.order_override or total_order_amount >= first_order_value:
        doc.approval_status = "Override"
        doc.form_status = "Aggreement"
        status_message = "Sales order mapped and dealership overridden"
    else:
        status_message = "Sales order mapped, amount below first order value"

    doc.save(ignore_permissions=True)
    frappe.db.commit()

    # -----------------------------
    # 1️⃣1️⃣ FINAL RESPONSE
    # -----------------------------
    return api_response(
        True,
        status_message,
        {
            "sales_order": sales_order,
            "approval_status": doc.approval_status,
            "first_order_value": first_order_value,
            "current_sales_order_amount": calculated_amount,
            "total_order_amount": total_order_amount,
            "valid_items": valid_items,
            "invalid_items": invalid_items,
            "form_status": doc.form_status
        }
    )

# working 
import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response
from shoption_api.dealership.dealership_item import get_allowed_item_codes_by_dealership

@frappe.whitelist(allow_guest=True)
def map_sales_order(docname, sales_order):
    api_auth()
    require_post()
    frappe.set_user("Administrator")

    # -----------------------------
    # FETCH APPLY DEALERSHIP
    # -----------------------------
    doc = frappe.get_doc("Apply Dealership", docname)

    if doc.approval_status != "Pending for Approval":
        return api_response(False, "Invalid state for sales order mapping")

    # -----------------------------
    # FETCH SALES ORDER
    # -----------------------------
    if not frappe.db.exists("Sales Order", sales_order):
        return api_response(False, "Sales order not found", {
            "sales_order": sales_order
        })

    so = frappe.get_doc("Sales Order", sales_order)

    # -----------------------------
    # PAYMENT STATUS CHECK
    # -----------------------------
    if so.custom_payment_status != "Fully Paid":
        return api_response(
            False,
            "Sales order is not fully paid. Only fully paid orders are allowed.",
            {
                "sales_order": sales_order,
                "billing_status": so.custom_payment_status
            }
        )

    # -----------------------------
    # CUSTOMER VALIDATION
    # -----------------------------
    mobile_no = doc.mobile_number
    if not mobile_no:
        return api_response(False, "Mobile number not found in Apply Dealership")

    customer = frappe.get_all(
        "Customer",
        filters={"mobile_no": mobile_no},
        fields=["name"],
        limit=1
    )

    if not customer:
        return api_response(False, "Customer not found for this dealer")

    expected_customer = customer[0].name

    if so.customer != expected_customer:
        return api_response(
            False,
            "Sales order does not belong to this dealer",
            {
                "sales_order_customer": so.customer,
                "expected_customer": expected_customer
            }
        )

    # -----------------------------
    # FETCH ALLOWED ITEM CODES (FIXED ROOT)
    # -----------------------------
    allowed_item_codes = get_allowed_item_codes_by_dealership(
        doc.dealership_type
    )

    # -----------------------------
    # VALIDATE SALES ORDER ITEMS (STEP-3)
    # -----------------------------
    valid_items = []
    invalid_items = []
    calculated_amount = 0.0

    for row in so.items:
        so_item_code = str(row.item_code).strip()

        if so_item_code in allowed_item_codes:
            valid_items.append(so_item_code)
            calculated_amount += float(row.amount or 0)
        else:
            invalid_items.append(so_item_code)
            
            
    # -----------------------------
    # STOP IF NO VALID ITEMS 
    # -----------------------------
    if not valid_items:
        return api_response(
            False,
            "Sales order has no valid items for this dealership plan",
            {
                "sales_order": sales_order,
                "valid_items": [],
                "invalid_items": invalid_items
            }
        )
    

    # -----------------------------
    # FETCH FIRST ORDER VALUE
    # -----------------------------
    first_order_value = 0.0
    if doc.delership_plan:
        first_order_value = float(
            frappe.db.get_value(
                "Dealership Plan",
                doc.delership_plan,
                "first_order_value"
            ) or 0
        )

    # -----------------------------
    # MAP SALES ORDER (CHILD TABLE)
    # -----------------------------
    existing_row = None
    for row in doc.dealership_sales_order:
        if row.sales_order == sales_order:
            existing_row = row
            break

    if existing_row:
        existing_row.order_amount = calculated_amount
    else:
        doc.append("dealership_sales_order", {
            "sales_order": sales_order,
            "order_amount": calculated_amount
        })

    # -----------------------------
    # TOTAL ORDER AMOUNT
    # -----------------------------
    total_order_amount = sum(
        float(r.order_amount or 0)
        for r in doc.dealership_sales_order
    )

    doc.order_amount = total_order_amount
    doc.total_paid_order_amount = total_order_amount

    # -----------------------------
    # STATUS DECISION
    # -----------------------------
    if doc.order_override:
        doc.approval_status = "Override"
        doc.form_status = "Aggreement"
        status_message = "Sales order mapped and dealership overridden"
    else:
        if total_order_amount >= first_order_value:
            doc.approval_status = "Override"
            doc.form_status = "Aggreement"
            status_message = "Sales order mapped and dealership overridden"
        else:
            status_message = "Sales order mapped, amount below first order value"

    doc.save(ignore_permissions=True)
    frappe.db.commit()

    # -----------------------------
    # EDGE CASE → NO VALID ITEMS
    # -----------------------------
    if not valid_items and calculated_amount == 0:
        return api_response(
            False,
            "Sales order has no valid items for this dealership plan",
            {
                "sales_order": sales_order,
                "approval_status": doc.approval_status,
                "first_order_value": first_order_value,
                "current_sales_order_amount": calculated_amount,
                "total_order_amount": total_order_amount,
                "valid_items": valid_items,
                "invalid_items": invalid_items,
                "form_status": doc.form_status
            }
        )

    # -----------------------------
    # FINAL RESPONSE
    # -----------------------------
    return api_response(
        True,
        status_message,
        {
            "sales_order": sales_order,
            "approval_status": doc.approval_status,
            "first_order_value": first_order_value,
            "current_sales_order_amount": calculated_amount,
            "total_order_amount": total_order_amount,
            "valid_items": valid_items,
            "invalid_items": invalid_items,
            "form_status": doc.form_status
        }
    )




# 24/
import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response

@frappe.whitelist(allow_guest=True)
def get_dealership_sales_order_state(docname=None):
    api_auth()
    require_post()
    frappe.set_user("Administrator")

    # -----------------------------
    # VALIDATION
    # -----------------------------
    if not docname:
        return api_response(False, "docname is required")

    if not frappe.db.exists("Apply Dealership", docname):
        return api_response(False, "Apply Dealership not found")

    # -----------------------------
    # FETCH DOCUMENT
    # -----------------------------
    doc = frappe.get_doc("Apply Dealership", docname)

    # -----------------------------
    # FETCH FIRST ORDER VALUE
    # -----------------------------
    first_order_value = 0.0
    if doc.delership_plan:
        first_order_value = float(
            frappe.db.get_value(
                "Dealership Plan",
                doc.delership_plan,
                "first_order_value"
            ) or 0
        )

    # -----------------------------
    # CHILD TABLE → SALES ORDERS
    # -----------------------------
    sales_orders = []
    total_order_amount = 0.0

    for row in doc.dealership_sales_order:
        amount = float(row.order_amount or 0)
        total_order_amount += amount

        sales_orders.append({
            "sales_order": row.sales_order,
            "order_amount": amount
        })

    # -----------------------------
    # RESPONSE
    # -----------------------------
    return api_response(
        True,
        "Dealership sales order state fetched",
        {
            "docname": doc.name,
            "approval_status": doc.approval_status,
            "form_status": doc.form_status,

            "first_order_value": first_order_value,
            "total_order_amount": total_order_amount,

            "sales_orders": sales_orders,
            "sales_order_count": len(sales_orders),

            "is_first_order_completed": total_order_amount >= first_order_value
        }
    )





import frappe
from frappe.utils import now_datetime
from shoption_api.erp_api.common import api_auth, require_post, api_response
from shoption_api.dealership.dealership_item import get_items_by_dealership_master
from shoption_api.area.api import get_marketplaces

@frappe.whitelist(allow_guest=True)
def get_dealership_agreement(docname=None):
    api_auth()
    require_post()
    frappe.set_user("Administrator")

    if not docname:
        return api_response(False, "docname is required")

    doc = frappe.get_doc("Apply Dealership", docname)

    # -----------------------------
    # COMPANY (STATIC)
    # -----------------------------
    company = {
        "name": "Shoption Pvt. Ltd.",
        "pan_no": "ABCCS4105L",
        "address": "Shop No. 24 & 25, City Vista, Fountain Road, Kharadi, Pune, Maharashtra, 411014",
        "authorized_signatory": "Somnath D Shendge",
        "place": "Pune, Maharashtra"
    }

    mobile_number = doc.mobile_number
    email_id = frappe.db.get_value(
        "Delear Registration",
        {"mobile_number": mobile_number},
        "email_id"
    )

    # -----------------------------
    # DEALER (FROM APPLY DEALERSHIP)
    # -----------------------------
    dealer = {
        "business_name": doc.shop_name,
        "authorized_person": doc.name1,
        "pan_no": doc.pan,
        "gst_no": doc.gst_number,
        "address": doc.address,
        "mobile_number": doc.mobile_number,
        "email_id": email_id
        
    }

    # -----------------------------
    # FINANCIAL TERMS
    # -----------------------------
    financial_terms = {
        "deposit_amount": doc.deposit_amount,
        "deposit_received_on": doc.current_date
    }

    # -----------------------------
    # SIGNATURES
    # -----------------------------
    signatures = {
        "company": {
            "signed_on": now_datetime()
        },
        # "dealer": {
        #     "name": doc.name1,
        #     "image": doc.sign,   # null OR stored signature
        #     "signed_on": None if not doc.sign else doc.modified
        # }
    }
    
    
    
    other = {
        "dealership_name" : doc.dealership_type,
        "dealership_plan" : doc.dealership_plan_name,
        "approved_amount" : doc.approved_amount,
        "approval_date" : doc.approval_date,
        "dealership_target" : doc.dealership_target
    }
    

    # ==========================================================
    # COVERAGE LOGIC (TEHSIL / MARKETPLACE)
    # ==========================================================
    coverage = []

    # ---------- CASE 1: TEHSIL PRESENT ----------
    if doc.tehsil:
        for row in doc.tehsil:
            tehsil_name = row.tehsil

            resp = get_marketplaces(tehsil_name)
            if resp.get("status"):
                for mp in resp.get("data", []):
                    parts = mp["id"].split("-")
                    if len(parts) >= 4:
                        coverage.append({
                            "marketplace": parts[0],
                            "tehsil": parts[1],
                            "district": parts[2],
                            "state": parts[3]
                        })

    # ---------- CASE 2: MARKETPLACE PRESENT ----------
    # elif doc.marketplaces:
    #     for row in doc.marketplaces:
    #         mp_name = row.marketplaces
    #         parts = mp_name.split("-")
    #         if len(parts) >= 4:
    #             coverage.append({
    #                 "marketplace": parts[0],
    #                 "tehsil": parts[1],
    #                 "district": parts[2],
    #                 "state": parts[3]
    #             })
    
    # ---------- CASE 2: MARKETPLACE PRESENT ----------
    elif doc.marketplaces:
        for row in doc.marketplaces:
            mp_name = row.marketplace   # correct fieldname

            parts = mp_name.split("-")
            if len(parts) >= 4:
                coverage.append({
                    "marketplace": parts[0],
                    "tehsil": parts[1],
                    "district": parts[2],
                    "state": parts[3]
                })

    
    items_data = []
    if doc.dealership_type:
        items_resp = get_items_by_dealership_master(
            dealership_master_name=doc.dealership_type,
            mobile_no=doc.mobile_number,
            page=1,
            page_size=10000
        )
        items_data = items_resp.get("data")


    return api_response(
        True,
        "Agreement details fetched successfully",
        {
            "company": company,
            "dealer": dealer,
            "financial_terms": financial_terms,
            "signatures": signatures,
            "other" : other,
            "coverage": coverage, 
            "dealership_items": items_data
            
        }
    )


from frappe.utils.file_manager import save_file

@frappe.whitelist(allow_guest=True)
def save_dealership_agreement(docname=None):
    api_auth()
    require_post()
    frappe.set_user("Administrator")

    if not docname:
        return api_response(False, "docname is required")

    uploaded_file = frappe.request.files.get("file")
    if not uploaded_file:
        return api_response(False, "Agreement PDF file is required")

    doc = frappe.get_doc("Apply Dealership", docname)

    # -----------------------------
    # SAVE FILE (Dealer Registration pattern)
    # -----------------------------
    content = uploaded_file.read()

    saved = save_file(
        uploaded_file.filename,
        content,
        "Apply Dealership",
        doc.name,
        is_private=0   # 🔥 mandatory for Attach field
    )

    if not saved or not saved.file_url:
        return api_response(False, "Failed to upload agreement file")

    # -----------------------------
    # MAP FILE + UPDATE STATUS
    # -----------------------------
    doc.dealership_aggrement = saved.file_url
    doc.approval_status = "Active"

    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return api_response(
        True,
        "Dealership agreement uploaded and dealership activated",
        {
            "docname": doc.name,
            "approval_status": doc.approval_status,
            "agreement_file": saved.file_url
        }
    )



@frappe.whitelist(allow_guest=True)
def get_form_status(docname=None):
    api_auth()
    require_post()
    frappe.set_user("Administrator")

    if not docname:
        return api_response(False, "docname is required")

    doc = frappe.get_doc("Apply Dealership", docname)

    return api_response(
        True,
        "Form status fetched successfully",
        {
            "docname": doc.name,
            "form_status": doc.form_status
        }
    )
    
    
def get_shop_types(doc):
    shop_types = []

    if doc.machinery == 1:
        shop_types.append({
            "key": "machinery",
            "label": "Machinery"
        })

    if doc.ksk == 1:
        shop_types.append({
            "key": "ksk",
            "label": "KSK"
        })

    if doc.consumable == 1:
        shop_types.append({
            "key": "consumable",
            "label": "Consumable"
        })

    if doc.other == 1:
        shop_types.append({
            "key": "other",
            "label": "Other",
            "value": doc.other_data
        })

    return shop_types

    
from frappe.utils import get_url
@frappe.whitelist(allow_guest=True)
def get_apply_details(docname):

    api_auth()
    require_post()
    frappe.set_user("Administrator")
    
    if not docname:
        return api_response(False , "Apply dealership not found")

    doc = frappe.get_doc("Apply Dealership", docname)
    
    data = {
        "shop_name": doc.shop_name,
        
        # "machinery": doc.machinery,
        # "ksk": doc.ksk,
        # "consumable": doc.consumable,
        # "other": doc.other,
        # "other_data": doc.other_data,
        "shop_types": get_shop_types(doc),
        
                    
        "country": doc.country,
        "state_": doc.state_,
        "district_":frappe.db.get_value("District", doc.district_, "district_name") or doc.district_,
        "tehsil_": frappe.db.get_value("Tahshil", doc.tehsil_, "tahshil") or doc.tehsil_,
        "marketplace": frappe.db.get_value("Marketplace", doc.marketplace, "marketplace_name") or  doc.marketplace,
        "pincode": doc.pincode,
        "address": doc.address,
        
        "shop_opening_year": doc.shop_opening_year,
        "employee_number": doc.employee_number,
        
        "have_godown": doc.have_godown,
        "godown_size": doc.godown_size,
        
        "gst_number": doc.gst_number,
        "primary_bank_name": doc.primary_bank_name,
        "last_year_turnover": doc.last_year_turnover,
        
        "deposited_amount": doc.approved_amount,
        "first_order_amount_paid": doc.total_paid_order_amount,
        
        "owner_name": doc.name1,
        "mobile_number": doc.mobile_number,
        "whatsapp": doc.whatsapp,
        "pan": doc.pan,
        "dob": doc.dob,
        
        "gst_certificate": get_url(doc.gst_certificate) if doc.gst_certificate else None,
        "owner_aadhar": get_url(doc.owner_aadhar) if doc.owner_aadhar else None,
        "dealership_aggrement": get_url(doc.dealership_aggrement) if doc.dealership_aggrement else None,
        "passport_photo": get_url(doc.passport_photo) if doc.passport_photo else None,
        "owner_pan": get_url(doc.owner_pan) if doc.owner_pan else None,
        "shop_photograph": get_url(doc.shop_photograph) if doc.shop_photograph else None,
        "address_proof": get_url(doc.address_proof) if doc.address_proof else None,
        "Dealership_certificate" : get_url(doc.certificate) if doc.certificate else None,
        
        "token_yantra" : doc.token_yantra,
        "mulching" : doc.mulching,
        "tarapaulin" : doc.tarapaulin,
        "tools" : doc.tools,
        "drip" : doc.drip,
        "kitkat" : doc.kitkat,
        "capacitor" : doc.capacitor,
        "motor_pump" : doc.motor_pump,
        "pipe" : doc.pipe,
        "starters" : doc.starters,
        "cables_wires" : doc.cables_wires,
        "spray_pump" : doc.spray_pump,
        "rope" : doc.rope,
        
        "shop_name_as_gst": doc.shop_name_as_gst,
        "authorized_person_name": doc.authorized_person_name,
        "place": doc.place,
        "date": doc.date,        
    }
    
    return api_response(True, "Dealership profile details fetched successfully", data)

        
        

    
    
    