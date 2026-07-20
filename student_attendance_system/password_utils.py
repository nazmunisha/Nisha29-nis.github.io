# ==========================================================
# File: password_utils.py
#
# Project: Attendance Management System
#
# Purpose:
# This module provides reusable password security functions.
# It hashes passwords using bcrypt and checks login passwords
# securely.
#
# Important:
# The check_password() function also supports old plain-text
# passwords for migration. This means existing accounts such
# as admin/admin123 can still log in, but new and changed
# passwords will be stored as bcrypt hashes.
# ==========================================================

import bcrypt


# ==========================================================
# Function: hash_password()
#
# Purpose:
# Convert a plain password into a secure bcrypt hash.
#
# Returns:
# Hashed password as a string.
# ==========================================================
def hash_password(password):
    password_bytes = str(password).encode("utf-8")
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


# ==========================================================
# Function: is_bcrypt_hash()
#
# Purpose:
# Check whether a stored password already looks like a
# bcrypt hash.
# ==========================================================
def is_bcrypt_hash(stored_password):
    stored_password = str(stored_password)
    return (
        stored_password.startswith("$2a$")
        or stored_password.startswith("$2b$")
        or stored_password.startswith("$2y$")
    )


# ==========================================================
# Function: check_password()
#
# Purpose:
# Compare the password typed by the user with the password
# stored in the database.
#
# Supports:
# - bcrypt hashed passwords
# - old plain-text passwords during migration
#
# Returns:
# True if password is correct, otherwise False.
# ==========================================================
def check_password(plain_password, stored_password):
    plain_password = str(plain_password)
    stored_password = str(stored_password)

    try:
        if is_bcrypt_hash(stored_password):
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                stored_password.encode("utf-8")
            )

        # Migration support for older plain-text passwords
        return plain_password == stored_password

    except Exception:
        return False
