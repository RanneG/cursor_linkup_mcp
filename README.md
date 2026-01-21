# Cursor Linkup MCP Server

Custom MCP (Model Context Protocol) server for Cursor IDE with:
- 🌐 **Web Search** - Deep web searches using [Linkup API](https://www.linkup.so/)
- 📚 **RAG (Retrieval Augmented Generation)** - Query documents using LlamaIndex with Ollama

## 🎯 What This Is

An MCP server that integrates with Cursor IDE to provide AI-powered tools:
1. **web_search** - Search the web using Linkup API with sourced answers
2. **rag** - Query your local documents (PDFs, markdown, etc.) using local AI

## ✨ Key Features

- ✅ **Local AI** - Uses Ollama (llama3.2) for complete privacy
- ✅ **Zero API Costs** - RAG tool is completely free (uses local models)
- ✅ **Source Citations** - Know where answers come from
- ✅ **Multiple Document Types** - Supports PDF, DOCX, MD, TXT, and more
- ✅ **Cursor Integration** - Works seamlessly in Cursor IDE

## 📋 Prerequisites

- **Python 3.12+**
- **[uv](https://github.com/astral-sh/uv)** package manager
- **[Ollama](https://ollama.ai/)** installed locally
- **Linkup API key** (optional, only for web search)
- **OpenAI API key** (currently not used, for future features)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
uv sync
```

### 2. Install Ollama & Model

```bash
# Install Ollama from https://ollama.ai/
# Then pull the model:
ollama pull llama3.2
```

### 3. Configure Environment Variables (Optional)

Create a `.env` file for web search (RAG works without API keys):

```bash
LINKUP_API_KEY=your_linkup_api_key  # Optional, for web_search tool
```

See `ENV_TEMPLATE.md` for more details.

### 4. Configure Cursor

Add to your `~/.cursor/mcp.json` (or `C:\Users\<username>\.cursor\mcp.json` on Windows):

```json
{
  "mcpServers": {
    "linkup-server": {
      "command": "C:\\Users\\YOUR_USERNAME\\AppData\\Local\\Microsoft\\WindowsApps\\python.exe",
      "args": [
        "-m",
        "uv",
        "run",
        "--directory",
        "C:\\path\\to\\cursor_linkup_mcp",
        "python",
        "server.py"
      ]
    }
  }
}
```

**Replace:**
- `YOUR_USERNAME` with your Windows username
- `C:\\path\\to\\cursor_linkup_mcp` with your actual project path

### 5. Restart Cursor

Close and reopen Cursor IDE completely.

### 6. Start Using!

In Cursor's chat, you can now:
- **"Use the rag tool to tell me about [topic]"**
- **"Search the web for [query]"** (requires Linkup API key)

## 📚 Using the RAG Tool

The RAG tool queries documents in the `data/` folder.

### Add Your Documents

```bash
data/
├── document1.pdf
├── notes.md
├── research/
│   └── paper.pdf
└── guides/
    └── tutorial.docx
```

Supported formats: PDF, DOCX, TXT, MD, HTML, and more.

### Example Queries

- "What does the DeepSeek paper say about training?"
- "Summarize the key points from my meeting notes"
- "What are the main features mentioned in the documentation?"

## 🌐 Using Web Search

Requires a Linkup API key in your `.env` file.

### Example Queries

- "Search for the latest developments in AI"
- "Find recent articles about Ollama models"
- "What's new in Python 3.13?"

## 🛠️ Project Structure

```
cursor_linkup_mcp/
├── server.py              # Main MCP server
├── rag.py                 # RAG workflow implementation
├── data/                  # Your documents for RAG
│   └── DeepSeek.pdf      # Example document
├── pyproject.toml         # Python dependencies
├── .env                   # Environment variables (create this)
├── ENV_TEMPLATE.md        # Environment variables guide
├── OLLAMA_SETUP.md        # Ollama installation guide
├── GITHUB_SETUP.md        # GitHub setup instructions
├── QUICK_START.md         # Quick start guide
└── README.md              # This file
```

## 🔧 How It Works

```
Cursor IDE
    ↓
MCP Server (server.py)
    ↓
┌─────────────────┬─────────────────┐
│   RAG Tool      │   Web Search    │
│   (rag.py)      │   (Linkup API)  │
└────────┬────────┴─────────────────┘
         ↓
    ┌─────────────────────┐
    │ Ollama (llama3.2)   │
    │ Running locally     │
    └─────────────────────┘
```

## 💰 Cost

- **RAG Tool**: $0/month (uses local Ollama)
- **Web Search**: ~$10-50/month (if you use it heavily)
- **Ollama**: $0 (runs locally on your machine)

## 📖 Documentation

- **[ENV_TEMPLATE.md](ENV_TEMPLATE.md)** - Environment variables setup
- **[OLLAMA_SETUP.md](OLLAMA_SETUP.md)** - Detailed Ollama installation
- **[GITHUB_SETUP.md](GITHUB_SETUP.md)** - How to push to GitHub
- **[QUICK_START.md](QUICK_START.md)** - Step-by-step getting started
- **[.cursorrules](.cursorrules)** - Cursor IDE configuration guide

## 🐛 Troubleshooting

### "MCP server not loading"

1. Check that Ollama is running: `ollama list`
2. Verify the path in `mcp.json` is correct
3. Check Cursor logs: `%APPDATA%\Cursor\logs\`

### "Ollama connection refused"

```bash
# Start Ollama service
ollama serve
```

### "No documents found"

Make sure you have documents in the `data/` folder and restart Cursor.

## 🎓 Learn More

- **Original Tutorial**: [Watch on YouTube](https://youtu.be/XMVzT8X0QTA)
- **MCP Documentation**: [Model Context Protocol](https://modelcontextprotocol.io/)
- **Linkup API**: [https://www.linkup.so/](https://www.linkup.so/)
- **LlamaIndex**: [https://docs.llamaindex.ai/](https://docs.llamaindex.ai/)
- **Ollama**: [https://ollama.ai/](https://ollama.ai/)

## 🔐 Privacy

- ✅ **RAG Tool**: 100% local, documents never leave your machine
- ✅ **Ollama**: Runs locally, no cloud API calls
- ⚠️ **Web Search**: Requires Linkup API (queries sent to their servers)

## 📝 License

MIT License - See [LICENSE](LICENSE) file

## 🙏 Credits

- Original implementation inspired by [patchy631/ai-engineering-hub](https://github.com/patchy631/ai-engineering-hub)
- Uses [Linkup](https://www.linkup.so/) for web search
- Uses [LlamaIndex](https://www.llamaindex.ai/) for RAG
- Uses [Ollama](https://ollama.ai/) for local AI

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📬 Support

- **Issues**: [GitHub Issues](https://github.com/RanneG/cursor_linkup_mcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/RanneG/cursor_linkup_mcp/discussions)

---

**Made with ❤️ for Cursor IDE users**
