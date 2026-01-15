import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
import os


DATABASE_URL = os.getenv("DATABASE_URL", "star_notifier.db")


class DatabaseManager:
    def __init__(self, db_path: str = DATABASE_URL):
        self.db_path = db_path
        self.init_db()

    @contextmanager
    def get_conn(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self):
        """Initialize database tables"""
        with self.get_conn() as conn:
            # Subscriptions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint TEXT UNIQUE NOT NULL,
                    p256dh TEXT NOT NULL,
                    auth TEXT NOT NULL,
                    user_agent TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)

            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_endpoint ON subscriptions(endpoint)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_is_active ON subscriptions(is_active)")

            # Notifications log table (optional)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo_full_name TEXT NOT NULL,
                    sender_login TEXT NOT NULL,
                    sender_avatar_url TEXT,
                    starred_at DATETIME,
                    payload TEXT,
                    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            print(f"Database initialized at {self.db_path}")

    def add_subscription(
        self,
        endpoint: str,
        p256dh: str,
        auth: str,
        user_agent: Optional[str] = None
    ) -> int:
        """Add a new subscription"""
        with self.get_conn() as conn:
            cursor = conn.execute(
                """
                INSERT OR REPLACE INTO subscriptions
                (endpoint, p256dh, auth, user_agent, last_seen, is_active)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, 1)
                """,
                (endpoint, p256dh, auth, user_agent)
            )
            return cursor.lastrowid

    def remove_subscription(self, endpoint: str) -> bool:
        """Remove a subscription"""
        with self.get_conn() as conn:
            cursor = conn.execute(
                "DELETE FROM subscriptions WHERE endpoint = ?",
                (endpoint,)
            )
            return cursor.rowcount > 0

    def get_subscription(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Get a subscription by endpoint"""
        with self.get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM subscriptions WHERE endpoint = ? AND is_active = 1",
                (endpoint,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def get_all_subscriptions(self) -> List[Dict[str, Any]]:
        """Get all active subscriptions"""
        with self.get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM subscriptions WHERE is_active = 1"
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_subscription_count(self) -> int:
        """Get count of active subscriptions"""
        with self.get_conn() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM subscriptions WHERE is_active = 1"
            )
            row = cursor.fetchone()
            return row["count"]

    def update_last_seen(self, endpoint: str):
        """Update last_seen timestamp for a subscription"""
        with self.get_conn() as conn:
            conn.execute(
                "UPDATE subscriptions SET last_seen = CURRENT_TIMESTAMP WHERE endpoint = ?",
                (endpoint,)
            )

    def mark_inactive(self, endpoint: str):
        """Mark a subscription as inactive (for failed push notifications)"""
        with self.get_conn() as conn:
            conn.execute(
                "UPDATE subscriptions SET is_active = 0 WHERE endpoint = ?",
                (endpoint,)
            )

    def log_notification(
        self,
        repo_full_name: str,
        sender_login: str,
        sender_avatar_url: Optional[str],
        starred_at: Optional[str],
        payload: Dict[str, Any]
    ):
        """Log a notification event"""
        with self.get_conn() as conn:
            conn.execute(
                """
                INSERT INTO notifications
                (repo_full_name, sender_login, sender_avatar_url, starred_at, payload)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    repo_full_name,
                    sender_login,
                    sender_avatar_url,
                    starred_at,
                    json.dumps(payload)
                )
            )

    def get_recent_notifications(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent notification logs"""
        with self.get_conn() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM notifications
                ORDER BY sent_at DESC
                LIMIT ?
                """,
                (limit,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]


# Global database instance
db = DatabaseManager()
