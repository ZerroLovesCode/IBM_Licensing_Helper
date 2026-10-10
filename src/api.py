from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Annotated
from agent import make_graph

app = FastAPI()

graph = make_graph()

MAX_QUERY_LENGTH = 1500
class ChatRequest(BaseModel):
    query: Annotated[str, Field(min_length=1, max_length=MAX_QUERY_LENGTH)]

class ChatResponse(BaseModel):
    message: str 


@app.get("/health")
def check_health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    prompt = {}
    prompt["messages"] = [("user", req.query)] 

    model_response = graph.invoke(prompt)
    model_response_text = model_response["messages"][-1].text 
    res = ChatResponse(message=model_response_text)
    return res