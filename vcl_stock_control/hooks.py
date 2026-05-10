app_name = "vcl_stock_control"
app_title = "VCL Stock Control"
app_publisher = "VCL"
app_description = "VCL Factory Stock Control App - Stock capture and visibility for inks, chemicals, raw materials, finished goods, cores, bearings, and fuel."
app_email = "info@vcl.co.tz"
app_license = "MIT"
required_apps = ["frappe", "erpnext"]

# Document Events
# ----------------
doc_events = {}

# Fixtures
# --------
fixtures = [
    {
        "doctype": "Stock Category",
        "filters": [["is_active", "=", 1]],
    }
]

# Web bundle for the Stock Portal pages
# -------------------------------------
# Per-page <script> tags load portal_sheet.js / portal_review.js explicitly,
# so we only register the shared CSS at the website level.
web_include_css = ["/assets/vcl_stock_control/css/portal.css"]

# Website route rules — pretty URLs for the portal
# ------------------------------------------------
website_route_rules = [
    {"from_route": "/stock-portal/sheet/<name>", "to_route": "stock-portal/sheet/[name]"},
    {"from_route": "/stock-portal/review/<name>", "to_route": "stock-portal/review/[name]"},
]

# Jinja
# -----
# jinja = {}

# Installation
# ------------
# before_install = "vcl_stock_control.install.before_install"
after_install = "vcl_stock_control.install.after_install"

# Scheduled Tasks
# ----------------
# scheduler_events = {}

# Permissions
# -----------
# has_permission = {}

# DocType Class
# -------------
# override_doctype_class = {}
