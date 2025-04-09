from typing import  List, Dict, Any
from database.mongo_db_connection import MongoDBDAO


def prepare_similar_documents(trial_documents: List[Dict[str, Any]], trail_documents_ids: List[str]) -> List[Dict[str, Any]]:
    """Fetches Trial Protocol Documents using the given list of Trial Document IDs."""
    similar_documents = []

    # Create an object for Mongo DAO
    mongo_client = MongoDBDAO(database_name="SSP-dev") # Using SSP-dev as Protocol Documents are not present in Trial Axis one

    # Filtered IDs
    filtered_ids = [item["nctId"] for item in trial_documents if item["nctId"] in trail_documents_ids]
    id2score = {item["nctId"]: item["similarity_score"] for item in trial_documents if item["nctId"] in filtered_ids}

    # Query Mongo DB
    similar_documents_response = mongo_client.find(
        collection_name="t2dm_final_data_samples_processed",
        query={"nctId": {"$in": filtered_ids}},
        projection={"_id": 0}
    )

    # Process documents for criteria generation
    for item in similar_documents_response:
        nct_id = item["nctId"]
        similar_documents.append({
            "nctId": nct_id,
            "similarity_score": id2score[nct_id],
            "document": {
            "title": item["officialTitle"],
            "inclusionCriteria": item["inclusionCriteria"],
            "exclusionCriteria": item["exclusionCriteria"],
            "primaryOutcomes": item["primaryOutcomes"],
        }
        })

    similar_documents.sort(key=lambda x: x["similarity_score"], reverse=True)
    return similar_documents

