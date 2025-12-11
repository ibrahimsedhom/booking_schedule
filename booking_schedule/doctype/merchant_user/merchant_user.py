# -*- coding: utf-8 -*-
# Copyright (c) 2023, Transcorp and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import hashlib

class BSUser(Document):
    def before_save(self):
        """Hash password before saving if it's a new password"""
        if self.password and not self.password.startswith("$pbkdf2"):
            self.password = hash_password(self.password)

def hash_password(password):
    """Hash password using pbkdf2_sha256 (compatible with Frappe)"""
    import hashlib
    import os
    salt = os.urandom(16).hex()
    iterations = 100000
    hash_bytes = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), iterations)
    return f"$pbkdf2${iterations}${salt}${hash_bytes.hex()}"

def verify_password(password, hashed):
    """Verify password against stored hash"""
    if not hashed or not hashed.startswith("$pbkdf2"):
        return False
    
    try:
        parts = hashed.split("$")
        iterations = int(parts[2])
        salt = parts[3]
        stored_hash = parts[4]
        
        hash_bytes = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), iterations)
        return hash_bytes.hex() == stored_hash
    except Exception:
        return False
