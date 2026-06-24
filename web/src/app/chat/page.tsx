'use client';

import { useEffect, useRef, useState } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader2, Send, Plus, Trash2, Upload, CheckCircle, AlertCircle } from 'lucide-react';
import { ActionConfirmation } from '@/components/ActionConfirmation';
import { OnboardingFlow } from '@/components/OnboardingFlow';

// All chat traffic goes through the BFF proxy (like the rest of the app): the
// proxy injects the logged-in user's token server-side, so the access token
// never reaches the browser and this works in production where the backend is
// not browser-reachable. The proxy now streams SSE through intact.
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || '/api/proxy';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  actions_taken?: Action[];
  attachments?: File[];
}

interface Action {
  id: string;
  description: string;
  status: 'pending' | 'completed' | 'failed';
  result?: unknown;
  type?: string;
  requires_confirmation?: boolean;
  message_id?: string;
}

interface ChatSession {
  id: string;
  title: string;
  created_at: Date;
  last_message_at: Date;
  message_count: number;
}

export default function ChatPage() {
  const router = useRouter();
  const { data: session, status } = useSession();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  // Open by default on desktop; collapsed on mobile (set after mount to avoid
  // an SSR/client mismatch). On mobile the sidebar overlays the chat as a
  // drawer rather than squeezing it into a sliver.
  const [showSidebar, setShowSidebar] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressStage, setProgressStage] = useState<string>('');
  const [pendingActions, setPendingActions] = useState<Action[]>([]);
  const [showActionConfirmation, setShowActionConfirmation] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Redirect only once auth has resolved. `useSession` starts in a "loading"
  // state where `session` is undefined; redirecting on `!session` then would
  // bounce authenticated users to /login on every full page load.
  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/login');
    }
  }, [status, router]);

  // Load chat sessions
  useEffect(() => {
    if (session?.user) {
      loadSessions();
      // Show onboarding if first time
      const hasSeenOnboarding = localStorage.getItem('onboarding-completed');
      if (!hasSeenOnboarding) {
        setShowOnboarding(true);
      }
    }
    // Intentionally re-runs only when the session changes; loadSessions reads
    // session at call time and need not retrigger the effect.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session]);

  const loadSessions = async () => {
    try {
      const response = await fetch(`${API_BASE}/chat/sessions`, { cache: 'no-store' });

      if (response.ok) {
        const data = await response.json();
        setSessions(data);
        // Load first session if available
        if (data.length > 0 && !currentSessionId) {
          loadSession(data[0].id);
        }
      }
    } catch (err) {
      console.error('Failed to load sessions:', err);
    }
  };

  const loadSession = async (sessionId: string) => {
    try {
      const response = await fetch(`${API_BASE}/chat/sessions/${sessionId}`, { cache: 'no-store' });

      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages || []);
        setCurrentSessionId(sessionId);
      }
    } catch (err) {
      console.error('Failed to load session:', err);
    }
  };

  const createNewSession = async () => {
    try {
      const response = await fetch(`${API_BASE}/chat/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: `Chat - ${new Date().toLocaleDateString()}`,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setSessions([data, ...sessions]);
        loadSession(data.id);
        setMessages([]);
      }
    } catch (err) {
      console.error('Failed to create session:', err);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.currentTarget.files;
    if (!files || !currentSessionId) return;

    setUploadingFile(true);
    try {
      for (const file of Array.from(files)) {
        const formData = new FormData();
        formData.append('file', file);

        // No explicit Content-Type: the browser sets the multipart boundary,
        // and the proxy forwards multipart bodies binary-safe.
        const response = await fetch(`${API_BASE}/chat/upload`, {
          method: 'POST',
          body: formData,
        });

        if (response.ok) {
          const fileData = await response.json();
          // Add file message
          const fileMsg: Message = {
            id: Math.random().toString(),
            role: 'user',
            content: `📎 Uploaded: ${file.name}`,
            timestamp: new Date(),
            attachments: [fileData],
          };
          setMessages([...messages, fileMsg]);
        }
      }
    } catch (err) {
      setError('Failed to upload file');
    } finally {
      setUploadingFile(false);
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim() || loading || !currentSessionId) return;

    setError(null);
    setLoading(true);

    const userMessage = input;

    // Add the user message and an empty assistant message we'll stream into.
    const assistantId = Math.random().toString();
    setMessages((prev) => [
      ...prev,
      { id: Math.random().toString(), role: 'user', content: userMessage, timestamp: new Date() },
      { id: assistantId, role: 'assistant', content: '', timestamp: new Date() },
    ]);
    setInput('');

    const appendToAssistant = (chunk: string) => {
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantId ? { ...m, content: m.content + chunk } : m))
      );
    };

    try {
      const response = await fetch(
        `${API_BASE}/chat/${currentSessionId}/message/stream`,
        {
          method: 'POST',
          headers: {
            Accept: 'text/event-stream',
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ message: userMessage }),
        }
      );

      if (!response.ok || !response.body) {
        throw new Error('Failed to send message');
      }

      // Parse the SSE stream: frames are separated by a blank line, each with
      // `event:` and `data:` lines.
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      const handleFrame = (frame: string) => {
        const lines = frame.split('\n');
        let eventType = 'message';
        const dataLines: string[] = [];
        for (const line of lines) {
          if (line.startsWith('event:')) eventType = line.slice(6).trim();
          // Per the SSE spec, strip a single optional leading space after the
          // colon and join multiple data lines with a newline (don't trim the
          // payload — token whitespace is significant).
          else if (line.startsWith('data:')) {
            dataLines.push(line.startsWith('data: ') ? line.slice(6) : line.slice(5));
          }
        }
        const dataStr = dataLines.join('\n');
        if (!dataStr) return;
        let data: Record<string, unknown> = {};
        try {
          data = JSON.parse(dataStr);
        } catch {
          return;
        }
        if (eventType === 'token') {
          appendToAssistant((data.text as string) || '');
        } else if (eventType === 'error') {
          appendToAssistant(`\n\n⚠️ ${(data.error as string) || 'stream error'}`);
        } else if (eventType === 'done') {
          const actions = (data.actions as Action[]) || [];
          const messageId = data.message_id as string;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, actions_taken: actions } : m
            )
          );
          const needConfirm = actions
            .filter((a) => a.requires_confirmation && a.status === 'pending')
            .map((a) => ({ ...a, message_id: messageId }));
          if (needConfirm.length > 0) {
            setPendingActions(needConfirm);
            setShowActionConfirmation(true);
          }
        }
      };

      // eslint-disable-next-line no-constant-condition
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        // Normalize CRLF so the frame delimiter and line parsing are consistent.
        buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n');
        let idx;
        while ((idx = buffer.indexOf('\n\n')) !== -1) {
          const frame = buffer.slice(0, idx);
          buffer = buffer.slice(idx + 2);
          if (frame.trim()) handleFrame(frame);
        }
      }
      // Flush any trailing frame not terminated by a blank line (e.g. a server
      // that closes right after the final `done` event).
      buffer += decoder.decode().replace(/\r\n/g, '\n');
      if (buffer.trim()) handleFrame(buffer);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      appendToAssistant('\n\n⚠️ Could not reach the assistant.');
    } finally {
      setLoading(false);
    }
  };

  const deleteSession = async (sessionId: string) => {
    try {
      await fetch(`${API_BASE}/chat/sessions/${sessionId}`, { method: 'DELETE' });

      setSessions(sessions.filter((s) => s.id !== sessionId));
      if (currentSessionId === sessionId) {
        if (sessions.length > 1) {
          const nextSession = sessions.find((s) => s.id !== sessionId);
          if (nextSession) loadSession(nextSession.id);
        } else {
          setMessages([]);
          setCurrentSessionId(null);
        }
      }
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  };

  const handleActionConfirm = async (actionIds: string[]) => {
    const results: { id: string; status: string }[] = [];
    for (const actionId of actionIds) {
      const action = pendingActions.find((a) => a.id === actionId);
      if (!action?.message_id) continue;
      try {
        const res = await fetch(`${API_BASE}/chat/actions/confirm`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message_id: action.message_id,
            action_id: actionId,
            confirmed: true,
          }),
        });
        const data = await res.json();
        results.push({ id: actionId, status: data.status });
      } catch {
        results.push({ id: actionId, status: 'failed' });
      }
    }
    setShowActionConfirmation(false);
    setPendingActions([]);
    const ok = results.filter((r) => r.status === 'executed').length;
    const failed = results.filter((r) => r.status === 'failed').length;
    const summary =
      `Executed ${ok} action${ok === 1 ? '' : 's'}` +
      (failed ? `, ${failed} failed` : '') + '.';
    setMessages((prev) => [
      ...prev,
      {
        id: Math.random().toString(),
        role: 'assistant',
        content: summary,
        timestamp: new Date(),
      },
    ]);
  };

  const handleActionReject = async (actionIds: string[]) => {
    for (const actionId of actionIds) {
      const action = pendingActions.find((a) => a.id === actionId);
      if (!action?.message_id) continue;
      try {
        await fetch(`${API_BASE}/chat/actions/confirm`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message_id: action.message_id,
            action_id: actionId,
            confirmed: false,
            notes: 'Rejected by user',
          }),
        });
      } catch {
        /* best-effort */
      }
    }
    setShowActionConfirmation(false);
    setPendingActions([]);
    setError('You rejected the proposed actions. The agent will suggest alternatives.');
  };

  const handleOnboardingComplete = () => {
    setShowOnboarding(false);
    localStorage.setItem('onboarding-completed', 'true');
  };

  // Open the sidebar by default on desktop only.
  useEffect(() => {
    setShowSidebar(window.innerWidth >= 1024);
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const userRole = (session?.user as { role?: string })?.role || 'candidate';

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <div
        className={`${
          showSidebar ? 'w-64' : 'w-0'
        } transition-all duration-300 border-r border-border bg-secondary/20 overflow-hidden flex flex-col absolute lg:relative inset-y-0 left-0 z-30 lg:z-auto`}
      >
        <div className="p-4 border-b border-border">
          <Button
            onClick={createNewSession}
            className="w-full justify-start gap-2"
            size="sm"
          >
            <Plus className="h-4 w-4" />
            New Chat
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {sessions.map((sess) => (
            <div
              key={sess.id}
              className={`p-3 rounded-lg mb-2 cursor-pointer transition-colors ${
                currentSessionId === sess.id
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-background hover:bg-secondary'
              }`}
              onClick={() => {
                loadSession(sess.id);
                if (window.innerWidth < 1024) setShowSidebar(false);
              }}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{sess.title}</p>
                  <p className="text-xs opacity-70">
                    {sess.message_count} messages
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteSession(sess.id);
                  }}
                  className="opacity-0 hover:opacity-100 transition-opacity"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="p-4 border-t border-border text-xs text-muted-foreground">
          <p>Role: <strong className="capitalize">{userRole}</strong></p>
          <p className="mt-1">
            {userRole === 'recruiter' && 'Hiring Assistant'}
            {userRole === 'candidate' && 'Career Coach'}
            {userRole === 'admin' && 'System Admin'}
          </p>
        </div>
      </div>

      {/* Backdrop: dismiss the drawer when tapping the chat on mobile. */}
      {showSidebar && (
        <div
          className="lg:hidden fixed inset-0 z-20 bg-black/30"
          onClick={() => setShowSidebar(false)}
          aria-hidden="true"
        />
      )}

      {/* Main Chat */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="border-b border-border bg-secondary/30 p-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowSidebar(!showSidebar)}
              className="lg:hidden p-2 hover:bg-secondary rounded"
            >
              ☰
            </button>
            <div>
              <h1 className="text-lg font-semibold">
                {userRole === 'recruiter' && '🎯 Recruiter Assistant'}
                {userRole === 'candidate' && '💼 Career Coach'}
                {userRole === 'admin' && '⚙️ System Admin'}
              </h1>
              <p className="text-sm text-muted-foreground">
                Ask anything about your hiring, career, or platform
              </p>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <p className="text-lg font-semibold mb-2">
                  {userRole === 'recruiter' &&
                    "Hi! 👋 I'm your Recruiter Assistant"}
                  {userRole === 'candidate' &&
                    "Hi! 👋 I'm your Career Coach"}
                  {userRole === 'admin' && "Hi! 👋 I'm your System Admin"}
                </p>
                <p className="text-sm text-muted-foreground mb-4">
                  {userRole === 'recruiter' &&
                    "Tell me about the role you're hiring for, upload candidates, or ask about your pipeline."}
                  {userRole === 'candidate' &&
                    "Share your CV, tell me your career goals, or ask for job recommendations."}
                  {userRole === 'admin' &&
                    "Ask about system health, governance reviews, or platform configuration."}
                </p>
                <div className="space-y-2 text-sm">
                  {userRole === 'recruiter' && (
                    <>
                      <p>💡 Try: "I need to hire 3 senior engineers"</p>
                      <p>💡 Try: "Upload these 50 resumes and rank them"</p>
                      <p>💡 Try: "Show me my pipeline status"</p>
                    </>
                  )}
                  {userRole === 'candidate' && (
                    <>
                      <p>💡 Try: "Analyze my CV for a senior role"</p>
                      <p>💡 Try: "What jobs match my profile?"</p>
                      <p>💡 Try: "Help me improve my CV"</p>
                    </>
                  )}
                  {userRole === 'admin' && (
                    <>
                      <p>💡 Try: "How's the system doing?"</p>
                      <p>💡 Try: "Show me pending reviews"</p>
                      <p>💡 Try: "What are my metrics?"</p>
                    </>
                  )}
                </div>
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-2xl rounded-lg p-4 ${
                  msg.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-secondary text-secondary-foreground'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>

                {/* Actions Taken */}
                {msg.actions_taken && msg.actions_taken.length > 0 && (
                  <div className="mt-3 space-y-2 text-xs border-t border-current opacity-75 pt-2">
                    {msg.actions_taken.map((action) => (
                      <div key={action.id} className="flex items-center gap-2">
                        {action.status === 'completed' && (
                          <span className="text-green-400">✓</span>
                        )}
                        {action.status === 'pending' && (
                          <Loader2 className="h-3 w-3 animate-spin" />
                        )}
                        {action.status === 'failed' && (
                          <span className="text-red-400">✗</span>
                        )}
                        <span>{action.description}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-secondary text-secondary-foreground rounded-lg p-4 max-w-md">
                <div className="flex items-center gap-2 mb-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm font-medium">
                    {progressStage ? progressStage.replace(/_/g, ' ') : 'Processing...'}
                  </span>
                </div>
                {progress > 0 && (
                  <div className="w-full bg-background/50 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-primary h-full transition-all"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                )}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Error */}
        {error && (
          <div className="mx-4 mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {/* Input Area */}
        <div className="border-t border-border bg-secondary/20 p-4">
          <div className="flex gap-2 mb-2">
            <label className="flex items-center gap-2 cursor-pointer text-sm">
              <Upload className="h-4 w-4" />
              <input
                type="file"
                multiple
                onChange={handleFileUpload}
                disabled={uploadingFile}
                className="hidden"
              />
              <span>{uploadingFile ? 'Uploading...' : 'Upload'}</span>
            </label>
          </div>

          <div className="flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              placeholder="Message your AI assistant... (Shift+Enter for newline)"
              disabled={loading || !currentSessionId}
              className="flex-1 px-4 py-2 rounded-lg border border-input bg-background focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
            />
            <Button
              onClick={handleSendMessage}
              disabled={loading || !input.trim() || !currentSessionId}
              size="sm"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Action Confirmation Dialog */}
      {showActionConfirmation && pendingActions.length > 0 && (
        <ActionConfirmation
          actions={pendingActions.map((a) => ({
            id: a.id,
            description: a.description,
            type: (a.type as 'schedule' | 'approve' | 'send' | 'modify') || 'modify',
            requiresConfirmation: a.requires_confirmation ?? true,
          }))}
          onConfirm={handleActionConfirm}
          onReject={handleActionReject}
        />
      )}

      {/* Onboarding Flow */}
      {showOnboarding && (
        <OnboardingFlow
          userRole={userRole as 'admin' | 'recruiter' | 'candidate'}
          onComplete={handleOnboardingComplete}
        />
      )}
    </div>
  );
}
