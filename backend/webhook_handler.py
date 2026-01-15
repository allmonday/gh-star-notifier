import hmac
import hashlib
import json
import os
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, status
from models import WebhookPayload, NotificationData


class WebhookHandler:
    def __init__(self):
        self.webhook_secret = os.getenv("WEBHOOK_SECRET", "")
        self.whitelist = self._parse_whitelist()

    def _parse_whitelist(self) -> set:
        """Parse whitelist from environment variable"""
        whitelist_str = os.getenv("WEBHOOK_WHITELIST", "[]")
        try:
            whitelist = json.loads(whitelist_str)
            return set(whitelist)
        except json.JSONDecodeError:
            print(f"Warning: Invalid WEBHOOK_WHITELIST format: {whitelist_str}")
            return set()

    def verify_signature(self, signature: str, body: bytes) -> bool:
        """
        Verify GitHub webhook signature using HMAC-SHA256

        Args:
            signature: X-Hub-Signature-256 header value
            body: Raw request body

        Returns:
            bool: True if signature is valid

        Raises:
            HTTPException: If signature is invalid or missing
        """
        if not self.webhook_secret:
            print("Warning: WEBHOOK_SECRET not configured, skipping signature verification")
            return True

        if not signature:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="X-Hub-Signature-256 header is missing"
            )

        # Signature format: "sha256=<hex_signature>"
        if not signature.startswith("sha256="):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid signature format"
            )

        received_hash = signature[7:]  # Remove "sha256=" prefix

        # Calculate expected signature
        expected_hash = hmac.new(
            self.webhook_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        # Use constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(received_hash, expected_hash):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid signature"
            )

        return True

    def verify_whitelist(self, repo_full_name: str) -> bool:
        """
        Verify repository is in whitelist

        Args:
            repo_full_name: Repository full name (e.g., "owner/repo")

        Returns:
            bool: True if repository is in whitelist

        Raises:
            HTTPException: If repository is not in whitelist
        """
        if not self.whitelist:
            print("Warning: WEBHOOK_WHITELIST is empty, allowing all repositories")
            return True

        if repo_full_name not in self.whitelist:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Repository '{repo_full_name}' is not in whitelist"
            )

        return True

    def parse_webhook_payload(self, body: bytes) -> WebhookPayload:
        """
        Parse and validate GitHub webhook payload

        Args:
            body: Raw request body

        Returns:
            WebhookPayload: Validated payload

        Raises:
            HTTPException: If payload is invalid
        """
        try:
            payload_data = json.loads(body)
            payload = WebhookPayload(**payload_data)
            return payload
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid payload: {str(e)}"
            )

    def create_notification_data(self, payload: WebhookPayload) -> NotificationData:
        """
        Create notification data from webhook payload

        Args:
            payload: Validated webhook payload

        Returns:
            NotificationData: Data for push notification
        """
        repo = payload.repository
        sender = payload.sender

        # Build detailed notification
        title = f"⭐ New Star on {repo['full_name']}"
        body = f"{sender['login']} starred your repository"

        # Add description if available
        description = repo.get('description', '')
        if description:
            body += f"\n\n{description}"

        # Add star count
        stargazers_count = repo.get('stargazers_count', 0)
        body += f"\n\n⭐ {stargazers_count} stars"

        # Add time if available
        if payload.starred_at:
            body += f"\n🕐 {payload.starred_at}"

        return NotificationData(
            title=title,
            body=body,
            icon=sender.get('avatar_url'),
            badge="https://github.githubassets.com/favicons/favicon.png",
            url=repo.get('html_url', f"https://github.com/{repo['full_name']}")
        )

    async def handle_webhook(self, request: Request) -> NotificationData:
        """
        Handle incoming GitHub webhook request

        Args:
            request: FastAPI request object

        Returns:
            NotificationData: Data for push notification

        Raises:
            HTTPException: If validation fails
        """
        # Step 1: Get signature header
        signature = request.headers.get("X-Hub-Signature-256")

        # Step 2: Get raw body
        body = await request.body()

        # Step 3: Verify signature (HMAC-SHA256)
        self.verify_signature(signature, body)

        # Step 4: Parse payload
        payload = self.parse_webhook_payload(body)

        # Step 5: Verify whitelist
        repo_full_name = payload.repository.get('full_name', '')
        self.verify_whitelist(repo_full_name)

        # Step 6: Check if action is 'started' (star event)
        if payload.action != 'started':
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail=f"Ignoring action: {payload.action}"
            )

        # Step 7: Create notification data
        notification_data = self.create_notification_data(payload)

        print(f"✅ Webhook validated: {repo_full_name} starred by {payload.sender['login']}")

        return notification_data


# Global webhook handler instance
webhook_handler = WebhookHandler()
