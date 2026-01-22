# How to Reuse This Chatbot in Other Projects

## 🎯 Quick Answer

**AI Model:** Your chatbot uses **Ollama (llama3.2)** running **locally on your machine**
- ✅ Completely private
- ✅ Zero API costs
- ✅ Works offline
- ✅ You control everything

---

## 🏗️ Three Ways to Reuse This Chatbot

### **Method 1: Python Package (Recommended)**

Use in ANY Python application!

#### **Setup:**

1. **In your new project:**
```bash
# Clone or add as git submodule
git submodule add https://github.com/RanneG/cursor_linkup_mcp.git chatbot

# Or copy the files
cp -r /path/to/cursor_linkup_mcp/rag*.py ./
cp -r /path/to/cursor_linkup_mcp/chatbot_api.py ./
```

2. **Install dependencies:**
```bash
# Copy pyproject.toml or install manually
pip install llama-index llama-index-llms-ollama llama-index-embeddings-huggingface
```

3. **Use in your code:**
```python
from chatbot_api import ChatbotAPI

# Initialize with your documents
bot = ChatbotAPI("./documents")

# Ask questions
answer = bot.ask("Your question here")
print(answer)
```

#### **Example: Flask Web App**

```python
from flask import Flask, request, jsonify
from chatbot_api import ChatbotAPI

app = Flask(__name__)
bot = ChatbotAPI("./data")  # Your documents

@app.route('/api/ask', methods=['POST'])
def ask():
    question = request.json.get('question')
    answer = bot.ask(question)
    return jsonify({'answer': answer})

if __name__ == '__main__':
    app.run(port=5000)
```

#### **Example: Next.js API Route**

```python
# api/chatbot.py (Python backend)
from chatbot_api import ChatbotAPI

bot = ChatbotAPI("./documents")

def handler(request):
    question = request.json['question']
    answer = bot.ask(question)
    return {'answer': answer}
```

```javascript
// app/api/chat/route.ts (Next.js frontend)
export async function POST(request: Request) {
  const { question } = await request.json();
  
  // Call your Python backend
  const response = await fetch('http://localhost:5000/api/ask', {
    method: 'POST',
    body: JSON.stringify({ question })
  });
  
  return response.json();
}
```

---

### **Method 2: Git Submodule (Clean Separation)**

Keep chatbot separate but linked!

#### **Setup:**

```bash
cd your-new-project

# Add as submodule
git submodule add https://github.com/RanneG/cursor_linkup_mcp.git chatbot

# Update whenever chatbot repo updates
git submodule update --remote
```

#### **Usage:**

```python
# your-app/main.py
import sys
sys.path.append('./chatbot')

from chatbot_api import ChatbotAPI

bot = ChatbotAPI("./chatbot/data")
answer = bot.ask("What's in the docs?")
```

#### **Project Structure:**

```
your-new-project/
├── app/
│   ├── main.py              # Your application
│   └── routes.py
├── chatbot/                 # Submodule → cursor_linkup_mcp
│   ├── rag_enhanced.py
│   ├── chatbot_api.py
│   └── data/                # Your documents
├── requirements.txt
└── README.md
```

---

### **Method 3: MCP Server (Cursor IDE Only)**

Use from any Cursor project!

#### **Setup:**

In your **new project**, create `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "shared-chatbot": {
      "command": "C:\\Users\\ranne\\AppData\\Local\\Microsoft\\WindowsApps\\python.exe",
      "args": [
        "-m",
        "uv",
        "run",
        "--directory",
        "C:\\Users\\ranne\\Cursor\\cursor_linkup_mcp",
        "python",
        "server.py"
      ]
    }
  }
}
```

Now every Cursor project can use your chatbot!

---

## 🔧 Customizing for Different Projects

### **Project 1: E-commerce Support Bot**

```
your-ecommerce-app/
├── chatbot/
│   └── data/
│       ├── products/
│       │   ├── product_catalog.pdf
│       │   └── specifications/
│       ├── policies/
│       │   ├── shipping.md
│       │   ├── returns.md
│       │   └── warranty.pdf
│       └── faq.md
└── app.py

# app.py
bot = ChatbotAPI("./chatbot/data")

# Customer asks:
bot.ask("What's your return policy?")
bot.ask("Do you have this product in blue?")
```

---

### **Project 2: Internal HR Portal**

```
hr-portal/
├── chatbot/
│   └── data/
│       ├── employee_handbook.pdf
│       ├── benefits_guide.docx
│       ├── time_off_policies.md
│       └── onboarding/
└── portal.py

# portal.py
bot = ChatbotAPI("./chatbot/data")

# Employee asks:
bot.ask("How do I request vacation time?")
bot.ask("What are the health insurance options?")
```

---

### **Project 3: Documentation Site**

```
docs-site/
├── chatbot/
│   └── data/
│       ├── api/
│       │   ├── reference.md
│       │   ├── authentication.md
│       │   └── examples/
│       ├── guides/
│       └── tutorials/
└── docs-app.py

# docs-app.py
bot = ChatbotAPI("./chatbot/data")

# Developer asks:
bot.ask("How do I authenticate API requests?")
bot.ask("Show me an example of creating a user")
```

---

## 🤖 What AI Models Are Used?

### **Your Chatbot Architecture:**

```
┌─────────────────────────────────────────┐
│  YOUR APPLICATION                       │
│  (Flask, FastAPI, Next.js, etc.)       │
└─────────────────────────────────────────┘
              ↓ calls
┌─────────────────────────────────────────┐
│  chatbot_api.py                         │
│  (Python interface)                     │
└─────────────────────────────────────────┘
              ↓ uses
┌─────────────────────────────────────────┐
│  RAG Workflow                           │
│  ├─ Embeddings: HuggingFace (local)    │
│  └─ LLM: Ollama llama3.2 (local)       │
└─────────────────────────────────────────┘
              ↓ runs on
┌─────────────────────────────────────────┐
│  YOUR MACHINE (Ollama Service)          │
│  - Completely local                     │
│  - Completely private                   │
│  - Zero API costs                       │
└─────────────────────────────────────────┘
```

### **Models Breakdown:**

| Component | Model | Purpose | Location |
|-----------|-------|---------|----------|
| **Embeddings** | BAAI/bge-small-en-v1.5 | Convert text to vectors | Local (HuggingFace) |
| **LLM** | Ollama llama3.2 | Generate responses | Local (Ollama) |
| **Vector Search** | Built-in | Find relevant docs | Local (LlamaIndex) |

### **You Can Change Models:**

```python
# Use different Ollama models
bot = ChatbotAPI("./data", model_name="codellama")  # For code docs
bot = ChatbotAPI("./data", model_name="llama3.1:8b")  # Larger model
bot = ChatbotAPI("./data", model_name="mistral")  # Faster
```

---

## 💰 Cost Comparison

### **Your Setup (Ollama):**
- Initial: $0
- Per query: $0
- Monthly: $0
- Total: **$0** 🎉

### **vs. Cloud AI (GPT-4):**
- Initial: $0
- Per query: ~$0.01-0.02
- Monthly (1000 queries): ~$300
- Total: **$3,600/year** 💸

### **vs. Fine-tuned Model:**
- Initial: $500-$5000 (training)
- Per query: $0.001-0.01
- Monthly (1000 queries): ~$50-200
- Total: **$1,100-$7,400/year** 💸💸

**Winner: Your setup saves $3,600-$7,400/year!**

---

## 🚀 Quick Start Templates

### **Template 1: Flask REST API**

```python
# flask_chatbot.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from chatbot_api import ChatbotAPI

app = Flask(__name__)
CORS(app)

# Initialize chatbot
bot = ChatbotAPI("./documents")

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    question = data.get('question', '')
    
    if not question:
        return jsonify({'error': 'No question'}), 400
    
    answer = bot.ask(question)
    return jsonify({
        'question': question,
        'answer': answer
    })

@app.route('/api/sources', methods=['GET'])
def sources():
    return jsonify({
        'sources': bot.get_document_sources()
    })

@app.route('/api/stats', methods=['GET'])
def stats():
    return jsonify(bot.get_stats())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### **Template 2: FastAPI (Async)**

```python
# fastapi_chatbot.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from chatbot_api import ChatbotAPI
import asyncio

app = FastAPI()
bot = ChatbotAPI("./documents")

class Question(BaseModel):
    question: str

@app.post("/api/chat")
async def chat(q: Question):
    if not q.question:
        raise HTTPException(400, "No question provided")
    
    answer = await bot.ask_async(q.question)
    return {"question": q.question, "answer": answer}

@app.get("/api/sources")
async def get_sources():
    return {"sources": bot.get_document_sources()}

# Run with: uvicorn fastapi_chatbot:app --reload
```

### **Template 3: Discord Bot**

```python
# discord_chatbot.py
import discord
from chatbot_api import ChatbotAPI

client = discord.Client()
bot = ChatbotAPI("./documents")

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.startswith('!ask '):
        question = message.content[5:]  # Remove '!ask '
        answer = await bot.ask_async(question)
        await message.channel.send(answer)

client.run('YOUR_BOT_TOKEN')
```

---

## 📦 Package It for Distribution

### **Create a Python Package:**

```
cursor_linkup_mcp/
├── setup.py
├── chatbot_rag/
│   ├── __init__.py
│   ├── api.py (chatbot_api.py)
│   └── rag.py (rag_enhanced.py)
└── README.md

# setup.py
from setuptools import setup, find_packages

setup(
    name="chatbot-rag",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "llama-index>=0.12.25",
        "llama-index-llms-ollama>=0.5.3",
        "llama-index-embeddings-huggingface>=0.5.2",
    ]
)
```

### **Install in Any Project:**

```bash
pip install git+https://github.com/RanneG/cursor_linkup_mcp.git
```

### **Use Anywhere:**

```python
from chatbot_rag import ChatbotAPI

bot = ChatbotAPI("./documents")
answer = bot.ask("Your question")
```

---

## ✅ Checklist for New Project

- [ ] Clone or add cursor_linkup_mcp as submodule
- [ ] Install Ollama on deployment machine
- [ ] Pull your chosen model (`ollama pull llama3.2`)
- [ ] Copy your documents to `data/` folder
- [ ] Import `ChatbotAPI` in your code
- [ ] Initialize with your documents path
- [ ] Start asking questions!
- [ ] Deploy and enjoy $0/month costs!

---

## 🎯 Summary

**Question:** What AI agent is the chatbot using?  
**Answer:** **Ollama (llama3.2)** running locally on your machine

**Question:** How do I use it in other projects?  
**Answer:** Three ways:
1. **Python Package** - Use `ChatbotAPI` in any Python app
2. **Git Submodule** - Link as submodule, keep separate
3. **MCP Server** - Share across all Cursor projects

**Best for most apps:** Method 1 (Python Package) via `chatbot_api.py`

**Cost:** $0/month with Ollama! 🎉

---

Need help setting this up in a specific project? Let me know what you're building! 🚀



