#!/usr/bin/env python3
"""
One-time script to create a SUPER_ADMIN user.

Usage (from health_backend/ with venv active):
    python create_superadmin.py
    python create_superadmin.py --email admin@example.com --password secret --name "Super Admin"
"""
from __future__ import annotations

import argparse
import asyncio
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.core.security import hash_password


async def create_superadmin(name: str, email: str, password: str, mobile_no: str | None) -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    hashed = hash_password(password)

    async with engine.begin() as conn:
        # Check if email already exists
        result = await conn.execute(
            text("SELECT id, role FROM users WHERE email = :email"),
            {"email": email},
        )
        existing = result.fetchone()
        if existing:
            print(f"[!] A user with email '{email}' already exists (id={existing[0]}, role={existing[1]}).")
            print("    If you want to promote them to super_admin, run:")
            print(f"    UPDATE users SET role='super_admin' WHERE email='{email}';")
            await engine.dispose()
            sys.exit(1)

        await conn.execute(
            text("""
                INSERT INTO users (name, email, password_hash, role, mobile_no, is_verified, is_active)
                VALUES (:name, :email, :pw, 'super_admin', :mobile, true, true)
            """),
            {"name": name, "email": email, "pw": hashed, "mobile": mobile_no},
        )

    await engine.dispose()
    print(f"[✓] Super admin created successfully!")
    print(f"    Email   : {email}")
    print(f"    Password: {password}")
    print(f"    Role    : super_admin")
    print()
    print("Log in at http://localhost:3000/auth/sign-in")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a SUPER_ADMIN user")
    parser.add_argument("--name",     default="Super Admin",        help="Full name")
    parser.add_argument("--email",    default="superadmin@health.local", help="Email address")
    parser.add_argument("--password", default="SuperAdmin@123",     help="Password")
    parser.add_argument("--phone",    default=None,                  help="Phone number (optional)")
    args = parser.parse_args()

    asyncio.run(create_superadmin(args.name, args.email, args.password, args.phone))


if __name__ == "__main__":
    main()
