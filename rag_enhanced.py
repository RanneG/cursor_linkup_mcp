"""
Enhanced RAG Workflow with Multiple Document Sources
Optimized for chatbot use cases with better retrieval and response quality
"""

import nest_asyncio
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.settings import Settings
from llama_index.core.workflow import Event, Context, Workflow, StartEvent, StopEvent, step
from llama_index.core.schema import NodeWithScore
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.response_synthesizers import CompactAndRefine
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.retrievers import VectorIndexRetriever
from pathlib import Path
from typing import List, Optional
import logging

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RetrieverEvent(Event):
    """Result of running retrieval"""
    nodes: list[NodeWithScore]
    query: str


class EnhancedRAGWorkflow(Workflow):
    """
    Enhanced RAG workflow optimized for chatbot applications.
    
    Features:
    - Multiple document source support
    - Better chunking for improved retrieval
    - Source citation in responses
    - Configurable retrieval parameters
    - Support for web content, markdown, code files
    """
    
    def __init__(
        self,
        model_name="llama3.2",
        embedding_model="BAAI/bge-small-en-v1.5",
        chunk_size=512,
        chunk_overlap=50,
        similarity_top_k=3,
        response_mode="compact"
    ):
        """
        Initialize enhanced RAG workflow.
        
        Args:
            model_name: Ollama model to use (llama3.2, codellama, etc.)
            embedding_model: HuggingFace embedding model
            chunk_size: Size of text chunks for indexing
            chunk_overlap: Overlap between chunks
            similarity_top_k: Number of similar chunks to retrieve
            response_mode: Response synthesis mode
        """
        super().__init__()
        
        # Initialize LLM and embedding model
        self.llm = Ollama(model=model_name, request_timeout=120.0)
        self.embed_model = HuggingFaceEmbedding(model_name=embedding_model)
        
        # Configure global settings
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model
        Settings.chunk_size = chunk_size
        Settings.chunk_overlap = chunk_overlap
        
        # Configure node parser for better chunking
        self.node_parser = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        self.similarity_top_k = similarity_top_k
        self.response_mode = response_mode
        self.index = None
        self.document_sources = []
        
        logger.info(f"Initialized RAG with model: {model_name}")

    @step
    async def ingest(self, ctx: Context, ev: StartEvent) -> StopEvent | None:
        """
        Entry point to ingest documents from one or more directories.
        Supports: PDF, TXT, MD, DOCX, HTML, JSON, CSV, and code files.
        """
        dirname = ev.get("dirname")
        if not dirname:
            return None

        logger.info(f"Loading documents from: {dirname}")
        
        # Configure reader to support multiple file types
        reader = SimpleDirectoryReader(
            input_dir=dirname,
            recursive=True,  # Search subdirectories
            required_exts=[
                ".pdf", ".txt", ".md", ".docx",  # Documents
                ".html", ".htm",                   # Web content
                ".json", ".csv",                   # Data files
                ".py", ".js", ".ts", ".jsx", ".tsx",  # Code files
                ".java", ".cpp", ".c", ".go", ".rs",  # More code
                ".yaml", ".yml", ".toml", ".json"  # Config files
            ]
        )
        
        documents = reader.load_data(show_progress=True)
        logger.info(f"Loaded {len(documents)} documents")
        
        # Store document sources for citation
        self.document_sources = [doc.metadata.get('file_name', 'Unknown') for doc in documents]
        
        # Create index with custom node parser
        self.index = VectorStoreIndex.from_documents(
            documents=documents,
            transformations=[self.node_parser]
        )
        
        logger.info(f"Index created with {len(documents)} documents")
        return StopEvent(result=self.index)

    @step
    async def retrieve(self, ctx: Context, ev: StartEvent) -> RetrieverEvent | None:
        """
        Entry point for RAG retrieval with enhanced parameters.
        """
        query = ev.get("query")
        index = ev.get("index") or self.index

        if not query:
            return None

        if index is None:
            logger.error("Index is empty, load documents before querying!")
            return None

        logger.info(f"Retrieving for query: {query[:50]}...")
        
        # Use enhanced retriever with configurable similarity
        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=self.similarity_top_k,
        )
        
        nodes = await retriever.aretrieve(query)
        
        logger.info(f"Retrieved {len(nodes)} relevant chunks")
        
        # Log sources for debugging
        for i, node in enumerate(nodes):
            source = node.node.metadata.get('file_name', 'Unknown')
            score = node.score
            logger.debug(f"  {i+1}. {source} (score: {score:.4f})")
        
        await ctx.set("query", query)
        await ctx.set("sources", [node.node.metadata for node in nodes])
        
        return RetrieverEvent(nodes=nodes, query=query)

    @step
    async def synthesize(self, ctx: Context, ev: RetrieverEvent) -> StopEvent:
        """
        Generate a response with source citations.
        """
        query = await ctx.get("query", default=None)
        sources = await ctx.get("sources", default=[])
        
        logger.info("Synthesizing response...")
        
        # Use compact and refine for better responses
        summarizer = CompactAndRefine(
            streaming=False,
            verbose=False
        )
        
        response = await summarizer.asynthesize(query, nodes=ev.nodes)
        
        # Add source citations
        source_files = list(set([s.get('file_name', 'Unknown') for s in sources]))
        citations = "\n\nSources:\n" + "\n".join([f"- {s}" for s in source_files])
        
        response_with_citations = str(response) + citations
        
        logger.info("Response generated successfully")
        return StopEvent(result=response_with_citations)

    async def query(self, query_text: str) -> str:
        """
        Helper method to perform a complete RAG query.
        Returns response with source citations.
        """
        if self.index is None:
            raise ValueError("No documents have been ingested. Call ingest_documents first.")
        
        result = await self.run(query=query_text, index=self.index)
        return result

    async def ingest_documents(self, directory: str) -> None:
        """
        Helper method to ingest documents from a directory.
        Supports multiple file types and subdirectories.
        """
        result = await self.run(dirname=directory)
        self.index = result
        logger.info("Document ingestion complete")
        return result


# Example usage for chatbot
async def chatbot_example():
    """
    Example of using enhanced RAG as a chatbot.
    """
    print("🤖 Initializing Enhanced RAG Chatbot...")
    
    # Initialize with chatbot-optimized settings
    chatbot = EnhancedRAGWorkflow(
        model_name="llama3.2",
        chunk_size=512,  # Smaller chunks for more precise answers
        similarity_top_k=3,  # Top 3 relevant chunks
    )
    
    # Load documents
    print("📚 Loading documents...")
    await chatbot.ingest_documents("data")
    
    print("\n✅ Chatbot ready! Available document sources:")
    for source in set(chatbot.document_sources):
        print(f"  - {source}")
    
    # Example queries
    queries = [
        "What is DeepSeek?",
        "How was the model trained?",
        "What are the key features?"
    ]
    
    print("\n💬 Example conversations:\n")
    for query in queries:
        print(f"User: {query}")
        response = await chatbot.query(query)
        print(f"Bot: {response}\n")
        print("-" * 80 + "\n")


if __name__ == "__main__":
    import asyncio
    asyncio.run(chatbot_example())





