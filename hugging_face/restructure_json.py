import json
import os

def categorize_item(url):
    if any(source in url for source in ['bankless', 'huberman_lab', 'laurashin', 'realvision', 'themintcondition']):
        return 'Podcasts'
    elif any(source in url for source in ['elonmusk', 'memecoin', 'milesdeutscher', 'themooncarl', 'trader_xo']):
        return 'Twitter(X)'
    elif 'jake_steeves' in url:
        return 'YouTube'
    else:
        return None

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the full path to the JSON file
input_file = os.path.join(script_dir, 'masa_foundation_datasets.json')
output_file = os.path.join(script_dir, 'masa_foundation_datasets_restructured.json')

# Read the original JSON file
try:
    with open(input_file, 'r') as file:
        data = [json.loads(line) for line in file if line.strip()]
except FileNotFoundError:
    print(f"Error: The file {input_file} was not found.")
    exit(1)

# Filter out items with null titles and categorize the rest
categorized_data = {
    'Twitter(X)': [],
    'Podcasts': [],
    'YouTube': []
}

for item in data:
    if item['title'] is not None:
        category = categorize_item(item['url'])
        if category:
            categorized_data[category].append(item)

# Create the new structure
new_structure = {
    "datasets": {
        "Twitter(X)": {
            "tag": "twitter",
            "items": categorized_data['Twitter(X)']
        },
        "Podcasts": {
            "tag": "podcast",
            "items": categorized_data['Podcasts']
        },
        "YouTube": {
            "tag": "youtube",
            "items": categorized_data['YouTube']
        }
    }
}

# Write the new structure to a JSON file
with open(output_file, 'w') as file:
    json.dump(new_structure, file, indent=2)

print(f"Restructuring complete. New file created: {output_file}")