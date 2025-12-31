import os
import logging
import json 
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, StorageContext, Settings, PromptTemplate
from llama_index.readers.docling import DoclingReader
from llama_index.node_parser.docling import DoclingNodeParser
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import SimpleDirectoryReader
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
    device="cpu" # Forces Mac to use its own RAM, leaving Linux VRAM for DeepSeek
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

# 3. Custom System Prompt for RAG in Latvian and English
SYSTEM_PROMPT = (
    "You are the Latvenergo Strategic Intelligence Bot. You are a professional energy market analyst.\n"
    "Your goal is to provide precise, data-driven answers based ONLY on the provided context.\n"
    "1. If the answer involves numbers, specify the unit (EUR, GWh, etc.).\n"
    "2. If the data is missing, say you don't have information.\n"
    "3. Respond in the same language as the user (Latvian or English).\n"
    "4. Always output your reasoning process inside <think></think> tags.\n"
    "---------------------\n"
    "CONTEXT INFORMATION:\n{context_str}\n"
    "---------------------\n"
    "QUERY: {query_str}\n"
    "ANSWER:"
)

def clean_metadata(metadata: dict) -> dict:
    """
    ChromaDB only supports flat metadata (str, int, float, bool).
    This function removes or converts nested structures (lists/dicts).
    """
    allowed_types = (str, int, float, bool)
    clean_dict = {}
    for key, value in metadata.items():
        if isinstance(value, allowed_types):
            clean_dict[key] = value
        elif value is None:
            clean_dict[key] = ""
        else:
            # Convert complex types (like doc_items) to string or drop them
            # For this project, dropping 'doc_items' is safest as it's redundant
            if key == "doc_items":
                continue 
            clean_dict[key] = str(value)
    return clean_dict


def initialize_index():
    db = chromadb.PersistentClient(path=CHROMA_PATH)
    # Using a fresh collection name to ensure clean schema
    chroma_collection = db.get_or_create_collection("latvenergo_v4_stable")
    
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
        node_parser = DoclingNodeParser()
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
    
    # Update the prompt template
    base_engine.update_prompts(
        {"response_synthesizer:text_qa_template": PromptTemplate(SYSTEM_PROMPT)}
    )
    
    # Wrap it in HyDE
    advanced_engine = TransformQueryEngine(base_engine, hyde)
    return advanced_engine

