def process_categorized_data(categorized_data):
    def build_documents(items, category, entry_type):
        documents = []
        seen = set()  # To track (criteriaID, tag) pairs

        for item in items:
            tags = item.get("tags", [])
            if not tags:
                tags = ["Others"]

            for tag in tags:
                final_tag = tag.split(":")[0]
                key = (item["criteriaID"], final_tag)  # Uniqueness key

                if key not in seen:
                    seen.add(key)
                    all_tags.add(final_tag)
                    documents.append({
                        "criteriaID": item["criteriaID"],
                        "criteria": item["criteria"],
                        "source": item["source"],
                        "status": "pastTrials",
                        "tag": final_tag,
                        "type": entry_type,
                        "score": item["operational_score"],
                        "best_trial": item["best_trial_id"],
                        "count": item["count"],
                        "category": item["class"]
                    })
        return documents

    # Initialize with default tags
    all_tags = {"HbA1c", "BMI", "Age", "eGFR", "FPG", "C-peptide", "ALT", "Condition", "Informed consent", "Pregnant",
                "Contraceptives", "Drug allergy", "Others", "Breastfeeding"}

    final_list = []

    for criteria_category, criteria in categorized_data.items():
        final_list += build_documents(criteria.get("Inclusion", []), criteria_category, "inclusion")
        final_list += build_documents(criteria.get("Exclusion", []), criteria_category, "exclusion")

    return {
        "final_data": final_list,
        "tags": list(all_tags),
    }
