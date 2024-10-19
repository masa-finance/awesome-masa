
# Telegram SRC Generator

A Python package designed to generate creative image prompts and corresponding validation questions using OpenAI's APIs. It generates images based on these prompts and manages associated metadata.

## Features

- **Structured Prompt Generation**: Utilize OpenAI's GPT API to create image prompts with hidden items.
- **Image Creation**: Generate images from prompts using OpenAI's DALL-E.
- **Metadata Management**: Save and manage metadata using DuckDB.
- **Command-Line Interface**: Interact with the tool easily via the CLI.
- **Asynchronous Processing**: Efficiently handle batch operations with asyncio.

## Installation

1. **Install [Poetry](https://python-poetry.org/):**

       ```bash
       curl -sSL https://install.python-poetry.org | python3 -
       ```

2. **Clone the Repository:**

       ```bash
       git clone https://github.com/yourusername/telegram-src-generator.git
       cd telegram-src-generator
       ```

3. **Install Dependencies:**

       ```bash
       poetry install
       ```

## Usage

    Before running the batch job, ensure you have set the `OPENAI_API_KEY` environment variable:
    
    ```bash
    export OPENAI_API_KEY=your_openai_api_key
    ```
    
### Running a Batch Job

    Generate a specified number of prompts and corresponding images:
    
    ```bash
    poetry run python cli.py run_batch --num-prompts 10
    ```
    
    This command will generate 10 prompts, create images based on them, and save the metadata.
    
### Running Tests

    To execute basic tests:
    
    ```bash
    poetry run python cli.py test
    ```
    
## Contributing

    Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.
    
## License
 
    This project is licensed under the MIT License.
