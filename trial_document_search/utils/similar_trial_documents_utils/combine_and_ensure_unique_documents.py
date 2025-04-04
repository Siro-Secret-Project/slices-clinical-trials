def combine_and_ensure_unique_documents(documents: list) -> dict:
    """
    Combine all documents and ensure uniqueness by retaining the entry with the highest similarity score.

    Args:
        documents (list): List of documents to combine.

    Returns:
        dict: Dictionary of unique documents with the highest similarity score.
    """
    unique_documents = {}
    for doc in documents:
        nctId = doc["nctId"]
        if nctId not in unique_documents or doc["similarity_score"] > unique_documents[nctId]["similarity_score"]:
            unique_documents[nctId] = doc
    return unique_documents