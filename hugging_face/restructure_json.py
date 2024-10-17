import json
import os

def categorize_item(url):
    sources = {
        'Podcasts': ['bankless', 'huberman_lab', 'laurashin', 'realvision', 'themintcondition'],
        'Twitter(X)': ['elonmusk', 'memecoin', 'milesdeutscher', 'themooncarl', 'trader_xo'],
        'YouTube': ['jake_steeves']
    }
    for category, keywords in sources.items():
        for keyword in keywords:
            if keyword in url:
                return category, keyword
    return None, None

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
        category, source = categorize_item(item['url'])
        if category:
            item['data_source'] = source  # Add data source to the item
            if category == 'Twitter(X)':
                # Remove "all tweets" from the title and update it with the source
                item['title'] = f"{source.capitalize()} tweets between {item['title'].replace('all tweets', '').strip()}"
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