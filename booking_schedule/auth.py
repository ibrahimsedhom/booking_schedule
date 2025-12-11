# -*- coding: utf-8 -*-
# Copyright (c) 2023, Transcorp and contributors
# JWT Authentication Module for Booking Schedule

import frappe
from frappe import _
from datetime import datetime, timedelta
from functools import wraps
import jwt
import json

# JWT Configuration - matching old project (365 days expiry)
JWT_SECRET = "Az@suitefleetmerchant@2020"  # Same as old project
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 365


@frappe.whitelist(allow_guest=True)
def authenticate(username, password):
    """
    Authenticate user and return JWT token.
    Matches the old Node.js authentication flow.
    """
    if not username or not password:
        frappe.throw(_("Username and password are required"), frappe.AuthenticationError)
    
    # Find user by username
    user = frappe.db.get_value("Merchant User", {"username": username}, 
        ["name", "username", "password", "ns_employee_id", "full_name", 
         "email", "phone", "user_type", "give_access", "mobile_access",
         "merchant_ns_id", "deleted", "inactive"], as_dict=True)
    
    if not user:
        return {
            "status": "Failure",
            "message": "User not found.",
            "data": None
        }
    
    # Check if deleted
    if user.deleted:
        return {
            "status": "Failure", 
            "message": "User not found.",
            "data": None
        }
    
    # Check if inactive
    if user.inactive:
        return {
            "status": "Failure",
            "message": "User is inactive.",
            "data": None
        }
    
    # Check give_access
    if not user.give_access:
        return {
            "status": "Failure",
            "message": "The user didn't have access.",
            "data": None
        }
    
    # Check user type
    if user.user_type != "merchant":
        return {
            "status": "Failure",
            "message": "Access is not enabled.",
            "data": None
        }
    
    # Verify password
    from booking_schedule.doctype.merchant_user.merchant_user import verify_password
    if not verify_password(password, user.password):
        return {
            "status": "Failure",
            "message": "Invalid username or password.",
            "data": None
        }
    
    # Create JWT payload
    payload = {
        "ns_employee_id": user.ns_employee_id,
        "username": user.username,
        "name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "user_type": user.user_type,
        "give_access": user.give_access,
        "mobile_access": user.mobile_access,
        "merchant_ns_id": user.merchant_ns_id,
        "exp": datetime.utcnow() + timedelta(days=JWT_EXPIRY_DAYS),
        "iat": datetime.utcnow()
    }
    
    # Generate token
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    # Calculate days until expiry
    expires_in = JWT_EXPIRY_DAYS
    
    # Prepare user data (excluding password)
    user_data = {
        "ns_employee_id": user.ns_employee_id,
        "username": user.username,
        "name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "user_type": user.user_type,
        "give_access": user.give_access,
        "mobile_access": user.mobile_access
    }
    
    return {
        "status": "Success",
        "message": "User found",
        "tokenexpireafter": expires_in,
        "data": user_data,
        "token": token
    }


def validate_token(token):
    """
    Validate JWT token and return decoded payload.
    """
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Check if user still exists and is valid
        user = frappe.db.get_value("Merchant User", {"username": payload.get("username")},
            ["deleted", "inactive", "give_access", "user_type", "merchant_ns_id"], as_dict=True)
        
        if not user or user.deleted or user.inactive or not user.give_access:
            return None
        
        if user.user_type != "merchant":
            return None
        
        # Add merchant_ns_id to payload (in case it changed)
        payload["merchant_ns_id"] = user.merchant_ns_id
        
        return payload
        
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def jwt_required(func):
    """
    Decorator to protect API endpoints with JWT authentication.
    Extracts token from 'x-access-token' header (matching old project).
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get token from header
        token = frappe.request.headers.get("x-access-token")
        
        if not token:
            frappe.throw(_("Token is required"), frappe.AuthenticationError)
        
        # Validate token
        payload = validate_token(token)
        
        if not payload:
            frappe.throw(_("Invalid or expired token"), frappe.AuthenticationError)
        
        # Add user data to frappe.local for access in the function
        frappe.local.jwt_payload = payload
        
        return func(*args, **kwargs)
    
    return wrapper


def get_current_merchant_ns_id():
    """
    Get the merchant_ns_id from the current JWT token.
    Use this in protected endpoints instead of passing as parameter.
    """
    if hasattr(frappe.local, 'jwt_payload') and frappe.local.jwt_payload:
        return frappe.local.jwt_payload.get("merchant_ns_id")
    return None


@frappe.whitelist(allow_guest=True)
def verify_token():
    """
    Verify if token is valid and return user info.
    Useful for clients to check token validity.
    """
    token = frappe.request.headers.get("x-access-token")
    
    if not token:
        return {
            "status": "Failure",
            "message": "Token is required",
            "valid": False
        }
    
    payload = validate_token(token)
    
    if not payload:
        return {
            "status": "Failure",
            "message": "Invalid or expired token",
            "valid": False
        }
    
    # Calculate remaining days
    exp_timestamp = payload.get("exp")
    if isinstance(exp_timestamp, datetime):
        remaining_days = (exp_timestamp - datetime.utcnow()).days
    else:
        remaining_days = 0
    
    return {
        "status": "Success",
        "message": "Token is valid",
        "valid": True,
        "tokenexpireafter": remaining_days,
        "data": {
            "username": payload.get("username"),
            "name": payload.get("name"),
            "email": payload.get("email"),
            "merchant_ns_id": payload.get("merchant_ns_id")
        }
    }
