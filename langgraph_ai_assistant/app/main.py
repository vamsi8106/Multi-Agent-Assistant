from fastapi import FastAPI
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from app.langgraph_nodes.state import AgentState
from app.langgraph_nodes.nodes import build_nodes
from langchain_core.messages import HumanMessage

app = FastAPI(title="LangGraph AI Assistant")

class AssistantInput(BaseModel):
    query: str
    groq_api_key: str
    model_name: str = "llama3-70b-8192"
    temperature: float = 0.2
    tavily_api_key: str

def build_graph(groq_api_key, model_name, temperature, tavily_api_key):
    nodes, route_supervisor = build_nodes(groq_api_key, model_name, temperature, tavily_api_key)
    graph = StateGraph(AgentState)
    graph.set_entry_point("supervisor")

    for name, func in nodes.items():
        graph.add_node(name, func)

    graph.add_conditional_edges("supervisor", route_supervisor, {
        "math_node": "math_node",
        "search_node": "search_node",
        "farewell": "farewell"
    })

    graph.add_edge("math_node", "farewell")
    graph.add_edge("search_node", "farewell")
    graph.add_edge("farewell", END)

    return graph.compile()

@app.post("/predict")
def ask_question(data: AssistantInput):
    graph_app = build_graph(
        data.groq_api_key,
        data.model_name,
        data.temperature,
        data.tavily_api_key
    )

    state = {
        "messages": [HumanMessage(content=data.query)],
        "step": "supervisor"
    }

    result = graph_app.invoke(state)
    return {
        "messages": [msg.content for msg in result["messages"]]
    }
