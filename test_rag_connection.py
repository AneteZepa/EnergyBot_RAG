import os
from engine import initialize_index, Settings
from llama_index.core.base.response.schema import StreamingResponse

def test_rag():
    print("Starting Latvenergo Bot Health Check...\n")

    # 1. Test LLM Connection
    try:
        response = Settings.llm.complete("Say 'Connection Successful'")
        print(f"LLM Connection: {response}")
    except Exception as e:
        print(f"LLM Connection Failed: {e}")
        return

    # 2. Test Indexing & Retrieval
    try:
        index = initialize_index()
        retriever = index.as_retriever(similarity_top_k=2)
        # Testing with a keyword likely to be in Latvenergo reports
        nodes = retriever.retrieve("EBITDA")
        
        if len(nodes) > 0:
            print(f"Retrieval: Found {len(nodes)} relevant context chunks.")
        else:
            print("Retrieval: No context found. Check if PDFs are in /docs.")
    except Exception as e:
        print(f"Indexing Error: {e}")

    # 3. Test Reasoning (The "Thinking" part)
    print("\nTesting Reasoning Engine (Latvian)...")
    query_engine = index.as_query_engine()
    response = query_engine.query("Kāds bija Latvenergo koncerna EBITDA 2025. gada 9 mēnešos?")
    print(f"Bot Response: {response}")

if __name__ == "__main__":
    test_rag()