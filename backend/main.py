from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import uvicorn

from models import SubscriptionModel, UnsubscribeModel, NotificationRequest
from database import db
from push_service import push_service
from webhook_handler import webhook_handler

app = FastAPI(
    title="GitHub Star Notifier API",
    description="PWA push notifications for GitHub star events",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for PWA
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    app.mount("/icons", StaticFiles(directory=os.path.join(static_dir, "icons")), name="icons")

    # Serve manifest.json and sw.js
    @app.get("/manifest.json")
    async def manifest():
        return FileResponse(os.path.join(static_dir, "manifest.json"))

    @app.get("/sw.js")
    async def service_worker():
        return FileResponse(os.path.join(static_dir, "sw.js"), media_type="application/javascript")


@app.get("/health")
async def health():
    """Health check endpoint"""
    sub_count = db.get_subscription_count()
    return {
        "status": "healthy",
        "subscriptions": sub_count
    }


@app.get("/api/vapid-public-key")
async def get_vapid_public_key():
    """Get VAPID public key for client-side subscription"""
    return {"publicKey": push_service.get_vapid_public_key()}


@app.post("/api/subscribe")
async def subscribe(data: SubscriptionModel):
    """Subscribe a client to push notifications"""
    try:
        subscription_data = data.subscription
        endpoint = subscription_data.get("endpoint", "")
        keys = subscription_data.get("keys", {})

        # Extract subscription keys
        p256dh = keys.get("p256dh", "")
        auth = keys.get("auth", "")

        if not endpoint or not p256dh or not auth:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid subscription data"
            )

        # Save to database
        db.add_subscription(endpoint, p256dh, auth)

        print(f"✅ New subscription: {endpoint}")

        return {
            "status": "success",
            "message": "Successfully subscribed",
            "endpoint": endpoint,
        }

    except Exception as e:
        print(f"❌ Subscription error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/unsubscribe")
async def unsubscribe(data: UnsubscribeModel):
    """Unsubscribe a client from push notifications"""
    try:
        subscription_data = data.subscription
        endpoint = subscription_data.get("endpoint", "")

        # Remove from database
        removed = db.remove_subscription(endpoint)

        if removed:
            print(f"✅ Unsubscribed: {endpoint}")
            return {
                "status": "success",
                "message": "Successfully unsubscribed"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unsubscribe error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/test-notification")
async def test_notification(data: NotificationRequest):
    """Send a test notification to all subscribers"""
    try:
        # Get all subscriptions
        subscriptions = db.get_all_subscriptions()

        if not subscriptions:
            return {
                "status": "warning",
                "message": "No active subscriptions",
                "count": 0
            }

        # Create test notification
        from models import NotificationData
        notification = NotificationData(
            title=data.title,
            body=data.body,
            icon="https://github.githubassets.com/favicons/favicon.png"
        )

        # Broadcast to all subscriptions
        results = push_service.broadcast_notification(subscriptions, notification)

        # Handle expired subscriptions
        for result in results:
            if result.get("result", {}).get("remove_subscription"):
                endpoint = result.get("endpoint", "")
                db.mark_inactive(endpoint)
                print(f"⚠️  Marked subscription as inactive: {endpoint}")

        success_count = sum(1 for r in results if r["status"] == "success")

        return {
            "status": "success",
            "message": f"Test notification sent to {success_count}/{len(subscriptions)} subscribers",
            "total": len(subscriptions),
            "success": success_count,
            "failed": len(subscriptions) - success_count,
            "results": results
        }

    except Exception as e:
        print(f"❌ Test notification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/webhook")
async def github_webhook(request: Request):
    """
    Handle GitHub webhook events

    This endpoint receives GitHub star events and triggers
    push notifications to all active subscribers.
    """
    try:
        # Validate and parse webhook
        notification_data = await webhook_handler.handle_webhook(request)

        # Get all subscriptions
        subscriptions = db.get_all_subscriptions()

        if not subscriptions:
            print("⚠️  No active subscriptions to notify")
            return {
                "status": "success",
                "message": "Webhook received, but no active subscribers",
                "subscribers": 0
            }

        # Broadcast notification
        results = push_service.broadcast_notification(subscriptions, notification_data)

        # Log notification event
        # (Extract repo and sender info from notification_data)
        # db.log_notification(...)

        # Handle expired subscriptions
        for result in results:
            if result.get("result", {}).get("remove_subscription"):
                endpoint = result.get("endpoint", "")
                db.mark_inactive(endpoint)

        success_count = sum(1 for r in results if r["status"] == "success")

        return {
            "status": "success",
            "message": f"Notification sent to {success_count}/{len(subscriptions)} subscribers",
            "subscribers": len(subscriptions),
            "success": success_count,
            "failed": len(subscriptions) - success_count
        }

    except HTTPException as http_exc:
        # Re-raise HTTP exceptions (validation errors)
        raise http_exc

    except Exception as e:
        print(f"❌ Webhook handling error: {e}")
        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/api/subscriptions")
async def get_subscriptions():
    """Get all active subscriptions"""
    try:
        subscriptions = db.get_all_subscriptions()

        # Return only endpoint and timestamps (hide sensitive keys)
        sanitized_subs = [
            {
                "endpoint": sub["endpoint"],
                "created_at": sub["created_at"],
                "last_seen": sub["last_seen"]
            }
            for sub in subscriptions
        ]

        return {
            "count": len(subscriptions),
            "subscriptions": sanitized_subs
        }

    except Exception as e:
        print(f"❌ Get subscriptions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# API info endpoint
@app.get("/api/info")
async def api_info():
    """API information"""
    return {
        "name": "GitHub Star Notifier API",
        "version": "1.0.0",
        "endpoints": {
            "info": "/api/info",
            "vapid_public_key": "/api/vapid-public-key",
            "subscribe": "/api/subscribe",
            "unsubscribe": "/api/unsubscribe",
            "test_notification": "/api/test-notification",
            "webhook": "/api/webhook",
            "subscriptions": "/api/subscriptions",
            "health": "/api/health"
        }
    }


# Root endpoint serves SPA
@app.get("/")
async def root():
    """Serve SPA index.html"""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return {
            "message": "GitHub Star Notifier",
            "status": "Frontend not built",
            "hint": "Run: npm run build in ../frontend"
        }


# SPA fallback: serve index.html for all non-API routes (must be last)
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve SPA index.html for all non-API routes"""
    # Don't intercept API routes
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")

    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        raise HTTPException(status_code=404, detail="Frontend not built. Run: npm run build in ../frontend")


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    print("=" * 60)
    print("🚀 GitHub Star Notifier API")
    print("=" * 60)
    print(f"📍 Server: http://{host}:{port}")
    print(f"📡 Webhook: http://{host}:{port}/api/webhook")
    print("=" * 60)

    uvicorn.run(app, host=host, port=port)
