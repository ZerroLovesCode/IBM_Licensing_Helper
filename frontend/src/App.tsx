import { useState } from "react";


interface ChatRequest {
  query: string;
  session_id?: string;
}

interface ChatResponse {
  respones: string;
  session_id: string
}

async function checkHealth() {
  const res = await fetch("http://127.0.0.1:8000/health")
  const data = await res.json()
  return data
}

async function sendMessage(message: string, session_id?: string): Promise<ChatResponse> {
  const chat_url = "http://127.0.0.1:8000/chat"
  const payload: ChatRequest = {
    query: message,
    session_id: session_id ?? undefined
  }
  const res = await fetch(chat_url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  })

  if (!res.ok) {
    throw new Error(`HTTP Error ${res.status}`)
  }

  const result = await res.json();
  console.log(result)
  return result
}

function App() {
  const [health, setHealth] = useState("")
  const [chatInput, setChatInput] = useState("")

  async function handleChatSubmit(e){
    e.preventDefault();
    const message = chatInput
    console.log(message)
    const res = await sendMessage(message)
    console.log(res)
    setChatInput("")
  }

  return (
    <div>
        <form onSubmit={handleChatSubmit}>
          <label htmlFor="query">Your Message:
          <input
            id="query"
            type="text"
            value={chatInput}
            onChange={(e)=>{
              setChatInput(e.target.value)
            }} />
            </label>
            <button type="submit">Submit</button>
        </form>
    </div>
  )
}

export default App;