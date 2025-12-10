app_name = "booking_schedule"
app_title = "Booking Schedule"
app_publisher = "Azdan"
app_description = "Booking Schedule Management"
app_email = "ibrahim.sedhom@azdan.com"
app_license = "MIT"
required_apps = ["frappe"]

# Fixtures - export these doctypes when using bench export-fixtures
# fixtures = ["Custom Field", "Property Setter"]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/booking_schedule/css/booking_schedule.css"
# app_include_js = "/assets/booking_schedule/js/booking_schedule.js"

# include js, css files in header of web template
# web_include_css = "/assets/booking_schedule/css/booking_schedule.css"
# web_include_js = "/assets/booking_schedule/js/booking_schedule.js"

# Home Pages
# ----------
# application home page (will override Website Settings)
# home_page = "login"

# Default Module for Workspace
# ----------------------------
# The module that will be used as default for the workspace
# default_module = "Booking Schedule"

# DocTypes to be created on install
# ----------------------------------
# This ensures that the Module Def is created
after_install = "booking_schedule.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config
# notification_config = "booking_schedule.notifications.get_notification_config"
