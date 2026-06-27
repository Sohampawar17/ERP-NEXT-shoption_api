import frappe
import time
from frappe.tests.utils import FrappeTestCase

from shoption_api.otp import api as otp_api


class TestOTPLeadCreate(FrappeTestCase):
    def test_create_lead_with_name(self):
        mobile = "91" + str(int(time.time() % 1000000000))
        # Create lead with name
        resp = otp_api.lead_create(mobile_no=mobile, name="Test User", role="Other")
        self.assertTrue(resp.get("status"))
        lead_name = frappe.db.get_value("Lead", {"mobile_no": mobile}, "name")
        self.assertIsNotNone(lead_name)
        # cleanup
        if lead_name:
            frappe.delete_doc("Lead", lead_name, force=True)

    def test_create_lead_without_name(self):
        mobile = "91" + str(int(time.time() % 1000000000))
        resp = otp_api.lead_create(mobile_no=mobile, name=None, role="Other")
        self.assertTrue(resp.get("status"))
        lead_name = frappe.db.get_value("Lead", {"mobile_no": mobile}, "name")
        self.assertIsNotNone(lead_name)
        if lead_name:
            frappe.delete_doc("Lead", lead_name, force=True)
