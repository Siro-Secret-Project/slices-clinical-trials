import re
import json
from concurrent.futures import ThreadPoolExecutor
from providers.aws.bedrock_connection import BedrockLlamaClient
from trial_criteria_generation.utils.prompts_file import primary_endpoints_tag_prompt


def generate_tags_for_trials(final_similar_trials):
    """
    Process a list of trial endpoints in parallel using 10 threads
    to generate tags via the Bedrock Llama model.

    Args:
        final_similar_trials (list): List of dictionaries containing endpoints.

    Returns:
        list: Updated list with 'tags' added to each item.
    """

    def process_item(item):
        """Process a single item to generate tags."""
        endpoint = item["endpoint"]
        prompt = primary_endpoints_tag_prompt + f"\n### Input endpoint: {endpoint}"
        bedrock_client = BedrockLlamaClient()
        response = bedrock_client.generate_text_llama(prompt, max_gen_len=2000)

        item["tags"] = []
        if response["success"] is False:
            print(response["message"])
        else:
            json_pattern = r'\{[\s\S]*\}'
            match = re.search(json_pattern, response["data"])
            if match:
                json_str = match.group(0)
                json_drug_metrics_output = json.loads(json_str)
                item["tags"] = json_drug_metrics_output.get("tags", [])

    # Run in parallel using 10 threads
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(process_item, final_similar_trials)

    return final_similar_trials