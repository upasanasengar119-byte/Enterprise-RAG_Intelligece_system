"""
Command-line interface for the Enterprise RAG system.
"""
import argparse
import sys
from pathlib import Path
from typing import List

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.core.rag_pipeline import RAGPipeline
from src.core.rbac_enforcer import RBACEnforcer
from src.utils.audit_logger import get_audit_logger


def print_banner():
    """Print CLI banner."""
    banner = """
================================================================
        Enterprise RAG Intelligence System - CLI
        Secure, Context-Aware, Role-Based Access Control
================================================================
    """
    print(banner)


def list_users():
    """List all available users."""
    rbac = RBACEnforcer()
    users = rbac.list_users()

    print("\n" + "=" * 70)
    print("Available Users")
    print("=" * 70)
    print(f"{'Username':<12} {'Full Name':<20} {'Role':<10} {'Department':<12}")
    print("-" * 70)
    for user in users:
        print(f"{user['username']:<12} {user['full_name']:<20} "
              f"{user['role']:<10} {user['department']:<12}")
    print()


def query_system(args):
    """Query the RAG system."""
    print_banner()

    # Get user
    rbac = RBACEnforcer()
    try:
        user = rbac.get_user(args.user)
    except ValueError as e:
        print(f"Error: {e}")
        print("\nAvailable users:")
        list_users()
        return

    print(f"\nUser: {user.full_name} ({user.username})")
    print(f"Role: {user.role_name} | Department: {user.department_name}")
    print(f"Query: {args.query}\n")

    # Initialize RAG pipeline
    print("Initializing RAG pipeline...")
    try:
        rag = RAGPipeline()
    except Exception as e:
        print(f"Error initializing RAG: {e}")
        return

    # Process query
    print("Processing query...\n")
    try:
        result = rag.query(
            query_text=args.query,
            user=user,
            top_k=args.top_k,
            require_citations=not args.no_citations
        )

        # Display results
        print("=" * 70)
        print("ANSWER")
        print("=" * 70)
        print(result.answer)
        print()

        if not args.no_citations and result.citations:
            print("=" * 70)
            print("CITATIONS")
            print("=" * 70)
            for i, citation in enumerate(result.citations, 1):
                print(f"{i}. {citation}")
            print()

        print("=" * 70)
        print("METADATA")
        print("=" * 70)
        print(f"Confidence: {result.confidence}")
        print(f"Processing time: {result.processing_time:.2f}s")
        print(f"Query type: {result.metadata.get('query_type', 'N/A')}")
        print(f"Target sources: {', '.join(result.metadata.get('target_sources', []))}")
        print(f"Retrieved: {result.metadata.get('num_results', 0)} documents")
        print()

    except Exception as e:
        print(f"Error processing query: {e}")
        import traceback
        traceback.print_exc()


def interactive_mode(args):
    """Run in interactive mode."""
    print_banner()

    # Get user
    rbac = RBACEnforcer()
    try:
        user = rbac.get_user(args.user)
    except ValueError as e:
        print(f"Error: {e}")
        print("\nAvailable users:")
        list_users()
        return

    print(f"\nLogged in as: {user.full_name} ({user.username})")
    print(f"Role: {user.role_name} | Department: {user.department_name}")
    print(f"\nAccessible:")
    accessible = rbac.get_accessible_sources(user)
    print(f"  Departments: {', '.join(accessible['departments'])}")
    print(f"  Sensitivity levels: {', '.join(accessible['sensitivity_levels'])}")
    print("\nType 'quit' or 'exit' to end session.")
    print("Type 'help' for available commands.\n")

    # Initialize RAG pipeline
    print("Initializing RAG pipeline...")
    try:
        rag = RAGPipeline()
    except Exception as e:
        print(f"Error initializing RAG: {e}")
        return

    print("Ready!\n")

    while True:
        try:
            query_text = input(f"[{user.username}] > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not query_text:
            continue

        if query_text.lower() in ['quit', 'exit']:
            print("Goodbye!")
            break

        if query_text.lower() == 'help':
            print("\nAvailable commands:")
            print("  <query>     - Ask a question")
            print("  whoami      - Show current user info")
            print("  stats       - Show system statistics")
            print("  users       - List all users")
            print("  help        - Show this help")
            print("  quit/exit   - Exit the session\n")
            continue

        if query_text.lower() == 'whoami':
            print(f"\nUser: {user.full_name} ({user.username})")
            print(f"Email: {user.email}")
            print(f"Role: {user.role_name}")
            print(f"Department: {user.department_name}")
            print(f"Queries made: {user.query_count}\n")
            continue

        if query_text.lower() == 'stats':
            try:
                stats = rag.get_statistics()
                print(f"\nSystem Statistics:")
                print(f"  Vector store: {stats['vector_store']}")
                print(f"  Embedding model: {stats['embedding_model']}")
                print(f"  Generation model: {stats['generator_model']}\n")
            except Exception as e:
                print(f"Error: {e}\n")
            continue

        if query_text.lower() == 'users':
            list_users()
            continue

        # Process query
        try:
            result = rag.query(
                query_text=query_text,
                user=user,
                top_k=args.top_k
            )

            print(f"\n{result.answer}\n")
            print(f"[Confidence: {result.confidence} | "
                  f"Time: {result.processing_time:.2f}s | "
                  f"Sources: {result.metadata.get('num_results', 0)}]\n")

        except Exception as e:
            print(f"Error: {e}\n")


def show_audit_logs(args):
    """Show recent audit logs."""
    audit = get_audit_logger()

    print("\n" + "=" * 70)
    print("Recent Audit Logs")
    print("=" * 70)

    logs = audit.get_recent_logs(limit=args.limit)

    if not logs:
        print("No logs found.")
        return

    for log in logs:
        print(f"\n[{log.get('timestamp', 'N/A')}] {log.get('event_type', 'unknown').upper()}")
        for key, value in log.items():
            if key not in ['timestamp', 'event_type']:
                print(f"  {key}: {value}")

    print()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Enterprise RAG Intelligence System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available users
  python cli.py --list-users

  # Run a single query
  python cli.py --query "What is the vacation policy?" --user alice

  # Start interactive session
  python cli.py --interactive --user bob

  # View audit logs
  python cli.py --audit-logs --limit 20

  # Ingest all data
  python ingest_data.py
        """
    )

    parser.add_argument(
        '--query', '-q',
        type=str,
        help='Single query to process'
    )

    parser.add_argument(
        '--user', '-u',
        type=str,
        help='Username for authentication'
    )

    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Run in interactive mode'
    )

    parser.add_argument(
        '--list-users',
        action='store_true',
        help='List all available users'
    )

    parser.add_argument(
        '--audit-logs',
        action='store_true',
        help='Show recent audit logs'
    )

    parser.add_argument(
        '--top-k', '-k',
        type=int,
        default=5,
        help='Number of results to retrieve (default: 5)'
    )

    parser.add_argument(
        '--no-citations',
        action='store_true',
        help='Disable citations in responses'
    )

    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=20,
        help='Limit for audit logs (default: 20)'
    )

    args = parser.parse_args()

    # Handle different modes
    if args.list_users:
        list_users()
    elif args.audit_logs:
        show_audit_logs(args)
    elif args.query and args.user:
        query_system(args)
    elif args.interactive and args.user:
        interactive_mode(args)
    else:
        parser.print_help()
        print("\n" + "=" * 70)
        print("Quick Start:")
        print("=" * 70)
        print("1. Generate synthetic data:  python generate_data.py")
        print("2. Ingest data:             python ingest_data.py")
        print("3. List users:              python cli.py --list-users")
        print("4. Run a query:             python cli.py --query 'Your question' --user alice")
        print("5. Interactive mode:        python cli.py --interactive --user bob")
        print()


if __name__ == "__main__":
    main()
