"""
MCP Server optimized for chatbot applications using Enhanced RAG
Supports multiple document sources and provides better responses for Q&A
"""

import asyncio
import os
from dotenv import load_dotenv
from linkup import LinkupClient
from rag_enhanced import EnhancedRAGWorkflow
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP('chatbot-server')

# Initialize LinkupClient only if API key is available
linkup_api_key = os.getenv('LINKUP_API_KEY')
client = None
if linkup_api_key:
    client = LinkupClient()

# Initialize enhanced RAG workflow with chatbot-optimized settings
rag_workflow = EnhancedRAGWorkflow(
    model_name="llama3.2",  # Change to "codellama" for code-heavy docs
    chunk_size=512,  # Smaller chunks for more precise answers
    chunk_overlap=50,  # Good overlap for context
    similarity_top_k=3,  # Top 3 relevant chunks
)

@mcp.tool()
def web_search(query: str) -> str:
    """Search the web for real-time information using Linkup."""
    if client is None:
        return "Error: LINKUP_API_KEY not set. Please add it to your .env file to use web search."
    
    search_response = client.search(
        query=query,
        depth="standard",
        output_type="sourcedAnswer",
        structured_output_schema=None,
    )
    return search_response

@mcp.tool()
async def ask_documents(query: str) -> str:
    """
    Ask questions about your documents. 
    Returns answers with source citations.
    Optimized for chatbot Q&A interactions.
    """
    response = await rag_workflow.query(query)
    return str(response)

@mcp.tool()
async def search_documents(keywords: str) -> str:
    """
    Search for specific keywords or topics in your documents.
    Returns relevant information with sources.
    """
    response = await rag_workflow.query(f"Find information about: {keywords}")
    return str(response)

@mcp.tool()
async def summarize_documents(topic: str) -> str:
    """
    Summarize information about a specific topic from all documents.
    Useful for getting overviews and aggregated information.
    """
    response = await rag_workflow.query(f"Provide a comprehensive summary about: {topic}")
    return str(response)

if __name__ == "__main__":
    # Ingest all documents from data directory
    print("🤖 Starting Chatbot Server...")
    print("📚 Loading documents...")
    asyncio.run(rag_workflow.ingest_documents("data"))
    print(f"✅ Loaded {len(rag_workflow.document_sources)} documents")
    print("🚀 Server ready!")
    
    # Start MCP server
    mcp.run(transport="stdio")



