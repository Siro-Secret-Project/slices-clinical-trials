from database.mongo_db_connection import MongoDBDAO
from datetime import datetime
from trial_document_search.utils.logger_setup import Logger

# Setup Logger
logger = Logger("trial_criteria_generation").get_logger()

# Initialize MongoDBDAO
mongo_client = MongoDBDAO()


def record_eligibility_criteria_job(
        job_id: str,
        categorized_data: dict,
        categorized_data_user: dict,
        metrics_data: dict,
        primary_endpoints: list,
) -> dict:
    """
    Stores or updates eligibility criteria in MongoDB.
    - For existing documents, extends Inclusion/Exclusion lists instead of replacing them.
    - Preserves the original creation date.
    - Updates metrics and primary endpoints.

    Args:
        job_id (str): Unique identifier for the job (trialId).
        categorized_data (dict): New categorized eligibility criteria.
        categorized_data_user (dict): New user-provided categorized criteria.
        metrics_data (dict): New metrics data.
        primary_endpoints (list): New primary endpoints.

    Returns:
        dict: Response containing success status, message, and data.
    """
    final_response = {
        "success": False,
        "message": "Failed to store similar trials criteria results",
        "data": None,
    }

    try:
        # Add Mapping
        mapping = {
            "Informed Consent": "Informed_Consent",
            "Lifestyle Requirements": "Lifestyle_Requirements",
            "Ability to Comply with Study Procedures": "Ability_to_Comply_with_Study_Procedures",
            "Reproductive Status": "Reproductive_Status",
            "Recent Participation in Other Clinical Trials": "Recent_Participation_in_Other_Clinical_Trials",
            "Allergies and Drug Reactions": "Allergies_and_Drug_Reactions",
            "Mental Health Disorders": "Mental_Health_Disorders",
            "Infectious Diseases": "Infectious_Diseases",
            "Other": "Other",
            "Co-morbid Conditions": "Co_morbid_Conditions",
            "Medication Status": "Medication_Status",
            "Age": "Age",
            "Clinical and Laboratory Parameters": "Clinical_and_Laboratory_Parameters",
            "Health Condition/Status": "Health_Condition_Status",
            "Gender": "Gender"
        }

        updated_categorized_data = {}
        for key, value in categorized_data.items():
            updated_categorized_data[mapping[key]] = value

        updated_user_categorized_data = {}
        for key, value in categorized_data_user.items():
            updated_user_categorized_data[mapping[key]] = value

        logger.debug(f"Retrieving eligibility criteria for job {job_id}")
        existing_doc = mongo_client.find_one(
            "similar_trials_criteria_results",
            {"trialId": job_id}
        )
        created_at = existing_doc.get("createdAt", datetime.now()) if existing_doc else datetime.now()

        # Initialize new data structures
        new_categorized = {}
        new_user_categorized = {}

        for category in list(mapping.values()):
          new_categorized[category] = {
              "Inclusion": existing_doc["categorizedData"][category]["Inclusion"] +
                           updated_categorized_data.get(category, {}).get("Inclusion", []),
              "Exclusion": existing_doc["categorizedData"][category]["Exclusion"] +
                           updated_categorized_data.get(category, {}).get("Exclusion", [])
          }

        for category in list(mapping.values()):
          new_user_categorized[category] = {
              "Inclusion": existing_doc["userCategorizedData"][category]["Inclusion"] +
                           updated_user_categorized_data.get(category, {}).get("Inclusion", []),
              "Exclusion": existing_doc["userCategorizedData"][category]["Exclusion"] +
                           updated_user_categorized_data.get(category, {}).get("Exclusion", [])
          }

        # Add the current metrics and primary endpoints data in existing data
        existing_metrics = existing_doc["metrics"]
        merged_metrics_dict = {
            key: existing_metrics.get(key, []) + metrics_data.get(key, [])
            for key in existing_metrics.keys() | metrics_data.keys()
        }

        exising_primary_endpoints = existing_doc["primary_endpoints"]
        new_primary_endpoints = exising_primary_endpoints + primary_endpoints
        # Prepare the final document
        document = {
            "trialId": job_id,
            "categorizedData": new_categorized,
            "userCategorizedData": new_user_categorized,
            "metrics": merged_metrics_dict,
            "primary_endpoints": new_primary_endpoints,
            "createdAt": created_at,
            "updatedAt": datetime.now(),
        }

        # # Upsert into MongoDB
        db_response = mongo_client.update(
            collection_name="similar_trials_criteria_results",
            update_values=document,
            query={"trialId": job_id},
            upsert=False,
        )

        # Return the response
        if db_response:
            final_response.update(
                success=True,
                message=f"Successfully updated criteria for job: {job_id}",
                data=db_response,
            )
            logger.debug(f"Successfully updated criteria for job: {job_id}-{db_response}")

    except Exception as e:
        final_response["message"] = f"Error updating criteria: {str(e)}"
        logger.error(f"Error updating criteria for job: {job_id}: {str(e)}")
        response = mongo_client.insert(
            collection_name="similar_trials_criteria_results_failed",
            document={
                "trialId": job_id,
                "categorizedData": categorized_data,
                "userCategorizedData": categorized_data_user,
                "metrics": metrics_data,
                "primary_endpoints": primary_endpoints,
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
            },
        )
        logger.debug(f"Successfully inserted Failed criteria for job: {job_id}-{response.inserted_id}")

    return final_response