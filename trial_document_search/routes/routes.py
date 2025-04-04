from fastapi import APIRouter, Response, status
from trial_document_search.models.routes_models import BaseResponse, DocumentFilters
from trial_document_search.services.similar_trail_documents_reterival_service import fetch_similar_trail_documents
from trial_document_search.utils.logger_setup import logger
from datetime import datetime

router = APIRouter()


@router.post("/search_documents", response_model=BaseResponse)
async def search_routes_new(request: DocumentFilters, response: Response):
    """
    Endpoint to search for documents based on inclusion criteria, exclusion criteria, and rationale.

    Args:
        request (DocumentFilters): The request body containing search criteria.
        response (Response): The FastAPI Response object.

    Returns:
        BaseResponse: A standardized response containing the search results or an error message.
    """
    base_response = BaseResponse(
        success=False,
        status_code=status.HTTP_400_BAD_REQUEST,
        data=None,
        message="Internal Server Error"
    )

    try:
        # Extract inputs for user identification
        user_data = {
            "userName": request.userName,
            "ecid": request.ecid
        }

        # Extract input for Document Search
        rationale = request.rationale if request.rationale != "" else None
        condition = request.condition if request.condition != "" else None
        inclusion_criteria = request.inclusionCriteria if request.inclusionCriteria != "" else None
        exclusion_criteria = request.exclusionCriteria if request.exclusionCriteria != "" else None
        trial_outcomes = request.efficacyEndpoints if request.efficacyEndpoints != "" else None
        title = request.title if request.title != "" else None
        # To bo added later
        # objective = request.objective if request.objective != "" else None
        # interventionType = request.interventionType if request.interventionType != "" else None
        weights = request.weights

        input_document = {
            "inclusionCriteria": inclusion_criteria,
            "exclusionCriteria": exclusion_criteria,
            "rationale": rationale,
            "condition": condition,
            "trialOutcomes": trial_outcomes,
            "title": title
        }

        # Lambda function to validate and format dates safely
        validate_date = lambda date_str: (datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
                                          if date_str else None) if isinstance(date_str,str) and len(date_str) >= 10 else None

        # Document filters
        phases = request.phase
        locations = request.country
        countryLogic = request.countryLogic
        startDate = validate_date(request.startDate)
        endDate = validate_date(request.endDate)
        sponsorType = request.sponsor if request.sponsor != "" else None
        sampleSizeMin = int(request.sampleSizeMin) if request.sampleSizeMin != "" else None
        sampleSizeMax = int(request.sampleSizeMax) if request.sampleSizeMax != "" else None

        # To be added later
        # safetyAssessment = request.safetyAssessment

        document_filters = {
            "phases": phases,
            "locations": locations,
            "countryLogic": countryLogic,
            "startDate": startDate,
            "endDate": endDate,
            "sponsorType": sponsorType,
            "sampleSizeMin": sampleSizeMin,
            "sampleSizeMax": sampleSizeMax
        }

        # Fetch similar documents based on the input criteria
        similar_documents_response = fetch_similar_trail_documents(documents_search_keys=input_document,
                                                                   custom_weights=weights.model_dump(),
                                                                   document_filters=document_filters,
                                                                   user_data=user_data)

        # Handle the response from the fetch function
        if similar_documents_response["success"] is False:
            base_response.success = False
            base_response.message = similar_documents_response["message"]
            response.status_code = status.HTTP_400_BAD_REQUEST
            return base_response
        else:
            base_response.success = True
            base_response.message = similar_documents_response["message"]
            base_response.status_code = status.HTTP_200_OK
            base_response.data = similar_documents_response["data"]
            response.status_code = status.HTTP_200_OK
            return base_response

    except Exception as e:
        # Handle unexpected errors and log them
        logger.error(f"Unexpected error: {e}")
        base_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        base_response.message = f"Unexpected error: {e}"
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return base_response