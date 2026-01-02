import time
import pandas as pd
from engine import get_query_engine
from tqdm import tqdm

# A "Golden Dataset" of questions and expected keywords/facts
TEST_DATASET = [
    {
        "query": "Kāds bija Latvenergo koncerna EBITDA 2025. gada 9 mēnešos?",
        "expected_fact": "350,2",
        "expected_source": "1_Latvenergo_9M_2025_LAT.pdf"
    },
    {
        "query": "What was the total electricity generation in 9M 2025?",
        "expected_fact": "3512", # or 3,5 TWh
        "expected_source": "1_Latvenergo_9M_2025_LAT.pdf"
    },
    {
        "query": "Kāda ir Latvenergo siltumenerģijas ieņēmumu daļa?",
        "expected_fact": "8", # 8% or 8 %
        "expected_source": "1_Latvenergo_9M_2025_LAT.pdf"
    },
    {
        "query": "Tell me about average USA household energy expenditure.",
        "expected_fact": "cannot find", # Expecting a negative response
        "expected_source": "N/A" # No source expected
    }
]

def run_benchmark():
    print("Starting RAG Benchmark...")
    print("Initializing Engine (CPU/MPS)...")
    
    # Initialize engine once
    query_engine = get_query_engine()
    
    results = []
    
    for case in tqdm(TEST_DATASET, desc="Running Test Cases"):
        start_time = time.time()
        
        # Run Query
        response = query_engine.query(case["query"])
        duration = time.time() - start_time
        
        response_text = str(response)
        
        # 1. Check Retrieval Accuracy (Did we find the right file?)
        retrieved_files = [node.node.metadata.get("file_name", "") for node in response.source_nodes]
        hit_rate = 1 if any(case["expected_source"] in f for f in retrieved_files) else 0
        if case["expected_source"] == "N/A" and not retrieved_files:
            hit_rate = 1 # Correctly found nothing for out-of-scope
            
        # 2. Check Answer Fidelity (Did it contain the key fact?)
        # Simple string matching for now (in prod, use LLM-as-a-Judge)
        fact_check = 1 if case["expected_fact"] in response_text else 0
        
        results.append({
            "Query": case["query"],
            "Latency (s)": round(duration, 2),
            "Retrieval Hit": hit_rate,
            "Fact Check": fact_check,
            "Response Preview": response_text[:100].replace("\n", " ") + "..."
        })

    # Summary Metrics
    df = pd.DataFrame(results)
    print("\nBenchmark Results:")
    print(df.to_markdown(index=False))
    
    avg_latency = df["Latency (s)"].mean()
    accuracy = df["Fact Check"].mean() * 100
    
    print(f"\nAverage Latency: {avg_latency:.2f}s")
    print(f"Fact Accuracy: {accuracy:.1f}%")
    
    # Save to CSV for the interview
    df.to_csv("benchmark_results_final.csv", index=False)

if __name__ == "__main__":
    run_benchmark()