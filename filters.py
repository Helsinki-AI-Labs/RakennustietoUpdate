from typing import List, Dict, Callable

# Define type for filter functions
FilterFunction = Callable[[Dict], bool]


def text_length_filter(chunk: Dict, min_length: int = 2) -> bool:
    return len(chunk.get("text", "")) >= min_length


def space_count_filter(chunk: Dict) -> bool:
    text = chunk.get("text", "")
    first_part = text[:10]
    last_part = text[-10:]
    return first_part.count(" ") < 5 and last_part.count(" ") < 5


def filter_chunks(chunks: List[Dict], filters: List[FilterFunction]) -> List[Dict]:
    filtered_chunks = []
    for chunk in chunks:
        keep = True
        for filter_func in filters:
            if not filter_func(chunk):
                print(f"Filtered out chunk: {chunk}")
                keep = False
                break
        if keep:
            filtered_chunks.append(chunk)
    return filtered_chunks
