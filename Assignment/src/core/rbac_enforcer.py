"""
RBAC (Role-Based Access Control) enforcement.
"""
from typing import List, Dict, Set
from ..models.user import User
from ..models.document import Document, DocumentChunk
from ..config import (
    ROLE_SENSITIVITY_ACCESS,
    ROLE_HIERARCHY,
    SENSITIVITY_HIERARCHY,
    get_accessible_departments,
    USERS_DB
)


class RBACEnforcer:
    """
    Enforces role-based access control across the system.
    """

    def __init__(self):
        self.access_log = []

    def get_user(self, username: str) -> User:
        """
        Retrieve a user from the user database.
        """
        from ..models.user import UserRole, Department
        from datetime import datetime

        if username not in USERS_DB:
            raise ValueError(f"User '{username}' not found")

        user_data = USERS_DB[username]
        return User(
            username=user_data["username"],
            full_name=user_data["full_name"],
            email=user_data["email"],
            role=UserRole(user_data["role"]),
            department=Department(user_data["department"]),
            created_at=datetime.now()
        )

    def list_users(self) -> List[Dict]:
        """
        List all users in the system.
        """
        return list(USERS_DB.values())

    def check_access(self, user: User, document: Document) -> bool:
        """
        Check if a user can access a specific document.
        """
        return user.can_access_document(document)

    def filter_documents(
        self,
        user: User,
        documents: List[Document]
    ) -> List[Document]:
        """
        Filter documents based on user's RBAC permissions.
        """
        accessible = []
        for doc in documents:
            if self.check_access(user, doc):
                accessible.append(doc)
            else:
                self._log_access(user, doc, granted=False, reason="RBAC denied")

        return accessible

    def filter_chunks(
        self,
        user: User,
        chunks: List[DocumentChunk]
    ) -> List[DocumentChunk]:
        """
        Filter document chunks based on user's RBAC permissions.
        """
        accessible = []
        for chunk in chunks:
            # Check chunk metadata for sensitivity and department
            sensitivity = chunk.metadata.get("sensitivity_level", "internal")
            department = chunk.metadata.get("department", "general")

            if user.can_access_sensitivity(sensitivity) and user.can_access_department(department):
                accessible.append(chunk)
            else:
                self._log_access(
                    user,
                    None,
                    granted=False,
                    reason=f"Chunk access denied: dept={department}, sens={sensitivity}"
                )

        return accessible

    def get_accessible_sources(self, user: User) -> Dict[str, List[str]]:
        """
        Get accessible data sources for a user.
        """
        return {
            "departments": list(get_accessible_departments(user.role_name, user.department_name)),
            "sensitivity_levels": list(ROLE_SENSITIVITY_ACCESS.get(user.role_name, set()))
        }

    def enforce_query_filter(
        self,
        user: User,
        metadata_filters: Dict
    ) -> Dict:
        """
        Add RBAC filters to a metadata query.
        Returns ChromaDB-compatible filter format.
        """
        accessible_departments = get_accessible_departments(user.role_name, user.department_name)
        accessible_sensitivities = ROLE_SENSITIVITY_ACCESS.get(user.role_name, set())

        # Build RBAC filter using $and with $in operators
        conditions = []

        if accessible_departments:
            conditions.append({"department": {"$in": list(accessible_departments)}})

        if accessible_sensitivities:
            conditions.append({"sensitivity_level": {"$in": list(accessible_sensitivities)}})

        # If no conditions, allow all
        if not conditions:
            return {}

        rbac_filter = conditions[0] if len(conditions) == 1 else {"$and": conditions}

        # Merge with existing filters if any
        if metadata_filters:
            if "$and" in rbac_filter:
                rbac_filter["$and"].append(metadata_filters)
            else:
                rbac_filter = {"$and": [rbac_filter, metadata_filters]}

        return rbac_filter

    def _log_access(self, user: User, document: Document, granted: bool, reason: str = ""):
        """
        Log access attempts.
        """
        from ..utils.audit_logger import get_audit_logger

        log_data = {
            "user": user.username,
            "role": user.role_name,
            "department": user.department_name,
            "document": document.id if document else "unknown",
            "granted": granted,
            "reason": reason
        }

        self.access_log.append(log_data)

        # Also log to audit log
        try:
            audit_logger = get_audit_logger()
            audit_logger.log_access_attempt(
                user_id=user.username,
                document_id=document.id if document else "unknown",
                access_granted=granted,
                reason=reason
            )
        except Exception as e:
            print(f"Failed to write audit log: {e}")

    def get_access_log(self) -> List[Dict]:
        """
        Get the in-memory access log.
        """
        return self.access_log

    def clear_access_log(self):
        """
        Clear the in-memory access log.
        """
        self.access_log = []
