"""Document event hooks."""
from __future__ import annotations

import frappe

from autoom_dealer.integration.customer_service import sync_customer_from_doc


def on_pbf_validate(doc, method=None):
	settings = frappe.get_single("Autoom Settings")
	if not settings.auto_sync_customer_on_save:
		return
	if doc.is_new() and not doc.get("erpnext_customer"):
		return
	if doc.has_value_changed("mobile_number") or doc.has_value_changed("customer_name") or not doc.get("erpnext_customer"):
		try:
			sync_customer_from_doc(doc.doctype, doc.name)
		except Exception:
			frappe.log_error(title="Autoom PBF auto-sync failed")
