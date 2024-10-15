from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class DatasetInfo(BaseModel):
    name: str = Field(..., description="Name of the dataset")
    description: str = Field(..., description="Description of the dataset")
    fields: List[str] = Field(default_factory=list, description="List of fields in the dataset")
    organization: str = Field(..., description="Organization that owns the dataset")
    dataset_slug: str = Field(..., description="Unique identifier for the dataset")

class DatacardInfo(BaseModel):
    name: str = Field(..., description="Name of the datacard")
    description: str = Field(..., description="Description of the datacard")
    organization: str = Field(..., description="Organization that owns the datacard")
    datacard_slug: str = Field(..., description="Unique identifier for the datacard")

class RetrievedInfo(BaseModel):
    datasets: List[DatasetInfo] = Field(default_factory=list, description="List of relevant datasets")
    datacards: List[DatacardInfo] = Field(default_factory=list, description="List of relevant datacards")

class ChatResult(BaseModel):
    message: str = Field(..., description="The final response message")
    retrieved_information: RetrievedInfo = Field(..., description="Retrieved information from datasets and datacards")
    suggested_query: Optional[Dict] = Field(None, description="Suggested query for data analysis")
    code_execution_result: Optional[Dict] = Field(None, description="Results of code execution, if any")
