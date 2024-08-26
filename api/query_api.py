# api/query_api.py

from fastapi import FastAPI
import uvicorn

class QueryAPI:
    def __init__(self, host: str, port: int):
        self.app = FastAPI()
        self.host = host
        self.port = port

        @self.app.get("/")
        def read_root():
            return {"message": "Data Query API"}

        @self.app.get("/query")
        def query_data(q: str):
            # TODO: Implement query execution using DuckDB
            return {"query": q, "result": "Not implemented yet"}

    def start(self):
        uvicorn.run(self.app, host=self.host, port=self.port)