from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from typing import List, Dict

class StoreEligibilityCriteria(BaseModel):
    trialId: str
    categorizedData: dict
    userCategorizedData: dict
    metrics: dict
    primary_endpoints: list
    createdAt: datetime
    updatedAt: datetime

class NotificationData(BaseModel):
    trialId: str
    userName: str
    notificationMessage: str
    seen: bool = False
    createdAt: datetime
    updatedAt: datetime

class WorkflowStates(BaseModel):
    trialId: str
    step: str
    status: str
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
    trialId: str
    userName: str
    documentSearch: Optional[JobStatus] = None
    criteriaCreation: Optional[JobStatus] = None
    createdAt: datetime
    updatedAt: datetime

class CriteriaItem(BaseModel):
    criteria: str
    criteriaID: str
    source: Dict[str, str]
    tags: List[str]
    operational_score: float
    count: int
    percentile: float

class InclusionExclusion(BaseModel):
    Inclusion: List[CriteriaItem]
    Exclusion: List[CriteriaItem]

class CategorizedData(BaseModel):
    Age: InclusionExclusion
    Gender: InclusionExclusion
    Health_Condition_Status: InclusionExclusion
    Clinical_and_Laboratory_Parameters: InclusionExclusion
    Medication_Status: InclusionExclusion
    Informed_Consent: InclusionExclusion
    Ability_to_Comply_with_Study_Procedures: InclusionExclusion
    Lifestyle_Requirements: InclusionExclusion
    Reproductive_Status: InclusionExclusion
    Co_morbid_Conditions: InclusionExclusion
    Recent_Participation_in_Other_Clinical_Trials: InclusionExclusion
    Allergies_and_Drug_Reactions: InclusionExclusion
    Mental_Health_Disorders: InclusionExclusion
    Infectious_Diseases: InclusionExclusion
    Other: InclusionExclusion

class DraftEligibilityCriteria(BaseModel):
    sample_trial_rationale: str
    similar_trial_documents: Dict
    user_provided_inclusion_criteria: str
    user_provided_exclusion_criteria: str
    user_provided_trial_conditions: str
    user_provided_trial_outcome: str
    generated_inclusion_criteria: Optional[List] = None
    generated_exclusion_criteria: Optional[List] = None
