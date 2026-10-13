'use client';

import { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Send, MessageCircle, Loader2 } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface CVFollowUpChatProps {
  analysisId: string;
  suggestedPrompts?: string[];
}

export function CVFollowUpChat({
  analysisId,
  suggestedPrompts = [
    'What skills should I prioritize learning first?',
    'How can I transition to this role?',
    'What projects would strengthen my profile?',
    'How long would it take to close these gaps?',
  ],
}: CVFollowUpChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return;

    setError(null);
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // API call to backend for Claude chat
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          analysisId,
          message: text,
          conversationHistory: messages,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response from Claude');
      }

      const data = await response.json();
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="flex flex-col h-full">
      <CardHeader className="border-b">
        <CardTitle className="flex items-center gap-2 text-lg">
          <MessageCircle className="h-5 w-5" />
          Ask Claude about your CV
        </CardTitle>
        <p className="text-xs text-muted-foreground mt-1">
          Get personalized advice on your analysis
        </p>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col min-h-[400px]">
        {/* Messages area */}
        <div className="flex-1 overflow-y-auto space-y-3 mb-4">
          {messages.length === 0 ? (
            <div className="h-full flex items-center justify-center text-center py-8">
              <div>
                <MessageCircle className="h-8 w-8 text-muted-foreground/30 mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">
                  No messages yet. Try one of the suggested questions below.
                </p>
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <div key={msg.id} className={`flex gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-xs px-3 py-2 rounded-lg text-sm ${
                    msg.role === 'user'
                      ? 'bg-primary text-primary-foreground rounded-br-none'
                      : 'bg-muted text-muted-foreground rounded-bl-none'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                  <span className="text-xs opacity-70 mt-1 block">
                    {msg.timestamp.toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </div>
              </div>
            ))
          )}
          {loading && (
            <div className="flex gap-2 justify-start">
              <div className="bg-muted text-muted-foreground rounded-lg rounded-bl-none px-3 py-2 flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">Thinking...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-3 p-2 rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs">
            {error}
          </div>
        )}

        {/* Suggested prompts */}
        {messages.length === 0 && (
          <div className="mb-4 space-y-2">
            <p className="text-xs font-medium text-muted-foreground">Suggested questions:</p>
            <div className="grid grid-cols-1 gap-2">
              {suggestedPrompts.map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendMessage(prompt)}
                  disabled={loading}
                  className="text-left px-3 py-2 rounded-lg border border-border hover:bg-accent text-xs transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span className="text-muted-foreground">{prompt}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input area */}
        <div className="border-t pt-3 mt-3 flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage(input);
              }
            }}
            placeholder="Ask a question..."
            disabled={loading}
            className="flex-1 px-3 py-2 rounded-lg border border-input text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50"
            aria-label="Chat message input"
          />
          <Button
            size="sm"
            onClick={() => handleSendMessage(input)}
            disabled={loading || !input.trim()}
            aria-label="Send message"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
