"""Customer + Contact sync from DMS documents."""
from __future__ import annotations

import frappe
from frappe.utils import cstr

from autoom_dealer.integration.reference import ERROR, SYNCED, mark_source_sync_fields, upsert_reference


def _settings():
	return frappe.get_single("Autoom Settings")


def _normalize_mobile(mobile: str | None) -> str:
	if not mobile:
		return ""
	digits = "".join(ch for ch in cstr(mobile) if ch.isdigit())
	if len(digits) >= 10:
		return digits[-10:]
	return digits


def find_customer_by_mobile(mobile: str) -> str | None:
	norm = _normalize_mobile(mobile)
	if not norm:
		return None

	# Contact mobile lookup
	contacts = frappe.get_all(
		"Contact",
		filters={"mobile_no": ["like", f"%{norm}"]},
		pluck="name",
		limit=5,
	)
	for contact in contacts:
		link = frappe.db.get_value(
			"Dynamic Link",
			{"link_doctype": "Customer", "parenttype": "Contact", "parent": contact},
			"link_name",
		)
		if link:
			return link

	# Customer direct mobile field (if populated)
	return frappe.db.get_value("Customer", {"mobile_no": ["like", f"%{norm}"]}, "name")


def find_customer_by_name(name: str | None) -> str | None:
	if not name:
		return None
	exact = frappe.db.get_value("Customer", {"customer_name": name}, "name")
	if exact:
		return exact
	return frappe.db.get_value("Customer", {"customer_name": ["like", f"%{name}%"]}, "name")


def find_customer_by_email(email: str | None) -> str | None:
	if not email:
		return None
	return frappe.db.get_value("Customer", {"email_id": email}, "name")


def sync_customer_from_doc(source_doctype: str, source_name: str) -> dict:
	doc = frappe.get_doc(source_doctype, source_name)
	settings = _settings()

	customer_name = getattr(doc, "customer_name", None)
	mobile = getattr(doc, "mobile_number", None) or getattr(doc, "customer_phone", None)
	email = getattr(doc, "email", None)
	customer_ic = getattr(doc, "customer_ic", None) or getattr(doc, "nric", None)

	try:
		existing = (
			find_customer_by_mobile(mobile)
			or find_customer_by_email(email)
			or find_customer_by_name(customer_name)
		)
		if existing:
			customer = frappe.get_doc("Customer", existing)
			action = "linked"
		else:
			customer = frappe.new_doc("Customer")
			customer.customer_name = f"{customer_name} - DEMO" if settings.demo_mode else customer_name
			customer.customer_type = "Individual"
			customer.customer_group = "Individual"
			customer.territory = "India"
			customer.mobile_no = mobile
			customer.email_id = email
			customer.tax_id = customer_ic if not settings.demo_mode else None
			customer.insert(ignore_permissions=True)
			action = "created"

		contact = _ensure_contact(customer.name, customer_name, mobile, email)
		extra = {"erpnext_customer": customer.name, "erpnext_contact": contact}
		mark_source_sync_fields(source_doctype, source_name, SYNCED, extra=extra)
		upsert_reference(
			source_doctype,
			source_name,
			"Customer",
			customer.name,
			SYNCED,
			company=settings.default_company,
		)
		if contact:
			upsert_reference(
				source_doctype,
				source_name,
				"Contact",
				contact,
				SYNCED,
				company=settings.default_company,
			)

		frappe.db.commit()
		return {
			"action": action,
			"customer": customer.name,
			"contact": contact,
			"source_doctype": source_doctype,
			"source_name": source_name,
		}
	except Exception as exc:
		frappe.db.rollback()
		mark_source_sync_fields(source_doctype, source_name, ERROR, sync_error=str(exc))
		frappe.db.commit()
		raise


def _ensure_contact(customer: str, full_name: str, mobile: str | None, email: str | None) -> str | None:
	existing = frappe.db.get_value(
		"Dynamic Link",
		{"link_doctype": "Customer", "link_name": customer, "parenttype": "Contact"},
		"parent",
	)
	if existing:
		return existing

	contact = frappe.new_doc("Contact")
	contact.first_name = full_name
	contact.mobile_no = mobile
	contact.email_id = email
	contact.append("links", {"link_doctype": "Customer", "link_name": customer})
	contact.insert(ignore_permissions=True)
	return contact.name
