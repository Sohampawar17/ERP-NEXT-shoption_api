

# updateed code with MOQ logic 16/12
# import frappe
# from shoption_api.erp_api.common import api_auth, require_post, api_response

# @frappe.whitelist(allow_guest=True)
# def get_top_deals(page=1, page_size=20, mobile_no=None):

#     api_auth()
#     require_post()

#     # -------------------------------------
#     # 1️⃣ Mobile required
#     # -------------------------------------
#     if not mobile_no:
#         return api_response(False, "mobile_no is required")

#     # -------------------------------------
#     # 2️⃣ Get Customer
#     # -------------------------------------
#     customer = frappe.get_all(
#         "Customer",
#         filters={"mobile_no": mobile_no},
#         fields=["name", "customer_group"],
#         limit=1
#     )

#     user_id = None
#     customer_group = None

#     if customer:
#         customer_name = customer[0].name
#         customer_group = customer[0].customer_group

#         # -------------------------------------
#         # 3️⃣ Try to get Portal User
#         # -------------------------------------
#         portal_user = frappe.get_all(
#             "Portal User",
#             filters={"parent": customer_name},
#             fields=["user"],
#             limit=1
#         )

#         if portal_user:
#             user_id = portal_user[0].user

#     # -------------------------------------
#     # 4️⃣ Set user context
#     # -------------------------------------
#     if user_id:
#         frappe.set_user(user_id)
#     else:
#         frappe.set_user("Administrator")

#     # -------------------------------------
#     # Pagination
#     # -------------------------------------
#     try:
#         page = int(page)
#         page_size = int(page_size)
#     except:
#         page, page_size = 1, 20

#     start = (page - 1) * page_size

#     try:
#         # -------------------------------------
#         # 5️⃣ Fetch Top Deals
#         # -------------------------------------
#         top_rows = frappe.get_list(
#             "Top Deals",
#             fields=["item_code", "item_name", "image"],
#             limit_start=start,
#             limit_page_length=page_size,
#             order_by="creation desc"
#         )

#         response_data = []

#         # -------------------------------------
#         # 6️⃣ Process each deal
#         # -------------------------------------
#         for row in top_rows:

#             item_code = row.get("item_code")

#             # Fetch item details
#             item_doc = frappe.get_all(
#                 "Item",
#                 filters={"name": item_code},
#                 fields=[
#                     "name as item_code",
#                     "item_name",
#                     "item_group",
#                     "brand",
#                     "stock_uom",
#                     "gst_hsn_code",
#                     "custom_sub_category",
#                     "custom_image_1"
#                 ],
#                 limit=1
#             )

#             if not item_doc:
#                 continue

#             item = item_doc[0]

#             # -------------------------------------
#             # 7️⃣ Price Logic (unchanged)
#             # -------------------------------------
#             price_row = frappe.get_list(
#                 "Item Price",
#                 filters={"item_code": item_code},
#                 fields=[
#                     "price_list",
#                     "custom_mrp",
#                     "price_list_rate",
#                     "discount",
#                     "custom_oem_code"
#                 ],
#                 order_by="valid_from desc",
#                 limit=1
#             )

#             if user_id and price_row:
#                 p = price_row[0]
#                 item["price_list"] = p.get("price_list")
#                 item["mrp"]        = p.get("custom_mrp")
#                 item["price"]      = p.get("price_list_rate")
#                 item["discount"]   = p.get("discount")
#                 item["oem_code"]   = p.get("custom_oem_code")
#             else:
#                 item["price_list"] = None
#                 item["mrp"] = None
#                 item["price"] = None
#                 item["discount"] = None
#                 item["oem_code"] = None

#             # -------------------------------------
#             # 8️⃣ MOQ LOGIC (NEW)
#             # -------------------------------------
#             item["moq"] = None

#             if customer_group:
#                 item_full_doc = frappe.get_doc("Item", item_code)

#                 for moq_row in item_full_doc.get("custom_moq", []):
#                     if moq_row.customer_group == customer_group:
#                         item["moq"] = moq_row.min_qty
#                         break

#             response_data.append(item)

#         # -------------------------------------
#         # Pagination response
#         # -------------------------------------
#         total = frappe.db.count("Top Deals")
#         total_pages = (total + page_size - 1) // page_size

#         return api_response(True, "Top Deals fetched", {
#             "total": total,
#             "page": page,
#             "page_size": page_size,
#             "total_pages": total_pages,
#             "data": response_data
#         })

#     except Exception as e:
#         return api_response(False, f"Error: {str(e)}")

# farmer override price list logic added 20/12
# import frappe
# from shoption_api.erp_api.common import api_auth, require_post, api_response
# from shoption_api.cart.cart import get_item_price_withgst #18/12

# @frappe.whitelist(allow_guest=True)
# def get_top_deals(page=1, page_size=20, mobile_no=None):

#     api_auth()
#     require_post()

#     # -------------------------------------
#     # Mobile required
#     # -------------------------------------
#     if not mobile_no:
#         return api_response(False, "mobile_no is required")

#     # -------------------------------------
#     # Find Customer
#     # -------------------------------------
#     customer = frappe.get_all(
#         "Customer",
#         filters={"mobile_no": mobile_no},
#         fields=["name", "customer_group"],
#         limit=1
#     )

#     user_id = None
#     customer_group = None

#     if customer:
#         customer_name = customer[0].name
#         customer_group = customer[0].customer_group

#         portal_user = frappe.get_all(
#             "Portal User",
#             filters={"parent": customer_name},
#             fields=["user"],
#             limit=1
#         )

#         if portal_user:
#             user_id = portal_user[0].user

#     # -------------------------------------
#     # Set user context
#     # -------------------------------------
#     if user_id:
#         frappe.set_user(user_id)
#     else:
#         frappe.set_user("Administrator")

#     # -------------------------------------
#     # Pagination
#     # -------------------------------------
#     try:
#         page = int(page)
#         page_size = int(page_size)
#     except:
#         page, page_size = 1, 20

#     start = (page - 1) * page_size

#     try:
#         # -------------------------------------
#         # Fetch Top Deals
#         # -------------------------------------
#         top_rows = frappe.get_list(
#             "Top Deals",
#             fields=["item_code", "item_name", "image"],
#             limit_start=start,
#             limit_page_length=page_size,
#             order_by="creation desc"
#         )

#         response_data = []

#         for row in top_rows:

#             item_code = row.get("item_code")

#             # Item details
#             item_doc = frappe.get_all(
#                 "Item",
#                 filters={"name": item_code},
#                 fields=[
#                     "name as item_code",
#                     "item_name",
#                     "item_group",
#                     "brand",
#                     "stock_uom",
#                     "gst_hsn_code",
#                     "custom_sub_category",
#                     "custom_image_1"
#                 ],
#                 limit=1
#             )

#             if not item_doc:
#                 continue

#             item = item_doc[0]

#             # -------------------------------------
#             # PRICE FILTERS (ONLY FARMER OVERRIDE)
#             # -------------------------------------
#             price_filters = {
#                 "item_code": item_code
#             }

#             if customer_group == "Farmer":
#                 price_filters["price_list"] = f"{item.get('brand')}-Farmer"

#             price_row = frappe.get_list(
#                 "Item Price",
#                 filters=price_filters,
#                 fields=[
#                     "price_list",
#                     "custom_mrp",
#                     "price_list_rate",
#                     # "custom_app_diplay_rate",
#                     "discount",
#                     "custom_oem_code"
#                 ],
#                 order_by="valid_from desc",
#                 limit=1
#             )

#             if user_id and price_row:
#                 p = price_row[0]
#                 item["price_list"] = p.get("price_list")
#                 item["mrp"] = p.get("custom_mrp")
#                 item["price"] = p.get("price_list_rate")
#                 # item["price"] = p.get("custom_app_diplay_rate")
#                 item["discount"] = p.get("discount")
#                 item["oem_code"] = p.get("custom_oem_code")
#             else:
#                 item["price_list"] = None
#                 item["mrp"] = None
#                 item["price"] = None
#                 item["discount"] = None
#                 item["oem_code"] = None

#             # -------------------------------------
#             # MOQ LOGIC (UNCHANGED)
#             # -------------------------------------
#             item["moq"] = None

#             if customer_group:
#                 item_full_doc = frappe.get_doc("Item", item_code)
#                 for moq_row in item_full_doc.get("custom_moq", []):
#                     if moq_row.customer_group == customer_group:
#                         item["moq"] = moq_row.min_qty
#                         break

#             response_data.append(item)
            
#             # -------------------------------------
#             # GST PRICE (NEW ADDITION)
#             # ------------------------------------- 18/12
#             item["gst_price"] = None
#             if user_id and customer_group and item.get("price"):
#                 try:
#                     gst_data = get_item_price_withgst(
#                         item_code=item_code,
#                         customer=customer_name,
#                         customer_group=customer_group,
#                         company=frappe.defaults.get_global_default("company"),
#                         currency=frappe.defaults.get_global_default("currency"),
#                         qty=1,
#                         brand=item.get("brand")
#                     )
#                     item["gst_price"] = gst_data.get("rate_incl_gst")
#                 except Exception:
#                     item["gst_price"] = None

#         # -------------------------------------
#         # Pagination response
#         # -------------------------------------
#         total = frappe.db.count("Top Deals")
#         total_pages = (total + page_size - 1) // page_size

#         return api_response(True, "Top Deals fetched", {
#             "total": total,
#             "page": page,
#             "page_size": page_size,
#             "total_pages": total_pages,
#             "data": response_data
#         })

#     except Exception as e:
#         return api_response(False, f"Error: {str(e)}")

# updated code with key name changes 18/12
import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response
from shoption_api.cart.cart import get_item_price_withgst  # 18/12

@frappe.whitelist(allow_guest=True)
def get_top_deals(page=1, page_size=20, mobile_no=None):
    api_auth()
    require_post()

    if not mobile_no:
        return api_response(False, "mobile_no is required")

    original_user = frappe.session.user

    try:
        # ----------------------------
        # 1) Customer + Portal User (optimized)
        # ----------------------------
        customer = frappe.db.get_value(
            "Customer",
            {"mobile_no": mobile_no},
            ["name", "customer_group"],
            as_dict=True
        )

        user_id = None
        customer_group = None
        customer_name = None

        if customer:
            customer_name = customer.name
            customer_group = customer.customer_group

            user_id = frappe.db.get_value(
                "Portal User",
                {"parent": customer_name},
                "user"
            )

        # ----------------------------
        # 2) Set User Context
        # ----------------------------
        frappe.set_user(user_id if user_id else "Administrator")

        # ----------------------------
        # 3) Pagination
        # ----------------------------
        try:
            page = int(page)
            page_size = int(page_size)
        except:
            page, page_size = 1, 20
        start = (page - 1) * page_size

        # ----------------------------
        # 4) Fetch Top Deals
        # ----------------------------
        top_rows = frappe.get_list(
            "Top Deals",
            fields=["item_code"],
            limit_start=start,
            limit_page_length=page_size,
            order_by="creation desc"
        )

        if not top_rows:
            return api_response(True, "No deals found", {
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "data": []
            })

        item_codes = [row.item_code for row in top_rows]

        # ----------------------------
        # 5) Fetch Items in bulk
        # ----------------------------
        items = frappe.get_all(
            "Item",
            filters={"name": ["in", item_codes], "disabled": 0},
            fields=[
                "name as item_code",
                "item_name",
                "item_group",
                "brand",
                "stock_uom",
                "gst_hsn_code",
                "custom_sub_category",
                "custom_image_1"
            ]
        )

        item_map = {i.item_code: i for i in items}

        # ----------------------------
        # 6) Fetch Brand Names in bulk
        # ----------------------------
        brand_ids = list({i.brand for i in items if i.brand})
        brand_map = {}
        if brand_ids:
            brands = frappe.get_all(
                "Brand",
                filters={"name": ["in", brand_ids]},
                fields=["name", "brand as brand_name"]
            )
            brand_map = {b.name: b.brand_name for b in brands}

        # ----------------------------
        # 7) Fetch MOQ in bulk
        # ----------------------------
        moq_map = {}
        if customer_group and item_codes:
            moqs = frappe.get_all(
                "MOQ Items",
                filters={
                    "parent": ["in", item_codes],
                    "customer_group": customer_group
                },
                fields=["parent", "min_qty"]
            )
            moq_map = {b.parent: b.min_qty for b in moqs}

        response_data = []

        # ----------------------------
        # 8) Loop Top Deals (original logic)
        # ----------------------------
        for code in item_codes:
            item = item_map.get(code)
            if not item:
                continue

            # Brand name instead of ID
            
            price_row=[]
            # Price filters (Farmer override)
            price_filters = {"item_code": code}
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

                # GST price
                try:
                    gst_data = get_item_price_withgst(
                        item_code=code,
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

            # Final Price
            item["no_gst_price"] = base_price
            item["price"] = gst_price
            item["actual_rate"] = gst_price

            # MOQ
            item["moq"] =moq_map.get(code, 0)
            item["brand_id"] = item.get("brand")
            item["brand"] = brand_map.get(item.get("brand"))
            
            response_data.append(item)

        # ----------------------------
        # 9) Pagination Meta
        # ----------------------------
        total = frappe.db.count("Top Deals")
        total_pages = (total + page_size - 1) // page_size

        return api_response(True, "Top Deals fetched", {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "data": response_data
        })

    except Exception as e:
        return api_response(False, f"Error: {str(e)}")
