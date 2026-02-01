import os
import warnings
# Suppress LangChain deprecation warnings to keep logs clean
warnings.filterwarnings("ignore", category=UserWarning, module="langchain")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Configuration
PERSIST_DIRECTORY = os.path.join(os.path.dirname(__file__), "chroma_db")
EMBEDDING_MODEL = "nomic-embed-text"

class KnowledgeBase:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(
            base_url="http://localhost:11434",
            model=EMBEDDING_MODEL
        )
        self.vector_store = Chroma(
            persist_directory=PERSIST_DIRECTORY,
            embedding_function=self.embeddings
        )
        self.n_results = 3 # Default depth

    def set_depth(self, k: int):
        self.n_results = k
        return f"RAG search depth set to {k}"

    def clear_index(self):
        try:
            self.vector_store.delete_collection()
            # Re-init
            self.vector_store = Chroma(
                persist_directory=PERSIST_DIRECTORY,
                embedding_function=self.embeddings
            )
            return True, "Knowledge Base cleared."
        except Exception as e:
            return False, f"Error clearing KB: {str(e)}"

    def ingest_manual(self, pdf_path: str):
        """
        Loads a PDF manual, splits it into chunks, and stores it in the vector DB.
        """
        if not os.path.exists(pdf_path):
            return False, "File not found."

        try:
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            
            # Split documents into smaller chunks for better retrieval
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            chunks = text_splitter.split_documents(documents)
            
            # Add to vector store
            self.vector_store.add_documents(chunks)
            self.vector_store.persist()
            
            return True, f"Successfully assimilated {len(chunks)} chunks from manual."
        except Exception as e:
            return False, f"Error ingesting manual: {str(e)}"

    def search_manuals(self, query: str, k=None):
        """
        Retrieves top-k relevant chunks for a given query.
        """
        if k is None: k = self.n_results
        try:
            results = self.vector_store.similarity_search(query, k=k)
            return [doc.page_content for doc in results]
        except Exception as e:
            print(f"RAG Search Error: {e}")
            return []

# Singleton instance
kb = KnowledgeBase()
