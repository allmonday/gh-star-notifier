from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List
import json


class SubscriptionModel(BaseModel):
    """Push subscription model"""
    subscription: Dict[str, Any]

    @validator('subscription')
    def validate_subscription(cls, v):
        """Validate subscription format"""
        required_fields = ['endpoint', 'keys']
        if not all(field in v for field in required_fields):
            raise ValueError("Invalid subscription format")

        keys = v.get('keys', {})
        if 'p256dh' not in keys or 'auth' not in keys:
            raise ValueError("Invalid subscription keys")

        # Validate endpoint is HTTPS
        endpoint = v.get('endpoint', '')
        if not endpoint.startswith('https://'):
            raise ValueError("Endpoint must use HTTPS")

        return v


class UnsubscribeModel(BaseModel):
    """Unsubscribe model"""
    subscription: Dict[str, Any]


class NotificationRequest(BaseModel):
    """Test notification request"""
    title: str = Field(..., min_length=1, max_length=100)
    body: str = Field(..., min_length=1, max_length=500)


class WebhookPayload(BaseModel):
    """GitHub webhook payload model"""
    action: str
    repository: Dict[str, Any]
    sender: Dict[str, Any]
    starred_at: Optional[str] = None

    @validator('action')
    def validate_action(cls, v):
        """Validate action is 'started'"""
        if v not in ['started', 'deleted']:
            raise ValueError(f"Invalid action: {v}")
        return v


class WebhookHeaders(BaseModel):
    """GitHub webhook headers"""
    x_hub_signature_256: Optional[str] = Field(None, alias="X-Hub-Signature-256")
    x_github_event: Optional[str] = Field(None, alias="X-GitHub-Event")
    x_github_delivery: Optional[str] = Field(None, alias="X-GitHub-Delivery")
    content_type: str = Field(..., alias="content-type")

    class Config:
        allow_population_by_field_name = True


class NotificationData(BaseModel):
    """Data for push notification"""
    title: str
    body: str
    icon: Optional[str] = None
    badge: Optional[str] = None
    image: Optional[str] = None
    url: Optional[str] = None
