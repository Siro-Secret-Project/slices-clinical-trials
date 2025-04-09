import concurrent.futures
from datetime import datetime
from typing import List, Dict, Any
from agents.TrialEligibilityAgent import TrialEligibilityAgent
from database.trial_document_search.job_status import add_job, update_job
from database.trial_document_search.update_workflow_status import update_workflow_status
from database.trial_criteria_generation.store_notification_data import store_notification_data
from database.trial_criteria_generation.record_eligibility_criteria_job import record_eligibility_criteria_job
from trial_document_search.utils.logger_setup import Logger
from trial_criteria_generation.utils.process_batch import process_batch
from trial_criteria_generation.utils.assign_unique_ids import assign_unique_ids
from trial_criteria_generation.utils.fetch_user_inputs import fetch_user_inputs
from trial_criteria_generation.utils.fetch_endpoints_module import fetch_endpoints_module
from trial_criteria_generation.utils.fetch_additional_metrics import fetch_additional_metrics
from trial_criteria_generation.utils.prepare_similar_documents import prepare_similar_documents
from trial_criteria_generation.utils.categorize_and_merge_data import categorize_and_merge_data


# Setup Logger
logger = Logger("trial_eligibility_criteria").get_logger()

def generate_trial_eligibility_criteria(trialId: str, trail_documents_ids: List[str],
                                        total_batches_count:int, current_batch_num: int) -> Dict[str, Any]:
    """Generate trial eligibility criteria in batches of 2 documents."""
    final_response = {
        "success": False,
        "message": "",
        "data": None
    }

    # Add Criteria Creation Search Job to Job Log
    add_job_response = add_job(trialId=trialId, job_id=2)
    logger.debug(add_job_response["message"])
    try:
        # Fetch the user inputted and results
        user_inputs_data = fetch_user_inputs(trialId=trialId)
        user_inputs = user_inputs_data["userInput"]
        trial_documents = user_inputs_data["similarTrials"]

        # Fetch the documents details and sort them based on similarity score
        logger.debug("Fetching Similar documents")
        similar_documents = prepare_similar_documents(trial_documents, trail_documents_ids)
        logger.info(f"{len(similar_documents)} similar documents found")

        # Create an Object for the TrialEligibilityAgent
        eligibility_agent = TrialEligibilityAgent()

        # Create Empty Lists to store the outputs
        generated_inclusion_criteria = []
        generated_exclusion_criteria = []
        drug_ranges = []
        time_line = []

        logger.debug(f"Generating trial eligibility criteria")
        batches = [similar_documents[i] for i in range(0, len(similar_documents))]

        # Run the Jobs to draft the eligibility Criteria and their tags
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_batch = {executor.submit(process_batch, batch, eligibility_agent, user_inputs, generated_inclusion_criteria, generated_exclusion_criteria): batch for batch in batches}

            for future in concurrent.futures.as_completed(future_to_batch):
                result = future.result()
                if "error" in result:
                    final_response["message"] = result["error"]
                    break
                # Merge the Latest Generated data with the existing list
                generated_inclusion_criteria.extend(result["inclusionCriteria"])
                generated_exclusion_criteria.extend(result["exclusionCriteria"])
                drug_ranges.extend(result["drugRanges"])
                time_line.extend(result["timeFrame"])

        # Add unique ids to each criteria
        assign_unique_ids(generated_inclusion_criteria)
        assign_unique_ids(generated_exclusion_criteria)
        logger.debug(f"Generated trial eligibility criteria")

        # Categorize the Generated and User Provided data into Predefined buckets
        logger.debug("Categorizing Generated Eligibility")
        similar_documents_ids = [item["nctId"] for item in trial_documents]
        categorized_data = categorize_and_merge_data(
            generated_inclusion_criteria, generated_exclusion_criteria, drug_ranges, time_line,
            eligibility_agent, user_inputs.get("inclusionCriteria", "No inclusion criteria provided"),
            user_inputs.get("exclusionCriteria", "No exclusion criteria provided"),
            trail_documents_ids=similar_documents_ids
        )
        logger.debug(f"Categorized Generated Eligibility")

        # Fetch the Additional Metrics from the documents
        additional_metrics_response = fetch_additional_metrics(trial_document_ids=trail_documents_ids)
        if additional_metrics_response["success"] is False:
            logger.debug(f"Failed to fetch additional metrics")
            logger.debug(additional_metrics_response["message"])
            metrics_data = categorized_data["metrics_data"]
        else:
            logger.debug(f"Successfully fetched additional metrics")
            metrics_data = additional_metrics_response["data"] | categorized_data["metrics_data"]

        # Fetch the metrics from the Primary Endpoint Module
        primary_endpoints = fetch_endpoints_module(trail_documents_ids)

        # Store the data and workflow status into Mongo DB
        db_response = record_eligibility_criteria_job(trialId, categorized_data["categorized_generated_data"], categorized_data["categorized_user_data"], metrics_data, primary_endpoints)
        store_notification_data(trialId=trialId)

        final_response["data"] = primary_endpoints
        final_response["success"] = True
        final_response["message"] = db_response.get("message", "Successfully generated trial eligibility criteria.")

    except Exception as e:
        final_response['message'] = f"Failed to generate trial eligibility criteria. Error: {e}"
        logger.error(f"Failed to generate trial eligibility criteria. Error: {e}")

    finally:
        if total_batches_count == current_batch_num:
            # Update Workflow status
            update_workflow_status(trialId=trialId, step="similar-criteria")

            # Update Job Status
            update_values = {"criteriaCreation.completionStatus": True,
                             "criteriaCreation.success": final_response["success"],
                             "criteriaCreation.finishedAt": datetime.now(),
                             "criteriaCreation.message": final_response["message"]}
            update_job_response = update_job(trialId=trialId, job_id=2, update_fields=update_values)
            logger.debug(update_job_response["message"])
        else:
            print("*"*100)
            logger.debug(f"Successfully completed batch: {current_batch_num}/{total_batches_count}")
            print("#"*100)

    return final_response