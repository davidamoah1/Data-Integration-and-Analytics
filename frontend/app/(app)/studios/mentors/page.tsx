'use client';

import { useEffect, useState, useRef } from 'react';
import { BotMessageSquare, Send, User } from 'lucide-react';
import { mentorService, type MentorProfile, type MentorSession } from '@/services/studios/studiosService';

export default function DataAssistantsPage() {
  const [mentors, setMentors] = useState<MentorProfile[]>([]);
  const [sessions, setSessions] = useState<MentorSession[]>([]);
  const [activeSession, setActiveSession] = useState<number | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function loadData() {
    try {
      const [mentorsRes, sessionsRes] = await Promise.all([
        mentorService.list(),
        mentorService.listSessions(),
      ]);
      setMentors(mentorsRes.mentors || []);
      setSessions(sessionsRes.sessions || []);
    } catch {
      // Empty state
    } finally {
      setLoading(false);
    }
  }

  async function startSession(mentorType: string) {
    try {
      const res = await mentorService.createSession(mentorType);
      setActiveSession(res.id);
      // Load initial messages
      setMessages([]);
    } catch {
      // Error handled
    }
  }

  async function sendMessage() {
    if (!input.trim() || !activeSession) return;
    const content = input;
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content }]);
    try {
      const res = await mentorService.sendMessage(activeSession, content);
      setMessages(res.messages || []);
    } catch {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }]);
    }
  }

  if (loading) {
    return (
      <div className="p-8 max-w-7xl mx-auto">
        <p className="text-gray-500">Loading data assistants...</p>
      </div>
    );
  }

  // If a session is active, show chat interface
  if (activeSession) {
    return (
      <div className="p-8 max-w-4xl mx-auto h-[calc(100vh-8rem)] flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold text-gray-900">Data Assistant Chat</h1>
          <button
            onClick={() => { setActiveSession(null); setMessages([]); }}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            ← Back to assistants
          </button>
        </div>

        <div className="flex-1 overflow-y-auto bg-white rounded-2xl border border-gray-200 p-6 mb-4">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex gap-3 mb-4 ${msg.role === 'user' ? 'justify-end' : ''}`}
            >
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0">
                  <BotMessageSquare size={16} className="text-amber-600" />
                </div>
              )}
              <div
                className={`max-w-[80%] p-4 rounded-2xl ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              </div>
              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                  <User size={16} className="text-blue-600" />
                </div>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Ask your data assistant..."
            className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-amber-500"
          />
          <button
            onClick={sendMessage}
            className="px-6 py-3 bg-amber-600 text-white rounded-xl hover:bg-amber-700 transition-colors"
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Data Assistants</h1>
        <p className="text-gray-600 mt-1">Role-based guidance to help you with data, research, and business decisions</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {mentors.map((mentor) => (
          <div
            key={mentor.mentor_type}
            className="bg-white rounded-2xl border border-gray-200 p-6 hover:border-amber-300 hover:shadow-md transition-all"
          >
            <div className="w-12 h-12 rounded-xl bg-amber-100 flex items-center justify-center mb-4">
              <BotMessageSquare size={24} className="text-amber-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900">{mentor.name}</h3>
            <p className="text-sm text-gray-600 mt-1 mb-4">{mentor.description}</p>

            <div className="mb-4">
              <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Capabilities</h4>
              <ul className="space-y-1">
                {mentor.capabilities.slice(0, 3).map((c, i) => (
                  <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                    <span className="text-amber-500 mt-0.5">•</span> {c}
                  </li>
                ))}
              </ul>
            </div>

            <div className="mb-4">
              <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Try asking</h4>
              <div className="space-y-1">
                {mentor.suggested_questions.slice(0, 2).map((q, i) => (
                  <p key={i} className="text-xs text-gray-500 italic">&ldquo;{q}&rdquo;</p>
                ))}
              </div>
            </div>

            <button
              onClick={() => startSession(mentor.mentor_type)}
              className="w-full py-2 bg-amber-600 text-white rounded-xl hover:bg-amber-700 transition-colors text-sm font-medium"
            >
              Start Conversation
            </button>
          </div>
        ))}
      </div>

      {/* Recent Sessions */}
      {sessions.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Conversations</h2>
          <div className="space-y-2">
            {sessions.map((s) => (
              <button
                key={s.id}
                onClick={() => setActiveSession(s.id)}
                className="w-full text-left p-4 bg-white rounded-xl border border-gray-200 hover:border-amber-300 transition-colors"
              >
                <span className="font-medium text-gray-900">{s.title}</span>
                <span className="text-sm text-gray-500 ml-2">({s.mentor_type.replace(/_/g, ' ')})</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
