'use client';

export const dynamic = 'force-dynamic';

import { useState, useEffect, useRef } from 'react';
import { useSession } from 'next-auth/react';
import { PageHeader } from '@/components/shared/AppShell';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Send, Bot, User, Plus } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  feedback_type?: string;
  created_at: string;
}

export default function TrainingChatPage() {
  const { data: session } = useSession();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize session
  useEffect(() => {
    if (session && !sessionId) {
      // Generate a new session ID
      setSessionId(`session-${Date.now()}`);
    }
  }, [session, sessionId]);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !session || !sessionId) return;

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: input,
      created_at: new Date().toISOString(),
    };

    setMessages([...messages, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const token = (session as any)?.accessToken || (session?.user as any)?.accessToken;
      if (!token) throw new Error('No access token');

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/training/data/chat`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          message: input,
        }),
      });

      if (!response.ok) throw new Error('Failed to send message');
      const data = await response.json();

      const assistantMessage: Message = {
        id: data.message_id,
        role: 'assistant',
        content: data.ai_response,
        feedback_type: data.feedback_type,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `Error: ${err instanceof Error ? err.message : 'Unknown error'}`,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col">
      <PageHeader
        title="Training Chat"
        subtitle="Provide feedback to train the virtual brain. Examples: 'This candidate should match Senior Engineer', 'Improve Python matching', 'Why did you score John 0.65?'"
      />

      {/* Chat Container */}
      <div className="flex-1 overflow-hidden flex flex-col">
        {/* Messages Area */}
        <Card className="flex-1 overflow-hidden flex flex-col border-none rounded-none">
          <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="flex items-center justify-center h-full text-center">
                <div>
                  <Bot className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                  <p className="text-muted-foreground">
                    Start a training conversation. Tell the system what it should learn.
                  </p>
                </div>
              </div>
            ) : (
              <>
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    {message.role === 'assistant' && (
                      <Bot className="h-6 w-6 text-blue-600 flex-shrink-0 mt-1" />
                    )}
                    <div
                      className={`max-w-md px-4 py-2 rounded-lg ${
                        message.role === 'user'
                          ? 'bg-blue-600 text-white rounded-br-none'
                          : 'bg-gray-100 text-foreground rounded-bl-none'
                      }`}
                    >
                      <p className="text-sm">{message.content}</p>
                      {message.feedback_type && (
                        <Badge className="mt-2 text-xs">{message.feedback_type}</Badge>
                      )}
                    </div>
                    {message.role === 'user' && (
                      <User className="h-6 w-6 text-gray-600 flex-shrink-0 mt-1" />
                    )}
                  </div>
                ))}
                {loading && (
                  <div className="flex gap-3">
                    <Bot className="h-6 w-6 text-blue-600 flex-shrink-0 mt-1" />
                    <div className="bg-gray-100 px-4 py-2 rounded-lg rounded-bl-none">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </CardContent>
        </Card>

        {/* Input Area */}
        <Card className="border-none rounded-none border-t">
          <CardContent className="p-4">
            <form onSubmit={handleSendMessage} className="flex gap-2">
              <input
                type="text"
                placeholder="Tell the system what to learn... (e.g., 'Jane should match Senior Engineer')"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={loading}
                className="flex-1 px-4 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Send className="h-4 w-4" />
              </button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
