from typing import Any
from pydantic import BaseModel

class BaseResponse(BaseModel):
    success: bool
    data: Any
    message: str
    status_code: int


class GenerateEligibilityCriteria(BaseModel):
    trialId: str
    trialDocuments: list


