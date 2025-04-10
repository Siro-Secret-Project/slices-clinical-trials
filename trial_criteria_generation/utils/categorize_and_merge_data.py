from typing import List, Dict, Any
from agents.TrialEligibilityAgent import TrialEligibilityAgent
from trial_document_search.utils.logger_setup import Logger
from database.mongo_db_connection import MongoDBDAO
from trial_criteria_generation.utils.categorize_generated_criteria import categorize_generated_criteria
from trial_criteria_generation.utils.calculate_trial_operational_score import calculate_trial_operational_score
from trial_criteria_generation.utils.categorize_eligibility_criteria import categorize_eligibility_criteria
from trial_criteria_generation.utils.merge_duplicate_values import merge_duplicate_values, normalize_bmi_ranges

# Setup logger
logger = Logger("trial_criteria_generation").get_logger()

def categorize_and_merge_data(generated_inclusion_criteria: List[Dict[str, Any]],
                             generated_exclusion_criteria: List[Dict[str, Any]],
                             drug_ranges: List[Dict[str, Any]], time_line: List[Dict[str, Any]],
                             eligibility_agent: TrialEligibilityAgent, inclusion_criteria: str, exclusion_criteria: str,
                             trail_documents_ids: List[str]) -> Dict[str, Any]:
    """Categorize and merge generated and user data."""
    categorized_generated_data = {}
    categorized_user_data = {}
    metrics_data = {}
    logger.debug("Categorizing generated criteria")
    try:
        categorized_generated_data = categorize_generated_criteria(
            generated_inclusion_criteria=generated_inclusion_criteria,
            generated_exclusion_criteria=generated_exclusion_criteria
        )
        logger.debug("Generated criteria categorized")
        categorized_generated_data_copy = categorized_generated_data.copy()
        scoring_response = calculate_trial_operational_score(document_id_list=trail_documents_ids,
                                                             categorized_data=categorized_generated_data)

        if scoring_response["success"]:
            categorized_generated_data = scoring_response['data']
        else:
            categorized_generated_data = categorized_generated_data_copy
    except Exception as e:
        logger.error(f"Error categorizing generated criteria: {e}")


    try:
        logger.debug("Categorizing user data")
        categorized_user_data_response = categorize_eligibility_criteria(eligibility_agent, inclusion_criteria, exclusion_criteria)
        categorized_user_data = categorized_user_data_response["data"] if categorized_user_data_response["success"] else {}
        logger.debug("User data categorized")
    except Exception as e:
        logger.error(f"Error categorizing user data: {e}")

    try:
        logger.info(f"DRUG RANGES: {drug_ranges}")
        drug_ranges = normalize_bmi_ranges(drug_ranges)
        drug_ranges = merge_duplicate_values(drug_ranges)
        time_line = merge_duplicate_values(time_line)

        # Initialize MongoDBDAO
        mongo_dao = MongoDBDAO(database_name="SSP-dev") # Using to Read data from SSP-dev. No Write

        # Query DB to fetch Prompt
        response = mongo_dao.find_one(collection_name="LOVs", query={"name": "metrics_prompt_data"})
        if response is None:
            return {}
        else:
            values = response["values"]

        keys = [item["value"].lower() for item in values]

        # Initialize metrics_data dynamically based on keys
        metrics_data = {"timeline": []}
        for key in keys:
            metrics_data[key] = []

        # Categorize drug ranges dynamically
        for item in drug_ranges:
            value = item["value"].lower()
            for key in keys:  # Check if any key is present in value
                if key in value:
                    metrics_data[key].append(item)
                    break  # Avoid duplicate assignments
        for item in time_line:
            metrics_data["timeline"].append(item)

        # Filter Hba1c values
        data = metrics_data["hba1c"]
        logger.debug(f"Old List: {data}")
        for item in data:
            value = item["value"]
            item["value"] = value.replace(".0", "")

        new_list = [item for item in metrics_data["hba1c"] if item["count"] > 0]
        logger.debug(f"New List: {new_list}")
        metrics_data["hba1c"] = new_list

    except Exception as e:
        logger.error(f"Error categorizing metrics data: {e}")


    return {
        "categorized_generated_data": categorized_generated_data,
        "categorized_user_data": categorized_user_data,
        "metrics_data": metrics_data
    }