import { useState } from "react";


interface ChatRequest {
  query: string;
  session_id?: string;
}

interface ChatResponse {
  message: string;
  session_id: string
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
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
  // const [health, setHealth] = useState("")
  const [chatInput, setChatInput] = useState("")
  const [messages, setMessages] = useState<Message[]>([])
  const [session_id, setSession_id] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  // const [agentResponse, setAgentResponse] = useState("")

  function displayMessages(messageList: Message[]) {
    return (
      <>
        {messageList.map((message) => {
          return (
            <div key={message.id}>
              {message.role}: {message.content}
            </div>)
        })}
      </>
    )
  }
  async function handleChatSubmit(e: React.SubmitEvent<HTMLFormElement>) {
    e.preventDefault();
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: chatInput
    }
    setMessages(prev => [...prev, userMessage])
    const query = userMessage.content
    const res = await sendMessage(query, session_id ?? undefined)
    const assistantMessage: Message = {
      id: crypto.randomUUID(),
      role: "assistant",
      content: res.message
    }
    setMessages(prev => [...prev, assistantMessage])
    if (!session_id) {
      setSession_id(res.session_id)
    }
    console.log(messages)
    // setAgentResponse(res.message)
    setChatInput("")
  }

  return (
    <div>
      {displayMessages(messages)}
      <form onSubmit={handleChatSubmit}>
        <label htmlFor="query">Your Message:
          <input
            id="query"
            type="text"
            value={chatInput}
            onChange={(e) => {
              setChatInput(e.target.value)
            }} />
        </label>
        <button type="submit">Submit</button>
      </form>

    </div>
  )
}

export default App;