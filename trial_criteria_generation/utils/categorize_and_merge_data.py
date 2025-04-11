from typing import List, Dict, Any
from agents.TrialEligibilityAgent import TrialEligibilityAgent
from trial_document_search.utils.logger_setup import Logger
from trial_criteria_generation.utils.categorize_generated_criteria import categorize_generated_criteria
from trial_criteria_generation.utils.calculate_trial_operational_score import calculate_trial_operational_score
from trial_criteria_generation.utils.categorize_eligibility_criteria import categorize_eligibility_criteria

# Setup logger
logger = Logger("trial_criteria_generation").get_logger()

def categorize_and_merge_data(generated_inclusion_criteria: List[Dict[str, Any]],
                             generated_exclusion_criteria: List[Dict[str, Any]],
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


    return {
        "categorized_generated_data": categorized_generated_data,
        "categorized_user_data": categorized_user_data,
        "metrics_data": metrics_data
    }