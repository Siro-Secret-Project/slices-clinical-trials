from providers.pinecone.query_pinecone_db import query_pinecone_db


def fetch_similar_documents_using_pinecone(documents_search_keys: dict) -> list:
    """
    Process all criteria (inclusion, exclusion, rationale, conditions, outcomes, title) and return combined documents.

    Args:
        documents_search_keys (dict): Dictionary containing search keys for documents.

    Returns:
        list: List of documents processed from all criteria.
    """

    def _process_criteria(criteria: str, module: str = None) -> list:
        """
        Process a single search criteria, query the Pinecone DB, validate documents,
        and return a list of documents with high similarity scores.
        """
        if not criteria:
            return []

        pinecone_response = query_pinecone_db(query=criteria, module=module)

        # generate a final data list
        final_list = []
        for ele in pinecone_response["data"]:
            new_item = {
                "nctId": ele["nctId"],
                "module": ele["module"],
                "similarity_score": ele["similarity_score"],
            }
            final_list.append(new_item)

        return final_list
    inclusion_criteria_documents = _process_criteria(
        documents_search_keys.get("inclusionCriteria"),
        module="eligibilityModule",
    )
    exclusion_criteria_documents = _process_criteria(
        documents_search_keys.get("exclusionCriteria"),
        module="eligibilityModule",
    )
    trial_rationale_documents = _process_criteria(
        documents_search_keys.get("rationale"),
    )
    for item in trial_rationale_documents:
        item["module"] = "trialRationale"

    trial_conditions_documents = _process_criteria(
        documents_search_keys.get("condition"),
        module="conditionsModule",
    )

    trial_outcomes_documents = _process_criteria(
        documents_search_keys.get("trialOutcomes"),
        module="outcomesModule",
    )

    trial_title_documents = _process_criteria(
        documents_search_keys.get("title"),
        module="identificationModule",
    )

    return (
        inclusion_criteria_documents
        + exclusion_criteria_documents
        + trial_rationale_documents
        + trial_conditions_documents
        + trial_outcomes_documents
        + trial_title_documents
    )