dataflare/
├── crawler/
│   ├── __init__.py
│   ├── base_crawler.py  # Abstract base class for crawlers
│   └── web_crawler.py   # Implement web crawling functionality
├── agent/
│   ├── __init__.py
│   ├── data_source_agent.py  # Agent for identifying and indexing data sources
│   └── workflow_creator.py   # Agent for creating Python workflows
├── workflows/
│   ├── __init__.py
│   ├── base_workflow.py      # Abstract base class for workflows
│   ├── world_bank_workflow.py  # Workflow for World Bank data
│   └── us_labor_workflow.py  # Workflow for US labor data
├── workflow_manager/
│   ├── __init__.py
│   └── manager.py            # Manages and runs workflows, collects metadata
├── data_storage/
│   ├── __init__.py
│   └── parquet_storage.py    # Handles saving data to Parquet files
├── data_binding/
│   ├── __init__.py
│   └── duckdb_binder.py      # Binds data using DuckDB
├── api/
│   ├── __init__.py
│   └── query_api.py          # API for querying the bound data
├── utils/
│   ├── __init__.py
│   └── helpers.py            # Helper functions and utilities
├── config/
│   └── config.yaml           # Configuration file for the system
├── main.py                   # Entry point for running the system
└── requirements.txt          # Project dependencies