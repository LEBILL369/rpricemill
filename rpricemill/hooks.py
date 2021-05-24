# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "rpricemill"
app_title = "rpricemill"
app_publisher = "Aerele Technologies Private Limited"
app_description = "RP Modern Rice Mill"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "vignesh@aerele.in"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/rpricemill/css/rpricemill.css"
# app_include_js = "/assets/rpricemill/js/rpricemill.js"

# include js, css files in header of web template
# web_include_css = "/assets/rpricemill/css/rpricemill.css"
# web_include_js = "/assets/rpricemill/js/rpricemill.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "rpricemill/public/scss/website"

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

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "rpricemill.install.before_install"
# after_install = "rpricemill.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "rpricemill.notifications.get_notification_config"

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
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"rpricemill.tasks.all"
# 	],
# 	"daily": [
# 		"rpricemill.tasks.daily"
# 	],
# 	"hourly": [
# 		"rpricemill.tasks.hourly"
# 	],
# 	"weekly": [
# 		"rpricemill.tasks.weekly"
# 	]
# 	"monthly": [
# 		"rpricemill.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "rpricemill.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "rpricemill.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "rpricemill.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

doc_events = {
    "Contact": {
        "on_update": "rpricemill.custom.save_customer",
        "before_save": "rpricemill.custom.contact_before_save"
    },
    "Sales Invoice": {
        "on_submit": ["rpricemill.custom.update_loyality", "rpricemill.custom.add_vehicle_log"],
        "validate": ["rpricemill.custom.update_loyalty_account", "rpricemill.custom.get_gstno", "rpricemill.custom.scgst", "rpricemill.custom.pos_batch"],
        "autoname": "rpricemill.custom.name_sales_invoice",
        "on_update_after_submit": "rpricemill.custom.add_vehicle_log"
    },
    "POS Invoice": {
        "on_submit": ["rpricemill.custom.update_loyality","rpricemill.custom.rice_allert"],
        "validate": ["rpricemill.custom.update_loyalty_account", "rpricemill.custom.pos_batch"],
        "autoname": "rpricemill.custom.name_pos_invoice"
    },
    "Vehicle": {
        "validate": "rpricemill.custom.create_events_from_vehicle_remainder"
    },
    "Customer": {
        "validate": "rpricemill.custom.add_mobile_search",
    },
    "Purchase Order": {
        "autoname": "rpricemill.custom.name_purchase_order"
    },
    "Purchase Receipt": {
        "autoname": "rpricemill.custom.name_purchase_receipt"
    },
    "Purchase Invoice": {
        "autoname": "rpricemill.custom.name_purchase_invoice"
    },
    "Sales Order": {
        "autoname": "rpricemill.custom.name_sales_order"
    },
    "Payment Entry": {
        "autoname": "rpricemill.custom.name_payment_entry"
    }
}

doctype_js = {
    "POS Closing Entry": "rpricemill/custom_scripts/denominations.js",
    "Sales Invoice": "rpricemill/custom_scripts/sales_invoice.js",
    "Sales Order":  "rpricemill/custom_scripts/sales_order.js",
    "Purchase Invoice":  "rpricemill/custom_scripts/purchase_invoice.js",
    "Purchase Order":  "rpricemill/custom_scripts/purchase_order.js",
    "Purchase Receipt":  "rpricemill/custom_scripts/purchase_receipt.js",
    "Delivery Note":  "rpricemill/custom_scripts/delivery_note.js",
    "Payment Entry":  "rpricemill/custom_scripts/payment_entry.js"
}

jenv = {"methods": [
        "pos_qty:rpricemill.custom.pos_qty"
        ]
        }
