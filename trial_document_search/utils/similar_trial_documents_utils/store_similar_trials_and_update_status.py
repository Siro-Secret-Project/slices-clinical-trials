from database.trial_document_search.store_similar_trials import store_similar_trials
from database.trial_document_search.update_workflow_status import update_workflow_status
from trial_document_search.utils.logger_setup import logger
from datetime import datetime
from database.trial_document_search.job_status import update_job

def store_similar_trials_and_update_status(user_data: dict, user_inputs: dict, trial_documents: list, final_response: dict) -> None:
    """
    Store similar trials and update workflow status.

    Args:
        user_data (dict): Dictionary containing user-specific data.
        user_inputs (dict): Dictionary containing user inputs.
        trial_documents (list): List of trial documents.
        final_response (dict): Dictionary containing final response.
    """
    db_response = store_similar_trials(
        user_name=user_data["userName"],
        trialId=user_data["trialId"],
        user_input=user_inputs,
        similar_trials=trial_documents,
    )
    status_response = update_workflow_status(trialId=user_data["trialId"], step="trial-services")
    logger.debug(status_response)
    logger.debug(db_response)
    # Update Job Log Status
    update_values = {"documentSearch.completionStatus": True,
                     "documentSearch.success": final_response["success"],
                     "documentSearch.finishedAt": datetime.now(),
                     "documentSearch.message": final_response["message"],
                     }
    update_status_response = update_job(trialId=user_data["trialId"],
                                        job_id=1,
                                        update_fields=update_values)
    logger.debug(update_status_response["message"])