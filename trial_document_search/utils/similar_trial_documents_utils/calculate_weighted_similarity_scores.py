import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from providers.openai.openai_connection import OpenAIClient
from database.mongo_db_connection import MongoDBDAO


def _generate_document_embeddings(document: dict) -> dict:
    """Generates embeddings for each section of the provided document.

    Args:
        document (dict): Dictionary containing different sections of the document.

    Returns:
        dict: Dictionary containing section-wise embeddings.
    """
    openai_client = OpenAIClient()
    return {
        section: openai_client.generate_embeddings(content)["data"].flatten().tolist()
        for section, content in document.items()
        if content is not None
    }


def _calculate_cosine_similarity(user_embedding: list, target_embedding: list) -> float:
    """Computes cosine similarity between two embeddings.

    Args:
        user_embedding (list): Embedding vector for user input.
        target_embedding (list): Embedding vector for target document.

    Returns:
        float: Cosine similarity score.
    """
    return cosine_similarity(
        np.array(user_embedding).reshape(1, -1),
        np.array(target_embedding).reshape(1, -1)
    )[0][0]


def _calculate_similarity_score(user_embeddings: dict, weights: dict, target_embeddings: dict) -> dict:
    """Calculates the weighted similarity score between a user input document and a target document.

    Args:
        user_embeddings (dict): Embedded User input document with different sections.
        target_embeddings (dict): Embedded target document
        weights (dict): Dictionary containing similarity weights for each section.

    Returns:
        dict: Dictionary with success status, message, and similarity scores.
    """
    try:
        similarity_scores = {
            module: _calculate_cosine_similarity(user_embeddings[module], target_embeddings[module])
            for module in user_embeddings.keys()
        }

        sum_weights = sum(weights[module] for module in similarity_scores.keys())
        weighted_similarity_score = (
                sum(similarity_scores[module] * weights[module] for module in similarity_scores)
                / sum_weights
        )

        return {
            "success": True,
            "message": "Weighted similarity score calculated successfully",
            "data": {
                "weighted_similarity_score": weighted_similarity_score,
                "similarity_scores": similarity_scores,
            },
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to calculate weighted similarity score: {e}",
            "data": None,
        }


def process_similarity_scores(target_documents_ids: list, user_input_document: dict, weights: dict) -> dict:
    """Processes similarity scores for a list of target documents against a user input document.

    Args:
        target_documents_ids (list): List of target document NCT IDs.
        user_input_document (dict): User-provided document sections.
        weights (dict): Dictionary containing similarity weights.

    Returns:
        dict: Dictionary with success status, message, and list of similarity scores per document.
    """
    try:
        trial_target_documents = []
        # Prepare User Document
        user_document = {
            "inclusionCriteria": user_input_document["inclusionCriteria"],
            "exclusionCriteria": user_input_document["exclusionCriteria"],
            "title": user_input_document["title"],
            "trialOutcomes": user_input_document["trialOutcomes"],
            "condition": user_input_document["condition"],
        }

        # Generate Embeddings for User Document
        user_embeddings = _generate_document_embeddings(user_document)

        print(f"Calculating similarity scores for {len(target_documents_ids)} documents...")
        counter = 0
        # Initialize MongoDBDAO
        mongo_dao = MongoDBDAO(database_name="SSP-dev")

        documents = mongo_dao.find(
            collection_name="t2dm_final_data_samples_processed_embeddings",
            query={"nctId": {"$in": target_documents_ids}},
            projection={"_id": 0}
        )
        for document in documents:
            nct_id = document["nctId"]
            target_embeddings = {
                "inclusionCriteria": document["inclusionCriteria"],
                "exclusionCriteria": document["exclusionCriteria"],
                "title": document["officialTitle"],
                "trialOutcomes": document["primaryOutcomes"],
                "condition": document["conditions"],
            }

            similarity_response = _calculate_similarity_score(
                user_embeddings, weights, target_embeddings
            )
            counter += 1
            print(f"{counter}/{len(target_documents_ids)}: {nct_id}")
            if not similarity_response["success"]:
                print(f"Failed to calculate weighted similarity score for {nct_id}")
                continue

            trial_target_documents.append({
                "nctId": nct_id,
                "weighted_similarity_score": similarity_response["data"]["weighted_similarity_score"],
                "similarity_scores": {
                    module: weights[module] * value
                    for module, value in similarity_response["data"]["similarity_scores"].items()
                },
            })

        return {
            "success": True,
            "message": "Weighted similarity scores processed successfully",
            "data": trial_target_documents,
        }
    except Exception as e:
        print(f"Failed to process weighted similarity scores: {e}")
        return {
            "success": False,
            "message": f"Failed to process weighted similarity scores: {e}",
            "data": None,
        }


def calculate_weighted_similarity_scores(trial_documents: list, documents_search_keys: dict, custom_weights: dict) -> None:
    """
    Calculate weighted similarity scores for trial documents.

    Args:
        trial_documents (list): List of trial documents.
        documents_search_keys (dict): Dictionary containing search keys for documents.
        custom_weights (dict): Dictionary containing custom weights for similarity score calculation.
    """
    nctIds = [item["nctId"] for item in trial_documents]
    weighted_similarity_scores_response = process_similarity_scores(
        target_documents_ids=nctIds,
        user_input_document=documents_search_keys,
        weights=custom_weights,
    )
    if weighted_similarity_scores_response["success"]:
        for item in weighted_similarity_scores_response["data"]:
            for subitem in trial_documents:
                if subitem["nctId"] == item["nctId"]:
                    subitem["weighted_similarity_score"] = item["weighted_similarity_score"]
                    subitem["module_similarity_scores"] = item["similarity_scores"]