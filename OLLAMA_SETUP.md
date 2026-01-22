# Ollama Setup Guide

## Step 1: Install Ollama

I've opened the download page for you: https://ollama.ai/download

### Installation Steps:

1. **Download:** Click "Download for Windows" button
2. **Run the installer:** OllamaSetup.exe
3. **Follow the installation wizard:**
   - Click "Next"
   - Accept the license
   - Choose installation location (default is fine)
   - Click "Install"
4. **Finish:** Ollama will start automatically

## Step 2: Verify Installation

After installation, open a **new terminal** and run:

```bash
ollama --version
```

You should see something like: `ollama version 0.x.x`

## Step 3: Pull the llama3.2 Model

Once Ollama is installed, run:

```bash
ollama pull llama3.2
```

This will download the llama3.2 model (~2GB). It may take a few minutes.

## Step 4: Test Ollama

Try running a quick test:

```bash
ollama run llama3.2 "Hello, how are you?"
```

If you see a response, Ollama is working! Press `Ctrl+D` or type `/bye` to exit.

## Step 5: Start Ollama Service (if needed)

Ollama should start automatically, but if it's not running:

```bash
# Check if Ollama is running
ollama list

# If not running, start it:
ollama serve
```

## After Installation

Once Ollama is installed and llama3.2 is pulled:

1. **Restart Cursor** (so it can detect Ollama)
2. **Test your MCP server:**
   - Open Cursor chat
   - Try: "Use RAG to tell me about DeepSeek"
   - The `rag` tool should work now!

## Troubleshooting

### "Ollama not found" after installation
- Close and reopen your terminal
- Restart your computer if needed
- Check if Ollama is in: `C:\Users\ranne\AppData\Local\Programs\Ollama`

### Model download is slow
- Normal! llama3.2 is about 2GB
- Keep the terminal open until it completes

### "Connection refused" error
- Make sure Ollama service is running: `ollama serve`
- Check Task Manager for "ollama" process

## Available Models

After llama3.2, you can try other models:

```bash
# Smaller, faster
ollama pull llama3.2:1b

# Larger, more capable
ollama pull llama3.1:8b
ollama pull llama3.1:70b

# Code-focused
ollama pull codellama
ollama pull deepseek-coder

# List all installed models
ollama list
```

## Next Steps

After Ollama is set up, return to Cursor and your MCP server will be able to use the RAG tool! 🎉








