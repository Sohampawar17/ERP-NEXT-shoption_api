import frappe

def set_user_name_as_username(doc, method):
    """
    After User Insert:
    Replace User.name (email) → username
    Only if username exists and name != username
    """

    if not doc.username:
        return

    # Name is email? Replace with username
    if doc.name != doc.username:
        # Change the primary key value
        frappe.db.set_value("User", doc.name, "name", doc.username)
        
        # Also update doc.name in memory (optional but clean)
        doc.name = doc.username
