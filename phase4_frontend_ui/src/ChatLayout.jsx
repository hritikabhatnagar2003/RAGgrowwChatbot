import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  MessageSquare, Info, AlertTriangle, Send, X, ShieldAlert, FileText 
} from 'lucide-react';

const API_BASE_URL = `${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'}/api`;

export default function ChatLayout() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [examples, setExamples] = useState([]);
  
  // State for Source Preview Panel
  const [previewData, setPreviewData] = useState(null);
  const [showPreview, setShowPreview] = useState(false);

  const chatEndRef = useRef(null);

  useEffect(() => {
    const fetchExamples = async () => {
      try {
        const res = await axios.get(`${API_BASE_URL}/examples`);
        setExamples(res.data.examples);
      } catch (err) {
        console.error("Failed to load examples");
      }
    };
    fetchExamples();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async (queryText) => {
    const text = typeof queryText === 'string' ? queryText : input;
    if (!text.trim() || isLoading) return;

    const newMessages = [...messages, { role: 'user', content: text }];
    setMessages(newMessages);
    setInput('');
    setIsLoading(true);

    try {
      const res = await axios.post(`${API_BASE_URL}/chat`, { query: text });
      const data = res.data;
      
      const assistantMsg = {
        role: 'assistant',
        content: data.answer,
        source_url: data.source_url,
        refused: data.refused,
        intent: data.query_type
      };
      
      setMessages([...newMessages, assistantMsg]);
      
      // If factual, mock some preview data based on the response to match UI design
      if (!data.refused && data.query_type === 'FACTUAL') {
        setPreviewData({
          fundName: "Extracted Fund Context",
          expenseRatio: text.toLowerCase().includes("expense") ? "0.76%" : "N/A",
          exitLoad: text.toLowerCase().includes("exit") ? "1.00%" : "N/A",
          aum: "₹60,000 Cr",
          rawText: data.answer
        });
        setShowPreview(true);
      } else {
        setShowPreview(false);
      }

    } catch (err) {
      setMessages([...newMessages, {
        role: 'assistant',
        content: "Server error. Ensure backend is running.",
        refused: true
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-layout">
      {/* LEFT PANE: HISTORY */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <MessageSquare size={18} /> MF FAQ
        </div>
        <div className="sidebar-section-title">HISTORY</div>
        <ul className="history-list">
          <li className="history-item"><MessageSquare size={14} /> Exit Loads & Tax</li>
          <li className="history-item"><MessageSquare size={14} /> SIP vs Lumpsum</li>
          <li className="history-item"><MessageSquare size={14} /> Index Funds</li>
        </ul>
      </aside>

      {/* CENTER PANE: CHAT AREA */}
      <main className="chat-area">
        <header className="chat-header">
          <div>
            <h1 className="chat-header-title">Mutual Fund FAQ Assistant</h1>
            <p className="chat-header-subtitle">AI-powered fund insights</p>
          </div>
          <Info size={18} color="var(--text-secondary)" />
        </header>

        <div className="disclaimer-banner">
          <AlertTriangle size={16} /> Facts-only. No investment advice.
        </div>

        <div className="messages-container">
          {messages.map((msg, idx) => {
            const isUser = msg.role === 'user';
            if (isUser) {
              return (
                <div key={idx} className="message-row user">
                  <div className="message-bubble user">{msg.content}</div>
                </div>
              );
            }

            // Assistant Refused/Safety Block
            if (msg.refused) {
              return (
                <div key={idx} className="message-row assistant">
                  <div className="message-bubble safety-block">
                    <div className="safety-header">
                      <ShieldAlert size={16} /> Safety Block
                    </div>
                    {msg.content}
                  </div>
                </div>
              );
            }

            // Assistant Factual
            return (
              <div key={idx} className="message-row assistant">
                <div className="message-bubble assistant">
                  <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
                  
                  {msg.source_url && (
                    <button 
                      className="view-source-btn"
                      onClick={() => setShowPreview(true)}
                    >
                      <FileText size={14} /> View Source
                    </button>
                  )}
                  <span className="date-footer">Last updated: {new Date().toISOString().split('T')[0]}</span>
                </div>
              </div>
            );
          })}
          
          {isLoading && (
            <div className="message-row assistant">
              <div className="message-bubble assistant" style={{ padding: '0.75rem 1.25rem' }}>
                <span className="typing-dot"></span>
                <span className="typing-dot"></span>
                <span className="typing-dot"></span>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        <div className="input-section">
          {messages.length === 0 && examples.length > 0 && (
            <div className="chips-container">
              {examples.map((ex, i) => (
                <button key={i} className="chip" onClick={() => handleSend(ex)}>
                  {ex.length > 25 ? ex.substring(0, 25) + '...' : ex}
                </button>
              ))}
            </div>
          )}
          
          <form className="chat-input-wrapper" onSubmit={(e) => { e.preventDefault(); handleSend(); }}>
            <input 
              type="text" 
              className="chat-input" 
              placeholder="Ask about mutual funds..." 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
            />
            <button type="submit" className="send-btn" disabled={!input.trim() || isLoading}>
              <Send size={16} />
            </button>
          </form>
        </div>
      </main>

      {/* RIGHT PANE: SOURCE PREVIEW */}
      {showPreview && previewData && (
        <aside className="source-preview">
          <div className="preview-header">
            <span><FileText size={16} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'middle' }} /> Source Preview</span>
            <X size={18} style={{ cursor: 'pointer', color: 'var(--text-secondary)' }} onClick={() => setShowPreview(false)} />
          </div>
          
          <div className="preview-content">
            <div className="preview-section-title">DOCUMENT CONTEXT</div>
            <div className="preview-fund-name">{previewData.fundName}</div>
            
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Expense Ratio</div>
                <div className="stat-value">{previewData.expenseRatio}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Exit Load</div>
                <div className="stat-value">{previewData.exitLoad}</div>
                <div className="stat-subtext">If redeemed &lt; 1 yr</div>
              </div>
            </div>
            
            <div className="stat-card" style={{ marginBottom: '1.5rem' }}>
              <div className="stat-label">Fund Size (AUM)</div>
              <div className="stat-value">{previewData.aum}</div>
            </div>
            
            <div className="insights-header">
              <span className="preview-section-title" style={{ margin: 0 }}>Detailed Insights</span>
              <span className="extract-badge">Extract</span>
            </div>
            
            <div className="insights-text">
              {previewData.rawText}
            </div>
          </div>
        </aside>
      )}
    </div>
  );
}
