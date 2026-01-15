import os
import json
from typing import Dict, Any, List
from pywebpush import webpush, WebPushException
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from dotenv import load_dotenv
from models import NotificationData

load_dotenv()


class PushNotificationService:
    def __init__(self):
        self.vapid_private_key = None
        self.vapid_public_key = None
        self.vapid_subject = os.getenv(
            "VAPID_SUBJECT", "mailto:example@example.com"
        )

        # Load or generate VAPID keys
        self._init_vapid_keys()

    def _init_vapid_keys(self):
        """Initialize VAPID keys from environment or generate new ones"""
        private_key = os.getenv("VAPID_PRIVATE_KEY")
        public_key = os.getenv("VAPID_PUBLIC_KEY")

        if private_key and public_key:
            self.vapid_private_key = private_key
            self.vapid_public_key = public_key
            print("✅ Loaded VAPID keys from environment")
        else:
            # Generate new VAPID keys
            self.vapid_private_key, self.vapid_public_key = (
                self._generate_vapid_keys()
            )
            print("\n" + "=" * 60)
            print("⚠️  Generated new VAPID keys (save these to .env file):")
            print("=" * 60)
            print(f"VAPID_PRIVATE_KEY={self.vapid_private_key}")
            print(f"VAPID_PUBLIC_KEY={self.vapid_public_key}")
            print("=" * 60 + "\n")

    def _generate_vapid_keys(self) -> tuple[str, str]:
        """Generate VAPID key pair"""
        import base64

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

    def get_vapid_public_key(self) -> str:
        """Get VAPID public key"""
        return self.vapid_public_key

    def send_notification(
        self,
        subscription_data: Dict[str, Any],
        notification: NotificationData
    ) -> Dict[str, Any]:
        """
        Send a push notification to a single subscription

        Args:
            subscription_data: Push subscription data
            notification: Notification data to send

        Returns:
            Dict with status information

        Raises:
            WebPushException: If push fails
        """
        try:
            # Prepare notification payload
            payload = json.dumps({
                "title": notification.title,
                "body": notification.body,
                "icon": notification.icon,
                "badge": notification.badge,
                "image": notification.image,
                "url": notification.url
            })

            # Send push notification
            response = webpush(
                subscription_info=subscription_data,
                data=payload,
                vapid_private_key=self.vapid_private_key,
                vapid_claims={"sub": self.vapid_subject},
            )

            return {
                "status": "sent",
                "response": str(response)
            }

        except WebPushException as exc:
            print(f"❌ Failed to send push notification: {exc}")

            # Check if subscription is invalid (410 Gone or 404 Not Found)
            if exc.response and exc.response.status_code in [410, 404]:
                print(f"⚠️  Subscription expired or invalid: {subscription_data.get('endpoint', 'unknown')}")
                # Mark for deletion (caller should remove from database)
                return {
                    "status": "expired",
                    "error": str(exc),
                    "remove_subscription": True
                }

            raise exc

    def broadcast_notification(
        self,
        subscriptions: List[Dict[str, Any]],
        notification: NotificationData
    ) -> List[Dict[str, Any]]:
        """
        Send notification to all subscriptions

        Args:
            subscriptions: List of subscription data
            notification: Notification data to send

        Returns:
            List of results for each subscription
        """
        results = []
        success_count = 0
        failed_count = 0

        print(f"📢 Broadcasting to {len(subscriptions)} subscriptions...")

        for subscription in subscriptions:
            endpoint = subscription.get("endpoint", "unknown")
            p256dh = subscription.get("p256dh", "")
            auth = subscription.get("auth", "")
            subscription_data = {
                "endpoint": endpoint,
                "keys": {
                    "p256dh": p256dh,
                    "auth": auth
                }
            }
            try:
                result = self.send_notification(subscription_data, notification)
                results.append({
                    "endpoint": endpoint,
                    "status": "success",
                    "result": result
                })
                success_count += 1
                print(f"✅ Sent to {endpoint}")

            except Exception as e:
                results.append({
                    "endpoint": endpoint,
                    "status": "failed",
                    "error": str(e)
                })
                failed_count += 1
                print(f"❌ Failed to send to {endpoint}: {e}")

        print(f"\n📊 Broadcast complete: {success_count} success, {failed_count} failed")

        return results


# Global push service instance
push_service = PushNotificationService()
