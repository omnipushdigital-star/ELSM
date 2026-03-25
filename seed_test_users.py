#!/usr/bin/env python3
"""
ELSM — Seed test users for all 5 roles.
Run ONCE before validate_rbac_tickets.py

Usage: python seed_test_users.py
"""
import requests

BASE = "http://localhost:8000/api/v1"

def login(email, password="Admin@1234"):
    r = requests.post(f"{BASE}/auth/login", json={"email": email, "password": password})
    if r.status_code == 200:
        return r.json()["access_token"]
    return None

def create_user(token, user):
    r = requests.post(
        f"{BASE}/users/",
        json=user,
        headers={"Authorization": f"Bearer {token}"}
    )
    return r.status_code, r.json()

# Login as super admin
print("Logging in as admin@elsm.in ...")
SA_TOKEN = login("admin@elsm.in")
if not SA_TOKEN:
    print("ERROR: Cannot login as super_admin. Is the backend running?")
    exit(1)

print(f"Got token: {SA_TOKEN[:30]}...\n")

USERS_TO_CREATE = [
    {"name": "BSNL Admin",       "email": "bsnl@elsm.in",     "phone": "9000000001", "password": "Admin@1234", "role": "BSNL_ADMIN"},
    {"name": "Nodal Officer",    "email": "nodal@elsm.in",    "phone": "9000000002", "password": "Admin@1234", "role": "NODAL_OFFICER"},
    {"name": "Field Engineer",   "email": "engineer@elsm.in", "phone": "9000000003", "password": "Admin@1234", "role": "FIELD_ENGINEER"},
    {"name": "Auditor",          "email": "auditor@elsm.in",  "phone": "9000000004", "password": "Admin@1234", "role": "AUDITOR"},
]

for u in USERS_TO_CREATE:
    status, data = create_user(SA_TOKEN, u)
    if status == 201:
        print(f"  ✓ Created: {u['email']} ({u['role']})")
    elif status == 400 and "already" in str(data):
        print(f"  - Exists:  {u['email']} ({u['role']})")
    else:
        print(f"  ✗ Failed:  {u['email']} → {status}: {data}")

print("\nDone. Run: python validate_rbac_tickets.py")
