import os
import boto3
import json
from dotenv import load_dotenv
from botocore.exceptions import ClientError


class BedrockLlamaClient:
    """
    A client for interacting with AWS Bedrock Llama 3 model.

    This class provides methods to generate text responses using the Bedrock Runtime API.
    """

    def __init__(self, region_name: str = None) -> None:
        """
        Initializes the BedrockLlamaClient with AWS credentials and model parameters.
        """
        load_dotenv()

        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        region_name = region_name if region_name is not None else "us-east-1"
        if region_name == "us-east-1":
            self.llama_model_id = "us.meta.llama3-3-70b-instruct-v1:0"
            self.fallback_llama_model = "us.meta.llama3-1-70b-instruct-v1:0"
        else:
            raise ValueError("Unrecognized region")


        self.client = boto3.client(
            "bedrock-runtime",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )

    def _invoke_model(self, model_id: str, request_payload: str):
        """
        Helper function to invoke a specified model and return the response.

        Args:
            model_id (str): The model ID to invoke.
            request_payload (str): The JSON payload for the request.

        Returns:
            dict: Response dictionary with success status, message, and generated text.
        """
        try:
            response = self.client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=request_payload
            )

            model_response = json.loads(response["body"].read().decode("utf-8"))
            return {
                "success": True,
                "message": f"Successfully generated text using {model_id}.",
                "data": model_response.get("generation", "")
            }
        except (ClientError, Exception) as e:
            print(f"Error using model {model_id}: {e}")
            return None

    def generate_text_llama(self, prompt: str, max_gen_len: int = 2000, temperature: float = 0.5) -> dict:
        """
        Generates a text response using Llama 3 via AWS Bedrock.
        If the primary model fails, it retries using the fallback model.

        Args:
            prompt (str): The input text prompt for the model.
            max_gen_len (int, optional): Maximum response length. Defaults to 2000.
            temperature (float, optional): Controls randomness in responses. Defaults to 0.5.

        Returns:
            dict: A dictionary containing the API response, success status, and message.
        """
        formatted_prompt = f"""
        <|begin_of_text|><|start_header_id|>user<|end_header_id|>
        {prompt}
        <|eot_id|>
        <|start_header_id|>assistant<|end_header_id|>
        """

        request_payload = json.dumps({
            "prompt": formatted_prompt,
            "max_gen_len": max_gen_len,
            "temperature": temperature,
        })

        # **Try Primary Model**
        final_response = self._invoke_model(self.llama_model_id, request_payload)

        # **If Primary Model Fails, Try Fallback**
        if final_response is None:
            print("Switching to fallback model...")
            final_response = self._invoke_model(self.fallback_llama_model, request_payload)

        # **If Both Fail, Return Error Message**
        if final_response is None:
            final_response = {
                "success": False,
                "message": "Both primary and fallback models failed.",
                "data": None
            }

        return final_response
