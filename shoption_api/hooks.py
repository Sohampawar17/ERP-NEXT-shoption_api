app_name = "shoption_api"
app_title = "Shoption test api"
app_publisher = "Abhishek"
app_description = "."
app_email = "abhishekdubey6674@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "shoption_api",
# 		"logo": "/assets/shoption_api/logo.png",
# 		"title": "Shoption test api",
# 		"route": "/shoption_api",
# 		"has_permission": "shoption_api.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/shoption_api/css/shoption_api.css"
# app_include_js = "/assets/shoption_api/js/shoption_api.js"

# include js, css files in header of web template
# web_include_css = "/assets/shoption_api/css/shoption_api.css"
# web_include_js = "/assets/shoption_api/js/shoption_api.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "shoption_api/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "shoption_api/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "shoption_api.utils.jinja_methods",
# 	"filters": "shoption_api.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "shoption_api.install.before_install"
# after_install = "shoption_api.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "shoption_api.uninstall.before_uninstall"
# after_uninstall = "shoption_api.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "shoption_api.utils.before_app_install"
# after_app_install = "shoption_api.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "shoption_api.utils.before_app_uninstall"
# after_app_uninstall = "shoption_api.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "shoption_api.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"shoption_api.tasks.all"
# 	],
# 	"daily": [
# 		"shoption_api.tasks.daily"
# 	],
# 	"hourly": [
# 		"shoption_api.tasks.hourly"
# 	],
# 	"weekly": [
# 		"shoption_api.tasks.weekly"
# 	],
# 	"monthly": [
# 		"shoption_api.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "shoption_api.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "shoption_api.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "shoption_api.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["shoption_api.utils.before_request"]
# after_request = ["shoption_api.utils.after_request"]

# Job Events
# ----------
# before_job = ["shoption_api.utils.before_job"]
# after_job = ["shoption_api.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"shoption_api.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

doc_events = {
    "Customer": {
        "after_insert": "shoption_api.erp_api.customer_events.create_customer_address"
    }
}

# override_doctype_class = {
#     "User": "shoption_api.overrides.custom_user.CustomUser"
# }

# doc_events = {
#     "User": {
#         "after_insert": "shoption_api.overrides.user_hooks.set_user_name_as_username"
#     }
# }

# override_doctype_class = {
#     "User": "shoption_api.overrides.custom_user.CustomUser"
# }

# doc_events = {
#     "Sell This to Shoption": {
#         "validate": "shoption_api.erp_api.sell_to_shoption.fill_details"
#     }
# }

# doc_events = {
#     # "Demand Special Rate": {
#     #     "validate": "shoption_api.scripts.demand_special_rate.fill_details"
#     # },
#     "Demand Special Rate": {
#         "validate": "shoption_api.erp_api.demand_special_rate.fill_details"
#     }
# }
doc_events = {
    "Sell This to Shoption": {
        "validate": "shoption_api.erp_api.sell_to_shoption.fill_details"
    },
    "Demand Special Rate": {
        "validate": "shoption_api.erp_api.demand_special_rate.fill_details"
    },
    "Farmer Registration": {
        "on_submit":[ "shoption_api.farmer_registration.update_completion_status.update_completion_status",
                                 "shoption_api.whatsapp_events.handle_farmers_registration"],
        "validate": "shoption_api.farmer_registration.update_completion_status.update_completion_status"
    },
   "Delear Registration":  {
        "on_submit": ["shoption_api.dealer_registration.update_completion_status.update_completion_status",
                                  "shoption_api.whatsapp_events.handle_dealer_registration",],
        "validate": "shoption_api.dealer_registration.update_completion_status.update_completion_status"
    },
    "Sales Order": {
            "on_update_after_submit": "shoption_api.public.sales_order_public.update_payment_status",
            "on_submit": "shoption_api.whatsapp_events.handle_order_placed"
        },
    "Sales Invoice": {
        "on_submit": "shoption_api.whatsapp_events.handle_invoice_generated"
    },
    "Indian Post Tracking Log": {
        "after_insert": "shoption_api.whatsapp_events.handle_indian_post_tracking_dispatch"
    },
    "Upload LR Main": {
        "on_submit": "shoption_api.whatsapp_events.handle_upload_lr_main_dispatch"
    },
    "Shipment": {
        "on_submit": "shoption_api.whatsapp_events.handle_shipment_delivered"
    },
    "Payment Entry": {
        "on_submit":[ "shoption_api.public.payment_entry.update_sales_order_from_payment",
         "shoption_api.whatsapp_events.handle_payment_entry_whatsapp",
        ],
        "on_cancel": "shoption_api.public.payment_entry.update_sales_order_from_payment"
    },
     "PayU Response": {
        "before_insert": "shoption_api.whatsapp_events.handle_payu_transaction",
        "before_save": "shoption_api.whatsapp_events.handle_payu_transaction"
    },
    "Rupifi Webhook Log":{
        "before_insert": "shoption_api.whatsapp_events.handle_rupifi_webhook_log",
        "before_save": "shoption_api.whatsapp_events.handle_rupifi_webhook_log"
    }

}

fixtures = [
    {
        "doctype": "Partner Authentication"
    }
]
