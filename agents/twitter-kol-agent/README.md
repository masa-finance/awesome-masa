README for the @agent module:

# @agent

The @agent module is a sophisticated AI-powered system designed for processing and analyzing Twitter conversations, particularly focusing on trading and cryptocurrency discussions. It utilizes advanced natural language processing techniques and a flexible graph-based workflow to provide insightful responses to user queries.

## Key Components

1. **RAG (Retrieval-Augmented Generation) Agent**
   - Main entry point for generating responses
   - Utilizes a graph-based workflow for flexible processing

2. **Data Management**
   - Loads and preprocesses Twitter data
   - Creates vector representations for efficient retrieval

3. **Vector Store**
   - Uses SKLearnVectorStore for document storage and retrieval
   - Employs OpenAIEmbeddings for creating vector representations

4. **Graph Workflow**
   - Implements a state-based graph for processing steps
   - Includes nodes for data retrieval, web search, and response generation

5. **RAG Chain Setup**
   - Configures the language model and prompt template
   - Uses Ollama for text generation

6. **Search Tools**
   - Integrates Tavily Search for web-based information retrieval

7. **Evaluation**
   - Includes tools for evaluating the accuracy and trajectory of responses

## Usage

To use the @agent module, you can import the `get_rag_response` function from the `rag_agent.py` file:

```python
from src.agent import get_rag_response

question = "What's the latest trend in Bitcoin trading?"
answer, steps = get_rag_response(question)
print(f"Answer: {answer}")
print("\nSteps:")
for step in steps:
    print(f"- {step}")
```

## Configuration

The module uses environment variables for configuration. Ensure you have a `.env` file with the necessary API keys and settings.

## Data Sources

The system primarily works with Twitter data stored in JSON format. The data loader supports multiple file types, with a focus on tweet processing.

## Workflow

1. Data is retrieved based on the user's question
2. The system decides whether to perform a web search or generate a response
3. If needed, a web search is conducted to supplement the data
4. The final response is generated using the RAG chain

## Evaluation

The module includes evaluation tools to assess the accuracy of responses and the correctness of the processing trajectory.

## Dependencies

- langchain
- langchain_ollama
- langchain_openai
- SKLearn
- dotenv

## Note

This module is designed to work with data up to July 28th, 2024. Ensure your data sources are updated accordingly for the most relevant responses.

For more detailed information on each component, refer to the individual Python files in the `src/agent/` directory.