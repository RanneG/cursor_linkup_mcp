# Environment Variables Template

Create a `.env` file in the project root with the following variables:

```bash
# Linkup API Key - Get your key from https://www.linkup.so/
LINKUP_API_KEY=your_linkup_api_key_here

# OpenAI API Key - Required for some operations
OPENAI_API_KEY=your_openai_api_key_here
```

## Getting API Keys

### Linkup API Key
1. Visit [https://www.linkup.so/](https://www.linkup.so/)
2. Sign up for an account
3. Generate your API key from the dashboard

### OpenAI API Key
1. Visit [https://platform.openai.com/](https://platform.openai.com/)
2. Sign up or log in to your account
3. Navigate to API keys section
4. Create a new API key

**Important**: Never commit your `.env` file to version control. It's already included in `.gitignore`.






