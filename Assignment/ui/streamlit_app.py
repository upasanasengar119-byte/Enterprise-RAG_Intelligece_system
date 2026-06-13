"""
Streamlit UI for the Enterprise RAG Intelligence System.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from src.core.rag_pipeline import RAGPipeline
from src.core.rbac_enforcer import RBACEnforcer
from src.utils.audit_logger import get_audit_logger


# Page configuration
st.set_page_config(
    page_title="Enterprise RAG Intelligence",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .user-info {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .citation-box {
        background-color: #f8f9fa;
        border-left: 3px solid #1f77b4;
        padding: 0.8rem;
        margin: 0.5rem 0;
        border-radius: 0.3rem;
    }
    .metric-box {
        background-color: #e8f4f8;
        padding: 0.5rem;
        border-radius: 0.3rem;
        text-align: center;
    }
    .stAlert {
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'rag_pipeline' not in st.session_state:
        st.session_state.rag_pipeline = None
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'rbac_enforcer' not in st.session_state:
        st.session_state.rbac_enforcer = RBACEnforcer()
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'system_initialized' not in st.session_state:
        st.session_state.system_initialized = False


def login_section():
    """Display login section in sidebar."""
    st.sidebar.markdown("###  User Login")

    rbac = st.session_state.rbac_enforcer
    users = rbac.list_users()

    # User selection
    user_options = {f"{u['full_name']} ({u['username']}) - {u['role']}/{u['department']}": u['username']
                   for u in users}

    selected = st.sidebar.selectbox(
        "Select User",
        options=list(user_options.keys()),
        index=0
    )

    if st.sidebar.button(" Login", use_container_width=True):
        username = user_options[selected]
        try:
            user = rbac.get_user(username)
            st.session_state.current_user = user
            st.sidebar.success(f" Logged in as {user.full_name}")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Login failed: {e}")


def user_info_panel():
    """Display user information in sidebar."""
    if st.session_state.current_user:
        user = st.session_state.current_user

        st.sidebar.markdown("---")
        st.sidebar.markdown("###  Current User")

        st.sidebar.markdown(f"""
        <div class="user-info">
            <b>{user.full_name}</b><br>
            <small>@{user.username}</small><br>
            <small>{user.email}</small>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.markdown(f'<div class="metric-box"><b>Role</b><br>{user.role_name.title()}</div>',
                       unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-box"><b>Dept</b><br>{user.department_name.title()}</div>',
                       unsafe_allow_html=True)

        # Show accessible resources
        accessible = rbac := st.session_state.rbac_enforcer.get_accessible_sources(user)
        with st.sidebar.expander(" Access Permissions"):
            st.write("**Departments:**")
            for dept in accessible['departments']:
                st.write(f"- {dept}")
            st.write("**Sensitivity Levels:**")
            for sens in accessible['sensitivity_levels']:
                st.write(f"- {sens}")

        st.sidebar.markdown(f"**Queries:** {user.query_count}")

        if st.sidebar.button(" Logout", use_container_width=True):
            st.session_state.current_user = None
            st.session_state.chat_history = []
            st.rerun()


def initialize_rag_system():
    """Initialize the RAG system."""
    if not st.session_state.system_initialized:
        with st.spinner(" Initializing RAG system... This may take a moment..."):
            try:
                st.session_state.rag_pipeline = RAGPipeline()
                st.session_state.system_initialized = True
                return True
            except Exception as e:
                st.error(f"Failed to initialize RAG system: {e}")
                return False
    return True


def display_chat_message(role, content, metadata=None):
    """Display a chat message with optional metadata."""
    with st.chat_message(role):
        st.markdown(content)
        if metadata:
            cols = st.columns(4)
            with cols[0]:
                st.caption(f" Confidence: {metadata.get('confidence', 0):.2f}")
            with cols[1]:
                st.caption(f" Time: {metadata.get('time', 0):.2f}s")
            with cols[2]:
                st.caption(f" Sources: {metadata.get('sources', 0)}")
            with cols[3]:
                st.caption(f" Type: {metadata.get('query_type', 'N/A')}")


def main():
    """Main application."""
    initialize_session_state()

    # Header
    st.markdown('<div class="main-header"> Enterprise RAG Intelligence</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Secure, Context-Aware Retrieval-Augmented Generation with RBAC</div>',
                unsafe_allow_html=True)

    # Sidebar - Login
    login_section()
    user_info_panel()

    # Check if user is logged in
    if not st.session_state.current_user:
        st.info(" Please log in from the sidebar to start querying the system.")
        st.markdown("""
        ### Welcome to the Enterprise RAG System

        This system provides:
        - ** Multi-format data search** across PDFs, databases, and JSON logs
        - ** Role-based access control** with department and sensitivity filtering
        - ** AI-powered answers** with source citations
        - ** Audit logging** for all queries and access attempts

        ### Getting Started:
        1. Select a user from the sidebar
        2. Click "Login" to authenticate
        3. Start asking questions about your enterprise data
        """)
        return

    # Initialize RAG system
    if not initialize_rag_system():
        return

    # Main chat interface
    st.markdown("---")

    # Display chat history
    for message in st.session_state.chat_history:
        display_chat_message(
            role=message['role'],
            content=message['content'],
            metadata=message.get('metadata')
        )

    # Chat input
    user_input = st.chat_input("Ask a question about your enterprise data...")

    if user_input:
        user = st.session_state.current_user

        # Add user message to history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input
        })

        # Display user message
        display_chat_message('user', user_input)

        # Process query
        with st.spinner(" Searching and generating answer..."):
            try:
                result = st.session_state.rag_pipeline.query(
                    query_text=user_input,
                    user=user,
                    top_k=5
                )

                # Display answer
                display_chat_message('assistant', result.answer)

                # Display citations in expandable section
                if result.citations:
                    with st.expander(f" View {len(result.citations)} Source Citations"):
                        for i, citation in enumerate(result.citations, 1):
                            st.markdown(f"""
                            <div class="citation-box">
                                <b>Source {i}:</b> {citation}
                            </div>
                            """, unsafe_allow_html=True)

                # Display retrieved documents
                if result.retrieved_documents:
                    with st.expander(f" View {len(result.retrieved_documents)} Retrieved Documents"):
                        for i, doc in enumerate(result.retrieved_documents, 1):
                            st.markdown(f"""
                            **Document {i}: {doc['title']}**
                            - Department: `{doc['department']}`
                            - Sensitivity: `{doc['sensitivity']}`
                            - Relevance Score: `{doc['score']:.3f}`
                            - Preview: {doc['text_preview']}
                            """)

                # Add to chat history with metadata
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': result.answer,
                    'metadata': {
                        'confidence': result.confidence,
                        'time': result.processing_time,
                        'sources': len(result.retrieved_documents),
                        'query_type': result.metadata.get('query_type', 'N/A')
                    }
                })

            except Exception as e:
                error_msg = f" Error processing query: {e}"
                st.error(error_msg)
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': error_msg
                })


if __name__ == "__main__":
    main()
