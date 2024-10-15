from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field
from models.retrieved_info import RetrievedInfo
from datetime import datetime

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"] = Field(..., description="The role of the message sender")
    content: str = Field(..., description="The content of the message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of when the message was sent")

class ChatHistory(BaseModel):
    messages: List[ChatMessage] = Field(default_factory=list, description="List of chat messages")

    def add_message(self, role: Literal["user", "assistant", "system"], content: str):
        self.messages.append(ChatMessage(role=role, content=content))

    def get_last_n_messages(self, n: int) -> List[ChatMessage]:
        return self.messages[-n:]

class SuggestedQuery(BaseModel):
    query: str = Field(..., description="The suggested query string")
    dataset: str = Field(..., description="The dataset to query")
    parameters: Dict = Field(default_factory=dict, description="Additional query parameters")

class CodeExecutionResult(BaseModel):
    output: Optional[str] = Field(None, description="The output of the code execution")
    error: Optional[str] = Field(None, description="Any error message from the code execution")
    plot: Optional[str] = Field(None, description="Base64 encoded plot image, if generated")
    dataframes: Optional[Dict[str, str]] = Field(None, description="Dictionary of dataframe names and their string representations")

class ChatResult(BaseModel):
    message: str = Field(..., description="The final response message")
    retrieved_information: RetrievedInfo = Field(..., description="Retrieved information from datasets and datacards")
    suggested_query: Optional[SuggestedQuery] = Field(None, description="Suggested query for data analysis")
    code_execution_result: Optional[CodeExecutionResult] = Field(None, description="Results of code execution, if any")

class ChatSession(BaseModel):
    session_id: str = Field(..., description="Unique identifier for the chat session")
    history: ChatHistory = Field(default_factory=ChatHistory, description="Chat history for the session")
    current_result: Optional[ChatResult] = Field(None, description="The most recent chat result")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of when the session was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the last update to the session")

    def add_message(self, role: Literal["user", "assistant", "system"], content: str):
        self.history.add_message(role, content)
        self.updated_at = datetime.utcnow()

    def set_current_result(self, result: ChatResult):
        self.current_result = result
        self.updated_at = datetime.utcnow()
