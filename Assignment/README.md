# Enterprise RAG Intelligence System

A secure, context-aware Retrieval-Augmented Generation (RAG) system with strict role-based access control (RBAC) for navigating large-scale enterprise data silos.

## Features

- **Multi-format Data Ingestion**: PDFs, CSV, SQL, JSON logs
- **Role-Based Access Control**: 3 roles x 5 departments x 4 sensitivity levels
- **Semantic Search**: TF-IDF based embeddings (or HuggingFace sentence-transformers if available)
- **Intelligent Routing**: Query-aware routing to relevant data sources
- **Source Attribution**: Every response includes citations
- **Audit Logging**: All queries and access attempts logged
- **CLI + Streamlit UI**: Two interfaces for different use cases

## Architecture

```
src/
  config.py              # RBAC policies, model config
  models/                # Document, User, Query data models
  utils/                 # Embeddings, text splitter, audit logger
  data_sources/          # PDF, database, JSON processors
  core/                  # RAG pipeline, retriever, generator, RBAC
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate Synthetic Data

```bash
python generate_data.py
```

### 3. Ingest Data

```bash
python ingest_data.py
```

### 4. Run CLI

```bash
# List users
python cli.py --list-users

# Query as a user
python cli.py --query "What is the vacation policy?" --user alice

# Interactive mode
python cli.py --interactive --user bob
```

### 5. Launch UI

```bash
streamlit run ui/streamlit_app.py
```

## Test Users

| Username | Role | Department |
|----------|------|------------|
| alice | employee | engineering |
| bob | manager | finance |
| carol | manager | hr |
| dave | admin | operations |
| eve | employee | hr |
| frank | employee | finance |

## RBAC Rules

- **employee**: public + internal sensitivity, own department
- **manager**: public + internal + confidential, all departments
- **admin**: all sensitivity levels, all departments

## License


