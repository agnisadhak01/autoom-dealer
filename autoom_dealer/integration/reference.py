"""Integration Reference helpers."""
from __future__ import annotations

import frappe
from frappe.utils import now_datetime


SYNCED = "Synced"
PENDING = "Pending"
ERROR = "Error"


def get_reference(source_doctype: str, source_name: str, erpnext_doctype: str) -> dict | None:
	row = frappe.db.get_value(
		"Integration Reference",
		{
			"source_doctype": source_doctype,
			"source_name": source_name,
			"erpnext_doctype": erpnext_doctype,
		},
		["name", "erpnext_name", "sync_status", "sync_error", "last_synced_at"],
		as_dict=True,
	)
	return row


def upsert_reference(
	source_doctype: str,
	source_name: str,
	erpnext_doctype: str,
	erpnext_name: str,
	sync_status: str = SYNCED,
	sync_error: str | None = None,
	company: str | None = None,
) -> str:
	existing = get_reference(source_doctype, source_name, erpnext_doctype)
	if existing:
		doc = frappe.get_doc("Integration Reference", existing.name)
	else:
		doc = frappe.new_doc("Integration Reference")
		doc.source_doctype = source_doctype
		doc.source_name = source_name
		doc.erpnext_doctype = erpnext_doctype

	doc.erpnext_name = erpnext_name
	doc.sync_status = sync_status
	doc.sync_error = sync_error or ""
	doc.last_synced_at = now_datetime()
	if company:
		doc.company = company
	doc.save(ignore_permissions=True)
	return doc.name


def mark_source_sync_fields(
	source_doctype: str,
	source_name: str,
	sync_status: str,
	sync_error: str | None = None,
	extra: dict | None = None,
):
	values = {
		"sync_status": sync_status,
		"last_sync_at": now_datetime(),
		"sync_error": sync_error or "",
	}
	if extra:
		values.update(extra)
	frappe.db.set_value(source_doctype, source_name, values, update_modified=False)
