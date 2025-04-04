from trial_analysis.utils.logger_setup import logger
def process_filters(documents, filters):
    try:
        filtered_docs = []

        for doc in documents:
            # Check phase match (OR logic)
            if filters['phases'] and not any(phase in filters['phases'] for phase in doc['phases']):
                continue

            # Check location match based on countryLogic
            if filters['locations']:
                if filters['countryLogic'] == 'AND':
                    if not all(loc in doc['locations'] for loc in filters['locations']):
                        continue
                else:  # OR logic
                    if not any(loc in doc['locations'] for loc in filters['locations']):
                        continue

            # Check sponsorType match
            if filters['sponsorType'] and doc['sponsorType'] != filters['sponsorType']:
                continue

            # Check date range
            if filters['startDate'] and filters['endDate']:
                if not (filters['startDate'] <= doc['startDate'] <= filters['endDate'] and
                        filters['startDate'] <= doc['endDate'] <= filters['endDate']):
                    continue

            # Check sample size range
            if filters['sampleSizeMin'] is not None and filters['sampleSizeMax'] is not None:
                if not (filters['sampleSizeMin'] <= doc['enrollmentCount'] <= filters['sampleSizeMax']):
                    continue

            filtered_docs.append(doc)
        logger.debug(f"Filtered {len(filtered_docs)} documents")
        return filtered_docs
    except Exception as e:
        logger.error(f"Failed to process filters: {e}")
        return documents
