from trial_document_search.utils.logger_setup import logger
from database.trial_analysis.job_status import create_empty_job, add_job
from trial_document_search.utils.similar_trial_documents_utils.fetch_similar_document_using_pinecone import fetch_similar_documents_using_pinecone
from trial_document_search.utils.similar_trial_documents_utils.combine_and_ensure_unique_documents import combine_and_ensure_unique_documents
from trial_document_search.utils.similar_trial_documents_utils.filter_documents import filter_documents
from trial_document_search.utils.similar_trial_documents_utils.store_and_return_empty_response import store_and_return_empty_response
from trial_document_search.utils.similar_trial_documents_utils.calculate_weighted_similarity_scores import calculate_weighted_similarity_scores
from trial_document_search.utils.similar_trial_documents_utils.store_similar_trials_and_update_status import store_similar_trials_and_update_status

def fetch_similar_trail_documents(documents_search_keys: dict, custom_weights: dict, document_filters: dict, user_data: dict) -> dict:
    """
    Fetch similar documents based on inclusion criteria, exclusion criteria, and trial rationale,
    ensuring unique values in the final list by retaining the entry with the highest similarity score.

    Args:
        documents_search_keys (dict): Dictionary containing search keys for documents.
        custom_weights (dict): Dictionary containing custom weights for similarity score calculation.
        document_filters (dict): Dictionary containing filters to apply on documents.
        user_data (dict): Dictionary containing user-specific data.

    Returns:
        dict: Response dictionary with success status, message, and data.
    """
    final_response = {
        "success": False,
        "message": "No Documents Found matching criteria.",
        "data": None,
    }

    user_inputs = documents_search_keys | document_filters
    trial_documents = []

    # Create an Empty Job Log with no Job
    create_job_response = create_empty_job(ecid=user_data["ecid"], user_name=user_data["userName"])
    logger.debug(create_job_response["message"])

    # Add Document Search Job to Job Log
    add_job_response = add_job(ecid=user_data["ecid"], job_id=1)
    logger.debug(add_job_response["message"])
    try:

        # Process each criterion and store the results
        logger.debug(f"Pinecone DB Started")
        criteria_documents = fetch_similar_documents_using_pinecone(documents_search_keys)
        logger.debug("Documents fetched")

        # Combine all documents and ensure uniqueness by retaining the highest similarity score
        unique_documents = combine_and_ensure_unique_documents(criteria_documents)
        logger.debug("Unique documents fetched")

        # Filter documents based on additional filters
        trial_documents = filter_documents(unique_documents, document_filters)
        logger.debug("Trial documents fetched")

        if not trial_documents:
            store_and_return_empty_response(user_data, user_inputs, final_response)
            return final_response

        # Calculate weighted average for similarity score
        calculate_weighted_similarity_scores(trial_documents, documents_search_keys, custom_weights)
        logger.debug("Calculated similarity scores")

        # Sort trial documents based on weighted similarity score
        trial_documents = sorted(trial_documents, key=lambda trial_item: trial_item["weighted_similarity_score"], reverse=True)
        logger.debug("Trial documents sorted by weighted similarity score")

        final_response["data"] = trial_documents[:100]
        final_response["success"] = True
        final_response["message"] = "Successfully fetched similar documents extended."

    except Exception as e:
        final_response["message"] += f"Unexpected error occurred while fetching similar documents: {e}"

    finally:
        # Store similar trials and update workflow status
        trial_documents = trial_documents
        store_similar_trials_and_update_status(user_data, user_inputs, trial_documents, final_response)
        logger.debug("Updated similar trials status")

    return final_response