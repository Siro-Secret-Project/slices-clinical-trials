from trial_document_search.utils.logger_setup import logger


def process_filters(documents: list, filters: dict) -> list:
    """Filter documents based on multiple criteria with different logics."""
    try:
        def passes_phases(doc):
            return not filters['phases'] or any(p in filters['phases'] for p in doc['phases'])

        def passes_locations(doc):
            if not filters['locations']:
                return True
            if filters['countryLogic'] == 'AND':
                return all(loc in doc['locations'] for loc in filters['locations'])
            return any(loc in doc['locations'] for loc in filters['locations'])

        def passes_sponsor(doc):
            return not filters['sponsorType'] or doc['sponsorType'] == filters['sponsorType']

        def passes_dates(doc):
            if not (filters['startDate'] and filters['endDate']):
                return True
            return (filters['startDate'] <= doc['startDate'] <= filters['endDate'] and
                    filters['startDate'] <= doc['endDate'] <= filters['endDate'])

        def passes_sample_size(doc):
            if None in (filters['sampleSizeMin'], filters['sampleSizeMax']):
                return True
            return filters['sampleSizeMin'] <= doc['enrollmentCount'] <= filters['sampleSizeMax']

        filtered = [
            doc for doc in documents
            if all([ passes_phases(doc), passes_locations(doc), passes_sponsor(doc), passes_dates(doc),
                passes_sample_size(doc)
            ])
        ]

        logger.debug(f"Filtered {len(filtered)} documents")
        return filtered

    except Exception as e:
        logger.error(f"Failed to apply filters: {e}")
        return documents