# -*- coding: utf-8 -*-
# Copyright (c) 2023, Transcorp and contributors
# Booking Schedule API with JWT Authentication

import frappe
from frappe import _
from frappe.utils import getdate, add_days, nowdate
from datetime import timedelta


def get_merchant_from_token():
    """
    Extract and validate merchant_ns_id from JWT token.
    Returns merchant_ns_id or throws error if invalid.
    """
    token = frappe.request.headers.get("x-access-token") if frappe.request else None
    
    if not token:
        frappe.throw(_("Token is required"), frappe.AuthenticationError)
    
    from booking_schedule.auth import validate_token
    payload = validate_token(token)
    
    if not payload:
        frappe.throw(_("Invalid or expired token"), frappe.AuthenticationError)
    
    merchant_ns_id = payload.get("merchant_ns_id")
    if not merchant_ns_id:
        frappe.throw(_("Merchant not linked to user"), frappe.AuthenticationError)
    
    return merchant_ns_id


# ==================== PROTECTED ENDPOINTS ====================

@frappe.whitelist(allow_guest=True)
def get_delivery_schedule():
    """
    Calculate available delivery slots for the authenticated merchant.
    merchant_ns_id is extracted from JWT token automatically.
    """
    merchant_ns_id = get_merchant_from_token()

    merchant = frappe.get_doc("Merchant", {"ns_merchant_id": merchant_ns_id})
    if not merchant:
        frappe.throw(_("Merchant not found"), exc=frappe.DoesNotExistError)

    if merchant.inactive or merchant.deleted:
        frappe.throw(_("Merchant is inactive or deleted"))

    available_slots = []
    
    # Process each schedule configuration
    for schedule in merchant.delivery_schedule:
        days_from_now = schedule.days_from_now or 0
        schedule_duration = schedule.schedule_duration or 0
        capacity = schedule.capacity or 0
        time_from = schedule.time_from_slot
        time_to = schedule.time_to_slot
        week_days = schedule.week_days.split(",") if schedule.week_days else []
        
        start_date = add_days(nowdate(), days_from_now)
        end_date = add_days(nowdate(), days_from_now + schedule_duration + 1)
        
        current_date = getdate(start_date)
        final_date = getdate(end_date)
        
        while current_date < final_date:
            date_str = current_date.strftime("%Y-%m-%d")
            day_name = current_date.strftime("%a")
            
            if is_holiday(current_date):
                current_date += timedelta(days=1)
                continue
                
            if day_name not in week_days:
                current_date += timedelta(days=1)
                continue
                
            occupied_slots = count_task(merchant_ns_id, date_str, time_from, time_to)
            remaining_slots = capacity - occupied_slots
            
            if remaining_slots > 0:
                available_slots.append({
                    "Date": date_str,
                    "Week_Day": day_name,
                    "Slots": f"{time_from} - {time_to}",
                    "Capacity": capacity,
                    "Occupied_Slots": occupied_slots,
                    "Remaining_Slots": remaining_slots
                })
                
            current_date += timedelta(days=1)

    available_slots.sort(key=lambda x: x["Date"])
    
    return {
        "status": "Success",
        "message": "The delivery Schedule has been found.",
        "count": len(available_slots),
        "data": available_slots
    }


@frappe.whitelist(allow_guest=True)
def create_booking(date, time_from, time_to):
    """
    Create a new booking for the authenticated merchant.
    """
    merchant_ns_id = get_merchant_from_token()
    
    if not (date and time_from and time_to):
        frappe.throw(_("Missing required parameters: date, time_from, time_to"))

    merchant = frappe.db.get_value("Merchant", {"ns_merchant_id": merchant_ns_id}, "name")
    if not merchant:
        frappe.throw(_("Merchant not found"))

    doc = frappe.get_doc({
        "doctype": "Booking",
        "date": date,
        "time_from": time_from,
        "time_to": time_to,
        "merchant_ns_id": merchant
    })
    doc.insert(ignore_permissions=True)
    
    return {
        "status": "Success",
        "message": "Booking created successfully",
        "data": {
            "id": doc.name,
            "date": str(doc.date),
            "time_from": str(doc.time_from),
            "time_to": str(doc.time_to)
        }
    }


@frappe.whitelist(allow_guest=True)
def update_booking(booking_id, date=None, time_from=None, time_to=None):
    """
    Update an existing booking. Only the owner merchant can update.
    """
    merchant_ns_id = get_merchant_from_token()
    
    if not booking_id:
        frappe.throw(_("Booking ID is required"))
    
    doc = frappe.get_doc("Booking", booking_id)
    
    # Verify ownership
    merchant_name = frappe.db.get_value("Merchant", {"ns_merchant_id": merchant_ns_id}, "name")
    if doc.merchant_ns_id != merchant_name:
        frappe.throw(_("Not authorized to update this booking"), frappe.AuthenticationError)
    
    if date:
        doc.date = date
    if time_from:
        doc.time_from = time_from
    if time_to:
        doc.time_to = time_to
    
    doc.save(ignore_permissions=True)
    
    return {
        "status": "Success",
        "message": "Booking updated successfully",
        "data": {
            "id": doc.name,
            "date": str(doc.date),
            "time_from": str(doc.time_from),
            "time_to": str(doc.time_to)
        }
    }


@frappe.whitelist(allow_guest=True)
def delete_booking(booking_id):
    """
    Delete a booking. Only the owner merchant can delete.
    """
    merchant_ns_id = get_merchant_from_token()
    
    if not booking_id:
        frappe.throw(_("Booking ID is required"))
    
    doc = frappe.get_doc("Booking", booking_id)
    
    # Verify ownership
    merchant_name = frappe.db.get_value("Merchant", {"ns_merchant_id": merchant_ns_id}, "name")
    if doc.merchant_ns_id != merchant_name:
        frappe.throw(_("Not authorized to delete this booking"), frappe.AuthenticationError)
    
    frappe.delete_doc("Booking", booking_id, ignore_permissions=True)
    
    return {
        "status": "Success",
        "message": "Booking deleted successfully"
    }


@frappe.whitelist(allow_guest=True)
def get_booking(booking_id):
    """
    Get a booking by ID.
    """
    merchant_ns_id = get_merchant_from_token()
    
    if not booking_id:
        frappe.throw(_("Booking ID is required"))
    
    doc = frappe.get_doc("Booking", booking_id)
    
    # Verify ownership
    merchant_name = frappe.db.get_value("Merchant", {"ns_merchant_id": merchant_ns_id}, "name")
    if doc.merchant_ns_id != merchant_name:
        frappe.throw(_("Not authorized to view this booking"), frappe.AuthenticationError)
    
    return {
        "status": "Success",
        "data": {
            "id": doc.name,
            "date": str(doc.date),
            "time_from": str(doc.time_from),
            "time_to": str(doc.time_to)
        }
    }


@frappe.whitelist(allow_guest=True)
def search_bookings(date=None, time_from=None, time_to=None):
    """
    Search bookings for the authenticated merchant.
    """
    merchant_ns_id = get_merchant_from_token()
    
    merchant_name = frappe.db.get_value("Merchant", {"ns_merchant_id": merchant_ns_id}, "name")
    if not merchant_name:
        frappe.throw(_("Merchant not found"))

    filters = {
        "merchant_ns_id": merchant_name,
        "deleted": 0,
        "inactive": 0
    }
    
    if date:
        filters["date"] = date
    if time_from:
        filters["time_from"] = [">=", time_from]
    if time_to:
        filters["time_to"] = ["<=", time_to]

    bookings = frappe.get_all("Booking", 
        filters=filters, 
        fields=["name", "date", "time_from", "time_to"]
    )
    
    return {
        "status": "Success",
        "count": len(bookings),
        "data": bookings
    }


# ==================== HELPER FUNCTIONS ====================

def is_holiday(date):
    """Check if date is a public holiday"""
    return frappe.db.exists("Public Holiday", {"date": date, "deleted": 0, "inactive": 0})


def count_task(merchant_ns_id, date, time_from, time_to):
    """Count existing bookings for a time slot"""
    merchant_name = frappe.db.get_value("Merchant", {"ns_merchant_id": merchant_ns_id}, "name")
    
    return frappe.db.count("Booking", {
        "merchant_ns_id": merchant_name,
        "date": date,
        "time_from": time_from,
        "time_to": time_to,
        "deleted": 0,
        "inactive": 0
    })
