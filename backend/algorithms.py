import re
from collections import Counter, defaultdict
from statistics import mean, median, mode
from typing import List, Dict, Any, Optional
from datetime import datetime

def linear_search(transactions: List[Dict[str, Any]], keyword: str, fields: List[str]) -> List[Dict[str, Any]]:
    result = []
    for t in transactions:
        for field in fields:
            if keyword.lower() in str(t.get(field, '')).lower():
                result.append(t)
                break
    return result

def hash_search(transactions: List[Dict[str, Any]], field: str, value: str) -> List[Dict[str, Any]]:
    index = defaultdict(list)
    for t in transactions:
        index[str(t.get(field, '')).lower()].append(t)
    return index[value.lower()]

def range_search(transactions: List[Dict[str, Any]], field: str, min_val: Optional[float], max_val: Optional[float]) -> List[Dict[str, Any]]:
    result = []
    for t in transactions:
        val = t.get(field)
        if val is not None:
            if (min_val is None or val >= min_val) and (max_val is None or val <= max_val):
                result.append(t)
    return result

def pattern_search(transactions: List[Dict[str, Any]], field: str, pattern: str) -> List[Dict[str, Any]]:
    regex = re.compile(pattern, re.IGNORECASE)
    return [t for t in transactions if regex.search(str(t.get(field, '')))]

def timsort(transactions: List[Dict[str, Any]], field: str, reverse: bool = False) -> List[Dict[str, Any]]:
    """Sorts transactions on *field* while tolerating None values.

    None values are grouped together and pushed to the end of an ascending sort
    (or to the front of a descending sort) so that mixed comparisons never
    occur, avoiding TypeError.
    """
    if not transactions:
        return []

    def key_func(t):
        val = t.get(field)
        none_marker = val is None
        return (none_marker, val) if not reverse else (not none_marker, val)

    return sorted(transactions, key=key_func, reverse=reverse)

def quicksort(transactions: List[Dict[str, Any]], field: str) -> List[Dict[str, Any]]:
    if len(transactions) <= 1:
        return transactions
    pivot = transactions[0]
    left = [t for t in transactions[1:] if t.get(field) <= pivot.get(field)]
    right = [t for t in transactions[1:] if t.get(field) > pivot.get(field)]
    return quicksort(left, field) + [pivot] + quicksort(right, field)

def compute_aggregates(transactions: List[Dict[str, Any]], field: str) -> Dict[str, Any]:
    values = [t.get(field) for t in transactions if t.get(field) is not None]
    if not values:
        return {"sum": 0, "mean": 0, "median": 0, "mode": None}
    agg = {
        "sum": sum(values),
        "mean": mean(values),
        "median": median(values),
        # Mode may raise StatisticsError in case of multimodal data
        "mode": None
    }
    if len(values) > 1:
        try:
            agg["mode"] = mode(values)
        except Exception:
            agg["mode"] = None
    return agg

def frequency_distribution(transactions: List[Dict[str, Any]], field: str) -> Dict[str, int]:
    return dict(Counter(t.get(field, 'Unknown') for t in transactions))

def monthly_aggregation(transactions: List[Dict[str, Any]], date_field: str, amount_field: str) -> Dict[str, float]:
    monthly = defaultdict(float)
    for t in transactions:
        date_val = t.get(date_field)
        amount = t.get(amount_field)
        if date_val and amount is not None:
            if isinstance(date_val, str):
                try:
                    date_val = datetime.fromisoformat(date_val)
                except Exception:
                    continue
            key = date_val.strftime('%Y-%m')
            monthly[key] += amount
    return dict(monthly)

def sliding_window_aggregation(monthly: Dict[str, float], window: int = 3) -> Dict[str, float]:
   
    keys = list(monthly.keys())
    values = list(monthly.values())
    result = {}
    for i in range(len(values)):
        window_vals = values[max(0, i-window+1):i+1]
        result[keys[i]] = sum(window_vals) / len(window_vals)
    return result 