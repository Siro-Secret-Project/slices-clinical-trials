from database.mongo_db_connection import MongoDBDAO
from datetime import datetime
from trial_document_search.models.db_models import JobLog, JobStatus

# Initialize MongoDB Data Access Object (DAO)
dao = MongoDBDAO()

def create_empty_job(trialId: str, user_name: str) -> dict:
    """
    Creates an empty job log with None for job statuses.
    """
    final_response = {
        "success": False,
        "message": f"Failed to create job log for Trial ID: {trialId}",
        "data": None
    }
    try:
        job_log = JobLog(trialId=trialId, userName=user_name, createdAt=datetime.now(), updatedAt=datetime.now())
        dao.insert("job_status", job_log.model_dump())
        final_response["success"] = True
        final_response["message"] = "Job log created successfully"
        final_response["data"] = job_log.model_dump()
    except Exception as e:
        final_response["message"] = f"Error creating job log: {str(e)}"
    return final_response

def add_job(trialId: str, job_id: int) -> dict:
    """
    Adds a new job to the job log.
    """
    final_response = {
        "success": False,
        "message": f"Failed to add job for Trial ID: {trialId}",
        "data": None
    }
    try:
        id2name = {
            1: "documentSearch",
            2: "criteriaCreation"
        }

        job_name = id2name[job_id]
        job_status = JobStatus(jobName=job_name, startedAt=datetime.now(), message=f"{job_name} Job Started")
        dao.update(
            "job_status",
            {"trialId": trialId},
            {job_name: job_status.model_dump(), "updatedAt": datetime.now()}
        )
        final_response["success"] = True
        final_response["message"] = "Job added successfully"
        final_response["data"] = job_status.model_dump()
    except Exception as e:
        final_response["message"] = f"Error adding job: {str(e)}"
    return final_response

def update_job(trialId: str, job_id: int, update_fields: dict) -> dict:
    """
    Updates an existing job, ensuring finishedAt is only set if startedAt exists.
    """
    final_response = {
        "success": False,
        "message": f"Failed to update job for Trial ID: {trialId}",
        "data": None
    }
    try:
        id2name = {
            1: "documentSearch",
            2: "criteriaCreation"
        }
        job_type = id2name[job_id]
        job_log = dao.find_one("job_status", {"trialId": trialId})
        if not job_log or job_type not in job_log:
            raise ValueError("Job not found")

        existing_job = job_log[job_type]
        if "finishedAt" in update_fields and not existing_job.get("startedAt"):
            raise ValueError("Cannot set finishedAt without a startedAt time")

        dao.update(
            "job_status",
            {"trialId": trialId},
            {**update_fields, "updatedAt": datetime.now()}
        )
        final_response["success"] = True
        final_response["message"] = "Job updated successfully"
        final_response["data"] = update_fields
    except Exception as e:
        final_response["message"] = f"Error updating job: {str(e)}"
    return final_response
