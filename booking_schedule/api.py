# -*- coding: utf-8 -*-
import frappe
from frappe import _
from frappe.utils import getdate, add_days, get_datetime, nowdate, time_diff_in_hours
from datetime import datetime, timedelta

@frappe.whitelist()
def get_delivery_schedule(merchant_ns_id):
	"""
	Calculate available delivery slots for a merchant.
	"""
	if not merchant_ns_id:
		frappe.throw(_("Merchant ID is required"))

	merchant = frappe.get_doc("BS Merchant", {"ns_merchant_id": merchant_ns_id})
	if not merchant:
		frappe.throw(_("Merchant not found"), exc=frappe.DoesNotExistError)

	if merchant.inactive or merchant.deleted:
		frappe.throw(_("Merchant is inactive or deleted"))

	available_slots = []
	
	# Process each schedule configuration
	for schedule in merchant.delivery_schedule:
		# Parse configuration
		days_from_now = schedule.days_from_now
		schedule_duration = schedule.schedule_duration
		capacity = schedule.capacity
		time_from = schedule.time_from_slot
		time_to = schedule.time_to_slot
		week_days = schedule.week_days.split(",") if schedule.week_days else []
		
		# Calculate date range
		start_date = add_days(nowdate(), days_from_now)
		# Duration is inclusive/exclusive depending on requirement, matching JS logic:
		# JS: enddate = startdate + duration + 1
		# Then loop: while m.isBefore(enddate)
		end_date = add_days(nowdate(), days_from_now + schedule_duration + 1)
		
		current_date = getdate(start_date)
		final_date = getdate(end_date)
		
		while current_date < final_date:
			date_str = current_date.strftime("%Y-%m-%d")
			day_name = current_date.strftime("%a") # Mon, Tue...
			
			# 1. Check Public Holidays
			if is_holiday(current_date):
				current_date += timedelta(days=1)
				continue
				
			# 2. Check Week Days
			# Note: JS used moment.js 'ddd' which gives 'Mon', 'Tue' etc.
			# Ensure week_days in DocType are stored as "Mon", "Tue" etc.
			if day_name not in week_days:
				current_date += timedelta(days=1)
				continue
				
			# 3. Count Existing Bookings
			occupied_slots = count_task(merchant_ns_id, date_str, time_from, time_to)
			
			# 4. Calculate Balance
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

	# Sort by date
	available_slots.sort(key=lambda x: x["Date"])
	
	return {
		"status": "Success",
		"message": "The delivery Schedule has been found.",
		"count": len(available_slots),
		"data": available_slots
	}

@frappe.whitelist()
def create_booking(date, time_from, time_to, merchant_ns_id):
	"""
	Create a new booking.
	"""
	if not (date and time_from and time_to and merchant_ns_id):
		frappe.throw(_("Missing required parameters"))

	# Validate Merchant
	merchant = frappe.db.get_value("BS Merchant", {"ns_merchant_id": merchant_ns_id}, "name")
	if not merchant:
		frappe.throw(_("Merchant not found"))

	# Create Booking
	doc = frappe.get_doc({
		"doctype": "BS Booking",
		"date": date,
		"time_from": time_from,
		"time_to": time_to,
		"merchant_ns_id": merchant, # Link field expects name
		"status": "Active"
	})
	doc.insert(ignore_permissions=True)
	
	return {
		"status": "Success",
		"message": "Booking created successfully",
		"data": doc.as_dict()
	}

@frappe.whitelist()
def update_booking(booking_id, data):
	"""
	Update an existing booking.
	"""
	if not booking_id:
		frappe.throw(_("Booking ID is required"))
		
	doc = frappe.get_doc("BS Booking", booking_id)
	
	# Parse data (assuming JSON string or dict)
	if isinstance(data, str):
		import json
		data = json.loads(data)
		
	doc.update(data)
	doc.save(ignore_permissions=True)
	
	return {
		"status": "Success",
		"message": "Booking updated successfully",
		"data": doc.as_dict()
	}

@frappe.whitelist()
def delete_booking(booking_id):
	"""
	Delete a booking (Soft delete logic as per simple delete req, or hard delete)
	JS version did hard delete. Here we can do delete()
	"""
	if not booking_id:
		frappe.throw(_("Booking ID is required"))
		
	frappe.delete_doc("BS Booking", booking_id, ignore_permissions=True)
	
	return {
		"status": "Success",
		"message": "Booking deleted successfully"
	}

@frappe.whitelist()
def search_bookings(merchant_ns_id, date, time_from, time_to):
	"""
	Search bookings by date and time range.
	"""
	merchant_name = frappe.db.get_value("BS Merchant", {"ns_merchant_id": merchant_ns_id}, "name")
	if not merchant_name:
		frappe.throw(_("Merchant not found"))

	bookings = frappe.get_all("BS Booking", filters={
		"merchant_ns_id": merchant_name,
		"date": date,
		"time_from": [">=", time_from],
		"time_to": ["<=", time_to],
		"deleted": 0,
		"inactive": 0
	}, fields=["name", "date", "time_from", "time_to", "merchant_ns_id"])
	
	return {
		"status": "Success",
		"data": bookings
	}

def is_holiday(date):
	return frappe.db.exists("BS Public Holiday", {"date": date, "deleted": 0, "inactive": 0})

def count_task(merchant_ns_id, date, time_from, time_to):
	# Find merchant name first for the link
	merchant_name = frappe.db.get_value("BS Merchant", {"ns_merchant_id": merchant_ns_id}, "name")
	
	return frappe.db.count("BS Booking", {
		"merchant_ns_id": merchant_name,
		"date": date,
		"time_from": time_from,
		"time_to": time_to,
		"deleted": 0,
		"inactive": 0
	})
