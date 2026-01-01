# Technical Implementation Log & Decisions

This document details the engineering challenges and pivots made during the development of the Latvenergo Strategic Intelligence Bot.



## 1. Document Parsing & Structure Extraction
- **Initial Strategy**: Naive Docling parsing.
- **Pivot**: Switched to **Docling JSON Export with Layout-Aware Parsing**.
- **Reasoning**: Standard text extraction failed on Latvenergo's multi-column financial tables. By leveraging Docling’s JSON output and the `DoclingNodeParser`, we successfully extracted table structures into Markdown and maintained metadata (Page Numbers). This was critical for ensuring the LLM could perform arithmetic on EBITDA figures correctly.

## 2. Advanced Retrieval (HyDE & Reranking)
- **Challenge**: Generic queries like "EBITDA change" often retrieved irrelevant footnotes or legal disclaimers.
- **Solution**: Implemented **HyDE (Hypothetical Document Embeddings)**. 
- **Mechanism**: The system first generates a hypothetical "ideal" answer, which is then used to query the Vector DB. This significantly improved the semantic hit rate for Latvian technical terms.
- **Optimization**: Added **LLMReranking**. The system retrieves the top 20 chunks but utilizes the DeepSeek reasoning model to "score" and select the top 5 most fact-dense chunks, ensuring high precision.

## 3. MLOps: Managing Hardware Constraints
- **Problem**: Encountered `RuntimeError: Invalid buffer size: 26.79 GiB` when attempting to run embeddings on the Mac M1 GPU (MPS).
- **Pivot**: Forced **CPU-only Embedding** for the local Mac client.
- **Reasoning**: While MPS is generally faster, it has strict allocation limits. Given the 16GB RAM limit on the Mac M1, the large Markdown blocks generated from dense tables caused buffer overflows. Moving to CPU allowed the 128GB Linux server's resources to be dedicated entirely to the LLM while the Mac handled a stable, crash-free indexing process.

## 4. Metadata Sanitization & ChromaDB
- **Constraint**: ChromaDB requires "flat" metadata (strings, ints, floats), while Docling produces complex nested JSON.
- **Solution**: Developed a custom **Metadata Sanitizer** within the ingestion pipeline. 
- **Benefit**: This flattens the metadata while preserving the `page_no` and `file_name` keys, enabling a professional "Source Audit" feature in the UI where analysts can verify facts against specific report pages.

## 5. Model Selection & Performance Trade-offs
- **Analysis**: We tested both **DeepSeek-R1 70B** and **qwen3-coder:30b**.
- **Decision**: Prioritized the **qwen3-coder:30b** for validation of RAG chunking quality without server timeouts.
- **Reasoning**: On consumer-grade hardware, **qwen3-coder:30b** provides good enough quality without server timeouts to test RAG and overall system architecture. It is easy to move to **DeepSeek-R1 70B** or **Distilled 32B** version when this part of the work is validated. 