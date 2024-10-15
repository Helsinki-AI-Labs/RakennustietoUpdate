import json
import time
from typing import List, TypedDict, Optional, Dict

from llm import OpenAI
from helpers import combine_title_content
from prompt import create_prompt
from os.path import basename


class Section(TypedDict):
    title: str
    content: List[str]


class Completion(TypedDict):
    title: str
    content: List[str]
    input: str
    output: str


class Error(TypedDict, total=False):
    # Define error structure if available
    message: str
    code: int


class TokensDetails(TypedDict):
    cached_tokens: int
    reasoning_tokens: Optional[int]


class Usage(TypedDict):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_tokens_details: TokensDetails
    completion_tokens_details: TokensDetails


class Message(TypedDict):
    role: str
    content: str
    refusal: Optional[str]


class Logprobs(TypedDict, total=False):
    # Define properties if available
    tokens: List[str]
    token_logprobs: List[Optional[float]]
    top_logprobs: Optional[List[dict]]
    text_offset: Optional[List[int]]


class Choice(TypedDict):
    index: int
    message: Message
    logprobs: Optional[Logprobs]
    finish_reason: str


class Body(TypedDict):
    id: str
    object: str
    created: int
    model: str
    choices: List[Choice]
    usage: Usage
    system_fingerprint: str


class Response(TypedDict):
    status_code: int
    request_id: str
    body: Body


class BatchRequest(TypedDict):
    id: str
    custom_id: str
    response: Response
    error: Optional[Error]


def prepare_batch_input(sections: List[Section], filename: str, law_text: str) -> str:
    """
    Prepares a JSONL file for Batch API with all section prompts.

    Args:
        sections (List[Section]): List of sections to process.
        filename (str): The source filename for generating custom_ids.
        law_text (str): The content of the law text.

    Returns:
        str: The path to the prepared batch input file.
    """
    batch_input_filename = f"batch_input_{basename(filename)}.jsonl"
    with open(batch_input_filename, "w", encoding="utf-8") as f:
        for index, section in enumerate(sections, start=1):
            combined_content = combine_title_content(section)
            prompt = create_prompt(law_text, combined_content)
            custom_id = f"{basename(filename)}-Section-{index}"
            request: BatchRequest = {
                "custom_id": custom_id,
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-4o-2024-08-06",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,
                },
            }
            f.write(json.dumps(request) + "\n")
    return batch_input_filename


def upload_batch_file(client: OpenAI, batch_input_path: str) -> str:
    """
    Uploads the batch input file to OpenAI.

    Args:
        client (OpenAI): The OpenAI client instance.
        batch_input_path (str): Path to the batch input JSONL file.

    Returns:
        str: The uploaded file's ID.
    """
    with open(batch_input_path, "rb") as file:
        response = client.files.create(
            file=file,
            purpose="batch",
        )
    return response.id


def create_batch_job(
    client: OpenAI, input_file_id: str, endpoint: str = "/v1/chat/completions"
) -> str:
    """
    Creates a batch job with the uploaded input file.

    Args:
        client (OpenAI): The OpenAI client instance.
        input_file_id (str): The ID of the uploaded batch input file.
        endpoint (str): The API endpoint to use for the batch.

    Returns:
        str: The created batch job's ID.
    """
    batch = client.batches.create(
        input_file_id=input_file_id,
        endpoint=endpoint,
        completion_window="24h",
        metadata={
            "description": "Automated batch processing for law sections analysis"
        },
    )
    return batch.id


def poll_batch_status(client: OpenAI, batch_id: str) -> Dict:
    """
    Polls the batch job status until completion.

    Args:
        client (OpenAI): The OpenAI client instance.
        batch_id (str): The ID of the batch job.

    Returns:
        Dict: The final batch object.
    """
    while True:
        batch = client.batches.retrieve(batch_id)
        status = batch.status
        print(f"Batch Status: {status}")
        if status in ["completed", "failed", "expired", "cancelled"]:
            break
        time.sleep(10)  # Wait for 10 seconds before polling again
    return batch


def retrieve_batch_results(client: OpenAI, output_file_id: str) -> List[Dict]:
    """
    Retrieves and parses the batch results from the output file.

    Args:
        client (OpenAI): The OpenAI client instance.
        output_file_id (str): The ID of the output file.

    Returns:
        List[Dict]: List of response objects.
    """
    file_content = client.files.content(output_file_id)
    results: List[Dict] = []
    for line in file_content.text.strip().split("\n"):
        result = json.loads(line)
        results.append(result)
    return results


def process_batch_results(
    results: List[Dict], filename: str, sections: Dict[str, Section]
) -> str:
    """
    Processes the batch results and compiles the analysis content.

    Args:
        results (List[Dict]): List of response objects from the batch.
        filename (str): The source filename for reference.
        sections (Dict[str, Section]): Dictionary mapping custom_ids to sections.

    Returns:
        str: The compiled analysis content.
    """
    analysis_content = f"Source File: {filename}\n"
    for result in results:
        custom_id = result.get("custom_id")
        response = result.get("response")
        error = result.get("error")

        if error:
            analysis_content += f"\nError in {custom_id}: {error}\n"
            continue

        content = response["body"]["choices"][0]["message"]["content"]
        combined_content = combine_title_content(sections[custom_id])
        analysis_result = (
            "\n\n====================================\n\n"
            f"\nTEXT SECTION:\n{combined_content}\n\nSUGGESTED CHANGES:\n"
            f"{content}"
        )
        analysis_content += analysis_result
    return analysis_content
