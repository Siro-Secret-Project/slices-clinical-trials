from datetime import datetime
from database.mongo_db_connection import MongoDBDAO
from trial_document_search.utils.logger_setup import Logger

# Setup logger
logger = Logger("trial_operational_score").get_logger()

def calculate_duration_ratio(start_date, primary_completion_date, actual_completion_date):
    # Convert string dates to datetime objects
    if len(start_date) < 8:
        datetime_format = "%Y-%m"
    else:
        datetime_format = "%Y-%m-%d"
    start_date = datetime.strptime(start_date, datetime_format)
    if len(primary_completion_date) < 8:
        datetime_format = "%Y-%m"
    else:
        datetime_format = "%Y-%m-%d"
    primary_completion_date = datetime.strptime(primary_completion_date, datetime_format)

    if len(actual_completion_date) < 8:
        datetime_format = "%Y-%m"
    else:
        datetime_format = "%Y-%m-%d"
    actual_completion_date = datetime.strptime(actual_completion_date, datetime_format)

    # Calculate durations in months
    planned_duration = (primary_completion_date.year - start_date.year) * 12 + (primary_completion_date.month - start_date.month)
    actual_duration = (actual_completion_date.year - start_date.year) * 12 + (actual_completion_date.month - start_date.month)

    # Calculate the ratio
    ratio = actual_duration / planned_duration if planned_duration > 0 else None

    # Calculate Score
    score = 10 * min(ratio, 1)
    return score


def mean_adverse_score(documents: list):
  try:
      total_sae_rate = 0
      total_mae_rate = 0
      for doc in documents:
          # Get the count of Serious and Non-Serious Events

          serious_event_count = 0
          non_serious_event_count = 0
          if doc["hasResults"] is False:
            continue

          eventGroups = doc["resultsSection"]["adverseEventsModule"]["eventGroups"]
          for event in eventGroups:
            otherNumAffected = event["otherNumAffected"]
            seriousNumAffected = event["seriousNumAffected"]
            serious_event_count += seriousNumAffected
            non_serious_event_count += otherNumAffected

          # Calculate the Score
          enrollment_count = doc["protocolSection"]["designModule"]["enrollmentInfo"]["count"]
          sae_rate = serious_event_count/enrollment_count
          mae_rate = non_serious_event_count/enrollment_count
          total_sae_rate += sae_rate
          total_mae_rate += mae_rate

      # Calculate mean
      mean_sae_rate = total_sae_rate/len(documents) * 100
      mean_mae_rate = total_mae_rate/len(documents) * 100

      return {
          "sae_rate": mean_sae_rate,
          "mae_rate": mean_mae_rate
      }

  except Exception as e:
    print(e)
    return 0


def get_document_score(similar_documents_data: list, preprocessed_trial_document_response: dict, primary_completion_date_response: dict):
  try:
      # Enrollment Score
      enrollment_count = preprocessed_trial_document_response["protocolSection"]["designModule"]["enrollmentInfo"]["count"]

      total_enrollment_count = 0
      for document in similar_documents_data:
          total_enrollment_count += document["protocolSection"]["designModule"].get("enrollmentInfo", {}).get(
                  "count", 0)

      mean_enrollment = total_enrollment_count / len(similar_documents_data)

      enrollment_score = 25 * min(enrollment_count/mean_enrollment, 1)

      ## Duration Score
      try:
        start_date = preprocessed_trial_document_response["protocolSection"]["statusModule"]["startDateStruct"]["date"]
        versions = primary_completion_date_response["versions"]
        try:
          estimated_completion_date = versions[0]["study"]["protocolSection"]["statusModule"]["completionDateStruct"]["date"]
        except:
          estimated_completion_date = preprocessed_trial_document_response["protocolSection"]["statusModule"]["primaryCompletionDateStruct"]["date"]
        actual_completion_date = preprocessed_trial_document_response["protocolSection"]["statusModule"]["completionDateStruct"]["date"]

        duration_score = calculate_duration_ratio(start_date, estimated_completion_date, actual_completion_date)
      except:
        duration_score = 0

      # Adverse Event Score
      if preprocessed_trial_document_response["hasResults"] is False:
        adverse_event_score = 0

      else:
        serious_event_count = 0
        non_serious_event_count = 0

        eventGroups = preprocessed_trial_document_response["resultsSection"]["adverseEventsModule"]["eventGroups"]
        for event in eventGroups:
          otherNumAffected = event["otherNumAffected"]
          seriousNumAffected = event["seriousNumAffected"]
          serious_event_count += seriousNumAffected
          non_serious_event_count += otherNumAffected

        # Calculate the Score
        sae_rate = serious_event_count/enrollment_count
        mae_rate = non_serious_event_count/enrollment_count
        response = mean_adverse_score(similar_documents_data)
        mean_sae_rate = response["sae_rate"]
        mean_mae_rate = response["mae_rate"]

        norm_sar = sae_rate/mean_sae_rate
        norm_mar = mae_rate/mean_mae_rate

        adverse_event_score = 1 - (0.7 * norm_sar + 0.3 * norm_mar)
        adverse_event_score = adverse_event_score * 30
      #print(f"Adverse Event Score: {adverse_event_score:.2f}")

      # Retention score
      if preprocessed_trial_document_response["hasResults"] is False:
        retention_score = 0
      else:
        try:
            data = preprocessed_trial_document_response["resultsSection"]["participantFlowModule"]
            # Initialize total dropout count
            total_dropouts = 0

            # Iterate through the dropWithdraws section
            for period in data["periods"]:
                for dropout in period["dropWithdraws"]:
                    for reason in dropout["reasons"]:
                        # Convert numSubjects to integer and add to total
                        total_dropouts += int(reason["numSubjects"])

            num_of_completors = enrollment_count - total_dropouts

            retention_score = 10 * (num_of_completors/enrollment_count)
        except Exception as e:
            logger.error(f"Error while getting retention score for document: "
                         f"{preprocessed_trial_document_response['identificationModule']['nctId']}: {e}")
            retention_score = 0
      #print(f"Retention Score: {retention_score:.2f}")

      total_score = enrollment_score + duration_score + adverse_event_score + retention_score
      max_score = 25 + 10 + 30 + 10
      #print(f"Total Score: {total_score:.2f}/{max_score}")

      return {
          "enrollment_score": enrollment_score,
          "duration_score": duration_score,
          "adverse_event_score": adverse_event_score,
          "retention_score": retention_score,
          "total_score": total_score,
          "max_score": max_score
      }

  except Exception as e:
    print(e)
    return 0

def get_percentile_score(current_score, all_scores):
  all_scores.sort()
  percentile = (all_scores.index(current_score) + 1) / (len(all_scores) + 1) * 100
  return round(percentile, 2)

def calculate_trial_operational_score(document_id_list: list, categorized_data: dict) -> dict:
    final_response = {
        "success": False,
        "message": "",
        "data": None
    }
    try:
        # Create a Mongo DAO instance
        mongo_dao = MongoDBDAO(database_name="SSP-dev")

        # Fetch all the similar document
        similar_documents = mongo_dao.find(
            collection_name="t2dm_data_preprocessed",
            query={"protocolSection.identificationModule.nctId": {"$in": document_id_list}},
            projection={"_id":0}
        )
        id2doc = {doc["protocolSection"]["identificationModule"]["nctId"]: doc for doc in similar_documents}

        # Fetch all documents versions
        version_documents = mongo_dao.find(
            collection_name="clinical_trial_versions",
            query={"nctId": {"$in": document_id_list}},
            projection={"_id": 0}
        )
        id2version_doc = {doc["nctId"]: doc for doc in version_documents}

        # calculate all the operational Scores
        for category, criteria in categorized_data.items():
            logger.debug(f"CATEGORY: {category}")

            # For Inclusion Criteria
            for item in criteria["Inclusion"]:
                trial_operational_score = 0
                for trail_id, statement in item["source"].items():
                    similar_documents_id = lambda similar_trials, current_id: list(filter(lambda x: x != current_id, similar_trials))
                    similar_documents_list = similar_documents_id(document_id_list, trail_id)
                    try:
                        operational_score = get_document_score(similar_documents_data=[id2doc[item] for item in similar_documents_list],
                                                               preprocessed_trial_document_response=id2doc[trail_id],
                                                               primary_completion_date_response=id2version_doc[trail_id])
                        operational_score = operational_score["total_score"]
                    except:
                        operational_score = 0
                    trial_operational_score = max(trial_operational_score, operational_score)
                item["operational_score"] = round(trial_operational_score, 2)
                item["count"] = len(item["source"])

            # For exclusion criteria
            for item in criteria["Exclusion"]:
                trial_operational_score = 0
                for trail_id, statement in item["source"].items():
                    similar_documents_id = lambda similar_trials, current_id: list(filter(lambda x: x != current_id, similar_trials))
                    similar_documents_list = similar_documents_id(document_id_list, trail_id)
                    try:
                        operational_score = get_document_score(similar_documents_data=[id2doc[item] for item in similar_documents_list],
                                                               preprocessed_trial_document_response=id2doc[trail_id],
                                                               primary_completion_date_response=id2version_doc[trail_id])
                        operational_score = operational_score["total_score"]
                    except:
                        operational_score = 0
                    trial_operational_score = max(trial_operational_score, operational_score)
                item["operational_score"] = round(trial_operational_score, 2)
                item["count"] = len(item["source"])

        # Calculate the Percentile Score
        for category, criteria in categorized_data.items():
            logger.debug(f"CATEGORY: {category}")
            all_scores = [item['operational_score'] for item in criteria["Inclusion"]]
            for item in criteria["Inclusion"]:
                current_score = item["operational_score"]
                percentile = get_percentile_score(current_score, all_scores)
                item["percentile"] = percentile

            all_scores = [item['operational_score'] for item in criteria["Exclusion"]]
            for item in criteria["Exclusion"]:
                current_score = item["operational_score"]
                percentile = get_percentile_score(current_score, all_scores)
                item["percentile"] = percentile

        final_response["success"] = True
        final_response["message"] = "Calculated trial operational score successfully."
        final_response["data"] = categorized_data
    except Exception as e:
        logger.error(f"Error while calculating trial operational score: {e}")
        final_response["message"] = f"Error while calculating trial operational score: {e}"

    return final_response