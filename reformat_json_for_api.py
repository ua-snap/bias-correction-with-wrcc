import json

from config import metrics


def convert_to_nested_json(input_file, output_file, metric):
    """Convert a list of dictionaries JSON file to a dictionary of dictionaries JSON file."""
    # Load the input JSON file
    with open(input_file, "r") as f:
        data = json.load(f)

    # Convert the list of dictionaries to a dictionary of dictionaries
    nested_data = {
        item["SNAP ID"]: item[f"bias corrected {metric} futures"] for item in data
    }

    # Write the nested dictionary to the output JSON file
    with open(output_file, "w") as f:
        json.dump(nested_data, f, indent=2)


for metric in metrics:
    # Convert the input JSON file to the output JSON file
    convert_to_nested_json(
        f"bias_corrected_{metric}_future_projections.json",
        f"nested_bias_corrected_{metric}_future_projections.json",
        metric,
    )
