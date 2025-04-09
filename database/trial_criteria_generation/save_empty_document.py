from datetime import datetime
from database.mongo_db_connection import MongoDBDAO
from trial_criteria_generation.models.db_models import InclusionExclusion, CategorizedData

def save_empty_document(trialId: str):
    # Create empty InclusionExclusion instances
    empty_inclusion_exclusion = InclusionExclusion(Inclusion=[], Exclusion=[])

    # Create empty CategorizedData instance
    empty_categorized_data = CategorizedData(
        Age=empty_inclusion_exclusion,
        Gender=empty_inclusion_exclusion,
        Health_Condition_Status=empty_inclusion_exclusion,
        Clinical_and_Laboratory_Parameters=empty_inclusion_exclusion,
        Medication_Status=empty_inclusion_exclusion,
        Informed_Consent=empty_inclusion_exclusion,
        Ability_to_Comply_with_Study_Procedures=empty_inclusion_exclusion,
        Lifestyle_Requirements=empty_inclusion_exclusion,
        Reproductive_Status=empty_inclusion_exclusion,
        Co_morbid_Conditions=empty_inclusion_exclusion,
        Recent_Participation_in_Other_Clinical_Trials=empty_inclusion_exclusion,
        Allergies_and_Drug_Reactions=empty_inclusion_exclusion,
        Mental_Health_Disorders=empty_inclusion_exclusion,
        Infectious_Diseases=empty_inclusion_exclusion,
        Other=empty_inclusion_exclusion
    )

    # Create a DB Document
    document = {
        "trialId": trialId,
        "categorizedData": empty_categorized_data.model_dump(),
        "userCategorizedData": empty_categorized_data.model_dump(),
        "primary_endpoints": [],
        "metrics": {},
        "createdAt": datetime.now(),
        "updatedAt": datetime.now(),
    }

    # Save document into DB
    mongo_client = MongoDBDAO()
    response = mongo_client.insert(collection_name="similar_trials_criteria_results", document=document)

    if response.inserted_id:
        return True
    else:
        return False