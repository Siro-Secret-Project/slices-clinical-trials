import logging
from typing import List, Dict, Any
from datetime import datetime
from database.mongo_db_connection import MongoDBDAO
from collections import defaultdict

# Setup Logger
logger = logging.getLogger("document_retrieval")
logger.setLevel(logging.DEBUG)


class TrialMetricsProcessor:
    def __init__(self):
        pass

    @staticmethod
    def get_country_count(trial_document):
        """
        Extracts the count of unique countries from trial documents and associates each country with its respective trials.

        Args:
            trial_document (list): A list of trial documents, each containing location information.

        Returns:
            list: A list of dictionaries, each containing:
                  - "value": Country name
                  - "count": Number of occurrences of the country in trials
                  - "source": List of unique trial NCT IDs related to that country
        """
        unique_countries = defaultdict(int)  # Dictionary to count occurrences of each country
        unique_countries_metrics = []  # List to store final output metrics
        unique_countries_source = {}  # Dictionary to store trial IDs associated with each country

        try:
            for document in trial_document:
                local_countries = set() # Store unique list of countries in current trial
                # Extract location details from each trial document
                locationModule = document["protocolSection"].get("contactsLocationsModule", {})
                locations = locationModule.get("locations", [])

                for location in locations:
                    country = location.get("country", None)
                    if country and country not in local_countries:
                        local_countries.add(country)
                        unique_countries[country] += 1  # Increment country count

                        # Store trial NCT ID corresponding to the country
                        nctId = document["protocolSection"]["identificationModule"]["nctId"]
                        unique_countries_source.setdefault(country, []).append(nctId)

            # Sort countries based on occurrence count in descending order
            unique_countries_sorted = dict(sorted(unique_countries.items(), key=lambda item: item[1], reverse=True))

            # Construct the final list of country metrics
            for country, count in unique_countries_sorted.items():
                unique_countries_metrics.append({
                    "value": country,
                    "count": count,
                    "source": list(set(unique_countries_source[country]))  # Ensure unique NCT IDs
                })

            return unique_countries_metrics
        except Exception as e:
            logger.error(f"Error in get_country_count: {e}")
            return []  # Return an empty list in case of an error

    @staticmethod
    def categorize_range(value: int, range_size: int = 50):
        """Categorizes a value into a range."""
        try:
            lower_bound = (value // range_size) * range_size
            upper_bound = lower_bound + range_size
            return f"{lower_bound}-{upper_bound}"
        except Exception as e:
            logger.error(f"Failed to categorize: {e}")
            return None

    @staticmethod
    def format_categorized_data(categorized_dict: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Formats categorized data into the desired structure."""
        return [{"value": key, "count": len(value), "source": value} for key, value in categorized_dict.items()]

    @staticmethod
    def extract_trial_data(preprocessed_trial_document: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts relevant trial data from a preprocessed document."""
        enrollment_count = preprocessed_trial_document["protocolSection"].get("designModule", {}).get("enrollmentInfo",
                                                                                                      {}).get("count",
                                                                                                              0)
        date_info = preprocessed_trial_document["protocolSection"].get("statusModule", {})
        start_date = date_info.get("startDateStruct", {}).get("date", None)
        end_date = date_info.get("primaryCompletionDateStruct", {}).get("date", None)
        if end_date is None:
            end_date = date_info.get("completionDateStruct", {}).get("date", None)

        try:
            if start_date and end_date:
                start_date_format = "%Y-%m-%d" if len(start_date) > 8 else "%Y-%m"
                end_date_format = "%Y-%m-%d" if len(end_date) > 8 else "%Y-%m"
                d1 = datetime.strptime(start_date, start_date_format)
                d2 = datetime.strptime(end_date, end_date_format)
                study_duration = (d2 - d1).days // 7  # Convert duration to weeks
            else:
                study_duration = None
        except Exception as e:
            logger.error(f"Error parsing dates: {e}")
            study_duration = None

        trial_locations = preprocessed_trial_document["protocolSection"].get("contactsLocationsModule", {}).get(
            "locations", [])
        no_of_locations = len(trial_locations) if len(trial_locations) > 0 else 1
        if study_duration is None:
            study_duration = 0

        return {
            "studyDuration": study_duration,
            "no_of_locations": no_of_locations,
            "enrollmentInfo": enrollment_count,
        }

    @staticmethod
    def categorize_metrics(final_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Categorizes and formats metrics with sorted ranges."""
        categorized_data = {
            "studyDuration": {},
            "no_of_locations": {},
            "enrollmentInfo": {}
        }

        for entry in final_data:
            nctId = entry['nctId']

            for key in categorized_data:
                category = TrialMetricsProcessor.categorize_range(entry[key])
                if category is None:
                    logger.error(f"Invalid category for entry: {entry}")
                    continue
                if category not in categorized_data[key]:
                    categorized_data[key][category] = []
                categorized_data[key][category].append(nctId)

        # Sort the keys numerically before formatting
        sorted_categorized_data = {}
        for key, value in categorized_data.items():
            sorted_keys = sorted(value.keys(), key=lambda x: int(x.split('-')[0]))  # Sort by lower bound
            sorted_categorized_data[key] = TrialMetricsProcessor.format_categorized_data(
                {k: value[k] for k in sorted_keys})

        return sorted_categorized_data


def fetch_additional_metrics(trial_document_ids: List[str]) -> Dict[str, Any]:
    """Fetches additional metrics for a list of clinical trial documents."""
    final_response = {"success": False, "message": "No additional metrics provided.", "data": None}

    # Initialize MongoDBDAO
    mongo_dao = MongoDBDAO(database_name="SSP-dev") # Using SSP-dev as protocol Documents are not in Current DB

    documents = mongo_dao.find(
        collection_name="t2dm_data_preprocessed",
        query={"protocolSection.identificationModule.nctId": {"$in": trial_document_ids}},
        projection={"_id": 0}
    )

    try:
        final_data = []
        for document in documents:
            nct_id = document["protocolSection"]["identificationModule"]["nctId"]
            trial_data = TrialMetricsProcessor.extract_trial_data(document)
            trial_data["nctId"] = nct_id
            final_data.append(trial_data)

        metrics = TrialMetricsProcessor.categorize_metrics(final_data)

        # Fetch Unique countries count
        unique_countries = TrialMetricsProcessor.get_country_count(documents)
        metrics["unique_countries"] = unique_countries
        final_response.update({"success": True, "message": "Additional metrics fetched successfully.", "data": metrics})
    except Exception as e:
        logger.exception(f"Exception while fetching additional metrics: {e}")
        final_response["message"] = f"Exception while fetching additional metrics: {e}"

    return final_response
