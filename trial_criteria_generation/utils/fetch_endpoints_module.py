from typing import List
from database.mongo_db_connection import MongoDBDAO
from utils.generate_object_id import generate_object_id
from providers.openai.openai_connection import OpenAIClient
from trial_criteria_generation.utils.prompts_file import similar_endpoint_prompt
from trial_criteria_generation.utils.fetch_similar_endpoints import fetch_similar_endpoints
from trial_criteria_generation.utils.generate_tags_for_trials import generate_tags_for_trials


def fetch_endpoints_module(document_ids: List[str]) -> List:
    """Fetch similar endpoints from the database."""
    mongo_client = MongoDBDAO("SSP-dev")

    # fetch documents
    query = {"protocolSection.identificationModule.nctId": {"$in": document_ids}}
    projection = {"_id": 0, "protocolSection": 1}
    documents = mongo_client.find(collection_name="t2dm_data_preprocessed", query=query, projection=projection)

    # create endpoints
    primary_endpoints = []
    for document in documents:
        nctId = document["protocolSection"]["identificationModule"]["nctId"]
        primary_outcomes = document["protocolSection"].get("outcomesModule", {}).get("primaryOutcomes", [])
        for outcome in primary_outcomes:
            objectId = generate_object_id()
            primary_endpoints.append({
                "nctId": nctId,
                "endpoint": f"measure: {outcome.get('measure', None)}, description: {outcome.get('description', None)}, timeFrame: {outcome.get('timeFrame', None)}",
                "endpointID": objectId
            })

    # create a client
    openai_client = OpenAIClient()

    # fetch the similar endpoints
    final_similar_trials = fetch_similar_endpoints(similar_endpoint_prompt=similar_endpoint_prompt,
                                                   openai_client=openai_client,
                                                   primary_endpoints=primary_endpoints)

    # fetch tags
    final_similar_trials = generate_tags_for_trials(final_similar_trials)

    return final_similar_trials

