import { useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";


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
            <div key={message.id} className={`turn turn-${message.role}`}>
              {message.role === "assistant" && <BrandMark />}
              <div className="turn-body">
                {message.role === "assistant"
                  ? <Markdown remarkPlugins={[remarkGfm]}>{message.content}</Markdown>
                  : message.content}
              </div>
            </div>)
        })}
      </>
    )
  }
  async function handleChatSubmit(e: React.SubmitEvent<HTMLFormElement>) {
    e.preventDefault();
    const query = chatInput
    if (query.trim() != ""){
      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: "user",
        content: query 
      }
      setMessages(prev => [...prev, userMessage])
      setChatInput("")
      setLoading(true)
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
      setLoading(false)
    }
    else{
      return;
    }
  }

  return (
    <div className="shell">
      {/* Shown only on narrow screens, where the side panel is hidden. */}
      <header className="topbar">
        <div className="brand">
          <BrandMark />
          IBM Licensing Assistant
        </div>
      </header>

      <div className="layout">
        <main className="main">
          {messages.length === 0 ? (
            <section className="intro">
              <h1>Ask the IBM licensing guides.</h1>
              <p className="intro-lede">
                Every answer comes from IBM's published licensing documentation and cites the
                guide and page it came from, so you can check it before you rely on it.
              </p>
              <ul className="starters" aria-label="Example questions">
                {STARTER_QUESTIONS.map((question) => (
                  <li key={question}>
                    <button type="button" className="starter" onClick={() => setChatInput(question)}>
                      {question}
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          ) : (
            <section className="transcript" aria-label="Conversation" aria-live="polite">
              {displayMessages(messages)}
              {loading && (
                <div className="turn turn-assistant turn-pending">
                  <BrandMark />
                  <div className="turn-body">
                    Searching the guides
                    <span className="dots" aria-hidden="true"><span /><span /><span /></span>
                  </div>
                </div>
              )}
            </section>
          )}

          <div className="composer-dock">
            <form className="composer" onSubmit={handleChatSubmit}>
              <label htmlFor="query" className="visually-hidden">Your message</label>
              <input
                id="query"
                type="text"
                autoComplete="off"
                placeholder="Ask about PVUs, sub-capacity, containers…"
                value={chatInput}
                onChange={(e) => {
                  setChatInput(e.target.value)
                }} />
              <button type="submit" disabled={loading || chatInput.trim()===""}>Ask</button>
            </form>
            <p className="composer-note">Answers cite the guide and page. Check the cited page before relying on it.</p>
          </div>
        </main>

        <aside className="rail">
          <div className="rail-panel">
            <div className="rail-brand">
              <BrandMark />
              <div>
                <div className="rail-name">IBM Licensing Assistant</div>
                <p className="rail-tagline">Your queries answered with citations from the official documentation</p>
              </div>
            </div>
            <h2>Guides searched <span className="rail-count">{SOURCE_GUIDES.length}</span></h2>
            <p>The assistant answers from these documents only.</p>
            <ul className="sources">
              {SOURCE_GUIDES.map((guide) => <li key={guide}>{guide}</li>)}
            </ul>
          </div>
        </aside>
      </div>
    </div>
  )
}

// Display-only content for the empty state and the sources rail.
const STARTER_QUESTIONS = [
  "What is a PVU and how is it counted?",
  "When do I need ILMT for sub-capacity licensing?",
  "How are containers licensed under Cloud Paks?",
  "Does a backup server need its own licence?",
]

// Mirrors the PDFs in data/Licensing_documents. Update it by hand when the guides change.
const SOURCE_GUIDES = [
  "Audit",
  "Backup",
  "Bundling and supporting programs",
  "Bring your own software licence",
  "Cloud Paks",
  "Container licensing",
  "Entitlements",
  "IASP program",
  "IBM licensing tools",
  "License Information documents",
  "Non-production usage",
  "Virtualization capacity",
]

function BrandMark() {
  // A guide page with its corner folded: the product answers from documents.
  return (
    <svg className="brand-mark" viewBox="0 0 24 24" aria-hidden="true">
      <rect width="24" height="24" rx="7" fill="#1b6e66" />
      <path d="M8 6h6l3 3v9H8z" fill="#fff" />
      <path d="M14 6v3h3" fill="#cfe3e0" />
      <path d="M10 12.5h5M10 15h3.5" stroke="#1b6e66" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  )
}

export default App;