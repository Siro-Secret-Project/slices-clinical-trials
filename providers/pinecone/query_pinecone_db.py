from providers.pinecone.pinecone_connection import PineconeVectorStore
from collections import defaultdict
from providers.openai.openai_connection import OpenAIClient
from database.mongo_db_connection import MongoDBDAO


def query_pinecone_db(query: str, module: str = None) -> dict:
    """
    Queries the Pinecone database to fetch documents related to the provided query and module.

    Parameters:
        query (str): The query to search for.
        module (str): The module to filter the results by.

    Returns:
        dict: The final response with documents fetched from Pinecone and MongoDB.
    """
    final_response = {
        "success": False,
        "message": "Failed to fetch documents",
        "data": None
    }

    try:
        # Generate embedding for the query
        openai_client = OpenAIClient()
        embedding_response = openai_client.generate_embeddings(query)
        embedding = embedding_response["data"].flatten().tolist()

        # Initialize Pinecone vector store
        pinecone_store = PineconeVectorStore()

        # Query Pinecone and fetch similar documents
        filters = {"module": {"$eq": module}} if module else None
        result = pinecone_store.query(vector=embedding, filters=filters, k=30)

        # Process the Response Results
        data = result

        # Prepare a dictionary to store NCT IDs with their related information
        nct_data = defaultdict(lambda: {'count': 0, 'max_score': 0, 'module_max_score': ''})

        # Process the data
        for match in data['matches']:
            nct_id = match['metadata']['nctId']
            module = match['metadata']['module']
            score = match['score']
            value = match['values']

            # Update the count
            nct_data[nct_id]['count'] += 1

            # Update the max score and corresponding module
            if score > nct_data[nct_id]['max_score']:
                nct_data[nct_id]['max_score'] = score
                nct_data[nct_id]['module_max_score'] = module
                nct_data[nct_id]['embeddings'] = value

        # Prepare the final response data
        final_data = []

        # Fetch all documents in once
        nctId_list = [key for key, value in nct_data.items()]
        # Mongo Client
        mongo_client = MongoDBDAO(database_name="SSP-dev")

        similar_documents = mongo_client.find(
            collection_name="t2dm_final_data_samples_processed",
            query={"nctId": {"$in": nctId_list}},
            projection={"_id": 0}
        )

        id2doc = {item["nctId"]:item for item in similar_documents}


        for key, value in nct_data.items():
            nctId = key
            module = value['module_max_score']
            similarity_score = int(value['max_score'] * 100)
            if similarity_score < 10:
                continue
            else:
                document_response = id2doc[nctId]
                final_data.append({
                        "nctId": nctId,
                        "module": module,
                        "similarity_score": similarity_score,
                        "document": document_response
                })

        # Return the final response
        final_response['data'] = final_data
        final_response['success'] = True
        final_response['message'] = "Successfully fetched documents"

    except Exception as e:
        final_response['message'] = f"Error occurred: {str(e)}"

    return final_response
