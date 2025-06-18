import operator
from typing import TypedDict, Annotated

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    step: str