from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class StoreSimilarTrials(BaseModel):
    ecid: str
    userName: str
    userInput: dict
    similarTrials: list
    createdAt: datetime
    updatedAt: datetime

class JobStatus(BaseModel):
    jobName: str
    completionStatus: bool = False
    success: bool = False
    message: str
    startedAt: datetime
    finishedAt: Optional[datetime] = None

class JobLog(BaseModel):
    ecid: str
    userName: str
    documentSearch: Optional[JobStatus] = None
    criteriaCreation: Optional[JobStatus] = None
    createdAt: datetime
    updatedAt: datetime

class WorkflowStates(BaseModel):
    ecid: str
    step: str
    status: str
    createdAt: datetime
    updatedAt: datetime