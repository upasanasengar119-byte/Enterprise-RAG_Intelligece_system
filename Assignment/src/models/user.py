"""
User models for the enterprise RAG system.
"""
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class UserRole(Enum):
    """User roles in the organization."""
    EMPLOYEE = "employee"
    MANAGER = "manager"
    ADMIN = "admin"


class Department(Enum):
    """Department options."""
    HR = "hr"
    FINANCE = "finance"
    ENGINEERING = "engineering"
    OPERATIONS = "operations"
    GENERAL = "general"


@dataclass
class User:
    """
    Represents a user in the organization.
    """
    username: str
    full_name: str
    email: str
    role: UserRole
    department: Department
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    session_id: Optional[str] = None
    query_count: int = 0
    preferences: Dict[str, str] = field(default_factory=dict)

    @property
    def role_name(self) -> str:
        """Get role name as string."""
        return self.role.value

    @property
    def department_name(self) -> str:
        """Get department name as string."""
        return self.department.value

    def can_access_sensitivity(self, sensitivity_level: str) -> bool:
        """
        Check if user can access documents with the given sensitivity level.
        """
        from ..config import ROLE_SENSITIVITY_ACCESS

        accessible_sensitivities = ROLE_SENSITIVITY_ACCESS.get(self.role_name, set())
        return sensitivity_level in accessible_sensitivities

    def can_access_department(self, department: str) -> bool:
        """
        Check if user can access data from the given department.
        """
        from ..config import get_accessible_departments

        accessible_departments = get_accessible_departments(self.role_name, self.department_name)
        return department in accessible_departments

    def can_access_document(self, document: "Document") -> bool:
        """
        Check if user can access a specific document based on RBAC rules.
        """
        # Check sensitivity
        if not self.can_access_sensitivity(document.sensitivity_level):
            return False

        # Check department
        if not self.can_access_department(document.department):
            return False

        # Check role requirement
        from ..config import ROLE_HIERARCHY
        if ROLE_HIERARCHY.get(document.role_required, -1) > ROLE_HIERARCHY.get(self.role_name, -1):
            return False

        return True

    def increment_query_count(self):
        """Increment the user's query count."""
        self.query_count += 1
        self.last_login = datetime.now()

    def to_dict(self) -> Dict:
        """Convert user to dictionary."""
        return {
            "username": self.username,
            "full_name": self.full_name,
            "email": self.email,
            "role": self.role_name,
            "department": self.department_name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "query_count": self.query_count,
            "preferences": self.preferences
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "User":
        """Create user from dictionary."""
        return cls(
            username=data["username"],
            full_name=data["full_name"],
            email=data["email"],
            role=UserRole(data["role"]),
            department=Department(data["department"]),
            is_active=data.get("is_active", True),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_login=datetime.fromisoformat(data["last_login"]) if data.get("last_login") else None,
            query_count=data.get("query_count", 0),
            preferences=data.get("preferences", {})
        )


@dataclass
class UserSession:
    """
    Represents a user session for authentication.
    """
    username: str
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=1))
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    def is_valid(self) -> bool:
        """Check if session is valid (not expired)."""
        return datetime.now() < self.expires_at

    def to_dict(self) -> Dict:
        """Convert session to dictionary."""
        return {
            "username": self.username,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent
        }


# For Python < 3.10 compatibility
from datetime import timedelta