"""Whitelisted integration API."""
from __future__ import annotations

import frappe

from autoom_dealer.integration.customer_service import sync_customer_from_doc
from autoom_dealer.integration.reference import get_reference
from autoom_dealer.integration.sales_service import create_sales_order_from_vso


@frappe.whitelist()
def sync_customer(source_doctype: str, source_name: str) -> dict:
	frappe.has_permission(source_doctype, "write", throw=True)
	return sync_customer_from_doc(source_doctype, source_name)


@frappe.whitelist()
def create_sales_order(vso_name: str) -> dict:
	frappe.has_permission("VSO", "write", throw=True)
	return create_sales_order_from_vso(vso_name)


@frappe.whitelist()
def get_integration_status(source_doctype: str, source_name: str) -> dict:
	frappe.has_permission(source_doctype, "read", throw=True)
	return {
		"customer": get_reference(source_doctype, source_name, "Customer"),
		"sales_order": get_reference(source_doctype, source_name, "Sales Order"),
		"contact": get_reference(source_doctype, source_name, "Contact"),
	}
