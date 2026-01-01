import pandas as pd
from engine import get_query_engine

def run_comprehensive_tests():
    query_engine = get_query_engine()
    
    test_cases = [
        # 1. Success Cases (Factual)
        {"type": "Fact-LV", "q": "Kāds bija Latvenergo koncerna EBITDA 2025. gada 9 mēnešos?"},
        {"type": "Fact-EN", "q": "What was the total electricity generation in 9M 2025?"},
        
        # 2. Out-of-Scope (Hallucination Check)
        {"type": "OOS", "q": "Who is the current CEO of Enefit (Estonia)?"},
        
        # 3. Composite Info (Table + Narrative)
        {"type": "Composite", "q": "Kā zemā pietece Daugavā ietekmēja 2025. gada peļņas rādītājus?"},
        
        # 4. Reasoning/Calculation
        {"type": "Logic", "q": "Calculate the EBITDA margin for 9M 2025 based on revenue and EBITDA values in the report."},

        # 5. Other Energy fact
        {"type": "Energy-fact-LV", "q": "Analizē ražošanas un tirdzniecības segmenta ieņēmumu struktūru. Cik liela daļa ir siltumenerģija?"}
    ]

    results = []
    for case in test_cases:
        print(f"\n--- Testing {case['type']}: {case['q']} ---")
        response = query_engine.query(case["q"])
        
        # Inspect Chunks
        print(f"Retrieved {len(response.source_nodes)} chunks.")
        for i, node in enumerate(response.source_nodes):
            print(f"  Chunk {i+1} Preview: {node.node.get_content()[:100]}... [Score: {node.score:.3f}]")
        
        results.append({
            "Query": case["q"],
            "Response": str(response),
            "Top_Score": response.source_nodes[0].score if response.source_nodes else 0
        })

    # Save results to inspect OCR quality later
    pd.DataFrame(results).to_csv("test_results_audit.csv", index=False)
    print("\n Audit Complete. Results saved to test_results_audit.csv")

if __name__ == "__main__":
    run_comprehensive_tests()