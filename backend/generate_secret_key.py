#!/usr/bin/env python3
"""
Generate a secure secret key for JWT tokens
Run this script and update your .env file with the generated key
"""

import secrets
import string

def generate_secret_key(length=64):
    """Generate a cryptographically secure secret key"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == "__main__":
    secret_key = generate_secret_key()
    print("Generated Secret Key:")
    print("=" * 50)
    print(secret_key)
    print("=" * 50)
    print("\nUpdate your .env file with:")
    print(f"SECRET_KEY={secret_key}")
    print("\nIMPORTANT: Keep this key secure and never share it publicly!")