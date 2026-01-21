# Setup Guide for Cursor Linkup MCP Server

## Quick Start

This MCP server provides two powerful tools for Cursor IDE:
1. **Web Search** - Deep web searches using Linkup API
2. **RAG (Retrieval Augmented Generation)** - Query documents using LlamaIndex

## Prerequisites

Before you begin, make sure you have:

- ✅ Python 3.12 or higher installed
- ✅ [uv](https://github.com/astral-sh/uv) package manager (`pip install uv`)
- ✅ [Ollama](https://ollama.ai/) installed locally
- ✅ Linkup API key from https://www.linkup.so/
- ✅ OpenAI API key from https://platform.openai.com/

## Step-by-Step Installation

### 1. Install uv (if not already installed)

```bash
# On Windows
pip install uv

# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Install Ollama and Download Model

```bash
# Download and install Ollama from https://ollama.ai/

# Pull the llama3.2 model
ollama pull llama3.2

# Verify installation
ollama list
```

### 3. Set Up Environment Variables

Create a `.env` file in the project root (see `ENV_TEMPLATE.md` for details):

```bash
LINKUP_API_KEY=your_actual_linkup_api_key
OPENAI_API_KEY=your_actual_openai_api_key
```

**Important:** Never commit your `.env` file to version control!

### 4. Install Project Dependencies

```bash
uv sync
```

This will install all required Python packages including:
- linkup-sdk
- llama-index
- mcp[cli]
- python-dotenv
- nest-asyncio
- and more...

### 5. Test the Server Locally (Optional)

Before integrating with Cursor, you can test the server:

```bash
# Test RAG workflow
uv run python rag.py

# This will:
# - Load documents from the data/ directory
# - Create vector embeddings
# - Query: "How was DeepSeekR1 trained?"
```

### 6. Configure Cursor IDE

#### Option A: Manual Configuration

1. Open Cursor IDE
2. Go to Settings → Extensions → Model Context Protocol
3. Add a new server configuration:

```json
{
  "mcpServers": {
    "linkup-server": {
      "command": "uv",
      "args": ["run", "python", "server.py"],
      "cwd": "C:\\Users\\ranne\\Cursor\\cursor_linkup_mcp",
      "env": {
        "LINKUP_API_KEY": "your_linkup_api_key",
        "OPENAI_API_KEY": "your_openai_api_key"
      }
    }
  }
}
```

#### Option B: Using .cursor Directory

Create `.cursor/mcp.json` in your project:

```json
{
  "mcpServers": {
    "linkup-server": {
      "command": "uv",
      "args": ["run", "python", "server.py"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

Note: When using this method, environment variables will be loaded from your `.env` file.

### 7. Restart Cursor

After configuration, restart Cursor IDE to load the MCP server.

## Using the MCP Server in Cursor

Once configured, you can use the following tools in your Cursor conversations:

### Web Search Tool

```
Can you search the web for the latest developments in AI?
```

This will use the `web_search` tool to fetch real-time information from the internet using Linkup.

### RAG Tool

```
What does the DeepSeek document say about training methods?
```

This will use the `rag` tool to query documents in your `data/` directory.

## Adding Your Own Documents

To use the RAG feature with your own documents:

1. Add PDF, TXT, or other supported documents to the `data/` directory
2. Restart the MCP server
3. The documents will be automatically indexed on startup

Supported formats:
- PDF (.pdf)
- Text files (.txt)
- Markdown (.md)
- Word documents (.docx)
- And more...

## Troubleshooting

### Issue: "Ollama connection refused"

**Solution:** Make sure Ollama is running:
```bash
ollama serve
```

### Issue: "LINKUP_API_KEY not found"

**Solution:** Check that your `.env` file exists and contains the correct keys.

### Issue: "Module not found"

**Solution:** Reinstall dependencies:
```bash
uv sync --refresh
```

### Issue: "MCP server not responding"

**Solution:**
1. Check Cursor's MCP logs
2. Verify the `cwd` path in your configuration
3. Test the server manually: `uv run python server.py`

## Advanced Configuration

### Changing the LLM Model

Edit `rag.py` line 18:

```python
def __init__(self, model_name="llama3.2", embedding_model="BAAI/bge-small-en-v1.5"):
```

Change `model_name` to any Ollama model you have installed.

### Adjusting Search Depth

Edit `server.py` line 18:

```python
depth="standard",  # Options: "standard" or "deep"
```

### Customizing RAG Retrieval

Edit `rag.py` line 54:

```python
retriever = index.as_retriever(similarity_top_k=2)  # Increase for more results
```

## Next Steps

- 📚 Add your own documents to the `data/` directory
- 🔧 Customize the RAG workflow for your use case
- 🌐 Experiment with different search depths in Linkup
- 🤖 Try different Ollama models for RAG

## Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [Linkup API Docs](https://www.linkup.so/docs)
- [LlamaIndex Documentation](https://docs.llamaindex.ai/)
- [Ollama Models](https://ollama.ai/library)

## Support

If you encounter any issues, please check:
1. This SETUP.md file
2. The `.cursorrules` file for additional context
3. The original repository: https://github.com/patchy631/ai-engineering-hub/tree/main/cursor_linkup_mcp






