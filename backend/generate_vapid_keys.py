#!/usr/bin/env python3
"""
Generate VAPID keys for Web Push notifications

This script generates a VAPID key pair and can optionally save them to .env files.
"""
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend


def generate_vapid_keys():
    """Generate VAPID key pair"""
    # Generate P-256 elliptic curve key pair
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())

    # Get the private key number and convert to bytes (32 bytes big-endian)
    private_key_int = private_key.private_numbers().private_value
    private_bytes = private_key_int.to_bytes(32, byteorder='big')

    # Get the public key coordinates and encode as uncompressed point (0x04 + x + y)
    public_numbers = private_key.public_key().public_numbers()
    x = public_numbers.x.to_bytes(32, byteorder='big')
    y = public_numbers.y.to_bytes(32, byteorder='big')
    public_bytes = b'\x04' + x + y

    # Convert to base64url format (replace + and / with - and _, remove padding =)
    private_key_b64 = base64.urlsafe_b64encode(private_bytes).rstrip(b'=').decode('utf-8')
    public_key_b64 = base64.urlsafe_b64encode(public_bytes).rstrip(b'=').decode('utf-8')

    return private_key_b64, public_key_b64


def save_to_env(private_key, public_key, env_file='.env'):
    """Save keys to .env file"""
    import os

    # Read existing .env file if it exists
    existing_lines = []
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            existing_lines = f.readlines()

    # Update or add VAPID keys
    updated_lines = []
    vapid_keys_updated = False

    for line in existing_lines:
        if line.startswith('VAPID_PRIVATE_KEY='):
            updated_lines.append(f'VAPID_PRIVATE_KEY={private_key}\n')
            vapid_keys_updated = True
        elif line.startswith('VAPID_PUBLIC_KEY='):
            updated_lines.append(f'VAPID_PUBLIC_KEY={public_key}\n')
            vapid_keys_updated = True
        else:
            updated_lines.append(line)

    # If keys didn't exist in file, append them
    if not vapid_keys_updated:
        if updated_lines and not updated_lines[-1].endswith('\n'):
            updated_lines.append('\n')
        updated_lines.append(f'VAPID_PRIVATE_KEY={private_key}\n')
        updated_lines.append(f'VAPID_PUBLIC_KEY={public_key}\n')

    # Write back to .env
    with open(env_file, 'w') as f:
        f.writelines(updated_lines)

    print(f"✅ Keys saved to {env_file}")


def main():
    """Main function"""
    print("=" * 70)
    print("🔐 VAPID Key Generator")
    print("=" * 70)
    print()

    # Generate keys
    print("⏳ Generating VAPID key pair...")
    private_key, public_key = generate_vapid_keys()

    print()
    print("✅ Keys generated successfully!")
    print()
    print("=" * 70)
    print("📋 Your VAPID Keys:")
    print("=" * 70)
    print()
    print(f"VAPID_PRIVATE_KEY={private_key}")
    print(f"VAPID_PUBLIC_KEY={public_key}")
    print()
    print("=" * 70)
    print()

    # Ask if user wants to save to .env
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--save':
        # Save to both backend/.env and root .env
        save_to_env(private_key, public_key, 'backend/.env')
        save_to_env(private_key, public_key, '.env')
    else:
        print("💡 To save these keys to your .env file, run:")
        print("   python backend/generate_vapid_keys.py --save")
        print()
        print("Or manually copy the keys above to your .env file:")
        print("   backend/.env")
        print("   .env")


if __name__ == '__main__':
    main()
