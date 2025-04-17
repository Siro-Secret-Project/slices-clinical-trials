import re
import json
from trial_criteria_generation.utils import prompts_file as prompts
from typing import Dict, List
from database.mongo_db_connection import MongoDBDAO
from providers.aws.bedrock_connection import BedrockLlamaClient
from trial_criteria_generation.models.db_models import DraftEligibilityCriteria
from trial_document_search.utils.logger_setup import Logger

# Setup Logger
logger = Logger("trial_criteria_generation").get_logger()


class TrialEligibilityAgentV2:
    def __init__(self) -> None:
        self.bedrock_client = BedrockLlamaClient()
        self.mongo_client = MongoDBDAO()
        self.tags_prompts = prompts.tags_generation
        self.medical_writer_agent_role = prompts.medical_writer_agent_role
        self.json_pattern = r'\{[\s\S]*\}'
        self.failure_json_pattern = r'\{\s*"criteria":\s*".*?"\s*,\s*"source":\s*".*?"\s*,\s*"class":\s*".*?"\s*\}'
        self.logs = {}

    def _construct_user_input(self, draft_criteria: DraftEligibilityCriteria) -> str:
        """
        Constructs the user input message for the medical writer agent.

        Args:
            draft_criteria(DraftEligibilityCriteria): The draft criteria inputs

        Returns:
            str: The constructed user input message.
        """
        user_input = f"""
            Medical Trial Rationale: {draft_criteria.sample_trial_rationale}
            Similar/Existing Medical Trial Document: {draft_criteria.similar_trial_documents}
            Trial Conditions: {draft_criteria.user_provided_trial_conditions}
            Trial Outcomes: {draft_criteria.user_provided_trial_outcome},
        """
        self.user_input = user_input
        return user_input

    def _generate_criteria_with_ai(self, user_input: str, system_prompt: str) -> tuple:
        """
        Generates inclusion and exclusion criteria using the AI model.

        Args:
            user_input (str): The constructed user input message.
            system_prompt (str): The system prompt.

        Returns:
            tuple: A tuple containing two lists:
                - inclusion_criteria (List): Generated inclusion criteria.
                - exclusion_criteria (List): Generated exclusion criteria.
        """
        try:
            processed_input = f"""### Now, extract eligibility criteria from the following input:{user_input}"""
            model_input_prompt = system_prompt + processed_input

            # Send the request to the AI model
            response = self.bedrock_client.generate_text_llama(prompt=model_input_prompt, max_gen_len=2000)
            if response["success"] is False:
                logger.error(response["message"])
                return [], []
            else:
                # Regex pattern to extract JSON
                match = re.search(self.json_pattern, response["data"])

                if match:
                    json_str = match.group(0)
                    try:
                        response_json = json.loads(json_str)
                        # Extract inclusion and exclusion criteria from the response
                        inclusion_criteria = response_json.get("inclusionCriteria", [])
                        exclusion_criteria = response_json.get("exclusionCriteria", [])
                        return inclusion_criteria, exclusion_criteria
                    except json.JSONDecodeError as e:
                        logger.error(f"Error generating criteria with AI: {e}")
                        inclusion_str = response["data"].split("exclusionCriteria")[0]
                        exclusion_str = response["data"].split("exclusionCriteria")[1]
                        inclusion_criteria = self._handle_string_to_failure(inclusion_str)
                        exclusion_criteria = self._handle_string_to_failure(exclusion_str)
                        return inclusion_criteria, exclusion_criteria
                else:
                    return [], []
        except Exception as e:
            logger.error(f"Error generating criteria with AI: {e}")
            return [], []

    def _prepare_final_data(self, inclusion_criteria: List, exclusion_criteria: List,
                            similar_trial_documents: Dict) -> Dict:
        """
        Prepares the final data structure for the response.

        Args:
            inclusion_criteria (List): Generated inclusion criteria.
            exclusion_criteria (List): Generated exclusion criteria.
            similar_trial_documents (Dict): A similar document from a database.

        Returns:
            Dict: The final data structure containing all extracted and generated criteria.
        """
        # Add source information to inclusion and exclusion criteria
        for item in inclusion_criteria:
            source_statement = item["source"]
            item["tags"] = self.generate_tags(criteria_text=item["criteria"])
            item["source"] = {similar_trial_documents["nctId"]: source_statement}
        self.logs[similar_trial_documents["nctId"]]["inclusion_tags"] = "Tags generated for inclusion criteria"
        logger.debug(f"Inclusion criteria Tags generated for NCT ID: {similar_trial_documents['nctId']}")


        for item in exclusion_criteria:
            source_statement = item["source"]
            item["tags"] = self.generate_tags(criteria_text=item["criteria"])
            item["source"] = {similar_trial_documents["nctId"]: source_statement}
        self.logs[similar_trial_documents["nctId"]]["exclusion_tags"] = "Tags generated for excluding criteria"
        logger.debug(f"Exclusion criteria Tags generated for NCT ID: {similar_trial_documents['nctId']}")

        final_eligibility_response = {
            "inclusionCriteria": inclusion_criteria,
            "exclusionCriteria": exclusion_criteria
        }
        self.final_eligibility_response = final_eligibility_response
        return final_eligibility_response

    def generate_eligibility_criteria(self, draft_criteria: DraftEligibilityCriteria) -> dict:

        final_response = {
            "success": False,
            "message": "",
            "data": None
        }
        try:
            nctId = draft_criteria.nctId
            self.logs[nctId] = {}
            # Construct the user input message for the medical writer agent
            user_input = self._construct_user_input(draft_criteria=draft_criteria)
            logger.info(f"User Input generated for NCT ID: {nctId}")
            self.logs[nctId]["user_input"] = "User Input generated"

            # Generate criteria using the AI model
            inclusion_criteria, exclusion_criteria = self._generate_criteria_with_ai(user_input,
                                                                                     self.medical_writer_agent_role)
            logger.info(f"Criteria generated for NCT ID: {nctId}")
            self.logs[nctId]["criteria_generated"] = "Criteria generated"

            # Prepare the final data structure
            final_data = self._prepare_final_data(inclusion_criteria, exclusion_criteria,
                                                  draft_criteria.similar_trial_documents)
            logger.info(f"Final data generated for NCT ID: {nctId}")

            # Generated Tags for the criteria

            self.logs[nctId]["final_data"] = "Final data generated"

            final_response.update({
                "success": True,
                "data": final_data,
                "message": "Successfully generated eligibility criteria"
            })

            return final_response
        except Exception as e:
            logger.error(f"Error generating eligibility criteria: {e}")
            final_response["success"] = False
            final_response["message"] = str(e)
            return final_response

    def _handle_string_to_failure(self, criteria_string: str) -> List:
        try:
            # Find all matches
            matches = re.findall(self.failure_json_pattern, criteria_string, re.DOTALL)
            # Optional: Convert each match to a Python dictionary
            sub_jsons = []
            for match in matches:
                try:
                    sub_json = json.loads(match)
                    sub_jsons.append(sub_json)
                except json.JSONDecodeError as e:
                    print(f"Failed to parse: {match}\nError: {e}")

            # Return the JSONs list
            return sub_jsons
        except Exception as e:
            logger.error(f"Error handling string to failure: {e}")
            return []

    def generate_tags(self, criteria_text):
        """
        Generates tags for the given criteria text using Bedrock Llama model.

        Args:
            criteria_text (str): The criteria text to extract tags from.

        Returns:
            list: A list of extracted tags.
        """
        try:
            processed_input = f"""### Now, extract tags from the following input: {criteria_text}"""
            model_input_prompt = self.tags_prompts + processed_input
            response = self.bedrock_client.generate_text_llama(model_input_prompt)

            if response["success"] is False:
                logger.exception(response["message"])
                return []

            pattern = r'\{[\s\S]*\}'  # Regex pattern to extract JSON
            match = re.search(pattern, response["data"])
            if match:
                json_str = match.group(0)
                try:
                    response_json = json.loads(json_str)
                    return response_json.get("tags", [])
                except Exception as e:
                    logger.info(f"String: {json_str}")
                    logger.error(f"Error generating tags: {e}")
                    return []

            return []
        except Exception as e:
            logger.exception(e)
            return []