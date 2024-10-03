import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

import uvicorn
import asyncio
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.exceptions import HTTPException
from fastapi.templating import Jinja2Templates
from api.query import QueryModel
from api.services import QueryService, DatacardService
from data_binding.database_engine import ConnectionManager, ConcreteConnectionManager  # Import the concrete class
from utils.config_loader import load_config  # Add this import
import logging
import traceback
from services.chat_service import ChatService
from services.search_service import SearchService
from services.llm_service import LLMService
import json
from utils.connection_manager import get_connection_manager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

def get_connection_manager():
    # Load the configuration
    config = load_config()  # Implement this function to load your configuration
    connection_config = config.get('connection', {})  # Adjust this based on your config structure
    return ConcreteConnectionManager(connection_config)

def get_query_service(connection_manager: ConnectionManager = Depends(get_connection_manager)):
    return QueryService()

def get_datacard_service(connection_manager: ConnectionManager = Depends(get_connection_manager)):
    return DatacardService(connection_manager)

@app.get("/", response_class=RedirectResponse)
async def read_root():
    return RedirectResponse(url="/chat")

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/render", response_class=HTMLResponse)
async def render():
    return HTMLResponse("render/datacard/render.html")

@app.post("/query/{organization}/{dataset}")
async def query(
    organization: str,
    dataset: str,
    query_model: QueryModel,
    service: QueryService = Depends(get_query_service)
):
    try:
        logger.debug(f"Received query for {organization}/{dataset}: {query_model}")
        
        if not query_model.description:
            raise ValueError("Query description is required")
        
        result = service.execute_query_on_dataset(query_model, organization, dataset)
        
        if not result:
            return JSONResponse(content={"message": "No data found for the given query"}, status_code=404)
        
        logger.debug(f"Query result: {result}")
        return result
    except ValueError as ve:
        logger.error(f"Invalid query: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error in query endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.get("/datacard/{organization}/{definition}", response_class=HTMLResponse)
async def render_datacard(organization: str, definition: str):
    try:
        with open("render/datacard/render.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Datacard not found")

@app.get("/api/datacard/{organization}/{definition}")
async def get_datacard_definition(
    organization: str,
    definition: str,
    service: DatacardService = Depends(get_datacard_service)
):
    try:
        logger.debug(f"Fetching datacard definition for {organization}/{definition}")
        result = service.get_datacard(organization, definition)
        logger.debug(f"Successfully fetched datacard definition: {result}")
        return result
    except FileNotFoundError as e:
        logger.error(f"Datacard definition not found: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Datacard definition not found: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching datacard definition: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error fetching datacard definition: {str(e)}")

print(f"ANTHROPIC_API_KEY is {'set' if os.environ.get('ANTHROPIC_API_KEY') else 'not set'}")

search_service = SearchService()
query_service = QueryService()
chat_service = ChatService()

@app.post("/api/chat")
async def chat(request: Request):
    if chat_service is None:
        error_message = "Chat service is not available. "
        if 'ANTHROPIC_API_KEY' not in os.environ:
            error_message += "ANTHROPIC_API_KEY is not set. Please set it and restart the server."
        else:
            error_message += "Please check the server logs for more information."
        return JSONResponse(content={"error": error_message}, status_code=503)
    
    form_data = await request.form()
    message = form_data.get('message')
    chat_history = json.loads(form_data.get('chat_history', '[]'))  # Get chat history from form data
    
    try:
        logger.debug(f"Processing message: {message}")
        logger.debug(f"Chat history: {chat_history}")
        response = chat_service.process_message(message, chat_history)
        logger.debug(f"Response generated: {response}")
        
        # Add this block to log the structure of the response
        logger.debug("Response structure:")
        logger.debug(f"Type: {type(response)}")
        
        # Ensure we're sending the correct structure
        if isinstance(response, str):
            return JSONResponse(content={
                "message": response,
                "retrieved_information": ""
            })
        elif isinstance(response, dict):
            return JSONResponse(content={
                "message": response.get("message", ""),
                "retrieved_information": response.get("retrieved_information", "")
            })
        else:
            raise ValueError(f"Unexpected response type: {type(response)}")
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}", exc_info=True)
        return JSONResponse(content={"error": f"An error occurred: {str(e)}"}, status_code=500)

@app.get("/api/search_dataset")
async def search_dataset(query: str):
    results = search_service.search_datasets(query)
    return JSONResponse(content=results)

@app.get("/api/search_datacard")
async def search_datacard(query: str):
    results = search_service.search_datacards(query)
    return JSONResponse(content=[d.to_dict() for d in results])

@app.post("/api/query_dataset")
async def query_dataset(request: Request):
    data = await request.json()
    query = data['query']
    dataset = data['dataset']
    org, dataset_code = dataset.split('/')
    results = query_service.execute_query_on_dataset(query, org, dataset_code)
    return JSONResponse(content=results)

def start_server(host: str, port: int):
    uvicorn.run(app, host=host, port=port)

def stop_server():
    print("Stopping server...")
    # Get the current event loop
    loop = asyncio.get_event_loop()

    # Check if there's a running server
    if hasattr(app, 'server'):
        # Stop the server
        app.server.should_exit = True
        loop.run_until_complete(app.server.shutdown())
        print("Server stopped.")
    else:
        print("No server instance found to stop.")

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)