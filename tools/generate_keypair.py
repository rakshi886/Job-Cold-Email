"""
generate_keypair.py — run ONCE to create the signing keypair for JobHunter licenses.

Outputs two files:
  • private_key.pem  → set as PRIVATE_KEY_PEM env var on your Render server.
                       NEVER commit. NEVER share. Keep on your laptop only.
  • public_key.pem   → embed into JobHunter/app/license_manager.py (PUBLIC_KEY_PEM)
                       AND set as PUBLIC_KEY_PEM env var on Render.

Run:
    python tools/generate_keypair.py
"""
from __future__ import annotations

from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


OUT_DIR = Path(__file__).resolve().parent.parent / "keys"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    priv = Ed25519PrivateKey.generate()
    pub  = priv.public_key()

    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_pem = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    priv_path = OUT_DIR / "private_key.pem"
    pub_path  = OUT_DIR / "public_key.pem"
    priv_path.write_bytes(priv_pem)
    pub_path.write_bytes(pub_pem)

    print("─" * 60)
    print("  Keypair generated.")
    print("─" * 60)
    print(f"  Private key: {priv_path}")
    print(f"  Public key:  {pub_path}")
    print()
    print("  NEXT STEPS:")
    print()
    print("  1. On Render → your service → Environment tab, set:")
    print("       PRIVATE_KEY_PEM = (paste full contents of private_key.pem)")
    print("       PUBLIC_KEY_PEM  = (paste full contents of public_key.pem)")
    print()
    print("  2. Copy the public_key.pem contents into the")
    print("     JobHunter/app/license_manager.py file at the EMBEDDED_PUBLIC_KEY constant.")
    print()
    print("  ⚠  Never commit private_key.pem to git. Add the keys/ folder to .gitignore.")
    print("─" * 60)


if __name__ == "__main__":
    main()
