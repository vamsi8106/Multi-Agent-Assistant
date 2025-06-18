import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from pydantic import BaseModel
from typing import Literal
from app.langgraph_nodes.state import AgentState
from app.langgraph_nodes.tools import get_tools
from app.core.logger import logger

ROUTER_PROMPT = """
Classify the user's input and pick one category:
- 'math_node' for math calculations
- 'search_node' for web search
- 'farewell' if user says bye or thanks

Respond in JSON:
{"next": "<node>", "reasoning": "<why>"}
"""

class Router(BaseModel):
    next: Literal["search_node", "math_node", "farewell"]
    reasoning: str

def build_nodes(groq_api_key, model_name, temperature, tavily_api_key):
    tools = get_tools(tavily_api_key)
    groq_model = ChatGroq(
        model=model_name,
        temperature=temperature,
        api_key=groq_api_key
    )

    def supervisor_node(state: AgentState):
        try:
            messages = [
                SystemMessage(content=ROUTER_PROMPT),
                HumanMessage(content=state["messages"][-1].content)
            ]
            response_msg = groq_model.invoke(messages)
            parsed = json.loads(response_msg.content)
            router_response = Router(**parsed)
            logger.info(f"Supervisor → Next: {router_response.next}, Reason: {router_response.reasoning}")
            return {"step": router_response.next}
        except Exception as e:
            logger.exception("Error in supervisor_node")
            return {"step": "farewell"}

    def math_node(state: AgentState):
        try:
            query = state["messages"][-1].content
            result = tools["calculator"].invoke({"expression": query})
            response = f"The answer is: {result}" if "Error" not in result else result
            return {"messages": [AIMessage(content=response)], "step": "farewell"}
        except Exception as e:
            logger.exception("Error in math_node")
            return {"messages": [AIMessage(content="Something went wrong in math_node.")], "step": "farewell"}

    def search_node(state: AgentState):
        try:
            query = state["messages"][-1].content
            if not tools["TAVILY_AVAILABLE"]:
                result = tools["fallback_search"].invoke({"query": query})
                return {"messages": [AIMessage(content=result)], "step": "farewell"}

            results = tools["tavily_search"].invoke({"query": query})
            if results:
                response = "Here's what I found:\n\n"
                for i, r in enumerate(results[:2], 1):
                    title = r.get('title', 'No title')
                    content = r.get('content', 'No content')[:200]
                    url = r.get('url', '')
                    response += f"{i}. {title}\n   {content}...\n   Source: {url}\n\n"
            else:
                response = "No results found."

            return {"messages": [AIMessage(content=response)], "step": "farewell"}
        except Exception as e:
            logger.exception("Error in search_node")
            return {"messages": [AIMessage(content=f"Search failed: {str(e)}")], "step": "farewell"}

    def farewell_node(state: AgentState):
        return {"messages": [AIMessage(content="Goodbye!")]}

    nodes = {
        "supervisor": supervisor_node,
        "math_node": math_node,
        "search_node": search_node,
        "farewell": farewell_node
    }

    return nodes, lambda s: s["step"]
