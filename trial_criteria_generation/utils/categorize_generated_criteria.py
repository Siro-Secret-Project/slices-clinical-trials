import json
import re
from utils.generate_object_id import generate_object_id
from trial_criteria_generation.utils.prompts_file import merge_prompt, llama_prompt
import concurrent.futures
from providers.aws.bedrock_connection import BedrockLlamaClient
from trial_document_search.utils.logger_setup import Logger

# Setup Logger
logger = Logger("trial_criteria_generation").get_logger()


criteria_categories = [
    "Gender", "Health Condition/Status", "Clinical and Laboratory Parameters",
    "Medication Status", "Informed Consent", "Ability to Comply with Study Procedures",
    "Lifestyle Requirements", "Reproductive Status", "Co-morbid Conditions",
    "Recent Participation in Other Clinical Trials", "Allergies and Drug Reactions",
    "Mental Health Disorders", "Infectious Diseases", "Other", "Age"
]

cedric_criteria_categories = ["Common to All Clinical Trials", "Common to Type 2 Diabetes Studies", "Common to the Study Drug", "Other"]



def _generate_tags(criteria_text):
    """
    Generates tags for the given criteria text using Bedrock Llama model.

    Args:
        criteria_text (str): The criteria text to extract tags from.

    Returns:
        list: A list of extracted tags.
    """
    bedrock_llama_client = BedrockLlamaClient()
    processed_input = f"""
      ### Now, extract tags from the following input:
      {criteria_text}
    """
    model_input_prompt = llama_prompt + processed_input
    response = bedrock_llama_client.generate_text_llama(model_input_prompt)

    if response["success"] is False:
        return []

    pattern = r'\{[\s\S]*\}'  # Regex pattern to extract JSON
    match = re.search(pattern, response["data"])
    if match:
        json_str = match.group(0)
        response_json = json.loads(json_str)
        return response_json.get("tags", [])

    return []


def _process_criteria(criteria_list, category):
    try:
        filtered_criteria = [item for item in criteria_list if item["class"] == category]

        if not filtered_criteria:
            return []

        # If the filtered list is greater than 25, split it into two
        if len(filtered_criteria) > 25:
            mid = len(filtered_criteria) // 2
            first_half = filtered_criteria[:mid]
            second_half = filtered_criteria[mid:]

            return _process_criteria(first_half, category) + _process_criteria(second_half, category)

        logger.debug(f"Found {len(filtered_criteria)} criteria for {category}.")

        llama_merge_prompt = merge_prompt +  (f"### This is the list of criteria for merging the duplicates: {filtered_criteria}. "
                                              f"Do not generate any code. Just generate the required output in provided json format.")

        bedrock_client = BedrockLlamaClient()
        llama_response = bedrock_client.generate_text_llama(llama_merge_prompt, max_gen_len=2000)
        try:
            if llama_response["success"] is False:
                logger.exception(f"Failed to fetch merged response: {llama_response['message']}")
                return filtered_criteria
            else:
                pattern = r'\{[\s\S]*\}'  # Regex pattern to extract JSON
                match = re.search(pattern, llama_response["data"])
                if match:
                    json_str = match.group(0)
                    merged_response = json.loads(json_str)
                    merged_response = merged_response.get("response", [])
                    print("Extracted merged response from draft criteria")
                else:
                    logger.exception(f"Failed to fetch merged response: {llama_response['message']}")
                    return filtered_criteria

        except Exception as e:
            logger.exception(f"Failed to parse merged response:{category} {e}")
            return filtered_criteria

        for res in merged_response:
            res["source"] = {}
            for criteria_id in res["criteriaID"]:
                for entry in filtered_criteria:
                    if entry["criteriaID"] == criteria_id:
                        res["source"].update(entry["source"])
            res["criteriaID"] = generate_object_id()

            # Generate Tags
            res["tags"] = _generate_tags(res["criteria"])

        return merged_response
    except Exception as e:
        logger.exception(f"Error processing criteria {category}: {e}")
        return []


def merge_by_tag(data, tags_not_to_consider: list = []):
    """
    Merges entries in the data list based on their tags, combining sources and avoiding redundancy.

    Args:
        data: List of dictionaries containing clinical criteria data with tags
        tags_not_to_consider: List of tags to consider

    Returns:
        List of merged dictionaries with unique tags and combined sources
    """
    tag_to_data = {}  # Dictionary to map tags to merged data

    for item in data:
        for criteria_tag in item["tags"]:
            # Normalize the tag by removing .0 and spaces for consistency
            normalized_tag = criteria_tag.replace(".0", "").strip()
            if normalized_tag in tags_not_to_consider:
                continue
            # If tag not seen before, create new entry
            if normalized_tag not in tag_to_data:
                tag_to_data[normalized_tag] = {
                    "criteria": item["criteria"],
                    "class": item["class"],
                    "source": item["source"].copy(),
                    "tags": {normalized_tag},
                    "criteriaID": item["criteriaID"]  # Keeping first encountered ID
                }
            else:
                # Merge with existing data for this tag
                existing = tag_to_data[normalized_tag]

                # Update sources (union of both)
                existing["source"].update(item["source"])

                # Keep the longer criteria text
                if len(item["criteria"]) > len(existing["criteria"]):
                    existing["criteria"] = item["criteria"]

                # Add any additional tags (though normalized_tag should be same)
                existing["tags"].add(normalized_tag)

    # Convert the dictionary values to a list
    merged_data = list(tag_to_data.values())

    # Convert sets back to lists for consistent output format
    for item in merged_data:
        item["tags"] = list(item["tags"])

    return merged_data


def categorize_generated_criteria(generated_inclusion_criteria, generated_exclusion_criteria):
    """
    Processes inclusion and exclusion criteria in parallel, merges similar criteria,
    updates source mappings, and assigns new object IDs.
    """
    categorized_data = {}
    for class_name in criteria_categories:
        categorized_data.setdefault(class_name, {"Inclusion": [], "Exclusion": []})

    for class_item in criteria_categories:
        current_list = []
        for item in generated_inclusion_criteria:
            for class_name in item["class"]:
                current_list.append(item)
        merged_data = merge_by_tag(current_list)
        categorized_data[class_item]["Inclusion"] = merged_data

    for class_item in criteria_categories:
        current_list = []
        for item in generated_exclusion_criteria:
            for class_name in item["class"]:
                current_list.append(item)
        merged_data = merge_by_tag(current_list)
        categorized_data[class_item]["Inclusion"] = merged_data

    return categorized_data