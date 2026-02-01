def search_web(query: str):
    """
    Searches the web for the given query using DuckDuckGo.
    Returns the search summary. Returns None if search fails.
    """
    try:
        from langchain_community.tools import DuckDuckGoSearchRun
        search = DuckDuckGoSearchRun()
        return search.run(query)
    except Exception as e:
        # Return None so the caller knows it failed, rather than an error string
        # that might be confused for a definition.
        print(f"Web Search Warning: {str(e)}")
        return None
