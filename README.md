# Latvenergo Strategic Intelligence Bot (RAG)

An AI-powered "Thinking Partner" for energy analysts, designed to synthesize complex financial reports and strategic presentations from Latvenergo. This project demonstrates a production-ready RAG (Retrieval-Augmented Generation) pipeline featuring high-fidelity OCR, a split-compute architecture, and advanced reasoning capabilities.



## Key Features
1. **Layout-Aware PDF Parsing**: Utilizes **Docling** (IBM/Hugging Face) to reconstruct financial tables into Markdown/JSON. Unlike standard OCR, this maintains the structural integrity of complex energy KPI tables.
2. **Split-Compute Architecture**: Orchestration, UI, and Embeddings run on a **Mac M1 Pro (16GB)**, while high-reasoning LLM inference is offloaded to a **Linux Server (128GB RAM)** hosting DeepSeek-R1.
3. **Advanced Retrieval Pipeline**: Implements **HyDE** (Hypothetical Document Embeddings) and **LLM-Reranking** to ensure that technical queries (like segment revenue or EBITDA drivers) map to the most relevant data chunks.
4. **Auditability & Traceability**: Every response includes an expandable "Reasoning Chain" and specific citations with **File Name** and **Page Number** metadata.

## Tech Stack
- **Framework**: LlamaIndex (Data Orchestration)
- **Vector DB**: ChromaDB (Persistent local storage)
- **LLMs**: DeepSeek-R1 70B (Production) / Qwen3-Coder 30B (Testing) via Ollama
- **Embeddings**: BAAI/bge-m3 (Multilingual support for Latvian/English)
- **Parsing**: Docling (JSON export with metadata extraction)
- **Environment**: Managed via `uv` (Faster, deterministic dependency management)

## Setup & Installation

### 1. Prerequisites
- Install `uv`: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Ensure Ollama is running on your inference server.

### 2. Environment Setup
```bash
# Clone the repo
git clone [https://github.com/anetezepa/EnergyBot_RAG.git](https://github.com/anetezepa/EnergyBot_RAG.git)
cd EnergyBot_RAG
```

Create virtual environment and sync dependencies
```bash
uv sync
```
Activate the environment
```bash
source .venv/bin/activate
```
### 3. Configuration
Create a .env file in the root directory:

```
OLLAMA_BASE_URL=http://your-linux-ip:11434
DATA_PATH=./docs
```
### 4. Running the Application

```bash
uv run streamlit run main_ui.py
```

### 4. Running tests

```bash
uv run python test_rag_cases.py
```
or
```bash
uv run python test_rag_connection.py
```

## Data & Benchmarking
The system is currently indexed with Latvenergo Group 9M 2025 data, specifically optimized to track:

- EBITDA shifts and hydroelectricity generation nuances.
- Strategic AER (Renewable Energy) portfolio targets (1,144 MW).
- Cross-referencing 2024 vs 2025 performance drivers.

## Roadmap
RAGAS Integration: Implementation of automated metrics for Faithfulness and Relevancy.

Knowledge Graphs: Transitioning to GraphRAG for better entity-relationship mapping between subsidiaries.

CI/CD: Automated vector store updates via GitHub Actions when new reports are uploaded.

