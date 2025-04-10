from typing import Dict, Any
from database.trial_criteria_generation.fetch_similar_trials_inputs_with_trial_id import fetch_similar_trials_inputs_with_trial_id

def fetch_user_inputs(trialId: str) -> Dict[str, Any]:
    """Fetch user inputs from the database."""
    response = fetch_similar_trials_inputs_with_trial_id(trialId=trialId)
    if not response["success"]:
        raise ValueError(response["message"])
    return response["data"]