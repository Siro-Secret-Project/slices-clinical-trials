from fastapi import APIRouter, Response, status
from database.trial_criteria_generation.save_empty_document import save_empty_document
from trial_criteria_generation.models.routes_models import BaseResponse, GenerateEligibilityCriteria
from trial_criteria_generation.services.generate_trial_eligibility_criteria import generate_trial_eligibility_criteria

# setup API Router
router = APIRouter()
global worker_process

@router.post("/generate_trial_eligibility_criteria", response_model=BaseResponse)
async def generate_trial_eligibility_criteria_route(request: GenerateEligibilityCriteria, response: Response):
    global worker_process
    base_response = BaseResponse(
        success=False,
        status_code=status.HTTP_400_BAD_REQUEST,
        data=None,
        message="Internal Server Error"
    )

    try:
        # workers = Worker.all(connection=redis_conn)
        #
        # # Start worker in burst mode if none exist
        # if not workers:
        #     worker_process = subprocess.Popen(
        #         [
        #             "rq", "worker", "criteria_task_queue",
        #             "--burst",
        #             "--name", f"auto_worker_{os.getpid()}",
        #             "--with-scheduler"
        #         ],
        #         env={**os.environ, "REDIS_URL": redis_url}
        #     )
        #
        #     base_response.message = "Started burst worker and enqueued jobs"
        # else:
        #     base_response.message = "Enqueued jobs to existing worker"

        # Original job enqueueing logic
        trialId = request.trialId
        trial_documents = request.trialDocuments
        save_empty_document(trialId=trialId) # Create an Empty Document to store Jobs

        batch_size = 10
        batches = [trial_documents[i:i + batch_size] for i in range(0, len(trial_documents), batch_size)]
        job_ids = []

        # for idx, batch in enumerate(batches):
        #     job = task_queue.enqueue(
        #         generate_trial_eligibility_criteria,
        #         trialId=trialId, trail_documents_ids=batch, total_batches_count=len(batches), current_batch_num=idx + 1,
        #         job_timeout=600,
        #         result_ttl=86400  # Keep results for 24 hours
        #     )
        #     job_ids.append(job.id)
        service_response = generate_trial_eligibility_criteria(trialId=trialId,
                                                               trail_documents_ids=trial_documents,
                                                               total_batches_count=3,
                                                               current_batch_num=3)
        if service_response["success"] is True:
            base_response.success = True
            base_response.status_code = status.HTTP_200_OK
            base_response.data = service_response["data"]
            response.status_code = status.HTTP_200_OK
            base_response.message = service_response["message"]
        else:
            base_response.message = service_response["message"]
        return base_response

    except Exception as e:
        # Handle unexpected errors, log them, and update the base response
        print(f"Unexpected error: {e}")
        base_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        base_response.message = f"Unexpected error: {e}"
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return base_response