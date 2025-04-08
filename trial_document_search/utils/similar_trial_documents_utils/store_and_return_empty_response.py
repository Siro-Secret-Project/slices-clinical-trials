from database.trial_document_search.store_similar_trials import store_similar_trials
from trial_document_search.utils.logger_setup import logger

def store_and_return_empty_response(user_data: dict, user_inputs: dict, final_response: dict) -> None:
    """
    Store similar trials and return an empty response if no documents are found.

    Args:
        user_data (dict): Dictionary containing user-specific data.
        user_inputs (dict): Dictionary containing user inputs.
        final_response (dict): Final response dictionary to update.
    """
    db_response = store_similar_trials(
        user_name=user_data["userName"],
        ecid=user_data["ecid"],
        user_input=user_inputs,
        similar_trials=[],
    )
    logger.debug(f"{db_response}")
    final_response["message"] = "No Documents Found matching criteria."
    final_response["success"] = True
    final_response["data"] = []