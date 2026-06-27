# Set LInk Feilds 
# Script Type - Dpctype event
# DocType - Address
# Doctype event - before save 
# if doc.custom_document and doc.custom_document_value:

#     # If links table is empty, create a new row
#     if not doc.links:
#         row = doc.append("links", {})
        
#         row.link_doctype = doc.custom_document
#         row.link_name = doc.custom_document_value
#         row.link_title = doc.custom_document_value

#     else:
#         # Update all existing link rows
#         for row in doc.links:
#             row.link_doctype = doc.custom_document
#             row.link_name = doc.custom_document_value
#             row.link_title = doc.custom_document_value

# Dealer Flag
# script type - Doctype Event 
# Doctype Event - Before save 
# # # -------- Dealer Registration: Auto Complete Flag --------

# # required_fields = [
# #     "mobile_number",
# #     "shop_name",
# #     # "email_id",
# #     "country",
# #     "state",
# #     "district",
# #     "tahshil",
# #     "marketplace",
# #     "pincode",
# #     "address_line_1",
# #     "gst_no",
# #     "gst_certificate",
# #     "shop_front_photo",
# #     "visiting_card",
# #     "passbook_or_checkbook"
# # ]

# # is_complete = True

# # for field in required_fields:
# #     if not doc.get(field):
# #         is_complete = False
# #         break

# # doc.is_completed = 1 if is_complete else 0

# # ---- Dealer Registration Profile Completion Logic ----

# # Base mandatory fields for all modes
# base_fields = [
#     "mobile_number",
#     "shop_name",
#     "country",
#     "state",
#     "district",
#     "tahshil",
#     "marketplace",
#     "pincode",
#     "address_line_1"
# ]

# # Mode specific fields
# mode_1_fields = ["gst_no"]
# mode_2_fields = ["gst_no", "gst_certificate", "shop_front_photo"]
# mode_3_fields = ["shop_front_photo", "visiting_card", "passbook_or_checkbook"]

# # Decide mandatory list based on mode
# mandatory = base_fields.copy()

# if doc.mode == "1":
#     mandatory += mode_1_fields
# elif doc.mode == "2":
#     mandatory += mode_2_fields
# elif doc.mode == "3":
#     mandatory += mode_3_fields

# # Validation check
# is_complete = True
# missing_fields = []

# for field in mandatory:
#     if not doc.get(field):
#         is_complete = False
#         missing_fields.append(field)

# # Set completion flag
# doc.is_completed = 1 if is_complete else 0

# # Optional: Log missing fields for debugging
# # frappe.logger().info(f"Dealer Profile Check: Mode {doc.mode}, Missing {missing_fields}")


