from langchain.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from app.core.logger import logger
import re
import os

def get_tools(tavily_api_key: str):
    print("key", tavily_api_key)
    
    @tool
    def calculator(expression: str) -> str:
        """Evaluate a math expression like '5 + 3'."""
        try:
            pattern = r'(\d+(?:\.\d+)?)\s*([+\-*/])\s*(\d+(?:\.\d+)?)'
            match = re.search(pattern, expression)
            if match:
                num1, op, num2 = match.groups()
                result = eval(f"{num1} {op} {num2}")
                return str(int(result) if result == int(result) else result)
            return "Could not parse expression"
        except Exception as e:
            logger.exception("Error in calculator")
            return f"Error: {str(e)}"
    
    TAVILY_AVAILABLE = False
    tavily_search = None
    
    try:
        if tavily_api_key:
            logger.info("Initializing TavilySearchResults with provided API key")
            
            # Set the environment variable temporarily for this process
            # This is the cleanest approach for LangChain's TavilySearchResults
            os.environ['TAVILY_API_KEY'] = tavily_api_key
            
            # Alternative approach: Try different parameter names
            try:
                # Method 1: Using environment variable (recommended)
                tavily_search = TavilySearchResults(
                    max_results=3,
                    search_depth="advanced"
                )
            except Exception as e1:
                logger.warning(f"Method 1 failed: {e1}")
                try:
                    # Method 2: Try different parameter name
                    tavily_search = TavilySearchResults(
                        api_key=tavily_api_key,
                        max_results=3,
                        search_depth="advanced"
                    )
                except Exception as e2:
                    logger.warning(f"Method 2 failed: {e2}")
                    # Method 3: Try with k parameter for max_results
                    tavily_search = TavilySearchResults(
                        k=3,
                        search_depth="advanced"
                    )
            
            TAVILY_AVAILABLE = True
            logger.info("TavilySearchResults initialized successfully")
            
        else:
            raise ValueError("Tavily API key not provided.")
            
    except Exception as e:
        logger.warning(f"Tavily not available: {e}")
        tavily_search = None
        # Clean up environment variable if it was set
        if 'TAVILY_API_KEY' in os.environ:
            del os.environ['TAVILY_API_KEY']
    
    @tool
    def fallback_search(query: str) -> str:
        """Return fallback message when Tavily is not configured."""
        return f"I would search for '{query}' but Tavily API key is not configured."
    
    return {
        "calculator": calculator,
        "tavily_search": tavily_search,
        "fallback_search": fallback_search,
        "TAVILY_AVAILABLE": TAVILY_AVAILABLE
    }