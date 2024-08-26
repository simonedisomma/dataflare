# workflow_manager/manager.py

from typing import Dict, List
from workflows.base_workflow import BaseWorkflow
import pandas as pd

class WorkflowManager:
    def __init__(self):
        self.workflows: Dict[str, BaseWorkflow] = {}

    def add_workflow(self, workflow: BaseWorkflow):
        self.workflows[workflow.name] = workflow

    def run_workflow(self, name: str) -> pd.DataFrame:
        if name not in self.workflows:
            raise ValueError(f"Workflow '{name}' not found")
        return self.workflows[name].run()

    def run_all_workflows(self) -> Dict[str, pd.DataFrame]:
        return {name: workflow.run() for name, workflow in self.workflows.items()}

    def get_workflow_metadata(self) -> List[Dict]:
        return [
            {
                "name": workflow.name,
                "start_time": workflow.start_time,
                "end_time": workflow.end_time,
                "duration": workflow.end_time - workflow.start_time if workflow.end_time else None
            }
            for workflow in self.workflows.values()
            if workflow.start_time
        ]