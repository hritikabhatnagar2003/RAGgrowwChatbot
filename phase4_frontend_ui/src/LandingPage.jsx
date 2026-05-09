import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, ShieldCheck, FileCheck } from 'lucide-react';

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="landing-page">
      <header className="landing-header">
        <div className="landing-logo">Groww AI</div>
        <nav className="landing-nav">
          <span className="nav-link">Direct Mutual Funds</span>
          <span className="nav-link">US Stocks</span>
          <span className="nav-link">ETFs</span>
          <span className="nav-link active">How it Works</span>
        </nav>
        <button className="btn-login" onClick={() => navigate('/chat')}>Login/Register</button>
      </header>

      <main>
        <section className="landing-hero">
          <h1 className="hero-title">Your Mutual Fund Expert, Powered by AI.</h1>
          <p className="hero-subtitle">Get instant, facts-only answers to all your investment queries. No jargon, just insights.</p>
          <button className="btn-primary" onClick={() => navigate('/chat')}>Try Groww AI</button>
        </section>

        <section className="hero-mockup">
          <div className="message-bubble user" style={{ marginLeft: 'auto', marginBottom: '1rem', width: 'fit-content' }}>
            What is the difference between an Index fund and an actively managed fund?
          </div>
          <div className="message-bubble assistant">
            An index fund passively tracks a specific market index (like the S&P 500) aiming to match its performance, usually resulting in lower fees. An actively managed fund is run by a manager who selects investments to try and beat the market, typically incurring higher fees.
          </div>
          <div className="chat-input-wrapper" style={{ marginTop: '2rem' }}>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Ask about mutual funds...</span>
          </div>
        </section>

        <section className="features-grid">
          <div className="feature-card">
            <div className="feature-icon"><Zap size={20} /></div>
            <h3>Instant Answers</h3>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem', fontSize: '0.85rem' }}>Skip the endless searching. Get precise answers to your mutual fund questions in seconds.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon"><FileCheck size={20} /></div>
            <h3>Verified Sources</h3>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem', fontSize: '0.85rem' }}>Information aggregated from trusted financial documents and official fund prospectuses.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon"><ShieldCheck size={20} /></div>
            <h3>Safe & Secure</h3>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem', fontSize: '0.85rem' }}>Your queries are private. Note: Groww AI provides facts, not personalized investment advice.</p>
          </div>
        </section>
      </main>
    </div>
  );
}
