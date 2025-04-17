from typing import List, Dict, Any
from trial_document_search.utils.logger_setup import Logger

# Setup Logger
logger = Logger("process_criteria_tag_list").get_logger()

def process_criteria_tag_list(criteria_items: List[Dict[str, Any]]) -> None:
    """
    Process criteria tags by adding types and extracting main tags.

    Args:
        criteria_items: List of criteria items (either inclusion or exclusion)
    """
    for item in criteria_items:
        try:
            for tag in item["tags"]:
                # Add type to tag
                category = tag["category"]
                if "Condition" in category:
                    tag["type"] = "Condition"
                elif tag.get("booleanValue", None) is not None:
                    tag["type"] = "Boolean"
                else:
                    tag["type"] = "Range"

                # Extract main tag based on type
                if tag["type"] == "Condition":
                    tag["main-tag"] = category
                    tag["condition"] = category.split(":")[1].strip()
                    tag.pop("lowerLimit")
                    tag.pop("upperLimit")
                elif tag["type"] == "Boolean":
                    tag["main-tag"] = f"{category} : {tag['booleanValue']}"
                elif tag["type"] == "Range":
                    # Process lower limit
                    lower_limit = tag["lowerLimit"] if tag["lowerLimit"] is not None else "X"
                    if isinstance(lower_limit, str) and lower_limit != "X":
                        if lower_limit.endswith(".00"):
                            lower_limit = lower_limit[:-3]
                        elif lower_limit.endswith(".0"):
                            lower_limit = lower_limit[:-2]

                    # Process upper limit
                    upper_limit = tag["upperLimit"] if tag["upperLimit"] is not None else "X"
                    if isinstance(upper_limit, str) and upper_limit != "X":
                        if upper_limit.endswith(".00"):
                            upper_limit = upper_limit[:-3]
                        elif upper_limit.endswith(".0"):
                            upper_limit = upper_limit[:-2]

                    tag["main-tag"] = f"{category} : {lower_limit} - {upper_limit}"
        except Exception as e:
            logger.exception(f"Error processing tags for criteria: {e}")
            logger.debug(f"Problematic item: {item}")

