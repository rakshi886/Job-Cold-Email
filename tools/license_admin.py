"""
license_admin.py - CLI tool for Rakshith to manage JobHunter license keys.

Talks to your deployed Render license server. Reads SERVER_URL and ADMIN_TOKEN
from a local .env file (or environment vars).

Usage:
    python tools/license_admin.py generate --customer "John Smith" --email "john@x.com"
    python tools/license_admin.py generate --count 10
    python tools/license_admin.py generate --customer "Trial User" --valid-days 30
    python tools/license_admin.py list                # all keys
    python tools/license_admin.py list --status available
    python tools/license_admin.py list --status used
    python tools/license_admin.py inspect JHTR-ABCD-EFGH-JKLM-NPQR
    python tools/license_admin.py revoke  JHTR-ABCD-EFGH-JKLM-NPQR --reason "abuse"
    python tools/license_admin.py stats

Setup:
    Create  JobHunter-Admin/.env  with:
        SERVER_URL=https://jobhunter-license-XXXX.onrender.com
        ADMIN_TOKEN=...the value Render generated for you...
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Fix Windows console encoding so the check marks and box-drawing chars
# don't crash on the default cp1252 code page.
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

try:
    import requests
except ImportError:
    print("Missing dependency. Run: pip install requests")
    sys.exit(1)


# Read .env if present
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


SERVER_URL = os.environ.get("SERVER_URL", "").rstrip("/")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")


def _check_config():
    if not SERVER_URL or not ADMIN_TOKEN:
        print("ERROR: SERVER_URL and ADMIN_TOKEN must be set.")
        print(f"  Edit:  {ENV_FILE}")
        print("  See:   JobHunter-Admin/license_server/README.md")
        sys.exit(2)


def _hdrs():
    return {"X-Admin-Token": ADMIN_TOKEN, "Content-Type": "application/json"}


def _call(method, path, json_body=None, params=None):
    url = f"{SERVER_URL}{path}"
    try:
        if method == "GET":
            r = requests.get(url, headers=_hdrs(), params=params, timeout=30)
        elif method == "POST":
            r = requests.post(url, headers=_hdrs(), json=json_body, timeout=30)
        elif method == "DELETE":
            r = requests.delete(url, headers=_hdrs(), params=params, timeout=30)
        else:
            raise ValueError(method)
    except requests.RequestException as e:
        print(f"ERROR contacting server: {e}")
        sys.exit(3)
    try:
        data = r.json()
    except ValueError:
        print(f"ERROR: non-JSON response (status {r.status_code}): {r.text[:300]}")
        sys.exit(3)
    if r.status_code >= 400:
        print(f"Server error {r.status_code}: {data}")
        sys.exit(3)
    return data


def cmd_generate(args):
    _check_config()
    body = {
        "customer_name":  args.customer or "",
        "customer_email": args.email or "",
        "notes":          args.notes or "",
        "count":          args.count,
    }
    if args.valid_days:
        body["valid_days"] = args.valid_days
    res = _call("POST", "/api/admin/keys", json_body=body)
    keys = res.get("keys", [])
    print()
    print(f"✓ Generated {len(keys)} key{'s' if len(keys) != 1 else ''}:")
    for k in keys:
        print(f"   {k}")
    print()
    if args.customer:
        print(f"   Assigned to: {args.customer}")
    if args.valid_days:
        print(f"   Valid for activation within {args.valid_days} days.")
    print()


def cmd_list(args):
    _check_config()
    res = _call("GET", "/api/admin/keys",
                params={"status": args.status} if args.status else None)
    rows = res.get("keys", [])
    if not rows:
        print("(no keys)")
        return
    print()
    print(f"{'KEY':<28} {'STATUS':<10} {'CUSTOMER':<25} {'ACTIVATED':<22}")
    print("─" * 90)
    for r in rows:
        if r.get("revoked"):
            status = "revoked"
        elif r.get("used"):
            status = "used"
        else:
            status = "available"
        cust = (r.get("customer_name") or "")[:24]
        act = (r.get("activated_at") or "")[:19]
        print(f"{r['key']:<28} {status:<10} {cust:<25} {act:<22}")
    print()
    print(f"Total: {len(rows)}")


def cmd_inspect(args):
    _check_config()
    res = _call("GET", f"/api/admin/keys/{args.key.upper()}")
    k = res.get("key", {})
    print()
    print(f"Key:          {k.get('key')}")
    print(f"Customer:     {k.get('customer_name') or '(none)'}")
    print(f"Email:        {k.get('customer_email') or '(none)'}")
    print(f"Notes:        {k.get('notes') or '(none)'}")
    print(f"Created:      {k.get('created_at')}")
    print(f"Expires:      {k.get('expires_at') or '(no expiry)'}")
    print(f"Used:         {'yes' if k.get('used') else 'no'}")
    if k.get("used"):
        print(f"Activated:    {k.get('activated_at')}")
        print(f"Fingerprint:  {k.get('fingerprint_hash')}")
        print(f"From IP:      {k.get('activation_ip')}")
    if k.get("revoked"):
        print(f"Revoked:      {k.get('revoked_at')}  reason: {k.get('revoke_reason')}")
    print()
    attempts = res.get("recent_attempts", [])
    if attempts:
        print(f"Recent activation attempts ({len(attempts)}):")
        for a in attempts:
            mark = "✓" if a["success"] else "✗"
            ip = a['ip'] or '-'
            print(f"  {mark} {a['attempted_at']}  ip={ip:<15}  {a['error'] or 'ok'}")
    print()


def cmd_revoke(args):
    _check_config()
    res = _call("DELETE", f"/api/admin/keys/{args.key.upper()}",
                params={"reason": args.reason or ""})
    print(f"✓ Revoked: {res.get('revoked')}")


def cmd_stats(args):
    _check_config()
    res = _call("GET", "/api/admin/stats")
    print()
    print(f"  Total keys:        {res.get('total_keys'):>5}")
    print(f"  Available:         {res.get('available'):>5}")
    print(f"  Used (activated):  {res.get('used'):>5}")
    print(f"  Revoked:           {res.get('revoked'):>5}")
    print(f"  Total attempts:    {res.get('total_attempts'):>5}")
    print(f"  Failed attempts:   {res.get('failed_attempts'):>5}")
    print()


def main():
    p = argparse.ArgumentParser(description="JobHunter license admin tool")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="Generate one or more keys")
    g.add_argument("--customer", help="Customer name (recommended)")
    g.add_argument("--email", help="Customer email")
    g.add_argument("--notes", help="Free-text notes")
    g.add_argument("--count", type=int, default=1,
                   help="How many to generate (default 1)")
    g.add_argument("--valid-days", type=int, dest="valid_days",
                   help="Activation window in days (default: never expires)")
    g.set_defaults(func=cmd_generate)

    l = sub.add_parser("list", help="List keys")
    l.add_argument("--status", choices=["available", "used", "revoked"])
    l.set_defaults(func=cmd_list)

    i = sub.add_parser("inspect", help="Inspect one key")
    i.add_argument("key")
    i.set_defaults(func=cmd_inspect)

    r = sub.add_parser(
        "revoke",
        help="Revoke a key (cannot activate; existing installs unaffected)",
    )
    r.add_argument("key")
    r.add_argument("--reason")
    r.set_defaults(func=cmd_revoke)

    s = sub.add_parser("stats", help="Overall stats")
    s.set_defaults(func=cmd_stats)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
