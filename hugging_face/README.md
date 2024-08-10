# Hugging Face Dataset Management Tool

This tool provides functionality for managing datasets and collections on Hugging Face. It allows you to process local datasets, upload them to Hugging Face, and manage collections and datasets within your organization.

## Features

1. Process and upload datasets to Hugging Face
2. Create and manage collections
3. Delete collections
4. Delete datasets

## Prerequisites

- Anaconda or Miniconda
- Hugging Face account and API token

## Setup

1. Clone this repository
2. Create and activate the Conda environment using the `environment.yml` file:

   ```bash
   conda env create -f environment.yml
   conda activate awesome-masa
   ```

3. Create a `.env` file in the project root with the following content:

   ```bash
   HF_ORG_NAME=your_organization_name
   HF_TOKEN=your_huggingface_api_token
   ```

## Usage

The script supports three main actions: process, delete_collection, and delete_dataset.

### Process Datasets

To process and upload datasets:

```bash
python hf_refactor.py process
```

This will:

- Iterate through the `datasets` folder
- Create collections based on folder structure
- Upload datasets to Hugging Face
- Add datasets to appropriate collections

To process datasets in a specific subfolder:

```bash
python hf_refactor.py process --subfolder <subfolder_name>
```

This will process only the datasets in the specified subfolder.

### Delete Collection

To delete a collection:

```bash
python hf_refactor.py delete_collection
```

This will:

- List all collections in your organization
- Allow you to choose a collection to delete or delete all collections

### Delete Dataset

To delete datasets:

```bash
python hf_refactor.py delete_dataset
```

This will:

- List all datasets in your organization
- Prompt for confirmation to delete all datasets

## File Structure

The script expects the following file structure for datasets:

```bash
datasets/
├── collection1/
│   ├── subfolder1/
│   │   ├── dataset1.csv
│   │   └── dataset2.json
│   └── subfolder2/
│       └── dataset3.txt
└── collection2/
    └── subfolder3/
        └── dataset4.csv
```

## Error Handling

The script includes error handling for:

- Rate limiting (429 errors)
- File processing errors
- API errors

Failed file uploads are logged and summarized at the end of the process.

## Notes

- The script uses a local JSON file (`hf_upload_record.json`) to keep track of uploaded files and avoid re-uploading unchanged files.
- There's a 5-second delay between file uploads to avoid overloading the API.
- Dataset names are sanitized to comply with Hugging Face naming conventions.

## Caution

Be careful when using the delete functions, as they can permanently remove data from your Hugging Face account. Always double-check before confirming deletions.