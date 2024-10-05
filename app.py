import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from api.query import QueryModel
from api.services import QueryService, DatacardService
from data_binding.database_engine import ConnectionManager, ConcreteConnectionManager
from utils.config_loader import load_config, load_dataset_definition
import logging
import traceback
from services.chat_service import ChatService
from services.search_service import SearchService
import json

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Dependency Injection
def get_connection_manager():
    config = load_config()
    connection_config = config.get('connection', {})
    return ConcreteConnectionManager(connection_config)

def get_query_service(connection_manager: ConnectionManager = Depends(get_connection_manager)):
    return QueryService(connection_manager)

def get_datacard_service(connection_manager: ConnectionManager = Depends(get_connection_manager)):
    return DatacardService(connection_manager)

# Routes
@app.get("/", response_class=RedirectResponse)
async def read_root():
    return RedirectResponse(url="/chat")

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/render", response_class=HTMLResponse)
async def render():
    try:
        with open("render/datacard/render.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Render file not found")

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
        return JSONResponse(content=result)
    except ValueError as ve:
        logger.error(f"Invalid query: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error in query endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred")

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
        return JSONResponse(content=result)
    except FileNotFoundError as e:
        logger.error(f"Datacard definition not found: {str(e)}")
        raise HTTPException(status_code=404, detail="Datacard definition not found")
    except Exception as e:
        logger.error(f"Error fetching datacard definition: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="An internal server error occurred")

# Instantiate Services for Dependency Injection
search_service = SearchService()
chat_service = ChatService()
query_service = QueryService()

@app.post("/api/chat")
async def chat(request: Request):
    if chat_service is None:
        error_message = "Chat service is not available. Please check the server logs for more information."
        return JSONResponse(content={"error": error_message}, status_code=503)

    form_data = await request.form()
    message = form_data.get('message')
    try:
        chat_history = json.loads(form_data.get('chat_history', '[]'))
    except json.JSONDecodeError:
        logger.error("Invalid chat history format")
        raise HTTPException(status_code=400, detail="Invalid chat history format")

    try:
        logger.debug(f"Processing message: {message}")
        logger.debug(f"Chat history: {chat_history}")
        response = chat_service.process_message(message, chat_history)
        logger.debug(f"Response generated: {response}")

        return JSONResponse(content={
            "message": response['message'],
            "retrieved_information": response['retrieved_information'],
            "suggested_query": response['suggested_query']
        })
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred")

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
    dataset_full_name = data['dataset']
    organization, dataset = dataset_full_name.split('/', 1) if '/' in dataset_full_name else (None, dataset_full_name)
    
    if not organization:
        raise HTTPException(status_code=400, detail="Organization not provided in the dataset name")
    
    try:
        # Execute the query
        results = query_service.execute_query_on_dataset(query, organization, dataset)
        return JSONResponse(content=results)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Dataset configuration for '{dataset_full_name}' not found")
    except Exception as e:
        logger.error(f"Error querying dataset: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error querying dataset: {str(e)}")

# Server Control
if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)