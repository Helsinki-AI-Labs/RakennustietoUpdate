import json


def clean_up_results():
    with open("voting_results.json", "r", encoding="utf-8") as file:
        voting_results = json.load(file)

    for file_id, entries in voting_results.items():
        for entry_id, data in entries.items():
            parsed_result = data.get("parsed_voting_result", {})
            otsikko_items = parsed_result.get("a. Otsikko:", [])
            if len(otsikko_items) > 5:
                print(
                    f"'a. Otsikko:' has more than 5 items in {file_id} entry {entry_id}."
                )


if __name__ == "__main__":
    clean_up_results()
