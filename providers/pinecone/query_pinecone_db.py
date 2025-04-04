from providers.pinecone.pinecone_connection import PineconeVectorStore
from providers.openai.openai_connection import OpenAIClient
from database.mongo_db_connection import MongoDBDAO


def query_pinecone_db(query: str, module: str = None) -> dict:
    """Query Pinecone for documents related to the query and module."""
    response = {"success": False, "message": "Failed to fetch documents", "data": None}

    try:
        # Generate embedding
        embedding = OpenAIClient().generate_embeddings(query)["data"].flatten().tolist()

        # Query Pinecone
        results = PineconeVectorStore().query(
            vector=embedding,
            filters={"module": {"$eq": module}} if module else None,
            k=30
        )['matches']

        if not results:
            return {**response, "message": "No matching documents found"}

        # Process results
        nct_data = {}
        for match in results:
            nct_id = match['metadata']['nctId']
            if nct_id not in nct_data or match['score'] > nct_data[nct_id]['score']:
                nct_data[nct_id] = {
                    'score': match['score'],
                    'module': match['metadata']['module'],
                    'values': match['values']
                }

        # Fetch documents from MongoDB
        docs = MongoDBDAO("SSP-dev").find(
            "t2dm_final_data_samples_processed",
            {"nctId": {"$in": list(nct_data.keys())}},
            {"_id": 0}
        )

        # Prepare final response
        response['data'] = [
            {
                "nctId": nct_id,
                "module": data['module'],
                "similarity_score": int(data['score'] * 100),
                "document": next(d for d in docs if d["nctId"] == nct_id)
            }
            for nct_id, data in nct_data.items()
            if int(data['score'] * 100) >= 10
        ]
        response.update(success=True, message="Successfully fetched documents")

    except Exception as e:
        response['message'] = f"Error occurred: {str(e)}"
        print(f"Error occurred: {str(e)}")

    return response