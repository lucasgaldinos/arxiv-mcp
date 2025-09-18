# Getting Started with the ArXiv MCP Server

This tutorial will guide you through the process of setting up and running the ArXiv MCP Server for the first time.

## Prerequisites

- Python 3.8+
- `uv` package manager

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/arxiv-mcp-improved.git
   cd arxiv-mcp-improved
   ```

1. **Create a virtual environment and install dependencies:**

   ```bash
   uv venv
   uv sync
   ```

## Running the Server

To start the MCP server, run the following command:

```bash
uv run python -m src.arxiv_mcp
```bash

The server will start and register the available tools. You can then interact with it through a compatible client.
