import frappe
from shoption_api.erp_api.common import api_auth, require_post, api_response
from shoption_api.cart.cart import get_item_price_withgst

@frappe.whitelist(allow_guest=True)
def get_trending_best_seller(page=1, page_size=20, mobile_no=None):
    api_auth()
    require_post()

    if not mobile_no:
        return api_response(False, "mobile_no is required")

    original_user = frappe.session.user

    try:
        # ----------------------------
        # 1) Customer + Portal User
        # ----------------------------
        customer = frappe.db.get_value(
            "Customer",
            {"mobile_no": mobile_no},
            ["name", "customer_group"],
            as_dict=True
        )

        frappe_user = None
        customer_group = None
        customer_name = None

        if customer:
            customer_name = customer.name
            customer_group = customer.customer_group
            frappe_user = frappe.db.get_value(
                "Portal User",
                {"parent": customer_name},
                "user"
            )

        # ----------------------------
        # 2) Set user context
        # ----------------------------
        frappe.set_user(frappe_user if frappe_user else "Administrator")

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
        # 4) Fetch Trending Best Seller
        # ----------------------------
        rows = frappe.get_list(
            "Trending Best Seller",
            fields=["item_code", "item_name", "image"],
            limit_start=start,
            limit_page_length=page_size,
            order_by="creation desc"
        )

        if not rows:
            return api_response(True, "No items found", {
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "data": []
            })

        item_codes = [row.item_code for row in rows]

        # ----------------------------
        # 5) Bulk fetch Items
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
        # 6) Bulk fetch Brand names
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
        # 7) Bulk fetch MOQ
        # ----------------------------
        moq_map = {}
        if customer_group and item_codes:
            moqs = frappe.get_all(
                "MOQ Items",
                filters={"parent": ["in", item_codes], "customer_group": customer_group},
                fields=["parent", "min_qty"]
            )
            moq_map = {b.parent: b.min_qty for b in moqs}

        response_data = []

        # ----------------------------
        # 8) Loop Trending Best Seller
        # ----------------------------
        for row in rows:
            code = row.item_code
            item = item_map.get(code)
            if not item:
                continue

            # Add image from list
            item["image"] = row.get("image")

           
           
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

            if frappe_user and price_row:
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
            item["moq"] = moq_map.get(code, 0)
            # Brand name
            item["brand_id"] = item.get("brand")
            item["brand"] = brand_map.get(item.get("brand"))
            
            response_data.append(item)

        # ----------------------------
        # 9) Pagination Meta
        # ----------------------------
        total = frappe.db.count("Trending Best Seller")
        total_pages = (total + page_size - 1) // page_size

        return api_response(True, "Trending Best Seller fetched", {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "data": response_data
        })

    except Exception as e:
        return api_response(False, f"Error: {str(e)}")
