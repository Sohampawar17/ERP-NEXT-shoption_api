import frappe
from shoption_api.otp.api import _validate_mobile


@frappe.whitelist(allow_guest=True)
def get_last_otp(mobile_no):
    """
    Fetch OTP details and customer information for a given mobile number.
    
    Args:
        mobile_no: Mobile number of the customer
        
    Returns:
        Dictionary with OTP details, customer information, and expiry details
    """
    ok, mobile = _validate_mobile(mobile_no)
    if not ok:
        return {"status": False, "message": mobile}

    # Get customer by mobile number
    customer = frappe.get_all("Customer", filters={"mobile_no": mobile}, limit_page_length=1)
    if not customer:
        return {"status": False, "message": "Customer not found"}

    customer_doc = frappe.get_doc("Customer", customer[0].name)

    # Get OTP details
    otp = customer_doc.custom_otp
    expiry = customer_doc.custom_otp_expiry
    # Get attempts information (if you have these fields)
    otp_attempts = getattr(customer_doc, 'custom_otp_attempts', 0)
    max_otp_attempts = getattr(customer_doc, 'custom_max_otp_attempts', 3)
    attempts_remaining = max_otp_attempts - otp_attempts if otp_attempts else max_otp_attempts

    # Return comprehensive OTP data
    # NOTE: For dev/testing only - showing plain OTP. In production, 
    # only return otp_hash for verification purposes
    return {
        "status": True,
        "otp": otp,  # Plain OTP for display (DEV/TESTING ONLY)
        "expiry": expiry,
        "expiry_time": expiry,  # For compatibility
        "mobile_no": mobile,
        "customer_id": customer_doc.name,
        "customer_name": customer_doc.customer_name,
        "attempts": otp_attempts,
        "attempts_remaining": attempts_remaining,
        "max_attempts": max_otp_attempts,
        "message": "OTP retrieved successfully"
    }
    
