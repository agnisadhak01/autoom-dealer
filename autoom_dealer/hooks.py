app_name = "autoom_dealer"
app_title = "Autoom Dealer"
app_publisher = "Autoom Studio"
app_description = "India/TVS dealership ERPNext integration layer for DMS Sales"
app_email = "demo.bengaluru@autoomstudio.com"
app_license = "mit"

required_apps = ["erpnext", "dms_sales"]

fixtures = [
	{
		"dt": "Custom Field",
		"filters": [
			[
				"name",
				"in",
				[
					"Prospect Booking Form-erpnext_customer",
					"Prospect Booking Form-erpnext_contact",
					"Prospect Booking Form-sync_status",
					"Prospect Booking Form-last_sync_at",
					"Prospect Booking Form-sync_error",
					"VSO-erpnext_customer",
					"VSO-erpnext_contact",
					"VSO-erpnext_sales_order",
					"VSO-erpnext_serial_no",
					"VSO-sync_status",
					"VSO-last_sync_at",
					"VSO-sync_error",
					"Car Details And Checklist-erpnext_serial_no",
					"Car Details And Checklist-erpnext_sales_invoice",
					"Car Model Variant-erpnext_item",
					"Sales Advisor-erpnext_employee",
				],
			]
		],
	},
	{
		"dt": "Client Script",
		"filters": [["name", "in", ["Autoom VSO Integration Buttons", "Autoom PBF Integration Buttons"]]],
	},
]

doc_events = {
	"Prospect Booking Form": {
		"validate": "autoom_dealer.integration.hooks.on_pbf_validate",
	},
}

override_whitelisted_methods = {}

after_install = "autoom_dealer.install.after_install"
