# Documentation MCP Server

A Model Context Protocol (MCP) server that provides access to technical documentation, API references, and code examples for AI agents.

## Features

- Technical documentation search
- Code example retrieval
- Multiple language and library support
- Result caching for improved performance
- Health monitoring

## Supported Documentation Sources

- Python
- JavaScript
- Node.js
- React
- TensorFlow
- Pandas
- Django
- Flask
- FastAPI
- NumPy
- PyTorch

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run server:
```bash
uvicorn src.mcp_server:app --reload
```

## API Endpoints

- POST /search_docs - Search for documentation
- POST /code_examples - Get code examples
- GET /available_docs - List available documentation sources
- GET /health - Check server health

## Example Usage

```python
# Search documentation
POST /search_docs
{
    "library": "python",
    "term": "asyncio",
    "max_results": 5
}

# Get code examples
POST /code_examples
{
    "library": "python",
    "function": "async with",
    "language": "python",
    "max_examples": 3
}
```

## MCP Integration

This server follows the MCP specification for tool integration with AI agents.