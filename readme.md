# DataFlare

DataFlare is a data processing and analysis platform that allows you to connect to various data sources, process data using custom workflows, and query the data using a SQL-like interface.

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
