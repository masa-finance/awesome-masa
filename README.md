# 🌟 Awesome Masa

A curated collection of datasets, tools, and agents for AI developers using the Masa protocol.

[Masa Protocol](https://github.com/masa-finance/masa-oracle)

## 🚀 Quick Start

1. Ensure you have Conda installed.
2. Create the environment:
   ```
   conda env create -f environment.yml
   conda activate awesome-masa
   ```
3. Set up environment variables:
   - Copy `env.example` to `.env`
   - Fill in the required values

## 📚 Contents

- [Datasets](#datasets)
- [Scrapers](#scrapers)
- [Agents](#agents)
- [Contribution](#contribution)
- [License](#license)

## 📊 Datasets

Our repository includes various datasets scraped and processed using the Masa Protocol:

### 🐦 Twitter Data

Scraped tweets related to various topics, including memecoin discussions.

*For more details, check out the [datasets README](datasets/README.md).*

### 🎙️ Podcast Data

- **Diarized Transcripts**: Podcast episodes with speaker identification and timestamps.
- **Examples**: Bankless, Huberman Lab, Laura Shin, Real Vision, The Mint Condition

### 💬 Discord Data

- **Channel Data**: Messages from Discord channels, including user information and timestamps.
- **Examples**: Guild: Masa, Channel ID: 1217114388373311640

This dataset contains community conversations related to Masa.

### 📺 YouTube Data

A collection of YouTube video transcripts, diarized with speaker labels.

## 🕷️ Scrapers

We provide several scraper libraries to collect data from different sources using the Masa Protocol:

- **Tweet Fetcher**: Retrieve tweets from specified Twitter accounts.
- **Discord Scraper**: Fetch and save messages from Discord channels.

*For usage instructions, refer to the respective README files in the `scrapers` directory.*

## 🤖 Agents

We provide example code for simple RAG (Retrieval-Augmented Generation) agents using our datasets. These agents demonstrate how to leverage the Masa protocol's structured data in AI applications.

### Example RAG Agent

Our example RAG agent showcases:

- Loading and preprocessing Masa datasets
- Implementing vector search for relevant context retrieval
- Integrating retrieved context with a language model for enhanced responses

*For the full implementation, see the `agents/rag_example.py` file.*

## 🤝 Contribution

We welcome contributions! If you have a dataset, tool, or agent that fits well with our collection, feel free to submit a pull request or open an issue.

For more information on using these datasets or contributing, please refer to the documentation or contact us directly.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

*Made with ❤️ by the Masa Foundation*