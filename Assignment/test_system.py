"""
Simple test script to verify system structure without full dependencies.
"""
import sys
import os
from pathlib import Path
import traceback

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Use ASCII-safe characters
TICK = "[OK]"
CROSS = "[FAIL]"
WARN = "[WARN]"

print("=" * 70)
print("Enterprise RAG System - Structure Test")
print("=" * 70)

# Test 1: Check file structure
print("\n[1/3] Checking file structure...")

required_files = [
    "src/__init__.py",
    "src/config.py",
    "src/models/document.py",
    "src/models/user.py",
    "src/models/query.py",
    "src/utils/embeddings.py",
    "src/utils/text_splitter.py",
    "src/utils/audit_logger.py",
    "src/data_sources/pdf_processor.py",
    "src/data_sources/database_handler.py",
    "src/data_sources/json_processor.py",
    "src/core/rag_pipeline.py",
    "src/core/retriever.py",
    "src/core/generator.py",
    "src/core/rbac_enforcer.py",
    "ui/streamlit_app.py",
    "cli.py",
    "ingest_data.py",
    "generate_data.py",
    "requirements.txt"
]

missing_files = []
for file_path in required_files:
    if Path(file_path).exists():
        print(f"  {TICK} {file_path}")
    else:
        print(f"  {CROSS} {file_path}")
        missing_files.append(file_path)

if missing_files:
    print(f"\nError: Missing {len(missing_files)} files")
    sys.exit(1)

print(f"\nAll {len(required_files)} files present!")

# Test 2: Check import structure (without loading models)
print("\n[2/3] Testing import structure...")

try:
    # Test config
    from src.config import (
        USERS_DB, DEPARTMENTS, ROLES,
        get_accessible_departments
    )
    print(f"  {TICK} Config imported successfully")
    print(f"    - {len(USERS_DB)} users in database")
    print(f"    - {len(ROLES)} roles: {ROLES}")
    print(f"    - {len(DEPARTMENTS)} departments: {DEPARTMENTS}")
except Exception as e:
    print(f"  {CROSS} Config import failed: {e}")
    traceback.print_exc()

try:
    # Test text splitter
    from src.utils.text_splitter import TextSplitter
    splitter = TextSplitter(chunk_size=10, chunk_overlap=2)
    chunks = splitter.split_text("This is a test sentence that will be split into smaller chunks.")
    print(f"  {TICK} Text splitter works - generated {len(chunks)} chunks")
except Exception as e:
    print(f"  {CROSS} Text splitter failed: {e}")
    traceback.print_exc()

try:
    # Test RBAC logic
    from src.core.rbac_enforcer import RBACEnforcer
    rbac = RBACEnforcer()
    users = rbac.list_users()
    print(f"  {TICK} RBAC enforcer loaded - {len(users)} users")

    # Test user retrieval
    alice = rbac.get_user("alice")
    print(f"  {TICK} Retrieved user: {alice.full_name} ({alice.role_name}/{alice.department_name})")

    # Test access permissions
    accessible = rbac.get_accessible_sources(alice)
    print(f"  {TICK} Alice's access: {accessible['departments']}")
except Exception as e:
    print(f"  {CROSS} RBAC enforcer failed: {e}")
    traceback.print_exc()

# Test 3: Generate synthetic data (if reportlab available)
print("\n[3/3] Testing synthetic data generation...")

try:
    import reportlab
    print(f"  {TICK} ReportLab available for PDF generation")
except ImportError:
    print(f"  {WARN} ReportLab not available - PDF generation will be skipped")
    print("    (You can install it separately: pip install reportlab)")

try:
    # Test file creation
    test_dir = Path("test_output")
    test_dir.mkdir(exist_ok=True)
    test_file = test_dir / "test.txt"
    test_file.write_text("Test file created successfully")
    print(f"  {TICK} File system access works")
    test_file.unlink()  # Clean up
    test_dir.rmdir()  # Clean up
except Exception as e:
    print(f"  {CROSS} File system test failed: {e}")

print("\n" + "=" * 70)
print("Structure Test Complete!")
print("=" * 70)

# Display usage instructions
print("\n" + "=" * 70)
print("Getting Started")
print("=" * 70)
print("\n1. Install dependencies (if network available):")
print("   py -m pip install -r requirements.txt")
print("\n2. Generate synthetic data:")
print("   python generate_data.py")
print("\n3. Ingest data into the RAG system:")
print("   python ingest_data.py")
print("\n4. Test CLI interface:")
print("   python cli.py --list-users")
print("   python cli.py --query 'What is the vacation policy?' --user alice")
print("\n5. Launch Streamlit UI:")
print("   streamlit run ui/streamlit_app.py")
print("\n6. Test with different users:")
print("   - alice (employee, engineering)")
print("   - bob (manager, finance)")
print("   - carol (manager, hr)")
print("   - dave (admin, operations)")
print("\nNote: First run will download HuggingFace models (~500MB)")
print("=" * 70)