"""
Standalone Chatbot API - Use in any application!
Works independently of Cursor/MCP

Usage:
    from chatbot_api import ChatbotAPI
    
    bot = ChatbotAPI("path/to/documents")
    response = bot.ask("Your question here")
    print(response)
"""

import asyncio
from pathlib import Path
from typing import Optional, List, Dict
from rag_enhanced import EnhancedRAGWorkflow
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatbotAPI:
    """
    Standalone chatbot that can be used in any Python application.
    Uses local Ollama for complete privacy and zero API costs.
    """
    
    def __init__(
        self,
        documents_path: str,
        model_name: str = "llama3.2",
        chunk_size: int = 512,
        similarity_top_k: int = 3
    ):
        """
        Initialize chatbot with your documents.
        
        Args:
            documents_path: Path to folder containing your documents
            model_name: Ollama model to use (llama3.2, codellama, etc.)
            chunk_size: Size of text chunks for indexing
            similarity_top_k: Number of relevant chunks to retrieve
        
        Example:
            bot = ChatbotAPI("./data", model_name="llama3.2")
        """
        self.documents_path = Path(documents_path)
        self.model_name = model_name
        
        # Initialize RAG workflow
        self.rag = EnhancedRAGWorkflow(
            model_name=model_name,
            chunk_size=chunk_size,
            similarity_top_k=similarity_top_k
        )
        
        # Load documents
        self._load_documents()
        
        logger.info(f"✅ Chatbot initialized with model: {model_name}")
        logger.info(f"📚 Loaded {len(self.rag.document_sources)} documents")
    
    def _load_documents(self):
        """Load documents synchronously."""
        if not self.documents_path.exists():
            raise ValueError(f"Documents path not found: {self.documents_path}")
        
        # Run async document loading in sync context
        asyncio.run(self.rag.ingest_documents(str(self.documents_path)))
    
    def ask(self, question: str) -> str:
        """
        Ask a question and get an answer with sources.
        
        Args:
            question: Your question
            
        Returns:
            Answer with source citations
            
        Example:
            response = bot.ask("What is DeepSeek?")
            print(response)
        """
        if not question.strip():
            return "Please provide a question."
        
        logger.info(f"❓ Question: {question[:50]}...")
        
        # Run async query in sync context
        response = asyncio.run(self.rag.query(question))
        
        logger.info(f"✅ Response generated")
        return response
    
    async def ask_async(self, question: str) -> str:
        """
        Async version of ask() for use in async applications.
        
        Args:
            question: Your question
            
        Returns:
            Answer with source citations
        """
        if not question.strip():
            return "Please provide a question."
        
        response = await self.rag.query(question)
        return response
    
    def get_document_sources(self) -> List[str]:
        """
        Get list of all loaded documents.
        
        Returns:
            List of document filenames
        """
        return list(set(self.rag.document_sources))
    
    def get_stats(self) -> Dict[str, any]:
        """
        Get chatbot statistics.
        
        Returns:
            Dictionary with stats
        """
        return {
            "model": self.model_name,
            "documents_loaded": len(self.rag.document_sources),
            "unique_documents": len(set(self.rag.document_sources)),
            "documents_path": str(self.documents_path)
        }


# Example usage functions

def simple_chatbot_example():
    """Simple example: Ask one question."""
    print("🤖 Simple Chatbot Example\n")
    
    # Initialize chatbot
    bot = ChatbotAPI("data")
    
    # Ask a question
    question = "What is DeepSeek?"
    print(f"❓ {question}\n")
    
    response = bot.ask(question)
    print(f"🤖 {response}\n")


def interactive_chatbot_example():
    """Interactive chatbot: Keep asking questions."""
    print("🤖 Interactive Chatbot")
    print("=" * 50)
    
    # Initialize chatbot
    bot = ChatbotAPI("data")
    
    # Show loaded documents
    print(f"\n📚 Loaded documents:")
    for doc in bot.get_document_sources():
        print(f"  - {doc}")
    
    print("\n💬 Start chatting! (Type 'quit' to exit)\n")
    
    while True:
        question = input("You: ").strip()
        
        if question.lower() in ['quit', 'exit', 'bye']:
            print("👋 Goodbye!")
            break
        
        if not question:
            continue
        
        response = bot.ask(question)
        print(f"\nBot: {response}\n")


def web_api_example():
    """Example: Use chatbot in a web API (Flask/FastAPI)."""
    print("🌐 Web API Example\n")
    print("Here's how to use the chatbot in a web API:\n")
    
    example_code = '''
from flask import Flask, request, jsonify
from chatbot_api import ChatbotAPI

app = Flask(__name__)

# Initialize chatbot once at startup
bot = ChatbotAPI("data")

@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.json
    question = data.get('question', '')
    
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    
    response = bot.ask(question)
    return jsonify({
        'question': question,
        'answer': response
    })

@app.route('/sources', methods=['GET'])
def get_sources():
    sources = bot.get_document_sources()
    return jsonify({'sources': sources})

if __name__ == '__main__':
    app.run(debug=True)
    '''
    
    print(example_code)


def async_example():
    """Example: Use chatbot in async applications."""
    print("⚡ Async Example\n")
    
    async def async_chatbot():
        bot = ChatbotAPI("data")
        
        questions = [
            "What is DeepSeek?",
            "How was it trained?",
            "What are its capabilities?"
        ]
        
        for question in questions:
            print(f"❓ {question}")
            response = await bot.ask_async(question)
            print(f"🤖 {response}\n")
            print("-" * 50 + "\n")
    
    asyncio.run(async_chatbot())


if __name__ == "__main__":
    print("="*60)
    print("  Chatbot API Examples")
    print("="*60)
    print("\nChoose an example:")
    print("1. Simple chatbot (ask one question)")
    print("2. Interactive chatbot (keep asking)")
    print("3. Web API example (Flask/FastAPI)")
    print("4. Async example")
    print("5. Run all examples")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == "1":
        simple_chatbot_example()
    elif choice == "2":
        interactive_chatbot_example()
    elif choice == "3":
        web_api_example()
    elif choice == "4":
        async_example()
    elif choice == "5":
        simple_chatbot_example()
        print("\n" + "="*60 + "\n")
        web_api_example()
        print("\n" + "="*60 + "\n")
        async_example()
    else:
        print("Invalid choice. Running simple example...")
        simple_chatbot_example()








