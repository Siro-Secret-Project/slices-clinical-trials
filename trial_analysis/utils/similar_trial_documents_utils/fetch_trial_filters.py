from trial_analysis.utils.logger_setup import logger
from database.mongo_db_connection import MongoDBDAO

def fetch_trial_filters(trial_documents: list) -> dict:
    final_response = {
        "success": False,
        "message": "Failed to filter trials by country",
        "data": None
    }
    try:
        # Fetch Documents from DB
        nctId_list = [item["nctId"] for item in trial_documents]
        mongo_client = MongoDBDAO(database_name="SSP-dev")
        similar_documents = mongo_client.find(
            collection_name="t2dm_data_preprocessed",
            query={"protocolSection.identificationModule.nctId": {"$in": nctId_list}},
            projection={"_id": 0}
        )

        id2doc = {item["protocolSection"]["identificationModule"]["nctId"]: item for item in similar_documents}
        for item in trial_documents:
            nct_id = item["nctId"]
            item["locations"] = []
            item["phases"] = []
            item["enrollmentCount"] = "Unknown"
            item["startDate"] = "Unknown"
            item["endDate"] = "Unknown"
            item["sponsorType"] = "Unknown"
            preprocessed_trial_document = id2doc.get(nct_id, None)
            if preprocessed_trial_document is None:
                continue
            else:

                # fetch country for each document
                trial_locations = preprocessed_trial_document["protocolSection"].get("contactsLocationsModule", {}).get("locations", [])
                countries = set()
                for location in trial_locations:
                    countries.add(location["country"])
                item["locations"] = list(countries)

                # fetch phase for document
                phases_info = preprocessed_trial_document["protocolSection"].get("designModule",{}).get("phases", ["Unknown"])
                trial_phases = phases_info
                item['phases'] = trial_phases

                # fetch trail participant count protocolSection.designModule.enrollmentInfo.count
                enrollment_info = preprocessed_trial_document["protocolSection"].get("designModule",{}).get("enrollmentInfo",{})
                enrollment = enrollment_info.get("count", 0)
                item['enrollmentCount'] = enrollment

                # fetch trial start date and end date
                date_info = preprocessed_trial_document["protocolSection"].get("statusModule",{})
                start_date = date_info.get("startDateStruct", {}).get("date", None)
                end_date = date_info.get("completionDateStruct", {}).get("date", None)
                item['startDate'] = start_date
                item['endDate'] = end_date

                # Fetch Sponsor Type
                sponsorType = preprocessed_trial_document["protocolSection"].get("sponsorCollaboratorsModule",{}).get("leadSponsor", {}).get("class", "Unknown")
                item['sponsorType'] = sponsorType

        final_response["success"] = True
        final_response["data"] = trial_documents
        final_response["message"] = "Successfully filtered trials by filters"
        logger.info(f"Successfully filtered trials by filters")
    except Exception as e:
        final_response["message"] = f"Failed to filter trials by country: {e}"
        logger.info(f"Failed to fetch filtered trials: {e}")

    return final_response
