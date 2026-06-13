"""
Generate synthetic enterprise data for testing the RAG system.
Creates text-based PDF replacements, CSV files, and JSON logs.
Works without external dependencies beyond Python stdlib.
"""
import csv
import json
import random
import uuid
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))


def generate_documents(output_dir: Path):
    """Generate sample document files (text-based, .pdf extension)."""
    output_dir.mkdir(parents=True, exist_ok=True)

    documents = [
        {
            "filename": "employee_handbook.pdf",
            "title": "Employee Handbook 2026",
            "department": "hr",
            "sensitivity": "public",
            "role": "employee",
            "tags": ["handbook", "policies", "onboarding"],
            "content": """Employee Handbook 2026

Welcome to the Company Employee Handbook.

This handbook contains important information about company policies, benefits, and procedures.

Section 1: Company Overview
Our mission is to deliver innovative solutions to our customers. We value integrity, collaboration, and excellence.

Section 2: Code of Conduct
All employees must adhere to our ethical guidelines. We treat each other with respect and maintain professional behavior at all times.

Section 3: Work Schedule
Standard work hours are 9 AM to 5 PM, Monday through Friday. Flexible work arrangements are available with manager approval.

Section 4: Benefits
We offer comprehensive health insurance, retirement plans, and paid time off. Health coverage begins on the first day of employment.

Section 5: Leave Policy
Employees are entitled to 20 days of paid vacation annually. Sick leave and personal days are available as needed.

Section 6: Performance Reviews
Annual performance reviews are conducted each December. Reviews include self-assessment, peer feedback, and manager evaluation.

Section 7: Professional Development
We support employee growth through training programs, conference attendance, and tuition reimbursement for relevant courses.

Section 8: Communication
Open communication between management and staff is encouraged. We hold monthly all-hands meetings and regular team standups.

Section 9: Diversity and Inclusion
We are committed to building a diverse and inclusive workforce. Our hiring practices ensure equal opportunity for all.

Section 10: Remote Work Policy
Remote work is supported with manager approval. Employees must maintain a dedicated workspace and reliable internet connection.
"""
        },
        {
            "filename": "security_protocol.pdf",
            "title": "Information Security Protocol",
            "department": "operations",
            "sensitivity": "confidential",
            "role": "manager",
            "tags": ["security", "protocol", "confidential"],
            "content": """Information Security Protocol - Confidential Document

This document outlines security procedures for handling sensitive company data.

Chapter 1: Data Classification
All data is classified as Public, Internal, Confidential, or Restricted. Each classification has specific handling requirements.

Chapter 2: Access Control
Role-based access control is enforced across all systems. Users only have access to data necessary for their job function.

Chapter 3: Password Policy
Passwords must be at least 12 characters with special characters, numbers, and uppercase letters. Passwords must be changed every 90 days.

Chapter 4: Incident Response
All security incidents must be reported within 1 hour of detection. The security team will investigate and remediate immediately.

Chapter 5: Data Encryption
All confidential data must be encrypted at rest and in transit. We use AES-256 encryption for data storage and TLS 1.3 for network traffic.

Chapter 6: Network Security
VPN access is required for remote work. Multi-factor authentication is mandatory for all systems.

Chapter 7: Audit Logging
All system access is logged and monitored. Logs are retained for one year and reviewed regularly.

Chapter 8: Compliance
We comply with GDPR, HIPAA, and SOC 2 standards. Annual audits ensure continued compliance.

Chapter 9: Security Training
All employees must complete annual security awareness training. Training covers phishing, social engineering, and data protection.

Chapter 10: Vendor Management
Third-party vendors with access to company data must meet our security standards. Contracts include security requirements.
"""
        },
        {
            "filename": "financial_report_q4.pdf",
            "title": "Q4 2025 Financial Report",
            "department": "finance",
            "sensitivity": "restricted",
            "role": "manager",
            "tags": ["finance", "quarterly", "earnings"],
            "content": """Q4 2025 Financial Report - Restricted Access

This report contains sensitive financial information for internal use only.

Executive Summary
Q4 2025 revenue increased 15% year-over-year to $125 million. Strong performance across all business units contributed to growth.

Revenue Breakdown
Product sales reached $75 million, representing 60% of total revenue. Services contributed $35 million (28%), and licensing added $15 million (12%).

Operating Expenses
Total operating costs were $85 million, up 8% from Q4 2024. Key drivers include hiring, infrastructure, and R&D investments.

Profitability
Net income reached $28 million, representing a 22% profit margin. This exceeds industry average of 18%.

Cash Flow
Operating cash flow was $32 million, with $50 million in total cash reserves. Strong cash position enables strategic investments.

Regional Performance
North America: $50M revenue (40% of total). Europe: $40M (32%). Asia-Pacific: $25M (20%). Rest of World: $10M (8%).

Customer Metrics
Total active customers: 1,250 (up 20% YoY). Average revenue per customer: $100,000. Customer retention rate: 95%.

Outlook
Q1 2026 projections show continued growth at 12-15%. We are investing in AI capabilities and international expansion.

Risk Factors
Market volatility and supply chain challenges remain key risks. We are diversifying our supplier base to mitigate supply chain issues.

Strategic Initiatives
Investment in AI and machine learning capabilities. Expansion into new geographic markets. Product line extensions planned for Q2 2026.
"""
        },
        {
            "filename": "engineering_best_practices.pdf",
            "title": "Engineering Best Practices Guide",
            "department": "engineering",
            "sensitivity": "internal",
            "role": "employee",
            "tags": ["engineering", "best-practices", "development"],
            "content": """Engineering Best Practices Guide

This guide outlines coding standards and development practices for our engineering teams.

Chapter 1: Code Review
All code must be reviewed by at least two engineers before merging. Reviews should focus on correctness, readability, and performance.

Chapter 2: Testing
Maintain at least 80% code coverage with unit and integration tests. End-to-end tests are required for critical user flows.

Chapter 3: Documentation
All public APIs must have comprehensive documentation. Internal code should include clear comments for complex logic.

Chapter 4: Version Control
Use Git with feature branches and meaningful commit messages. Follow conventional commits format for automated changelog generation.

Chapter 5: CI/CD
All code changes must pass continuous integration tests. Deployments are automated with blue-green deployment strategy.

Chapter 6: Security
Follow OWASP guidelines for secure coding practices. Security scanning is integrated into the CI/CD pipeline.

Chapter 7: Performance
Optimize for readability first, performance second. Use profiling tools to identify actual bottlenecks before optimizing.

Chapter 8: Monitoring
All production services must have proper monitoring and alerting. We use structured logging and distributed tracing.

Chapter 9: Database Best Practices
Use parameterized queries to prevent SQL injection. Index frequently queried columns. Monitor slow query logs.

Chapter 10: API Design
Follow REST principles for HTTP APIs. Use consistent naming conventions. Version all public APIs.
"""
        },
        {
            "filename": "compensation_policy.pdf",
            "title": "Employee Compensation Policy",
            "department": "hr",
            "sensitivity": "confidential",
            "role": "manager",
            "tags": ["compensation", "salary", "benefits"],
            "content": """Employee Compensation Policy - Confidential

This document outlines our compensation philosophy and salary structures.

Section 1: Compensation Philosophy
We offer competitive market-based compensation to attract and retain top talent. Our packages include base salary, bonuses, and equity.

Section 2: Salary Bands
Each role has defined minimum, midpoint, and maximum salary levels. Bands are reviewed annually based on market data.

Section 3: Performance Bonuses
Annual bonuses range from 5% to 20% of base salary. Bonuses are tied to individual and company performance.

Section 4: Equity Compensation
Senior employees receive stock option grants. Vesting schedules are typically 4 years with a 1-year cliff.

Section 5: Benefits Package
Comprehensive health, dental, and vision insurance. HSA and FSA accounts available. Life and disability insurance included.

Section 6: Retirement Plan
401(k) with up to 5% company match. Vesting begins immediately. Financial planning resources available.

Section 7: Pay Reviews
Salary reviews are conducted annually in March. Off-cycle adjustments may occur for promotions or market changes.

Section 8: Promotion Process
Promotions are based on performance and impact. Process includes manager nomination, peer review, and committee approval.

Section 9: Severance Policy
Standard severance is 2 weeks per year of service. Minimum 4 weeks, maximum 26 weeks. Health benefits continue during severance period.

Section 10: Compliance
All compensation practices comply with federal and state laws. Pay equity audits are conducted annually.
"""
        },
    ]

    for doc_data in documents:
        filepath = output_dir / doc_data["filename"]
        filepath.write_text(doc_data["content"], encoding="utf-8")
        print(f"Generated: {filepath.name}")

    return documents


def generate_csvs(output_dir: Path):
    """Generate sample CSV database files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Employees CSV
    employees = []
    departments = ["hr", "finance", "engineering", "operations"]
    for i in range(50):
        employees.append({
            "employee_id": f"EMP{1000 + i}",
            "name": f"Employee {i+1}",
            "department": random.choice(departments),
            "role": random.choice(["junior", "senior", "lead", "manager"]),
            "salary": random.randint(50000, 200000),
            "hire_date": (datetime.now() - timedelta(days=random.randint(30, 3000))).strftime("%Y-%m-%d"),
            "performance_score": round(random.uniform(2.5, 5.0), 2)
        })

    with open(output_dir / "employees.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=employees[0].keys())
        writer.writeheader()
        writer.writerows(employees)
    print(f"Generated: employees.csv ({len(employees)} rows)")

    # Sales CSV
    sales = []
    products = ["Product A", "Product B", "Product C", "Product D"]
    regions = ["North", "South", "East", "West"]
    for i in range(100):
        sales.append({
            "transaction_id": f"TXN{5000 + i}",
            "date": (datetime.now() - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d"),
            "product": random.choice(products),
            "region": random.choice(regions),
            "amount": round(random.uniform(100, 10000), 2),
            "quantity": random.randint(1, 50),
            "customer_id": f"CUST{random.randint(100, 999)}"
        })

    with open(output_dir / "sales.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=sales[0].keys())
        writer.writeheader()
        writer.writerows(sales)
    print(f"Generated: sales.csv ({len(sales)} rows)")

    # Budget CSV
    budget = []
    categories = ["Marketing", "R&D", "Operations", "HR", "IT", "Sales"]
    for i in range(30):
        budget.append({
            "budget_id": f"BUDG{2000 + i}",
            "department": random.choice(departments),
            "category": random.choice(categories),
            "allocated": round(random.uniform(10000, 500000), 2),
            "spent": round(random.uniform(5000, 450000), 2),
            "fiscal_year": "2026",
            "quarter": random.choice(["Q1", "Q2", "Q3", "Q4"])
        })

    with open(output_dir / "budget.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=budget[0].keys())
        writer.writeheader()
        writer.writerows(budget)
    print(f"Generated: budget.csv ({len(budget)} rows)")


def generate_sql(output_dir: Path):
    """Generate sample SQL schema file."""
    output_dir.mkdir(parents=True, exist_ok=True)

    sql_content = """-- Enterprise Database Schema
-- This file contains the database schema for the enterprise system

CREATE TABLE departments (
    department_id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    manager_id INTEGER,
    budget DECIMAL(15, 2),
    location VARCHAR(100)
);

CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    department_id INTEGER,
    hire_date DATE,
    salary DECIMAL(10, 2),
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

CREATE TABLE projects (
    project_id INTEGER PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    start_date DATE,
    end_date DATE,
    budget DECIMAL(15, 2),
    status VARCHAR(20)
);

CREATE TABLE employee_projects (
    employee_id INTEGER,
    project_id INTEGER,
    role VARCHAR(50),
    allocation_percentage DECIMAL(5, 2),
    PRIMARY KEY (employee_id, project_id),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE TABLE performance_reviews (
    review_id INTEGER PRIMARY KEY,
    employee_id INTEGER,
    reviewer_id INTEGER,
    review_date DATE,
    rating INTEGER,
    comments TEXT,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);
"""

    filepath = output_dir / "schema.sql"
    filepath.write_text(sql_content)
    print(f"Generated: schema.sql")


def generate_json_logs(output_dir: Path):
    """Generate sample JSON log files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # System audit logs
    audit_logs = []
    actions = ["login", "logout", "file_access", "data_export", "permission_change", "system_update"]
    users = ["alice", "bob", "carol", "dave", "eve", "frank"]

    for i in range(100):
        audit_logs.append({
            "log_id": f"LOG{i+1:04d}",
            "timestamp": (datetime.now() - timedelta(hours=random.randint(0, 720))).isoformat(),
            "user": random.choice(users),
            "action": random.choice(actions),
            "resource": f"resource_{random.randint(100, 999)}",
            "ip_address": f"192.168.1.{random.randint(1, 255)}",
            "status": random.choice(["success", "failed", "warning"]),
            "details": {
                "session_id": f"sess_{uuid.uuid4().hex[:8]}",
                "user_agent": "Mozilla/5.0"
            }
        })

    with open(output_dir / "audit_logs.json", 'w', encoding='utf-8') as f:
        json.dump(audit_logs, f, indent=2)
    print(f"Generated: audit_logs.json ({len(audit_logs)} entries)")

    # System alerts
    alerts = []
    alert_types = ["security", "performance", "error", "warning", "info"]
    severities = ["low", "medium", "high", "critical"]

    for i in range(50):
        alerts.append({
            "alert_id": f"ALERT{i+1:04d}",
            "timestamp": (datetime.now() - timedelta(hours=random.randint(0, 168))).isoformat(),
            "type": random.choice(alert_types),
            "severity": random.choice(severities),
            "service": random.choice(["api-gateway", "auth-service", "database", "cache", "queue"]),
            "message": f"Alert condition detected in {random.choice(['login', 'query', 'transaction', 'backup'])} operation",
            "affected_users": random.randint(0, 100),
            "status": random.choice(["open", "investigating", "resolved"])
        })

    with open(output_dir / "system_alerts.json", 'w', encoding='utf-8') as f:
        json.dump(alerts, f, indent=2)
    print(f"Generated: system_alerts.json ({len(alerts)} entries)")

    # Application logs
    app_logs = []
    for i in range(75):
        app_logs.append({
            "log_id": f"APP{i+1:04d}",
            "timestamp": (datetime.now() - timedelta(minutes=random.randint(0, 10080))).isoformat(),
            "level": random.choice(["DEBUG", "INFO", "WARN", "ERROR"]),
            "logger": random.choice(["api.handler", "db.connection", "auth.service", "cache.manager"]),
            "message": random.choice([
                "Request processed successfully",
                "Database query executed",
                "User authentication completed",
                "Cache miss occurred",
                "Failed to connect to external service"
            ]),
            "duration_ms": random.randint(1, 500),
            "request_id": f"req_{uuid.uuid4().hex[:12]}",
            "user_id": random.choice(users) if random.random() > 0.3 else None
        })

    with open(output_dir / "application_logs.json", 'w', encoding='utf-8') as f:
        json.dump(app_logs, f, indent=2)
    print(f"Generated: application_logs.json ({len(app_logs)} entries)")


def main():
    """Generate all synthetic data."""
    from src.config import ENTERPRISE_DATA_DIR

    print("=" * 60)
    print("Generating Synthetic Enterprise Data")
    print("=" * 60)

    print("\n[1/3] Generating documents...")
    generate_documents(ENTERPRISE_DATA_DIR / "pdfs")

    print("\n[2/3] Generating database files...")
    generate_csvs(ENTERPRISE_DATA_DIR / "databases")
    generate_sql(ENTERPRISE_DATA_DIR / "databases")

    print("\n[3/3] Generating JSON logs...")
    generate_json_logs(ENTERPRISE_DATA_DIR / "json_logs")

    print("\n" + "=" * 60)
    print("Data generation complete!")
    print(f"Location: {ENTERPRISE_DATA_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
