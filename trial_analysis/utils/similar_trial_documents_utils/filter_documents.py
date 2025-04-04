from trial_analysis.utils.similar_trial_documents_utils.fetch_trial_filters import fetch_trial_filters
from trial_analysis.utils.similar_trial_documents_utils.process_trial_filters import process_filters
def filter_documents(unique_documents: dict, document_filters: dict) -> list:
    """
    Filter documents based on additional filters.

    Args:
        unique_documents (dict): Dictionary of unique documents.
        document_filters (dict): Dictionary containing filters to apply on documents.

    Returns:
        list: List of filtered documents.
    """
    fetch_add_documents_filter_response = fetch_trial_filters(trial_documents=list(unique_documents.values()))
    if fetch_add_documents_filter_response["success"]:
        trial_documents_with_filters = fetch_add_documents_filter_response["data"]
        trial_documents = process_filters(documents=trial_documents_with_filters, filters=document_filters)
        return trial_documents
    return list(unique_documents.values())