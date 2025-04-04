from trial_document_search.utils.logger_setup import logger
from database.mongo_db_connection import MongoDBDAO


def fetch_trial_filters(trial_documents: list) -> dict:
    """Enrich trial documents with location, phase, and other metadata."""
    response = {
        "success": False,
        "message": "Failed to filter trials by country",
        "data": None
    }

    try:
        # Fetch documents from MongoDB
        nct_ids = [t["nctId"] for t in trial_documents]
        docs = MongoDBDAO("SSP-dev").find(
            "t2dm_data_preprocessed",
            {"protocolSection.identificationModule.nctId": {"$in": nct_ids}},
            {"_id": 0}
        )

        # Create lookup dictionary
        doc_map = {d["protocolSection"]["identificationModule"]["nctId"]: d for d in docs}

        # Enrich each trial document
        for trial in trial_documents:
            doc = doc_map.get(trial["nctId"])
            if not doc:
                continue

            protocol = doc["protocolSection"]
            trial.update({
                "locations": list({loc["country"] for loc in
                                   protocol.get("contactsLocationsModule", {}).get("locations", [])}),
                "phases": protocol.get("designModule", {}).get("phases", ["Unknown"]),
                "enrollmentCount": protocol.get("designModule", {}).get("enrollmentInfo", {}).get("count", 0),
                "startDate": protocol.get("statusModule", {}).get("startDateStruct", {}).get("date"),
                "endDate": protocol.get("statusModule", {}).get("completionDateStruct", {}).get("date"),
                "sponsorType": protocol.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {}).get("class",
                                                                                                         "Unknown")
            })

        response.update({
            "success": True,
            "data": trial_documents,
            "message": "Successfully filtered trials by filters"
        })
        logger.info("Successfully filtered trials by filters")

    except Exception as e:
        response["message"] = f"Failed to filter trials by country: {e}"
        logger.error(f"Failed to fetch filtered trials: {e}")

    return response