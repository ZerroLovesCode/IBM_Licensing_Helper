import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Annotated
from agent import make_graph
from uuid import uuid4, UUID

from langgraph.checkpoint.memory import InMemorySaver

app = FastAPI()

# Comma-separated list of frontend URLs allowed to call the API, e.g. the Render static site's URL.
origins = [
    origin.strip().rstrip("/")
    for origin in os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_methods = ["*"],
    allow_headers = ["*"]
)

checkpointer = InMemorySaver()
graph = make_graph(checkpointer=checkpointer)

MAX_QUERY_LENGTH = 1500
class ChatRequest(BaseModel):
    query: Annotated[str, Field(min_length=1, max_length=MAX_QUERY_LENGTH)]
    session_id: UUID | None = None

class ChatResponse(BaseModel):
    message: str 
    session_id: UUID


@app.get("/health")
def check_health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    prompt = {}
    prompt["messages"] = [("user", req.query)] 

    if not req.session_id:
        session_id = uuid4()
        cur_session = session_id
    else:
        cur_session = req.session_id

    model_response = graph.invoke(prompt, {"configurable": {"thread_id": str(cur_session)}})
    model_response_text = model_response["messages"][-1].text 
    res = ChatResponse(message=model_response_text, session_id = cur_session)
    return res