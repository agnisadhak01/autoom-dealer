"""Post-install: seed settings and map demo masters."""
import frappe


def map_demo_variant_items():
	mapping = {
		"TVS-APACHE-RTR160-2V-DEMO": "TVS-APACHE-RTR160-2V-DEMO",
		"TVS-APACHE-RTR160-4V-DEMO": "TVS-APACHE-RTR160-4V-DEMO",
		"TVS-RAIDER-125-DEMO": "TVS-RAIDER-125-DEMO",
		"TVS-JUPITER-110-DEMO": "TVS-JUPITER-110-DEMO",
		"TVS-NTORQ-125-XT-DEMO": "TVS-NTORQ-125-XT-DEMO",
	}
	for variant, item in mapping.items():
		if frappe.db.exists("Car Model Variant", variant):
			frappe.db.set_value("Car Model Variant", variant, "erpnext_item", item)


def after_install():
	if frappe.db.exists("Autoom Settings", "Autoom Settings"):
		map_demo_variant_items()
		frappe.db.commit()
		return

	settings = frappe.new_doc("Autoom Settings")
	settings.demo_mode = 1
	settings.default_company = "Autoom TVS Dealership — Demo"
	settings.default_vehicle_warehouse = "Vehicle Yard - ASD"
	settings.default_vehicle_tax_template = "DEMO Vehicle GST 28% Intra-State - ASD"
	settings.default_income_account = "Vehicle Sales - DEMO - ASD"
	settings.insert(ignore_permissions=True)
	map_demo_variant_items()
	frappe.db.commit()
