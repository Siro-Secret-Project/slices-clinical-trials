from typing import List, Dict, Any
from utils.generate_object_id import generate_object_id

def assign_unique_ids(criteria_list: List[Dict[str, Any]]) -> None:
    """Assign unique IDs to criteria items."""
    for item in criteria_list:
        item["criteriaID"] = f"cid_{generate_object_id()}"