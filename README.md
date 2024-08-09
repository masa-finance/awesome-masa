<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Awesome Masa</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1, h2 {
            color: #2c3e50;
        }
        .container {
            background-color: #f9f9f9;
            border-radius: 5px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .highlight {
            background-color: #e74c3c;
            color: white;
            padding: 3px 5px;
            border-radius: 3px;
        }
        code {
            background-color: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
        }
        ul {
            list-style-type: none;
            padding-left: 0;
        }
        li:before {
            content: "➜ ";
            color: #3498db;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            font-style: italic;
        }
    </style>
</head>
<body>
    <h1>🌟 Awesome Masa</h1>
    
    <p>A curated collection of datasets, tools, and agents for AI developers using the Masa protocol.</p>
    
    <img src="https://via.placeholder.com/800x200?text=Masa+Protocol" alt="Masa Protocol" style="width: 100%; height: auto;">
    
    <div class="container">
        <h2>🚀 Quick Start</h2>
        <ol>
            <li>Ensure you have Conda installed.</li>
            <li>Create the environment:
                <pre><code>conda env create -f environment.yml
conda activate awesome-masa</code></pre>
            </li>
            <li>Set up environment variables:
                <ul>
                    <li>Copy <code>env.example</code> to <code>.env</code></li>
                    <li>Fill in the required values</li>
                </ul>
            </li>
        </ol>
    </div>
    
    <div class="container">
        <h2>📚 Contents</h2>
        <ul>
            <li><a href="#datasets">Datasets</a></li>
            <li><a href="#scrapers">Scrapers</a></li>
            <li><a href="#agents">Agents</a></li>
            <li><a href="#contribution">Contribution</a></li>
            <li><a href="#license">License</a></li>
        </ul>
    </div>
    
    <div class="container" id="datasets">
        <h2>📊 Datasets</h2>
        <p>Our repository includes various datasets scraped and processed using the Masa protocol:</p>
        
        <h3>🐦 Twitter Data</h3>
        <p>Scraped tweets related to various topics, including memecoin discussions.</p>
        <p><em>For more details, check out the <a href="datasets/README.md">datasets README</a>.</em></p>
        
        <h3>🎙️ Podcast Data</h3>
        <ul>
            <li><strong>Diarized Transcripts</strong>: Podcast episodes with speaker identification and timestamps.</li>
            <li><strong>Examples</strong>: Bankless, Huberman Lab, Laura Shin, Real Vision, The Mint Condition</li>
        </ul>
        
        <h3>💬 Discord Data</h3>
        <ul>
            <li><strong>Channel Data</strong>: Messages from Discord channels, including user information and timestamps.</li>
            <li><strong>Examples</strong>: Guild: Masa, Channel ID: 1217114388373311640</li>
        </ul>
        <p>This dataset contains community conversations related to Masa.</p>
        
        <h3>📺 YouTube Data</h3>
        <p>A collection of YouTube video transcripts, diarized with speaker labels.</p>
    </div>
    
    <div class="container" id="scrapers">
        <h2>🕷️ Scrapers</h2>
        <p>We provide several scraper libraries to collect data from different sources using the Masa Protocol:</p>
        <ul>
            <li><strong>Tweet Fetcher</strong>: Retrieve tweets from specified Twitter accounts.</li>
            <li><strong>Discord Scraper</strong>: Fetch and save messages from Discord channels.</li>
        </ul>
        <p><em>For usage instructions, refer to the respective README files in the <code>scrapers</code> directory.</em></p>
    </div>
    
    <div class="container" id="agents">
        <h2>🤖 Agents</h2>
        <p>We provide example code for simple RAG (Retrieval-Augmented Generation) agents using our datasets. These agents demonstrate how to leverage the Masa protocol's structured data in AI applications.</p>
        
        <h3>Example RAG Agent</h3>
        <p>Our example RAG agent showcases:</p>
        <ul>
            <li>Loading and preprocessing Masa datasets</li>
            <li>Implementing vector search for relevant context retrieval</li>
            <li>Integrating retrieved context with a language model for enhanced responses</li>
        </ul>
        <p><em>For the full implementation, see the <code>agents/rag_example.py</code> file.</em></p>
    </div>
    
    <div class="container" id="contribution">
        <h2>🤝 Contribution</h2>
        <p>We welcome contributions! If you have a dataset, tool, or agent that fits well with our collection, feel free to submit a pull request or open an issue.</p>
        <p>For more information on using these datasets or contributing, please refer to the documentation or contact us directly.</p>
    </div>
    
    <div class="container" id="license">
        <h2>📄 License</h2>
        <p>This project is licensed under the MIT License. See the <a href="LICENSE">LICENSE</a> file for details.</p>
    </div>
    
    <div class="footer">
        <p>Made with ❤️ by the Masa community</p>
    </div>
</body>
</html>