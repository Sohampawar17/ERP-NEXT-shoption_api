
# # Exact match first, then fallback to like search 04/12
import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response
@frappe.whitelist(allow_guest=True)
def get_brands(search=None, page=1, page_size=20):
    api_auth()
    require_post()
    frappe.set_user("Administrator")

    # Safe convert
    try:
        page = int(page)
        page_size = int(page_size)
    except:
        page, page_size = 1, 20

    # ---- META CHECK ----
    brand_meta = frappe.get_meta("Brand")
    fields_available = {df.fieldname for df in brand_meta.fields}

    has_brand_name = "brand_name" in fields_available
    has_brand = "brand" in fields_available
    custom_id_exists = "custom_brand_id" in fields_available
    custom_image_exists = "custom_image_path" in fields_available

    start = (page - 1) * page_size

    # ------------------------------------------------------
    # 1️⃣ EXACT MATCH SEARCH FIRST
    # ------------------------------------------------------

    exact_filters = {}

    if search:
        if has_brand_name:
            exact_filters = {"brand_name": search}
        elif has_brand:
            exact_filters = {"brand": search}

    exact_rows = []
    if exact_filters:
        exact_rows = frappe.get_list(
            "Brand",
            filters=exact_filters,
            fields=["name as brand_id",
                    "brand_name" if has_brand_name else "brand as brand_name",
                    "custom_brand_id" if custom_id_exists else None,
                    "custom_image_path as image" if custom_image_exists else None],
            limit_start=start,
            limit_page_length=page_size,
            order_by="creation desc"
        )

    # If exact match found → return ONLY exact result
    if exact_rows:
        final_data = []
        for b in exact_rows:
            final_data.append({
                "brand_id": b.get("brand_id"),
                "brand_name": b.get("brand_name"),
                "custom_brand_id": b.get("custom_brand_id") or None,
                "image": b.get("image") or ""
            })

        return api_response(True, "Brand list fetched", {
            "total": 1,
            "page": page,
            "page_size": page_size,
            "total_pages": 1,
            "data": final_data
        })

    # ------------------------------------------------------
    # 2️⃣ NO EXACT → FALLBACK TO SIMPLE LIKE SEARCH
    # ------------------------------------------------------

    filters = {}

    if search:
        if has_brand_name:
            filters["brand_name"] = ["like", f"%{search}%"]
        elif has_brand:
            filters["brand"] = ["like", f"%{search}%"]

    # ------------------------------------------------------
    # DB FIELDS
    # ------------------------------------------------------

    fields = ["name as brand_id"]

    if has_brand_name:
        fields.append("brand_name")
    elif has_brand:
        fields.append("brand as brand_name")

    if custom_id_exists:
        fields.append("custom_brand_id")

    if custom_image_exists:
        fields.append("custom_image_path as image")

    # ------------------------------------------------------
    # FETCH DATA (LIKE RESULTS)
    # ------------------------------------------------------

    try:
        rows = frappe.get_list(
            "Brand",
            filters=filters,
            fields=fields,
            limit_start=start,
            limit_page_length=page_size,
            order_by="creation desc"
        )

        final_data = []
        for b in rows:
            final_data.append({
                "brand_id": b.get("brand_id"),
                "brand_name": b.get("brand_name"),
                "custom_brand_id": b.get("custom_brand_id") or None,
                "image": b.get("image") or ""
            })

        total = frappe.db.count("Brand", filters)
        total_pages = (total + page_size - 1) // page_size

        return api_response(True, "Brand list fetched", {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "data": final_data
        })

    except Exception as e:
        return api_response(False, f"Error: {str(e)}")


@frappe.whitelist(allow_guest=True)
def get_brands_by_subcategory(subcategory_id=None, page=1, page_size=20):
    from shoption_api.erp_api.common import api_auth, require_post, api_response

    api_auth()
    require_post()

    if not subcategory_id:
        return api_response(False, "subcategory_id is required")

    # pagination
    try:
        page = int(page)
        page_size = int(page_size)
    except:
        page, page_size = 1, 20

    # get subcategory
    try:
        subcat = frappe.get_doc("Sub Categoury", subcategory_id)
    except:
        return api_response(False, "Invalid subcategory_id")

    category = subcat.categoury
    if not category:
        return api_response(True, "Brands fetched", {
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
            "data": []
        })

    # ---------------------------------------
    # STEP 1 → Get brands having items
    # ---------------------------------------
    items = frappe.get_all(
        "Item",
        filters={
            "custom_sub_category": subcategory_id,
            "item_group": category,
            "disabled": 0
        },
        fields=["brand"],
        distinct=True
    )

    brand_ids = [i.brand for i in items if i.brand]

    if not brand_ids:
        return api_response(True, "Brands fetched", {
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
            "data": []
        })

    # ---------------------------------------
    # STEP 2 → Get brand details
    # ---------------------------------------
    brands = frappe.get_all(
        "Brand",
        filters={"name": ["in", brand_ids]},
        fields=["name", "brand", "custom_brand_id", "custom_image_path"]
    )

    # format response
    result = [
        {
            "brand_id": b.name,
            "brand_name": b.brand,
            "custom_brand_id": b.custom_brand_id,
            "image": b.custom_image_path or ""
        }
        for b in brands
    ]

    # sort
    result.sort(key=lambda x: (x.get("brand_name") or "").lower())

    # pagination
    total = len(result)
    start = (page - 1) * page_size
    end = start + page_size

    return api_response(True, "Brands fetched", {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "data": result[start:end]
    })
    
@frappe.whitelist(allow_guest=True)
def get_brands_by_category(category=None, page=1, page_size=20):
    from shoption_api.erp_api.common import api_auth, require_post, api_response

    api_auth()
    require_post()

    if not category:
        return api_response(False, "category is required")

    # pagination
    try:
        page = int(page)
        page_size = int(page_size)
    except:
        page, page_size = 1, 20

    # ---------------------------------------
    # STEP 1 → Get brands having items
    # ---------------------------------------
    items = frappe.get_all(
        "Item",
        filters={
            "item_group": category,
            "disabled": 0
        },
        fields=["brand"],
        distinct=True
    )

    brand_ids = [i.brand for i in items if i.brand]

    if not brand_ids:
        return api_response(True, "Brands fetched", {
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
            "data": []
        })

    # ---------------------------------------
    # STEP 2 → Get brand details
    # ---------------------------------------
    brands = frappe.get_all(
        "Brand",
        filters={"name": ["in", brand_ids]},
        fields=["name", "brand", "custom_brand_id", "custom_image_path"]
    )

    # ---------------------------------------
    # STEP 3 → Format
    # ---------------------------------------
    result = [
        {
            "brand_id": b.name,
            "brand_name": b.brand,
            "custom_brand_id": b.custom_brand_id,
            "image": b.custom_image_path or "",
            "category": category
        }
        for b in brands
    ]

    # sort
    result.sort(key=lambda x: (x.get("brand_name") or "").lower())

    # ---------------------------------------
    # PAGINATION
    # ---------------------------------------
    total = len(result)
    start = (page - 1) * page_size
    end = start + page_size

    return api_response(True, "Brands fetched", {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "data": result[start:end]
    })