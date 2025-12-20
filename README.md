# Latvenergo Strategic Intelligence Bot (RAG)
An AI-powered document intelligence system designed to analyze Latvenergo’s financial reports, sustainability targets, and strategic presentations. This project demonstrates a production-ready RAG (Retrieval-Augmented Generation) pipeline with swappable components, multimodal document parsing, and a hybrid local/remote inference architecture.

## Key Features
1. **Multimodal PDF Parsing**: Utilizes the new IBM/Hugging Face "Docling" (or Mistral OCR) to extract structured data from complex energy charts and financial tables in the 2025 interim reports.
2. **Hybrid Distributed Architecture**: Orchestration and UI run on a lightweight client (Mac M1), while heavy LLM inference is offloaded to a dedicated compute server (Ollama on PC).
3. **Swappable LLM Engine**: Built using LlamaIndex Settings, allowing seamless migration from local Ollama models to Azure OpenAI or Google Cloud Vertex AI with zero code changes.
4. **Persistent Knowledge Base**: Uses ChromaDB for efficient vector storage and metadata filtering (e.g., filtering by "Quarterly Report" vs. "Strategy Presentation").

## Tech Stack
1. **Orchestration**: LlamaIndex (Data Framework)
2. **Vector Database**: ChromaDB (Persistent)
3. **Models**: LLM: Llama 3.1 (via Ollama)
4. **Embeddings**: BGE-Small-v1.5 (Local)
5. **OCR/Parsing**: Docling (Hugging Face / IBM)
6. **DevOps**: Docker, Python 3.10+, Git

## System Architecture

## Data & Benchmarking
The system is currently indexed with the following Latvenergo Group data:
1. 2025 9-Month Interim Report: Analyzing the 28% EBITDA shift and the 90% increase in RES investments.
2. 2025 Strategy Presentations: Extracting targets for the 1,144 MW solar/wind portfolio.
3. Quarterly Comparisons: Cross-referencing 3-month, 6-month, and 9-month KPIs to track progress on Baltic synchronization.

## Setup & Installation
1. Clone the Repo:

```Bash

git clone https://github.com/your-username/latvenergo-rag-bot.git
```

2. Environment Setup: Create a .env file to point to your inference server:

```Plaintext

OLLAMA_BASE_URL=http://your-pc-ip:11434
DATA_PATH=./docs
```

3. Run with Docker:

```Bash

docker build -t latvenergo-bot .
docker run -p 8501:8501 latvenergo-bot
```

## Example Query Performance
**User**: "How did the Daugava River inflow affect the 2025 Q3 profit?"

**Bot Response**: "In the first 9 months of 2025, a 20% decrease in electricity generation at the Daugava HPPs (2.2 TWh) due to lower inflow directly contributed to a 37% decrease in profit (EUR 163.9 mln) compared to the same period in 2024."

## Future MLOps Roadmap
**CI/CD Integration**: Automated re-indexing of vector DB when new reports are uploaded via GitHub Actions.

**Cloud Deployment**: Migration of the vector store to Managed Chroma or Azure AI Search.

**Advanced RAG**: Implementing "Reranking" (using Cohere/BGE-Reranker) to further refine financial data accuracy.

## A note on the OCR choice:
Since you mentioned using the new Hugging Face OCR (like Docling or SmolDocling), this is a huge selling point. It shows you aren't just reading text, but you are understanding the layout of the tables. At Latvenergo, where reports are full of energy production tables, this is the difference between a "toy" app and a "business" tool.
