"""
Configuration and RBAC policies for Enterprise RAG System.
"""
import os
from pathlib import Path
from typing import Dict, Set
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# Path Configuration
# ============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ENTERPRISE_DATA_DIR = DATA_DIR / "enterprise_data"
PROCESSED_DATA_DIR = DATA_DIR / "processed_data"
LOGS_DIR = DATA_DIR / "logs"
CHROMA_DIR = PROCESSED_DATA_DIR / "chroma"

# Ensure directories exist
for d in [DATA_DIR, ENTERPRISE_DATA_DIR, PROCESSED_DATA_DIR, LOGS_DIR, CHROMA_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Model Configuration
# ============================================================================
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
GENERATION_MODEL = os.getenv("GENERATION_MODEL", "google/flan-t5-base")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
TOP_K_RETRIEVAL = int(os.getenv("TOP_K_RETRIEVAL", "5"))


# ============================================================================
# RBAC Configuration
# ============================================================================

# Roles hierarchy (higher = more privileges)
ROLES = ["employee", "manager", "admin"]
ROLE_HIERARCHY = {role: idx for idx, role in enumerate(ROLES)}

# Departments
DEPARTMENTS = ["hr", "finance", "engineering", "operations", "general"]

# Sensitivity levels (ordered: public < internal < confidential < restricted)
SENSITIVITY_LEVELS = ["public", "internal", "confidential", "restricted"]
SENSITIVITY_HIERARCHY = {level: idx for idx, level in enumerate(SENSITIVITY_LEVELS)}


# Access policy: which sensitivity levels can each role access?
ROLE_SENSITIVITY_ACCESS: Dict[str, Set[str]] = {
    "employee": {"public", "internal"},
    "manager": {"public", "internal", "confidential"},
    "admin": {"public", "internal", "confidential", "restricted"},
}


# Department access: can role X from department Y access department Z's data?
# Default: users can access their own department + general data
# Managers can access all departments at their sensitivity level
# Admins can access everything
DEPARTMENT_ACCESS_MATRIX: Dict[str, Set[str]] = {
    # Employee can only see their own department + general
    "employee_hr": {"hr", "general"},
    "employee_finance": {"finance", "general"},
    "employee_engineering": {"engineering", "general"},
    "employee_operations": {"operations", "general"},
    "employee_general": {"general"},

    # Managers can see all departments at their level
    "manager_hr": {"hr", "finance", "engineering", "operations", "general"},
    "manager_finance": {"hr", "finance", "engineering", "operations", "general"},
    "manager_engineering": {"hr", "finance", "engineering", "operations", "general"},
    "manager_operations": {"hr", "finance", "engineering", "operations", "general"},
    "manager_general": {"hr", "finance", "engineering", "operations", "general"},

    # Admins see everything
    "admin_hr": {"hr", "finance", "engineering", "operations", "general"},
    "admin_finance": {"hr", "finance", "engineering", "operations", "general"},
    "admin_engineering": {"hr", "finance", "engineering", "operations", "general"},
    "admin_operations": {"hr", "finance", "engineering", "operations", "general"},
    "admin_general": {"hr", "finance", "engineering", "operations", "general"},
}


def get_accessible_departments(role: str, department: str) -> Set[str]:
    """Get departments a user can access based on role and their department."""
    key = f"{role}_{department}"
    return DEPARTMENT_ACCESS_MATRIX.get(key, {"general"})


# ============================================================================
# User Database (synthetic for demo)
# ============================================================================
USERS_DB = {
    "alice": {
        "username": "alice",
        "full_name": "Alice Johnson",
        "role": "employee",
        "department": "engineering",
        "email": "alice@company.com",
    },
    "bob": {
        "username": "bob",
        "full_name": "Bob Smith",
        "role": "manager",
        "department": "finance",
        "email": "bob@company.com",
    },
    "carol": {
        "username": "carol",
        "full_name": "Carol Williams",
        "role": "manager",
        "department": "hr",
        "email": "carol@company.com",
    },
    "dave": {
        "username": "dave",
        "full_name": "Dave Brown",
        "role": "admin",
        "department": "operations",
        "email": "dave@company.com",
    },
    "eve": {
        "username": "eve",
        "full_name": "Eve Davis",
        "role": "employee",
        "department": "hr",
        "email": "eve@company.com",
    },
    "frank": {
        "username": "frank",
        "full_name": "Frank Miller",
        "role": "employee",
        "department": "finance",
        "email": "frank@company.com",
    },
}


# ============================================================================
# Data Source Configuration
# ============================================================================
DATA_SOURCES = {
    "pdfs": {
        "path": ENTERPRISE_DATA_DIR / "pdfs",
        "type": "pdf",
        "extensions": [".pdf"],
    },
    "databases": {
        "path": ENTERPRISE_DATA_DIR / "databases",
        "type": "sql",
        "extensions": [".csv", ".sql", ".db"],
    },
    "json_logs": {
        "path": ENTERPRISE_DATA_DIR / "json_logs",
        "type": "json",
        "extensions": [".json", ".log"],
    },
}


# ============================================================================
# Generation Parameters
# ============================================================================
GENERATION_CONFIG = {
    "max_length": 512,
    "num_beams": 4,
    "temperature": 0.7,
    "top_p": 0.9,
    "do_sample": True,
}


# ============================================================================
# Logging Configuration
# ============================================================================
AUDIT_LOG_FILE = LOGS_DIR / "audit.log"
SYSTEM_LOG_FILE = LOGS_DIR / "system.log"
