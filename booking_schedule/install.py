import frappe

def after_install():
    """Run after app installation to ensure module is properly set up"""
    
    # Ensure Module Def exists for Booking Schedule
    if not frappe.db.exists("Module Def", "Booking Schedule"):
        module_def = frappe.get_doc({
            "doctype": "Module Def",
            "module_name": "Booking Schedule",
            "app_name": "booking_schedule",
            "custom": 0
        })
        module_def.insert(ignore_permissions=True)
        frappe.db.commit()
        print("Created Module Def for Booking Schedule")
    else:
        print("Module Def for Booking Schedule already exists")
    
    # Clear cache to ensure changes take effect
    frappe.clear_cache()
