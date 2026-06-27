import frappe
import os

DATA_DIR = frappe.get_app_path("shoption_api", "data_import")

def import_marketplace_all():
    files = sorted(f for f in os.listdir(DATA_DIR) if f.startswith("Marketplace_part_") and f.endswith(".csv"))

    frappe.logger().info(f"Found {len(files)} files to import.")

    for f in files:
        frappe.logger().info(f"Importing {f} ...")
        frappe.get_attr("shoption_api.data_import.import_master.import_marketplace")(filename=f)

    frappe.logger().info("All marketplace files imported successfully.")
    return "Done"
