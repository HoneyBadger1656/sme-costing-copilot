// NEW FILE: frontend/src/app/assistant/page.js

"use client";

import { useState, useEffect, useRef } from "react";

export default function AIAssistant() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const fetchHistory = async () => {
    try {
      const token = localStorage.getItem("token");
      const clientId = localStorage.getItem("selectedClientId") || 1;
      
      const response = await fetch(
        `http://localhost:8000/api/assistant/history?client_id=${clientId}`,
        { headers: { "Authorization": `Bearer ${token}` } }
      );
      
      const data = await response.json();
      setMessages(data.messages || []);
    } catch (error) {
      console.error("Error fetching history:", error);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    
    if (!input.trim()) return;
    
    const userMessage = input.trim();
    setInput("");
    
    // Add user message immediately
    setMessages(prev => [...prev, {
      role: "user",
      content: userMessage,
      timestamp: new Date().toISOString()
    }]);
    
    setLoading(true);
    
    try {
      const token = localStorage.getItem("token");
      const clientId = localStorage.getItem("selectedClientId") || 1;
      
      const response = await fetch("http://localhost:8000/api/assistant/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          message: userMessage,
          client_id: clientId
        })
      });
      
      const data = await response.json();
      
      // Add assistant response
      setMessages(prev => [...prev, {
        role: "assistant",
        content: data.message,
        timestamp: new Date().toISOString()
      }]);
      
    } catch (error) {
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "Sorry, I encountered an error. Please try again.",
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const suggestedQuestions = [
    "Which customer is most profitable this month?",
    "Show me orders with margins below 10%",
    "How much cash is overdue?",
    "What's my average margin across all orders?",
    "Which products have the highest costs?",
    "Summarize my cash flow for the next 30 days"
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar with suggestions */}
      <div className="w-80 bg-white border-r p-6">
        <h2 className="text-xl font-bold mb-4">AI Finance Assistant</h2>
        <p className="text-sm text-gray-600 mb-6">
          Ask questions about your finances, orders, customers, and cash flow.
        </p>
        
        <div className="space-y-3">
          <div className="text-sm font-semibold text-gray-700 mb-2">Try asking:</div>
          {suggestedQuestions.map((question, idx) => (
            <button
              key={idx}
              onClick={() => setInput(question)}
              className="w-full text-left p-3 bg-gray-50 hover:bg-gray-100 rounded-lg text-sm border border-gray-200"
            >
              {question}
            </button>
          ))}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-4xl mx-auto space-y-4">
            {messages.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                <div className="text-4xl mb-4">💬</div>
                <p className="text-lg">Ask me anything about your business finances!</p>
                <p className="text-sm mt-2">I can help analyze orders, margins, cash flow, and more.</p>
              </div>
            )}
            
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-2xl rounded-lg p-4 ${
                    msg.role === "user"
                      ? "bg-blue-600 text-white"
                      : "bg-white border border-gray-200"
                  }`}
                >
                  <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                  <div
                    className={`text-xs mt-2 ${
                      msg.role === "user" ? "text-blue-100" : "text-gray-500"
                    }`}
                  >
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
            
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: "0.1s"}}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: "0.2s"}}></div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input area */}
        <div className="border-t bg-white p-4">
          <form onSubmit={handleSend} className="max-w-4xl mx-auto">
            <div className="flex gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask a question about your finances..."
                disabled={loading}
                className="flex-1 px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                Send
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
