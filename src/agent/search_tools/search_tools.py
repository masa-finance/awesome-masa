from langchain_community.tools.tavily_search import TavilySearchResults

def get_web_search_tool():
    return TavilySearchResults()