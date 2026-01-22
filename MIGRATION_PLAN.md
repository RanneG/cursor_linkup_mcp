# Migration Plan: From Monorepo to Modular Architecture

## 🎯 Goal
Separate your chatbot into clean, focused repositories for better maintainability and distribution.

---

## 📦 Phase 1: Extract Core Library

### **Create `chatbot-rag-core` Repository**

#### **Step 1: Create new repo on GitHub**
```bash
# On GitHub, create new repo: chatbot-rag-core
# Then locally:
mkdir chatbot-rag-core
cd chatbot-rag-core
git init
```

#### **Step 2: Copy core files**
```bash
# From cursor_linkup_mcp, copy these files:
chatbot-rag-core/
├── chatbot_rag/
│   ├── __init__.py          # NEW
│   ├── api.py               # FROM: chatbot_api.py
│   ├── rag.py               # FROM: rag_enhanced.py
│   └── utils.py             # NEW (helper functions)
├── setup.py                 # NEW
├── requirements.txt         # FROM: pyproject.toml
├── examples/
│   ├── simple_usage.py      # NEW
│   ├── flask_example.py     # NEW
│   └── discord_bot.py       # NEW
├── tests/                   # NEW
│   └── test_rag.py
├── README.md                # NEW (library-focused)
├── LICENSE                  # Copy from main repo
└── .gitignore              # Python-specific
```

#### **Step 3: Create `setup.py`**
```python
# setup.py
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="chatbot-rag-core",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="RAG-powered chatbot using local Ollama models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/RanneG/chatbot-rag-core",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.12",
    install_requires=[
        "llama-index>=0.12.25",
        "llama-index-llms-ollama>=0.5.3",
        "llama-index-embeddings-huggingface>=0.5.2",
        "nest-asyncio>=1.6.0",
    ],
)
```

#### **Step 4: Create focused README.md**
```markdown
# Chatbot RAG Core

RAG-powered chatbot library using local Ollama models.
Zero API costs, complete privacy, runs 100% locally.

## Installation

```bash
pip install git+https://github.com/RanneG/chatbot-rag-core.git
```

## Quick Start

```python
from chatbot_rag import ChatbotAPI

# Initialize with your documents
bot = ChatbotAPI("./documents")

# Ask questions
answer = bot.ask("What's in the documentation?")
print(answer)
```

## Features
- ✅ Uses local Ollama models
- ✅ Supports PDF, DOCX, MD, HTML, code files
- ✅ Source citations included
- ✅ Zero API costs
- ✅ Complete privacy

## Requirements
- Python 3.12+
- Ollama installed locally
- llama3.2 model (or any Ollama model)

## Examples
See `examples/` folder for:
- Simple usage
- Flask web API
- Discord bot integration

## License
MIT
```

#### **Step 5: Commit and push**
```bash
git add .
git commit -m "Initial commit: Core RAG chatbot library"
git remote add origin https://github.com/RanneG/chatbot-rag-core.git
git push -u origin main
```

---

## 🌐 Phase 2: Create Production API Server

### **Create `chatbot-api-server` Repository**

#### **Step 1: Create new repo**
```bash
mkdir chatbot-api-server
cd chatbot-api-server
git init
```

#### **Step 2: Create server structure**
```bash
chatbot-api-server/
├── app/
│   ├── __init__.py
│   ├── main.py              # Flask/FastAPI server
│   ├── routes.py            # API endpoints
│   ├── config.py            # Configuration
│   └── middleware.py        # CORS, auth, etc.
├── documents/               # Example docs
│   └── README.md
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .dockerignore
├── .gitignore
├── README.md
└── LICENSE
```

#### **Step 3: Create `requirements.txt`**
```txt
chatbot-rag-core @ git+https://github.com/RanneG/chatbot-rag-core.git
flask==3.0.0
flask-cors==4.0.0
python-dotenv==1.0.0
gunicorn==21.2.0  # For production
```

#### **Step 4: Create `app/main.py`**
```python
from flask import Flask, request, jsonify
from flask_cors import CORS
from chatbot_rag import ChatbotAPI
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize chatbot
DOCUMENTS_PATH = os.getenv('DOCUMENTS_PATH', './documents')
bot = ChatbotAPI(DOCUMENTS_PATH)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    question = data.get('question', '')
    
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    
    answer = bot.ask(question)
    return jsonify({
        'question': question,
        'answer': answer
    })

@app.route('/api/sources', methods=['GET'])
def sources():
    return jsonify({
        'sources': bot.get_document_sources(),
        'count': len(bot.get_document_sources())
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

#### **Step 5: Create `Dockerfile`**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install Ollama
RUN apt-get update && apt-get install -y curl
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Pull Ollama model
RUN ollama pull llama3.2

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app.main:app"]
```

#### **Step 6: Create `docker-compose.yml`**
```yaml
version: '3.8'

services:
  chatbot-api:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./documents:/app/documents
    environment:
      - DOCUMENTS_PATH=/app/documents
    restart: unless-stopped
```

#### **Step 7: Create deployment README**
```markdown
# Chatbot API Server

Production-ready API server for the RAG chatbot.

## Quick Start

### Local Development
```bash
pip install -r requirements.txt
python app/main.py
```

### Docker Deployment
```bash
docker-compose up -d
```

### Production Deployment (DigitalOcean)
```bash
# See deploy/README.md for full instructions
./deploy/deploy.sh
```

## API Endpoints

### POST /api/chat
Ask a question
```json
{
  "question": "What is in the documentation?"
}
```

### GET /api/sources
List available documents

### GET /health
Health check

## Configuration

Copy `.env.example` to `.env`:
```env
DOCUMENTS_PATH=./documents
```

## Requirements
- Ollama installed
- llama3.2 model pulled
- Python 3.12+

## License
MIT
```

---

## 🔄 Phase 3: Update Main Repo

### **Update `cursor_linkup_mcp` Repository**

#### **Step 1: Update to use core library**

In `requirements.txt` or `pyproject.toml`:
```toml
dependencies = [
    "chatbot-rag-core @ git+https://github.com/RanneG/chatbot-rag-core.git",
    "mcp[cli]>=1.5.0",
    "linkup-sdk>=0.2.4",
    "python-dotenv>=1.0.0",
]
```

#### **Step 2: Simplify `server.py`**
```python
import asyncio
import os
from dotenv import load_dotenv
from linkup import LinkupClient
from chatbot_rag import ChatbotAPI  # Use library now!
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP('linkup-server')

# Initialize clients
linkup_client = LinkupClient() if os.getenv('LINKUP_API_KEY') else None
chatbot = ChatbotAPI("./data")

@mcp.tool()
def web_search(query: str) -> str:
    """Search web using Linkup."""
    if not linkup_client:
        return "Error: LINKUP_API_KEY not set"
    return linkup_client.search(query)

@mcp.tool()
async def rag(query: str) -> str:
    """Query documents using RAG."""
    return await chatbot.ask_async(query)

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

#### **Step 3: Update README.md**
```markdown
# Cursor Linkup MCP Server

MCP server for Cursor IDE with web search and RAG capabilities.

## This Repo
- ✅ MCP integration for Cursor IDE
- ✅ Personal development environment
- ✅ Uses [chatbot-rag-core](https://github.com/RanneG/chatbot-rag-core)

## For External Use
Want to use the chatbot in your own applications?

- **Library**: [chatbot-rag-core](https://github.com/RanneG/chatbot-rag-core)
- **Production API**: [chatbot-api-server](https://github.com/RanneG/chatbot-api-server)

## Setup (Cursor)
See [SETUP.md](SETUP.md) for Cursor-specific setup.
```

---

## 📊 Final Structure

```
Your GitHub Repositories:

┌─────────────────────────────────────┐
│ cursor_linkup_mcp (Private/Public)  │
│ ├─ MCP server for Cursor           │
│ ├─ Your personal docs              │
│ └─ Development environment         │
└─────────────────────────────────────┘
            ↓ uses
┌─────────────────────────────────────┐
│ chatbot-rag-core (Public)          │
│ ├─ Core chatbot library            │
│ ├─ pip installable                 │
│ └─ Used by both repos below        │
└─────────────────────────────────────┘
            ↓ used by
┌─────────────────────────────────────┐
│ chatbot-api-server (Public)        │
│ ├─ Production API server           │
│ ├─ Docker deployment               │
│ └─ For external users              │
└─────────────────────────────────────┘
```

---

## ✅ Benefits of This Structure

| Benefit | Description |
|---------|-------------|
| **Separation of Concerns** | Each repo has one clear purpose |
| **Easy Distribution** | `pip install chatbot-rag-core` |
| **Clear Documentation** | Each README focuses on one audience |
| **Independent Versioning** | Update core without affecting servers |
| **Privacy** | Keep dev stuff private, share public stuff |
| **Professional** | Industry-standard repo organization |
| **Maintainable** | Easy to find and fix issues |

---

## 🎯 Timeline

- **Week 1**: Extract `chatbot-rag-core` library
- **Week 2**: Create `chatbot-api-server` repo
- **Week 3**: Update `cursor_linkup_mcp` to use core library
- **Week 4**: Documentation and examples

---

## 🚀 Next Steps

1. Create `chatbot-rag-core` repository
2. Extract and package core functionality
3. Test installation and usage
4. Create `chatbot-api-server` repository
5. Deploy and test production server
6. Update documentation across all repos

Need help with any of these steps? Let me know! 🎉



