import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response
from shoption_api.cart.cart import get_item_price_withgst  # 18/12

@frappe.whitelist(allow_guest=True)
def get_best_sellers(page=1, page_size=20, mobile_no=None):

    api_auth()
    require_post()

    # -------------------------------------
    # Mobile required
    # -------------------------------------
    if not mobile_no:
        return api_response(False, "mobile_no is required")

    # -------------------------------------
    # Find Customer
    # -------------------------------------
    customer = frappe.get_all(
        "Customer",
        filters={"mobile_no": mobile_no},
        fields=["name", "customer_group"],
        limit=1
    )

    user_id = None
    customer_group = None
    customer_name = None

    if customer:
        customer_name = customer[0].name
        customer_group = customer[0].customer_group

        portal_user = frappe.get_all(
            "Portal User",
            filters={"parent": customer_name},
            fields=["user"],
            limit=1
        )

        if portal_user:
            user_id = portal_user[0].user

    # -------------------------------------
    # Set User Context
    # -------------------------------------
    frappe.set_user(user_id if user_id else "Administrator")

    # -------------------------------------
    # Pagination
    # -------------------------------------
    try:
        page = int(page)
        page_size = int(page_size)
    except:
        page, page_size = 1, 20

    start = (page - 1) * page_size

    try:
        # -------------------------------------
        # Fetch Best Sellers
        # -------------------------------------
        best_rows = frappe.get_list(
            "Best Sellers",
            fields=["item_code", "item_name", "image"],
            limit_start=start,
            limit_page_length=page_size,
            order_by="creation desc"
        )

        response_data = []

        for row in best_rows:

            item_code = row.get("item_code")

            item_doc = frappe.get_all(
                "Item",
                filters={"name": item_code, "disabled": 0},
                fields=[
                    "name as item_code",
                    "item_name",
                    "item_group",
                    "brand",
                    "stock_uom",
                    "gst_hsn_code",
                    "custom_sub_category",
                    "custom_image_1"
                ],
                limit=1
            )

            if not item_doc:
                continue

            item = item_doc[0]

                       
            price_row=[]
            # Price filters (Farmer override)
            price_filters = {"item_code": item_code, "selling": 1}
            if customer_group == "Farmer":
                price_filters["price_list"] = frappe.db.get_value(
                    "Price List",
                    {"custom_customer_group": "Farmer",
                     "custom_brand": item.get("brand"),
                     "selling": 1},
                    "name"
                ) or f"{item['brand']}-Farmer"

            # Fetch Price
            if customer_group == "Farmer":
                 price_row = frappe.get_all(
                    "Item Price",
                    filters=price_filters,
                    fields=[
                        "price_list",
                        "custom_mrp",
                        "price_list_rate",
                        "custom_discount as discount",
                        "custom_oem_code"
                    ],
                    order_by="valid_from desc",
                    limit=1
                )
            else:
                price_row = frappe.get_list(
                    "Item Price",
                    filters=price_filters,
                    fields=[
                        "price_list",
                        "custom_mrp",
                        "price_list_rate",
                    "custom_discount as discount",
                        "custom_oem_code"
                    ],
                    order_by="valid_from desc",
                    limit=1
                )


            base_price = None
            gst_price = None

            if user_id and price_row:
                p = price_row[0]
                base_price = p.get("price_list_rate")

                item["price_list"] = p.get("price_list")
                item["mrp"] = p.get("custom_mrp")
                item["discount"] = p.get("discount")
                item["oem_code"] = p.get("custom_oem_code")

                # -------- GST PRICE --------
                try:
                    gst_data = get_item_price_withgst(
                        item_code=item_code,
                        customer=customer_name,
                        customer_group=customer_group,
                        company=frappe.defaults.get_global_default("company"),
                        currency=frappe.defaults.get_global_default("currency"),
                        qty=1,
                        brand=item.get("brand")
                    )
                    gst_price = gst_data.get("rate_incl_gst")
                except Exception:
                    gst_price = None
            else:
                item["price_list"] = None
                item["mrp"] = None
                item["discount"] = None
                item["oem_code"] = None

            # -------------------------------------
            # FINAL PRICE MAPPING (STANDARD)
            # -------------------------------------
            item["no_gst_price"] = base_price
            item["price"] = gst_price
            item["actual_rate"] = gst_price

            # -------------------------------------
            # MOQ LOGIC (UNCHANGED)
            # -------------------------------------
            item["moq"] = None
            if customer_group:
                item_full_doc = frappe.get_doc("Item", item_code)
                for moq_row in item_full_doc.get("custom_moq", []):
                    if moq_row.customer_group == customer_group:
                        item["moq"] = moq_row.min_qty
                        break

            response_data.append(item)

        # -------------------------------------
        # Pagination Info
        # -------------------------------------
        total = frappe.db.count("Best Sellers")
        total_pages = (total + page_size - 1) // page_size

        return api_response(True, "Best Sellers fetched", {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "data": response_data
        })

    except Exception as e:
        return api_response(False, f"Error: {str(e)}")
