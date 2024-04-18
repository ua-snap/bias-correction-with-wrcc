import json

from config import metrics


def convert_to_nested_json(input_file, output_file, metric):
    """Convert list of dicts JSON file to a dictionary of dictionaries JSON file."""
    with open(input_file, "r") as f:
        data = json.load(f)
    # convert the list of dictionaries to a dictionary of dictionaries
    nested_data = {
        item["SNAP ID"]: item[f"bias corrected {metric} futures"] for item in data
    }
    with open(output_file, "w") as f:
        json.dump(nested_data, f, indent=2)


def convert_uncorrected_to_nested_json(input_file, output_file, metric):
    """Convert list of dicts JSON file to a dictionary of dictionaries JSON file."""
    with open(input_file, "r") as f:
        data = json.load(f)
    # convert the list of dictionaries to a dictionary of dictionaries
    nested_data = {item["SNAP ID"]: item[f"biased {metric} futures"] for item in data}
    with open(output_file, "w") as f:
        json.dump(nested_data, f, indent=2)


for metric in metrics:
    # Convert the input JSON file to the output JSON file
    convert_to_nested_json(
        f"bias_corrected_{metric}_future_projections.json",
        f"nested_bias_corrected_{metric}_future_projections.json",
        metric,
    )
    convert_uncorrected_to_nested_json(
        f"uncorrected_{metric}_future_projections.json",
        f"nested_uncorrected_{metric}_future_projections.json",
        metric,
    )
