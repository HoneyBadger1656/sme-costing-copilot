// NEW FILE: frontend/src/app/assistant/page.js

"use client";

import { useState, useEffect, useRef } from "react";
import AppLayout from "../../components/layout/AppLayout";
import PageHeader from "../../components/layout/PageHeader";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function AIAssistant() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

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
        `${API_BASE_URL}/api/assistant/history?client_id=${clientId}`,
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

    if (!input.trim() && !uploadedFile) return;

    const userMessage = input.trim() || "Analyze this file";
    setInput("");

    // Add user message immediately
    const userMessageObj = {
      role: "user",
      content: uploadedFile ? `[File: ${uploadedFile.name}] ${userMessage}` : userMessage,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessageObj]);

    setLoading(true);

    try {
      const token = localStorage.getItem("token");
      const clientId = localStorage.getItem("selectedClientId") || 1;

      let response;

      if (uploadedFile) {
        // Handle file upload
        const formData = new FormData();
        formData.append("file", uploadedFile);
        formData.append("message", userMessage);
        formData.append("client_id", clientId);

        response = await fetch(`${API_BASE_URL}/api/assistant/upload-chat`, {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${token}`
          },
          body: formData
        });
      } else {
        // Handle regular chat
        response = await fetch(`${API_BASE_URL}/api/assistant/chat`, {
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
      }

      const data = await response.json();

      // Add assistant response
      setMessages(prev => [...prev, {
        role: "assistant",
        content: data.message,
        timestamp: new Date().toISOString(),
        query_type: data.query_type
      }]);

      // Clear uploaded file after sending
      setUploadedFile(null);

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

  const handleFileUpload = (file) => {
    const allowedTypes = ['application/pdf', 'text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
    
    if (!allowedTypes.includes(file.type)) {
      alert('Please upload PDF, CSV, or Excel files only.');
      return;
    }

    if (file.size > 10 * 1024 * 1024) { // 10MB limit
      alert('File size must be less than 10MB.');
      return;
    }

    setUploadedFile(file);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const removeFile = () => {
    setUploadedFile(null);
  };

  const suggestedQuestions = [
    "Which customer is most profitable this month?",
    "Show me orders with margins below 10%",
    "How much cash is overdue?",
    "What's my average margin across all orders?",
    "Which products have the highest costs?",
    "Summarize my cash flow for the next 30 days",
    "Which scenario gives the best profit?",
    "What's my current ratio?",
    "Is my Tally integration working?",
    "Compare my top 3 scenarios"
  ];

  return (
    <AppLayout>
      <PageHeader
        title="AI Financial Assistant"
        description="Ask questions about your finances, orders, customers, and cash flow"
        icon="🤖"
        breadcrumbs={[
          { name: "Dashboard", href: "/dashboard" },
          { name: "AI Assistant" }
        ]}
      />

      <div className="flex flex-col lg:flex-row h-full">
        {/* Sidebar with suggestions */}
        <div className="lg:w-80 bg-white border-r border-b lg:border-b-0 p-4 lg:p-6">
          <h2 className="text-lg font-semibold mb-4">Suggested Questions</h2>

        <div className="space-y-2 lg:space-y-3">
          <div className="text-sm font-semibold text-gray-700 mb-2">Try asking:</div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-2 lg:gap-3">
            {suggestedQuestions.map((question, idx) => (
              <button
                key={idx}
                onClick={() => setInput(question)}
                className="w-full text-left p-2 lg:p-3 bg-gray-50 hover:bg-gray-100 rounded-lg text-xs lg:text-sm border border-gray-200"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col min-h-0">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 lg:p-6">
          <div className="max-w-4xl mx-auto space-y-4">
            {messages.length === 0 && (
              <div className="text-center py-8 lg:py-12 text-gray-500">
                <div className="text-3xl lg:text-4xl mb-4">💬</div>
                <p className="text-base lg:text-lg">Ask me anything about your business finances!</p>
                <p className="text-sm mt-2">I can help analyze orders, margins, cash flow, and more.</p>
              </div>
            )}

            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-xs sm:max-w-md lg:max-w-2xl rounded-lg p-3 lg:p-4 ${msg.role === "user"
                      ? "bg-blue-600 text-white"
                      : "bg-white border border-gray-200"
                    }`}
                >
                  <div className="text-sm whitespace-pre-wrap break-words">{msg.content}</div>
                  <div
                    className={`text-xs mt-2 ${msg.role === "user" ? "text-blue-100" : "text-gray-500"
                      }`}
                  >
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="bg-white border border-gray-200 rounded-lg p-3 lg:p-4">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input area */}
        <div className="border-t bg-white p-3 lg:p-4">
          <form onSubmit={handleSend} className="max-w-4xl mx-auto">
            
            {/* File upload area */}
            {uploadedFile && (
              <div className="mb-3 lg:mb-4 p-2 lg:p-3 bg-blue-50 border border-blue-200 rounded-lg flex items-center justify-between">
                <div className="flex items-center space-x-2 min-w-0">
                  <div className="text-blue-600">📎</div>
                  <span className="text-xs lg:text-sm text-blue-800 truncate">{uploadedFile.name}</span>
                  <span className="text-xs text-blue-600 flex-shrink-0">({(uploadedFile.size / 1024).toFixed(1)} KB)</span>
                </div>
                <button
                  type="button"
                  onClick={removeFile}
                  className="text-blue-600 hover:text-blue-800 text-xs lg:text-sm ml-2 flex-shrink-0"
                >
                  Remove
                </button>
              </div>
            )}

            {/* Drag and drop area */}
            <div
              className={`mb-3 lg:mb-4 border-2 border-dashed rounded-lg p-3 lg:p-4 text-center transition-colors ${
                dragActive 
                  ? 'border-blue-400 bg-blue-50' 
                  : 'border-gray-300 hover:border-gray-400'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <div className="text-gray-500 text-xs lg:text-sm">
                <div className="mb-2">📁</div>
                <p>Drag & drop files here or <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="text-blue-600 hover:text-blue-800 underline"
                >
                  browse
                </button></p>
                <p className="text-xs mt-1">Supports PDF, CSV, Excel files (max 10MB)</p>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.csv,.xlsx,.xls"
                onChange={(e) => e.target.files[0] && handleFileUpload(e.target.files[0])}
                className="hidden"
              />
            </div>

            <div className="flex gap-2 lg:gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={uploadedFile ? "Ask about the uploaded file..." : "Ask a question about your finances..."}
                disabled={loading}
                className="flex-1 px-3 lg:px-4 py-2 lg:py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 text-sm lg:text-base"
              />
              <button
                type="submit"
                disabled={loading || (!input.trim() && !uploadedFile)}
                className="bg-blue-600 text-white px-4 lg:px-8 py-2 lg:py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-sm lg:text-base"
              >
                {uploadedFile ? "Analyze" : "Send"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
    </AppLayout>
  );
}
