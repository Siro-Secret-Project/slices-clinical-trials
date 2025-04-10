from typing import Dict, Any, List
from trial_criteria_generation.models.db_models import DraftEligibilityCriteria
from agents.TrialEligibilityAgent import TrialEligibilityAgent

def process_batch(batch: Dict[str, Any], eligibility_agent: TrialEligibilityAgent, user_inputs: Dict[str, Any],
                 generated_inclusion_criteria: List[Any], generated_exclusion_criteria: List[Any]) -> Dict[str, Any]:
    """Process a batch of similar trial documents."""
    draft_criteria = DraftEligibilityCriteria(
        sample_trial_rationale=user_inputs.get("rationale") or "No rationale provided",
        similar_trial_documents=batch,
        user_provided_inclusion_criteria=user_inputs.get("inclusionCriteria") or "No inclusion Criteria provided",
        user_provided_exclusion_criteria=user_inputs.get("exclusionCriteria") or "No exclusion Criteria provided",
        user_provided_trial_outcome=user_inputs.get("trialOutcomes") or "No trail outcomes provided",
        user_provided_trial_conditions=user_inputs.get("condition") or "No condition provided",
        generated_inclusion_criteria=generated_inclusion_criteria,
        generated_exclusion_criteria=generated_exclusion_criteria

    )
    response = eligibility_agent.draft_eligibility_criteria(draft_criteria=draft_criteria)
    if not response["success"]:
        return {"error": response["message"]}
    return response["data"]