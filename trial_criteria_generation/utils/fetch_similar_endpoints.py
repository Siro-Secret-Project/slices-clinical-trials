import json
from trial_document_search.utils.logger_setup import Logger

# Setup Logger
logger = Logger(name='trial_criteria_generation').get_logger()

def fetch_similar_endpoints(primary_endpoints, openai_client, similar_endpoint_prompt):
    """
    Fetch similar endpoints for each primary endpoint and update final_similar_trials.

    :param primary_endpoints: List of primary endpoint dictionaries.
    :param openai_client: OpenAI client instance.
    :param similar_endpoint_prompt: Prompt to use for similarity comparison.
    """

    completed_ids = set()
    final_similar_trials = []
    try:
        for item in primary_endpoints:
            target_endpoint = item

            # Skip if this endpoint is already processed
            if target_endpoint["endpointID"] in completed_ids:
                print(f"Skipping ID: {target_endpoint['endpointID']}")
                continue

            # Split primary_endpoints into two candidate lists excluding completed ones
            candidate_endpoints_list = [
                [ep for ep in primary_endpoints[:len(primary_endpoints) // 2] if ep["endpointID"] not in completed_ids],
                [ep for ep in primary_endpoints[len(primary_endpoints) // 2:] if ep["endpointID"] not in completed_ids]
            ]

            similar_endpoint_list = []
            for candidate_endpoints in candidate_endpoints_list:
                if not candidate_endpoints:  # Skip empty lists
                    continue

                user_message = f"Now use this target endpoint: {target_endpoint} and these candidate endpoints: {candidate_endpoints} to fetch the similar endpoints."
                messages = [
                    {"role": "system", "content": similar_endpoint_prompt},
                    {"role": "user", "content": user_message}
                ]

                response = openai_client.generate_text(messages=messages, response_format={"type": "json_object"})
                response_message = response["data"].choices[0].message.content
                try:
                    current_list = json.loads(response_message)["response"]
                except json.decoder.JSONDecodeError as e:
                    logger.exception(f"Failed to decode response message: {response_message}: {e}")
                    current_list = []
                similar_endpoint_list.extend(current_list)

            if similar_endpoint_list:  # Only proceed if similarities are found
                similar_endpoints = [
                    {ep["nctId"]: ep["endpoint"]}
                    for ep in primary_endpoints if ep["endpointID"] in similar_endpoint_list
                ]

                final_similar_trials.append({
                    "endpoint": target_endpoint["endpoint"],
                    "endpointID": target_endpoint["endpointID"],
                    "similar_endpoints": similar_endpoints
                })

                # Mark all similar endpoints as completed immediately
                completed_ids.update(similar_endpoint_list)
                completed_ids.add(target_endpoint["endpointID"])
            else:
                completed_ids.add(target_endpoint["endpointID"])

            logger.info(f"Found Similar for: {len(completed_ids)}")
    except Exception as e:
        logger.exception(f"Failed to fetch similar endpoints: {e}")

    return final_similar_trials



