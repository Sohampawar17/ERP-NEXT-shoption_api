import frappe
from frappe.core.doctype.user.user import User

class CustomUser(User):

    def after_insert(self):
        username = self.username

        if username and self.name != username:
            frappe.db.sql("""
                UPDATE `tabUser`
                SET name = %s
                WHERE name = %s
            """, (username, self.name))

            # Update cached doc name
            self.name = username

            frappe.db.commit()
