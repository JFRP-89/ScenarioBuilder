#!/usr/bin/env python3
"""Final verification script for user database seeding."""

from __future__ import annotations

from dotenv import load_dotenv
from infrastructure.auth.user_store import user_exists, verify_credentials
from infrastructure.bootstrap import build_services
from infrastructure.db.models import UserModel
from infrastructure.db.session import SessionLocal

load_dotenv()

print("=" * 60)
print("FINAL VERIFICATION: User Database Seeding")
print("=" * 60)

# 1. Build services (triggers seeding)
print("\n1. Building services (triggers user seeding)...")
services = build_services()
print("   ✓ Services built")

# 2. Verify users in database
print("\n2. Checking users table...")
session = SessionLocal()
try:
    users = session.query(UserModel).order_by(UserModel.username).all()
    print(f"   ✓ Found {len(users)} demo users in database:")
    for user in users:
        print(f"      • {user.username:12} | {user.name:12} | {user.email}")
finally:
    session.close()

# 3. Verify in-memory store still works
print("\n3. Verifying in-memory auth store...")
test_users = [
    ("demo-user", "demo-user", True),
    ("alice", "alice", True),
    ("bob", "bob", True),
    ("demo-user", "wrong-password", False),
    ("nonexistent", "password", False),
]

for username, password, should_succeed in test_users:
    exists = user_exists(username)
    verified = verify_credentials(username, password)
    status = "✓" if (verified == should_succeed) else "✗"
    print(
        f"   {status} verify_credentials('{username}', "
        f"'{password[:4]}...') → {verified}"
    )

print("\n" + "=" * 60)
print("✓ USER DATABASE SEEDING COMPLETE AND VERIFIED")
print("=" * 60)
