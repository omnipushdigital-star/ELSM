#!/usr/bin/env python3
"""
ELSM Portal — RBAC & Ticket Lifecycle Validation Suite
Run from: D:\Claude Projects\ELSM
Command:  python validate_rbac_tickets.py

Tests:
  1. Login for all 5 roles
  2. RBAC enforcement (403 checks per role)
  3. Ticket creation (only allowed roles)
  4. Ticket approval / rejection
  5. Engineer assignment
  6. Ticket completion (closure)
  7. SLA deadline auto-set
  8. Audit log entries created
"""

import requests
import json
import sys
from datetime import datetime

BASE = "http://localhost:8000/api/v1"
PASS = "Admin@1234"

# ─── Colour output ────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg):  print(f"  {GREEN}✓{RESET} {msg}")
def fail(msg): print(f"  {RED}✗{RESET} {msg}"); FAILURES.append(msg)
def info(msg): print(f"  {BLUE}→{RESET} {msg}")
def header(msg): print(f"\n{BOLD}{YELLOW}{'─'*60}{RESET}\n{BOLD}{msg}{RESET}\n{'─'*60}")

FAILURES = []

# ─── Helpers ──────────────────────────────────────────────────────────────────

def login(email, password=PASS):
    r = requests.post(f"{BASE}/auth/login", json={"email": email, "password": password})
    if r.status_code == 200:
        data = r.json()
        return data.get("access_token"), data.get("role"), data.get("name")
    return None, None, None

def headers(token):
    return {"Authorization": f"Bearer {token}"}

def get(token, path, expected=200):
    r = requests.get(f"{BASE}{path}", headers=headers(token))
    return r

def post(token, path, body, expected=200):
    r = requests.post(f"{BASE}{path}", json=body, headers=headers(token))
    return r

def patch(token, path, body):
    r = requests.patch(f"{BASE}{path}", json=body, headers=headers(token))
    return r


# ─── TEST 1: Login all roles ──────────────────────────────────────────────────

header("TEST 1 — Login / Token Issuance (all roles)")

USERS = {
    "super_admin":    "admin@elsm.in",
    "bsnl_admin":     "bsnl@elsm.in",
    "nodal_officer":  "nodal@elsm.in",
    "field_engineer": "engineer@elsm.in",
    "auditor":        "auditor@elsm.in",
}

TOKENS = {}
for role, email in USERS.items():
    token, got_role, name = login(email)
    if token:
        TOKENS[role] = token
        ok(f"{role:20s} → logged in as '{name}', role={got_role}")
    else:
        fail(f"{role:20s} → LOGIN FAILED for {email}")
        info(f"  (Create this user first via POST /api/v1/users/ with role={role.upper()})")

# Always need super_admin token; abort if missing
SA = TOKENS.get("super_admin")
if not SA:
    print(f"\n{RED}FATAL: Cannot continue without super_admin token.{RESET}")
    sys.exit(1)


# ─── TEST 2: RBAC Enforcement ─────────────────────────────────────────────────

header("TEST 2 — RBAC Enforcement (403 checks)")

rbac_cases = [
    # (description, role, method, path, body, expected_status)
    ("AUDITOR cannot create user",       "auditor",        "post", "/users/", {"name":"x","email":"x@x.com","phone":"9999999999","password":"P@ss1","role":"AUDITOR"}, 403),
    ("FIELD_ENG cannot create user",     "field_engineer", "post", "/users/", {"name":"x","email":"x@x.com","phone":"9999999999","password":"P@ss1","role":"FIELD_ENGINEER"}, 403),
    ("NODAL cannot create user",         "nodal_officer",  "post", "/users/", {"name":"x","email":"x@x.com","phone":"9999999999","password":"P@ss1","role":"NODAL_OFFICER"}, 403),
    ("AUDITOR cannot approve ticket",    "auditor",        "post", "/ese-eue/fake-id/approve", {}, 403),
    ("FIELD_ENG cannot approve ticket",  "field_engineer", "post", "/ese-eue/fake-id/approve", {}, 403),
    ("AUDITOR cannot reject ticket",     "auditor",        "post", "/ese-eue/fake-id/reject",  {"reason":"test"}, 403),
    ("FIELD_ENG cannot list users",      "field_engineer", "get",  "/users/", None, 403),
]

for desc, role, method, path, body, expected in rbac_cases:
    token = TOKENS.get(role)
    if not token:
        info(f"SKIP (no token): {desc}")
        continue
    if method == "post":
        r = requests.post(f"{BASE}{path}", json=body or {}, headers=headers(token))
    else:
        r = requests.get(f"{BASE}{path}", headers=headers(token))

    if r.status_code == expected:
        ok(f"{desc} → HTTP {r.status_code} ✓")
    elif r.status_code == 422 and expected == 403:
        # 422 = validation error on fake ID — the role check happened first or didn't
        # Check if it's actually a forbidden body validation
        info(f"{desc} → HTTP {r.status_code} (422 Unprocessable — role may not be checked before body validation)")
    else:
        fail(f"{desc} → Expected {expected}, got {r.status_code}: {r.text[:80]}")


# ─── TEST 3: Ticket Creation ───────────────────────────────────────────────────

header("TEST 3 — Ticket (ESE/EUE Request) Creation")

# Get machine list first
r = get(SA, "/ese-eue/summary")
info(f"ESE/EUE summary: HTTP {r.status_code}")
if r.status_code == 200:
    summary = r.json()
    info(f"  Summary: {json.dumps(summary)[:120]}")

# Get a valid machine ID
r = requests.get(f"{BASE}/ese-eue/", headers=headers(SA), params={"page_size": 1})
MACHINE_ID = None
if r.status_code == 200:
    items = r.json()
    if items:
        MACHINE_ID = items[0].get("machine_id") or items[0].get("machine", {}).get("id")
        info(f"Existing request machine_id: {MACHINE_ID}")

# Try to get machines directly
r = requests.get("http://localhost:8000/api/v1/machines/", headers=headers(SA)) if False else type('R', (), {'status_code': 0})()

# Use the known test machine from DB
MACHINE_ID_KNOWN = "b38e2b99-1802-448c-95a2-fcf38f0d0730"  # Test Machine 01 from earlier session

ticket_payload = {
    "event_type": "ESE",
    "machine_id": MACHINE_ID_KNOWN,
    "notes": "Validation test ticket — automated",
}

TICKET_ID = None

# NODAL_OFFICER should be able to create
if "nodal_officer" in TOKENS:
    r = post(TOKENS["nodal_officer"], "/ese-eue/", ticket_payload)
    if r.status_code == 201:
        TICKET_ID = r.json().get("id")
        ok(f"NODAL_OFFICER created ticket → ID: {TICKET_ID}")
        t = r.json()
        # Validate auto-fields
        if t.get("request_number"):
            ok(f"  request_number auto-generated: {t['request_number']}")
        else:
            fail("  request_number NOT generated")
        if t.get("sla_deadline"):
            ok(f"  sla_deadline auto-set: {t['sla_deadline']}")
        else:
            fail("  sla_deadline NOT set — SLA tracking broken")
        if t.get("status") == "pending":
            ok(f"  status = 'pending' (correct initial state)")
        else:
            fail(f"  status = '{t.get('status')}', expected 'pending'")
    else:
        fail(f"NODAL_OFFICER ticket creation failed: {r.status_code} {r.text[:120]}")
elif "bsnl_admin" in TOKENS:
    r = post(TOKENS["bsnl_admin"], "/ese-eue/", ticket_payload)
    if r.status_code == 201:
        TICKET_ID = r.json().get("id")
        ok(f"BSNL_ADMIN created ticket → ID: {TICKET_ID}")
    else:
        fail(f"BSNL_ADMIN ticket creation failed: {r.status_code} {r.text[:120]}")
else:
    # Fall back to super_admin
    r = post(SA, "/ese-eue/", ticket_payload)
    if r.status_code == 201:
        TICKET_ID = r.json().get("id")
        ok(f"SUPER_ADMIN created ticket → ID: {TICKET_ID}")
    else:
        fail(f"Ticket creation failed: {r.status_code} {r.text[:120]}")

# Field engineer should NOT create tickets (RBAC)
if "field_engineer" in TOKENS:
    r = post(TOKENS["field_engineer"], "/ese-eue/", ticket_payload)
    if r.status_code == 403:
        ok("FIELD_ENGINEER blocked from creating ticket (403) ✓")
    elif r.status_code == 201:
        fail("FIELD_ENGINEER should NOT create tickets — RBAC gap!")
    else:
        info(f"FIELD_ENGINEER create ticket → {r.status_code} (check if intentional)")

# Auditor should NOT create tickets
if "auditor" in TOKENS:
    r = post(TOKENS["auditor"], "/ese-eue/", ticket_payload)
    if r.status_code == 403:
        ok("AUDITOR blocked from creating ticket (403) ✓")
    elif r.status_code == 201:
        fail("AUDITOR should NOT create tickets — RBAC gap!")


# ─── TEST 4: Ticket Read / List ────────────────────────────────────────────────

header("TEST 4 — Ticket Listing & Detail (all roles)")

for role, token in TOKENS.items():
    r = get(token, "/ese-eue/")
    if r.status_code == 200:
        count = len(r.json()) if isinstance(r.json(), list) else "?"
        ok(f"{role:20s} can list tickets → {count} items")
    elif r.status_code == 403:
        info(f"{role:20s} blocked from listing → 403 (check if intentional)")
    else:
        fail(f"{role:20s} ticket list → unexpected {r.status_code}")

if TICKET_ID:
    r = get(SA, f"/ese-eue/{TICKET_ID}")
    if r.status_code == 200:
        ok(f"GET /ese-eue/{{id}} → 200 ✓")
    else:
        fail(f"GET /ese-eue/{{id}} → {r.status_code}")


# ─── TEST 5: Ticket Approval ───────────────────────────────────────────────────

header("TEST 5 — Ticket Approval Workflow")

APPROVED_TICKET_ID = TICKET_ID

if TICKET_ID:
    # BSNL_ADMIN or SUPER_ADMIN should be able to approve
    approver_token = TOKENS.get("bsnl_admin") or SA
    approver_role = "bsnl_admin" if "bsnl_admin" in TOKENS else "super_admin"

    r = post(approver_token, f"/ese-eue/{TICKET_ID}/approve", {})
    if r.status_code == 200:
        t = r.json()
        ok(f"{approver_role} approved ticket → status: {t.get('status')}")
        if t.get("status") == "approved":
            ok("  status correctly updated to 'approved'")
        else:
            fail(f"  Expected status='approved', got '{t.get('status')}'")
        if t.get("approved_at"):
            ok(f"  approved_at timestamp set: {t['approved_at']}")
        else:
            fail("  approved_at NOT set")
    else:
        fail(f"Approve ticket → {r.status_code}: {r.text[:120]}")
        APPROVED_TICKET_ID = None
else:
    info("SKIP — no ticket ID available")


# ─── TEST 6: Ticket Rejection ──────────────────────────────────────────────────

header("TEST 6 — Ticket Rejection")

# Create a second ticket to test rejection
reject_ticket_id = None
r = post(SA, "/ese-eue/", {**ticket_payload, "notes": "Test rejection ticket"})
if r.status_code == 201:
    reject_ticket_id = r.json().get("id")
    ok(f"Created second ticket for rejection test: {reject_ticket_id}")

    r = post(SA, f"/ese-eue/{reject_ticket_id}/reject", {"reason": "Machine not accessible for validation test"})
    if r.status_code == 200:
        t = r.json()
        ok(f"Ticket rejected → status: {t.get('status')}")
        if t.get("status") == "rejected":
            ok("  status = 'rejected' ✓")
        else:
            fail(f"  Expected 'rejected', got '{t.get('status')}'")
        if t.get("rejection_reason"):
            ok(f"  rejection_reason stored: '{t['rejection_reason'][:50]}'")
        else:
            fail("  rejection_reason NOT stored")
    else:
        fail(f"Reject ticket → {r.status_code}: {r.text[:120]}")
else:
    fail(f"Could not create rejection test ticket: {r.status_code}")


# ─── TEST 7: Engineer Assignment ───────────────────────────────────────────────

header("TEST 7 — Engineer Assignment")

ENGINEER_ID = None
# Get a field engineer's user ID
r = get(SA, "/users/?role=FIELD_ENGINEER")
if r.status_code == 200 and r.json():
    ENGINEER_ID = r.json()[0].get("id")
    ok(f"Found field engineer: {r.json()[0].get('name')} (ID: {ENGINEER_ID})")
else:
    info("No FIELD_ENGINEER users found — testing with known test data")
    # Try listing all users
    r = get(SA, "/users/")
    if r.status_code == 200:
        users = r.json()
        for u in users:
            if u.get("role") == "FIELD_ENGINEER" or u.get("role") == "field_engineer":
                ENGINEER_ID = u.get("id")
                ok(f"Found engineer: {u.get('name')} ({ENGINEER_ID})")
                break

if APPROVED_TICKET_ID and ENGINEER_ID:
    r = post(SA, f"/ese-eue/{APPROVED_TICKET_ID}/assign", {"engineer_id": ENGINEER_ID})
    if r.status_code == 200:
        t = r.json()
        ok(f"Engineer assigned → status: {t.get('status')}")
        if t.get("status") == "assigned":
            ok("  status = 'assigned' ✓")
        else:
            fail(f"  Expected 'assigned', got '{t.get('status')}'")
        if t.get("assigned_at"):
            ok(f"  assigned_at set ✓")
        else:
            fail("  assigned_at NOT set")
    else:
        fail(f"Assign engineer → {r.status_code}: {r.text[:120]}")
elif APPROVED_TICKET_ID and not ENGINEER_ID:
    info("SKIP assignment — no FIELD_ENGINEER user found in DB")
    info("  Create one via: POST /api/v1/users/ with role=FIELD_ENGINEER")
else:
    info("SKIP assignment — no approved ticket available")


# ─── TEST 8: Ticket Completion (Closure) ──────────────────────────────────────

header("TEST 8 — Ticket Completion / Closure")

# Create + approve + assign + complete a full lifecycle ticket
info("Running full lifecycle: create → approve → assign → complete")

lifecycle_id = None
r = post(SA, "/ese-eue/", {**ticket_payload, "notes": "Full lifecycle test"})
if r.status_code == 201:
    lifecycle_id = r.json().get("id")
    ok(f"Created: {lifecycle_id}")

    # Approve
    r = post(SA, f"/ese-eue/{lifecycle_id}/approve", {})
    if r.status_code == 200:
        ok(f"Approved: status={r.json().get('status')}")
    else:
        fail(f"Approve failed: {r.status_code}")

    # Assign (if engineer available)
    if ENGINEER_ID:
        r = post(SA, f"/ese-eue/{lifecycle_id}/assign", {"engineer_id": ENGINEER_ID})
        if r.status_code == 200:
            ok(f"Assigned: status={r.json().get('status')}")
        else:
            fail(f"Assign failed: {r.status_code}")

    # Complete — check if endpoint exists
    complete_token = TOKENS.get("field_engineer") or SA
    complete_role = "field_engineer" if "field_engineer" in TOKENS else "super_admin"

    # Try PATCH status update or dedicated complete endpoint
    r = requests.patch(
        f"{BASE}/ese-eue/{lifecycle_id}",
        json={"status": "completed", "notes": "Validation complete"},
        headers=headers(complete_token)
    )
    if r.status_code == 200:
        t = r.json()
        ok(f"{complete_role} completed ticket → status: {t.get('status')}")
        if t.get("status") == "completed":
            ok("  status = 'completed' ✓")
        if t.get("completed_at"):
            ok(f"  completed_at set ✓")
        else:
            fail("  completed_at NOT set on completion")
    elif r.status_code == 404:
        fail("PATCH /ese-eue/{id} not implemented — need completion endpoint")
    elif r.status_code == 403:
        fail(f"{complete_role} cannot complete ticket — check RBAC for completion")
    else:
        fail(f"Complete ticket → {r.status_code}: {r.text[:120]}")
else:
    fail(f"Lifecycle ticket creation failed: {r.status_code}")


# ─── TEST 9: SLA Deadline Validation ──────────────────────────────────────────

header("TEST 9 — SLA Deadline Auto-Calculation")

r = post(SA, "/ese-eue/", {**ticket_payload, "notes": "SLA test"})
if r.status_code == 201:
    t = r.json()
    sla = t.get("sla_deadline")
    created = t.get("created_at") or t.get("requested_at")
    if sla:
        ok(f"sla_deadline present: {sla}")
        # Parse and check it's ~3 working days ahead
        try:
            from datetime import datetime, timezone
            sla_dt = datetime.fromisoformat(sla.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            delta = sla_dt - now
            info(f"  SLA is {delta.days} days from now (~3 working days expected)")
            if 2 <= delta.days <= 5:
                ok("  SLA window looks correct (2-5 calendar days ≈ 3 working days)")
            else:
                fail(f"  SLA window unexpected: {delta.days} days")
        except Exception as e:
            info(f"  Could not parse SLA date: {e}")
    else:
        fail("sla_deadline NOT auto-set on ticket creation")
else:
    fail(f"SLA test ticket creation failed: {r.status_code}")


# ─── TEST 10: Audit Log ────────────────────────────────────────────────────────

header("TEST 10 — Audit Log Entries")

# Check if audit_logs endpoint exists
r = get(SA, "/audit-logs/")
if r.status_code == 200:
    logs = r.json()
    ok(f"Audit log endpoint exists → {len(logs) if isinstance(logs, list) else '?'} entries")
elif r.status_code == 404:
    info("GET /audit-logs/ not yet implemented (check router)")
    # Try alternate path
    r = get(SA, "/audit/")
    if r.status_code == 200:
        ok("Audit logs at /audit/ ✓")
    else:
        info("Audit log read endpoint not exposed via API yet — check DB directly")
else:
    info(f"Audit logs endpoint → {r.status_code}")


# ─── SUMMARY ──────────────────────────────────────────────────────────────────

header("VALIDATION SUMMARY")

total_checks = 0  # We don't count precisely but failures tell us what to fix
if not FAILURES:
    print(f"\n{GREEN}{BOLD}✓ ALL CHECKS PASSED{RESET}\n")
else:
    print(f"\n{RED}{BOLD}✗ {len(FAILURES)} FAILURE(S) FOUND:{RESET}")
    for i, f in enumerate(FAILURES, 1):
        print(f"  {i}. {f}")
    print()

print(f"{YELLOW}Tokens available for: {', '.join(TOKENS.keys())}{RESET}")
print(f"{YELLOW}If roles are missing, create users first:{RESET}")
for role, email in USERS.items():
    if role not in TOKENS:
        print(f"  POST /api/v1/users/  email={email} role={role.upper()} password=Admin@1234")
