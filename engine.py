import os
import logging
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, StorageContext, Settings, PromptTemplate, SimpleDirectoryReader
from llama_index.readers.docling import DoclingReader
from llama_index.node_parser.docling import DoclingNodeParser
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.indices.query.query_transform import HyDEQueryTransform
from llama_index.core.query_engine import TransformQueryEngine
from llama_index.core.postprocessor import LLMRerank
import chromadb

load_dotenv()

# Setup logging for MLOps visibility
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DATA_PATH = "./docs"
CHROMA_PATH = "./data/chroma_db"

# 1. MODEL CONFIGURATION
# Using BGE-M3 for multilingual (Latvian) retrieval
# 1. Force the Embedding model to stay on the Mac CPU to save Linux GPU VRAM
Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-m3",
    device="cpu",
    embed_batch_size=4 # Forces Mac to use its own RAM and mps, leaving Linux VRAM for DeepSeek
)

# 2. Configure Ollama to handle the context more efficiently
Settings.llm = Ollama(
    model="qwen3-coder:30b", 
    base_url=os.getenv("OLLAMA_BASE_URL"),
    request_timeout=600.0,
    # This is critical: context_window limits how much memory the KV cache uses
    additional_kwargs={
        "num_ctx": 8192,     # To ensure everything fits in context
        "temperature": 0.1   # Low temperature for accurate financial data
    }
)

def clean_metadata(metadata: dict) -> dict:
    """Enhanced metadata extraction for Docling structures."""
    allowed_types = (str, int, float, bool)
    clean_dict = {}
    
    # Docling stores page info in 'page_no' or 'dl_meta/page_no'
    page = metadata.get("page_no") or metadata.get("dl_meta", {}).get("page_no")
    
    # If it's a list (some parsers do this), take the first element
    if isinstance(page, list) and len(page) > 0:
        page = page[0]
        
    clean_dict["page_no"] = int(page) if page else "N/A"
    clean_dict["file_name"] = metadata.get("file_name", "Unknown")

    for key, value in metadata.items():
        if key in clean_dict: continue
        if isinstance(value, allowed_types):
            clean_dict[key] = value
        else:
            # Flatten everything else to string for ChromaDB
            clean_dict[key] = str(value)
    return clean_dict


def initialize_index():
    db = chromadb.PersistentClient(path=CHROMA_PATH)

    chroma_collection = db.get_or_create_collection("latvenergo_v6_final")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    if chroma_collection.count() == 0:
        print("Indeksēju Latvenergo pārskatus (tas var aizņemt dažas minūtes)...")
        
        # 1. Load data
        reader = DoclingReader(export_type=DoclingReader.ExportType.JSON)
        file_extractor = {".pdf": reader}
        dir_reader = SimpleDirectoryReader(input_dir=DATA_PATH, file_extractor=file_extractor)
        documents = dir_reader.load_data()
        
        # 2. Parse into nodes
        node_parser = DoclingNodeParser(
            # These settings help keep related strategic paragraphs together
            chunk_size=1024, 
            chunk_overlap=200 
        )
        nodes = node_parser.get_nodes_from_documents(documents)
        
        # 3. CLEAN METADATA (The Fix)
        for node in nodes:
            node.metadata = clean_metadata(node.metadata)
        
        # 4. Create index
        index = VectorStoreIndex(nodes, storage_context=storage_context)
        print("Indeksēšana pabeigta!")
    else:
        print("Ielādēju esošo indeksu no ChromaDB.")
        index = VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_context)
    
    return index

def get_query_engine():
    # 3. QUERY ENGINE SETUP WITH HYDE AND RERANKING
    """
    Returns the advanced HyDE + Reranking engine for the UI.
    """
    index = initialize_index()
    
    # Reranker: Filters the best chunks from the top 20
    reranker = LLMRerank(choice_batch_size=5, top_n=5)
    
    # HyDE: Generates a hypothetical 'ideal' answer to boost retrieval
    hyde = HyDEQueryTransform(include_original=True)
    
    # Base Engine with System Prompt
    base_engine = index.as_query_engine(
        similarity_top_k=20, 
        node_postprocessors=[reranker],
        streaming=True
    )
    
    # SYSTEM PROMPT: Enforce <thinking> tags and polite refusals
    qa_prompt = PromptTemplate(
        "You are a Latvenergo Strategic Analyst. Answer using ONLY the provided context.\n"
        "1. If the information is not in the context, output ONLY: 'I cannot find information about this in the provided Latvenergo reports.'\n"
        "2. You MUST enclose your internal reasoning inside <thinking> tags.\n"
        "3. Respond in the same language as the question.\n"
        "---------------------\n"
        "Context:\n{context_str}\n"
        "---------------------\n"
        "Query: {query_str}\n"
        "Answer:"
    )
    
    base_engine.update_prompts({"response_synthesizer:text_qa_template": qa_prompt})
    
    return TransformQueryEngine(base_engine, hyde)
    
    # Wrap it in HyDE
    advanced_engine = TransformQueryEngine(base_engine, hyde)
    return advanced_engine

