import uvicorn
import asyncio
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from api.query import QueryModel
from api.services import QueryService, DatacardService
from data_binding.database_engine import ConnectionManager
import logging


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_connection_manager():
    # This function should return a properly initialized ConnectionManager
    # You may need to add necessary parameters or configuration here
    return ConnectionManager()

def get_query_service(connection_manager: ConnectionManager = Depends(get_connection_manager)):
    return QueryService(connection_manager)

def get_datacard_service(connection_manager: ConnectionManager = Depends(get_connection_manager)):
    return DatacardService(connection_manager)

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("render/datacard/render.html", "r") as f:
        content = f.read()
    return HTMLResponse(content=content)

@app.post("/query/{organization}/{dataset}")
async def query(
    organization: str,
    dataset: str,
    query_model: QueryModel,
    service: QueryService = Depends(get_query_service)
):
    try:
        result = service.execute_query_on_dataset(query_model, organization, dataset)
        return result
    except Exception as e:
        logger.error(f"Error in query endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/datacard/{organization}/{definition}")
async def get_datacard(
    organization: str,
    definition: str,
    service: DatacardService = Depends(get_datacard_service)
):
    try:
        return service.get_datacard(organization, definition)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Datacard definition not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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