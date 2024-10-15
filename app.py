import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import logging
import pandas as pd
from services.dataframe import DataFrameService
from api.router import router

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include the router
app.include_router(router)

# Initialize DataFrameService
dataframe_service = DataFrameService()

# Add the dataframe_service to pandas app_context
pd.app_context = type('AppContext', (), {'dataframe_service': dataframe_service})()

# Server Control
if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
