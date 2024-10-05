# DataFlare

### Project Overview

DataFlare is a comprehensive data analysis and interaction platform built with Python. It provides a powerful set of tools for data processing, querying, and visualization. The core features include:

1. **Data Connectivity**: Connect to various data sources, including DuckDB databases.

2. **Smart Querying**: Execute SQL-like queries on datasets using a RESTful API.

3. **Chat Interface**: Interact with the data using natural language through an AI-powered chat service.

4. **Data Visualization**: Render datacards for visual representation of data insights.

5. **Data Search**: Search across datasets and datacards to find relevant information quickly.

Technically, DataFlare is built with the following features:

**LLM Integration**: Incorporates Large Language Models for intelligent data analysis and natural language processing.

**API first**: The project is designed to be API-first, with a focus on creating a set of RESTful APIs that can be used to interact with the data.

**Modular Architecture**: Well-structured codebase with separate services for different functionalities (e.g., QueryService, ChatService, SearchService).

**Configuration Management**: Flexible configuration system for easy setup and customization.

**Error Handling**: Robust error handling and logging for easier debugging and maintenance.

DataFlare aims to simplify complex data operations, making it easier for users to extract insights from their data through both programmatic and conversational interfaces.

## Getting Started

### Prerequisites

- Python 3.8+
- DuckDB
- FastAPI
- Uvicorn

### Installation

```bash
pip install -r requirements.txt
```

### Set your Anthropic API key
export ANTHROPIC_API_KEY=your_actual_api_key_here

### Running the Application

```bash
python3 -m uvicorn app:app --reload
```

### Running the Tests

```bash
python3 -m pytest tests
python3 -m pytest tests/test_render_flow.py // for specific tests
```

## Credits
DataFlare was created by Simone Di Somma.
