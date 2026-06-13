"""
Audit logging utilities for tracking system access and queries.
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class AuditLogger:
    """
    Logs all system access and query activities for security auditing.
    """

    def __init__(self, log_file: Optional[Path] = None):
        from ..config import AUDIT_LOG_FILE
        self.log_file = log_file or AUDIT_LOG_FILE
        self._setup_logger()

    def _setup_logger(self):
        """Set up the audit logger."""
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)

        # Create file handler if not already present
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_file)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log_query(self, user_id: str, query_text: str, result_count: int, processing_time: float, success: bool = True):
        """
        Log a query attempt.
        """
        log_data = {
            "event_type": "query",
            "user_id": user_id,
            "query_text": query_text[:200] + "..." if len(query_text) > 200 else query_text,
            "result_count": result_count,
            "processing_time": processing_time,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }

        self._write_log(log_data)

    def log_access_attempt(self, user_id: str, document_id: str, access_granted: bool, reason: str = ""):
        """
        Log an access attempt to a document.
        """
        log_data = {
            "event_type": "document_access",
            "user_id": user_id,
            "document_id": document_id,
            "access_granted": access_granted,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }

        self._write_log(log_data)

    def log_system_event(self, event_type: str, details: Dict[str, Any]):
        """
        Log system-level events.
        """
        log_data = {
            "event_type": event_type,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }

        self._write_log(log_data)

    def log_error(self, error_type: str, message: str, user_id: Optional[str] = None, details: Optional[Dict] = None):
        """
        Log an error.
        """
        log_data = {
            "event_type": "error",
            "error_type": error_type,
            "message": message,
            "user_id": user_id,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }

        self._write_log(log_data)

    def log_user_login(self, user_id: str, session_id: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None):
        """
        Log user login.
        """
        log_data = {
            "event_type": "login",
            "user_id": user_id,
            "session_id": session_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": datetime.now().isoformat()
        }

        self._write_log(log_data)

    def log_user_logout(self, user_id: str, session_id: str):
        """
        Log user logout.
        """
        log_data = {
            "event_type": "logout",
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }

        self._write_log(log_data)

    def _write_log(self, log_data: Dict[str, Any]):
        """Write log entry to file."""
        try:
            log_entry = json.dumps(log_data) + "\n"
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)

            # Also write to console for debugging
            self.logger.info(f"Audit Log: {log_entry.strip()}")
        except Exception as e:
            print(f"Failed to write audit log: {e}")

    def get_recent_logs(self, limit: int = 100) -> list:
        """
        Get recent log entries.
        """
        logs = []
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            logs.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
                        if len(logs) >= limit:
                            break
        except FileNotFoundError:
            pass

        return logs[-limit:]  # Return last N logs

    def get_user_activity(self, user_id: str, days: int = 30) -> list:
        """
        Get activity for a specific user over the last N days.
        """
        from datetime import datetime, timedelta

        cutoff = datetime.now() - timedelta(days=days)
        user_logs = []

        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            log = json.loads(line)
                            log_time = datetime.fromisoformat(log["timestamp"])
                            if log.get("user_id") == user_id and log_time >= cutoff:
                                user_logs.append(log)
                        except (json.JSONDecodeError, KeyError):
                            continue
        except FileNotFoundError:
            pass

        return user_logs


# Global audit logger instance
_audit_logger = None


def get_audit_logger() -> AuditLogger:
    """
    Get or create the global audit logger instance.
    """
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger