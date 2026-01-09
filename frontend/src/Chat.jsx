import { useState, useRef, useEffect } from "react";
import axios from "axios";

function Chat() {
  const [q, setQ] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const ask = async () => {
    if (!q.trim() || loading) return;

    const userMsg = { role: "user", content: q };
    setMessages(prev => [...prev, userMsg]);
    setQ("");
    setLoading(true);

    try {
      const res = await axios.post("http://localhost:8000/chat", { question: userMsg.content });
      const aiMsg = { role: "ai", content: res.data.answer || "I couldn't process that." };
      setMessages(prev => [...prev, aiMsg]);
    } catch (e) {
      setMessages(prev => [...prev, { role: "ai", content: "Error connecting to Agent." }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !loading) ask();
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h3>💬 AI Maintenance Assistant</h3>
      </div>

      <div className="chat-messages" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="empty-chat">
            <div className="ai-avatar-large">🤖</div>
            <p>How can I help you analyze your machine data today?</p>
            <div className="suggestions">
              <span onClick={() => setQ("Show me the failure distribution")}>"Show me the failure distribution"</span>
              <span onClick={() => setQ("Why is the robot overheating?")}>"Why is the robot overheating?"</span>
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`message-row ${m.role}`}>
            {m.role === 'ai' && <div className="avatar ai">🤖</div>}
            <div className={`bubble ${m.role}`}>
              {m.content.split('\n').map((l, ix) => <p key={ix}>{l}</p>)}
            </div>
            {m.role === 'user' && <div className="avatar user">👤</div>}
          </div>
        ))}

        {loading && (
          <div className="message-row ai">
            <div className="avatar ai">🤖</div>
            <div className="bubble ai typing">
              <span>.</span><span>.</span><span>.</span>
            </div>
          </div>
        )}
      </div>

      <div className="chat-input-wrapper">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask a question..."
          disabled={loading}
        />
        <button onClick={ask} disabled={loading || !q.trim()}>
          ➤
        </button>
      </div>
    </div>
  );
}

export default Chat;
