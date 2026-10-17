import { useState } from "react";

async function checkHealth(){
  const res = await fetch("http://127.0.0.1:8000/health")
  const data = await res.json()
  return data
}

function App() {
  const [health, setHealth] = useState("")
  return (
    <div>
      <button onClick={async () => {
        let data = await checkHealth()
        setHealth(data["status"])
        console.log(health)
      }}>Click me!</button>
      <p>{health}</p>
    </div>
  )
}

export default App;