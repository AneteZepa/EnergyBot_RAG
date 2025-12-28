import os
import logging
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, StorageContext, Settings, PromptTemplate
from llama_index.readers.docling import DoclingReader
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import SimpleDirectoryReader
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
    model="deepseek-r1:70b", 
    base_url=os.getenv("OLLAMA_BASE_URL"),
    request_timeout=600.0,
    # This is critical: context_window limits how much memory the KV cache uses
    additional_kwargs={
        "num_ctx": 4096,  # Reduces VRAM usage by limiting the 'memory' of the current chat
        "temperature": 0.1
    }
)

# Custom System Prompt to guide the "Thinking Partner"
SYSTEM_PROMPT = (
    "You are the Latvenergo Strategic Intelligence Bot. You provide expert analysis based on financial reports.\n"
    "Context information is below. Answer the question using only the context provided.\n"
    "If the answer is not in the context, state that you do not have enough information.\n"
    "Respond in the language the user uses (Latvian or English).\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "Query: {query_str}\n"
    "Answer:"
)

def initialize_index():
    # 2. VECTOR DATABASE SETUP
    db = chromadb.PersistentClient(path=CHROMA_PATH)
    chroma_collection = db.get_or_create_collection("latvenergo_2025")
    
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    if chroma_collection.count() == 0:
        logger.info("Indexing Latvenergo reports with Docling...")
        
        # Use Docling for high-fidelity table extraction
        file_extractor = {".pdf": DoclingReader()}
        reader = SimpleDirectoryReader(input_dir=DATA_PATH, file_extractor=file_extractor)
        
        documents = reader.load_data()
        index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
        logger.info("Indexing complete.")
    else:
        logger.info("Loading existing index from persistent storage.")
        index = VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_context)
    
    return index

def get_query_engine():
    index = initialize_index()
    query_engine = index.as_query_engine(
        streaming=True, 
        similarity_top_k=5 # Increased context for complex financial questions
    )
    
    # Apply the custom prompt
    query_engine.update_prompts(
        {"response_synthesizer:text_qa_template": PromptTemplate(SYSTEM_PROMPT)}
    )
    return query_engine