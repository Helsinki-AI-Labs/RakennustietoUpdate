from typing import List, Dict, Callable

# Define type for combine functions
CombineFunction = Callable[[List[Dict]], List[Dict]]


def combine_short_chunks(chunks: List[Dict], word_limit: int) -> List[Dict]:
    combined_chunks = []
    buffer = []

    for chunk in chunks:
        text = chunk.get("text", "")
        if len(text.split()) <= word_limit:
            buffer.append(text)
        else:
            if buffer:
                combined_chunks.append({"text": " ".join(buffer)})
                buffer = []
            combined_chunks.append(chunk)

    if buffer:
        combined_chunks.append({"text": " ".join(buffer)})

    return combined_chunks


def combine_chunks(
    chunks: List[Dict], combine_functions: List[CombineFunction]
) -> List[Dict]:
    combined_chunks = chunks
    for combine_func in combine_functions:
        combined_chunks = combine_func(combined_chunks)
    return combined_chunks
