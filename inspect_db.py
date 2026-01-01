import chromadb
db = chromadb.PersistentClient(path="./data/chroma_db")
collection = db.get_collection("latvenergo_v4_stable")
# Get 5 random entries
peek = collection.peek(5)
print(peek['documents']) # See the text chunks
print(peek['metadatas']) # Verify page numbers are there