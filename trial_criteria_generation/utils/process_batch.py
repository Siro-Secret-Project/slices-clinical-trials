from typing import Dict, Any, List
from trial_criteria_generation.models.db_models import DraftEligibilityCriteria
from agents.TrialEligibilityAgentV2 import TrialEligibilityAgentV2

def process_batch(batch: Dict[str, Any], eligibility_agent: TrialEligibilityAgentV2, user_inputs: Dict[str, Any],
                 generated_inclusion_criteria: List[Any], generated_exclusion_criteria: List[Any]) -> Dict[str, Any]:
    """Process a batch of similar trial documents."""
    if batch["document"]["inclusionCriteria"] != "inclusion criteria not available" and batch["document"][
        "exclusionCriteria"] != "exclusion criteria not available":
        draft_criteria = DraftEligibilityCriteria(
            nctId=batch["nctId"],
            sample_trial_rationale=user_inputs.get("rationale") or "No rationale provided",
            similar_trial_documents=batch,
            user_provided_inclusion_criteria=user_inputs.get("inclusionCriteria") or "No inclusion Criteria provided",
            user_provided_exclusion_criteria=user_inputs.get("exclusionCriteria") or "No exclusion Criteria provided",
            user_provided_trial_outcome=user_inputs.get("trialOutcomes") or "No trail outcomes provided",
            user_provided_trial_conditions=user_inputs.get("condition") or "No condition provided",
            generated_inclusion_criteria=generated_inclusion_criteria,
            generated_exclusion_criteria=generated_exclusion_criteria

        )
        response = eligibility_agent.generate_eligibility_criteria(draft_criteria=draft_criteria)
        if not response["success"]:
            return {"error": response["message"]}
        return response["data"]
    else:
        return {
            "inclusionCriteria":[],
            "exclusionCriteria":[],
        }
