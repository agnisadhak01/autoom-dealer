"""VSO → ERPNext Sales Order orchestration (idempotent)."""
from __future__ import annotations

import frappe
from frappe.utils import flt

from autoom_dealer.integration.customer_service import sync_customer_from_doc
from autoom_dealer.integration.reference import ERROR, SYNCED, get_reference, mark_source_sync_fields, upsert_reference


def create_sales_order_from_vso(vso_name: str) -> dict:
	vso = frappe.get_doc("VSO", vso_name)
	settings = frappe.get_single("Autoom Settings")

	existing = get_reference("VSO", vso_name, "Sales Order")
	if existing and existing.erpnext_name and existing.sync_status == SYNCED:
		if frappe.db.exists("Sales Order", existing.erpnext_name):
			return {
				"action": "already_linked",
				"sales_order": existing.erpnext_name,
				"message": "Sales Order already linked to this VSO",
			}

	try:
		if not vso.get("erpnext_customer"):
			sync_customer_from_doc("VSO", vso_name)
			vso.reload()

		item_code = _resolve_item_code(vso)
		company = settings.default_company
		warehouse = settings.default_vehicle_warehouse
		tax_template = settings.default_vehicle_tax_template

		so = frappe.new_doc("Sales Order")
		so.company = company
		so.customer = vso.erpnext_customer
		so.transaction_date = vso.date_vso or frappe.utils.today()
		so.delivery_date = frappe.utils.today()
		if tax_template:
			so.taxes_and_charges = tax_template

		rate = flt(vso.net_selling_price or vso.selling_price_standard_body or 0)
		if not rate:
			variant = frappe.get_doc("Car Model Variant", vso.car_model_variant)
			rate = flt(variant.approved_net_selling_price)

		so.append(
			"items",
			{
				"item_code": item_code,
				"qty": 1,
				"rate": rate,
				"warehouse": warehouse,
				"description": f"DMS VSO {vso_name}",
			},
		)
		so.insert(ignore_permissions=True)
		so.submit()

		extra = {"erpnext_sales_order": so.name}
		mark_source_sync_fields("VSO", vso_name, SYNCED, extra=extra)
		upsert_reference("VSO", vso_name, "Sales Order", so.name, SYNCED, company=company)

		frappe.db.commit()
		return {"action": "created", "sales_order": so.name, "item_code": item_code}

	except Exception as exc:
		frappe.db.rollback()
		mark_source_sync_fields("VSO", vso_name, ERROR, sync_error=str(exc))
		frappe.db.commit()
		raise


def _resolve_item_code(vso) -> str:
	if not vso.car_model_variant:
		frappe.throw("VSO has no Car Model Variant")

	custom_item = frappe.db.get_value("Car Model Variant", vso.car_model_variant, "erpnext_item")
	if custom_item:
		return custom_item

	model_code = frappe.db.get_value("Car Model Variant", vso.car_model_variant, "model_code")
	if model_code:
		candidate = f"{model_code}-DEMO"
		if frappe.db.exists("Item", candidate):
			return candidate

	candidate = f"{vso.car_model_variant}"
	if frappe.db.exists("Item", candidate):
		return candidate

	frappe.throw(f"No ERPNext Item mapped for variant {vso.car_model_variant}")
