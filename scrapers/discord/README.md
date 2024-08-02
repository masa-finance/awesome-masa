# Discord Scraper

This project contains a set of tools to fetch and save messages from a Discord channel. The main components are:

1. `discord_fetcher.py`: This script fetches messages from a specified Discord channel.
2. `discord_fetcher.yaml`: Configuration file for the fetcher script.
3. `discord_service.py`: Contains utility functions for logging, ensuring data directories, and saving messages.

## Setup

1. **Environment Setup**:
   - Ensure you have `conda` installed.
   - Create the environment using the provided `environment.yml` file:

     ```sh
     conda env create -f environment.yml
     conda activate awesome-masa
     ```

2. **Environment Variables**:
   - Create a `.env` file in the root directory and add your environment variables. For example:

     ```yaml
     DISCORD_API_TOKEN=your_discord_api_token
     ```

3. **Configuration**:
   - Update the `discord_fetcher.yaml` file with your specific settings:

     ```yaml
     # API settings
     api_endpoint: 'http://localhost:8080/api/v1/data/discord/channels/{channel_id}/messages'
     headers:
       accept: 'application/json'

     # Query params
     messages_per_request: 100 # 100 is the max

     # Number of iterations - starts from the most recent messages and iterates backwards by the number defined in messages_per_request
     iterations: 10

     # File settings
     data_directory: 'data/discord_data'

     # Timing settings
     request_delay: 5  # 5 seconds between requests

     # Logging settings
     log_level: 'INFO'
     log_format: '%(asctime)s - %(levelname)s - %(message)s'

     # Discord-specific settings
     guild_id: 'your_guild_id_here'
     channel_id: '1217114388373311640'
     ```

## Usage

1. **Fetching Messages**:
   - Run the `discord_fetcher.py` script to start fetching messages:

     ```sh
     python scrapers/discord/discord_fetcher.py
     ```

2. **Logging**:
   - The logging setup is configured in `discord_service.py` using `colorlog` for colored output. You can adjust the log level and format in the `discord_fetcher.yaml` file.

3. **Saving Messages**:
   - Messages are saved in JSON format in the directory specified by `data_directory` in the `discord_fetcher.yaml` file. The filename includes the channel ID and the timestamp of the fetch operation.

## Functions

### discord_service.py

- `setup_logging(log_level, log_format)`: Configures logging with the specified log level and format.
- `ensure_data_directory(directory)`: Ensures the specified data directory exists.
- `save_all_messages(messages, data_directory, channel_id)`: Saves all fetched messages to a JSON file in the specified data directory.

### discord_fetcher.py

- `load_config()`: Loads the configuration from `discord_fetcher.yaml`.
- `save_state(state, api_calls_count, records_fetched, all_messages)`: Saves the current state of the fetch operation.
- `load_state()`: Loads the last known state of the fetch operation.
- `fetch_messages(config)`: Fetches messages from the Discord channel based on the provided configuration.

## Example

To fetch messages from a Discord channel, ensure your configuration is set up correctly in `discord_fetcher.yaml` and run the fetcher script:
