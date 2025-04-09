from database.mongo_db_connection import MongoDBDAO
from datetime import datetime
from trial_document_search.models.db_models import StoreSimilarTrials

# Initialize MongoDB Data Access Object (DAO)
mongo_dao = MongoDBDAO()

def store_similar_trials(user_name: str, trialId: str, user_input: dict, similar_trials: list) -> dict:
    """
    Stores the results of similar trials in the MongoDB database.

    Args:
        user_name (str): The name of the user performing the operation.
        trialId (str): The trial ID for the trial.
        user_input (dict): The user-provided input details.
        similar_trials (list): A list of similar trial results to be stored.

    Returns:
        dict: A dictionary containing the status of the operation, message, and stored data if successful.
    """
    final_response = {
        "success": False,
        "message": "Failed to store similar trials results",
        "data": None
    }

    try:
        # Check for existing document to fetch createdAt timestamp
        existing_doc = mongo_dao.find_one(
            collection_name="similar_trials_results",
            query={"trialId": trialId},
            projection={"_id": 0}
        )
        if existing_doc:
            createdAt = existing_doc["createdAt"]
        else:
            createdAt = datetime.now()

        # Create a document instance using the StoreSimilarTrials model
        document = StoreSimilarTrials(
            userName=user_name,
            trialId=trialId,
            userInput=user_input,
            similarTrials=similar_trials,
            createdAt=createdAt,
            updatedAt=datetime.now()   # Timestamp for record update
        )

        # JSON Document
        json_document = document.model_dump()

        # Update the document into the MongoDB collection using DAO
        db_response = mongo_dao.update(
            collection_name="similar_trials_results",
            query={"trialId": trialId},
            update_values=json_document,
            upsert=True
        )

        # Check if the document was successfully inserted
        if db_response:
            final_response["success"] = True
            final_response["message"] = f"Successfully stored similar trials results: {db_response.matched_count}"
            final_response["data"] = db_response

    except Exception as e:
        # Handle any exceptions and update the response with the error message
        final_response["message"] = f"Error storing similar trials criteria results: {e}"

    return final_response
