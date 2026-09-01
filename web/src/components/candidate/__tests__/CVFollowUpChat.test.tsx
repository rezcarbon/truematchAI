import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CVFollowUpChat } from '../CVFollowUpChat';

// Mock the fetch API
global.fetch = jest.fn();

describe('CVFollowUpChat', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders chat component with title', () => {
    render(<CVFollowUpChat analysisId="123" />);
    expect(screen.getByText('Ask Claude about your CV')).toBeInTheDocument();
    expect(screen.getByText('Get personalized advice on your analysis')).toBeInTheDocument();
  });

  it('displays suggested prompts initially', () => {
    render(<CVFollowUpChat analysisId="123" />);
    expect(screen.getByText('What skills should I prioritize learning first?')).toBeInTheDocument();
    expect(screen.getByText('How can I transition to this role?')).toBeInTheDocument();
  });

  it('renders custom suggested prompts', () => {
    const customPrompts = ['Custom prompt 1', 'Custom prompt 2'];
    render(<CVFollowUpChat analysisId="123" suggestedPrompts={customPrompts} />);
    expect(screen.getByText('Custom prompt 1')).toBeInTheDocument();
    expect(screen.getByText('Custom prompt 2')).toBeInTheDocument();
  });

  it('sends message when clicking suggested prompt', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ response: 'Claude response' }),
    });

    render(<CVFollowUpChat analysisId="123" />);
    const prompt = screen.getByText('What skills should I prioritize learning first?');
    fireEvent.click(prompt);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/chat', expect.any(Object));
    });
  });

  it('sends message from input field', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ response: 'Assistant response' }),
    });

    const user = userEvent.setup();
    render(<CVFollowUpChat analysisId="123" />);

    const input = screen.getByPlaceholderText('Ask a question...');
    await user.type(input, 'What should I focus on?');

    const sendButton = screen.getByRole('button', { name: /Send message/i });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/chat',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        })
      );
    });
  });

  it('displays user message in chat', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ response: 'AI response' }),
    });

    const user = userEvent.setup();
    render(<CVFollowUpChat analysisId="123" />);

    const input = screen.getByPlaceholderText('Ask a question...');
    await user.type(input, 'Test message');

    const sendButton = screen.getByRole('button', { name: /Send message/i });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText('Test message')).toBeInTheDocument();
    });
  });

  it('displays assistant response in chat', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ response: 'This is the AI response' }),
    });

    const user = userEvent.setup();
    render(<CVFollowUpChat analysisId="123" />);

    const input = screen.getByPlaceholderText('Ask a question...');
    await user.type(input, 'Ask something');

    const sendButton = screen.getByRole('button', { name: /Send message/i });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText('This is the AI response')).toBeInTheDocument();
    });
  });

  it('clears input after sending message', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ response: 'Response' }),
    });

    const user = userEvent.setup();
    render(<CVFollowUpChat analysisId="123" />);

    const input = screen.getByPlaceholderText('Ask a question...') as HTMLInputElement;
    await user.type(input, 'Message');

    const sendButton = screen.getByRole('button', { name: /Send message/i });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(input.value).toBe('');
    });
  });

  it('disables send button when input is empty', () => {
    render(<CVFollowUpChat analysisId="123" />);
    const sendButton = screen.getByRole('button', { name: /Send message/i });
    expect(sendButton).toBeDisabled();
  });

  it('enables send button when input has text', async () => {
    const user = userEvent.setup();
    render(<CVFollowUpChat analysisId="123" />);

    const input = screen.getByPlaceholderText('Ask a question...');
    await user.type(input, 'Test');

    const sendButton = screen.getByRole('button', { name: /Send message/i });
    expect(sendButton).not.toBeDisabled();
  });

  it('shows loading state while sending message', async () => {
    (global.fetch as jest.Mock).mockImplementationOnce(
      () => new Promise((resolve) => setTimeout(() => resolve({
        ok: true,
        json: async () => ({ response: 'Response' }),
      }), 100))
    );

    const user = userEvent.setup();
    render(<CVFollowUpChat analysisId="123" />);

    const input = screen.getByPlaceholderText('Ask a question...');
    await user.type(input, 'Message');

    const sendButton = screen.getByRole('button', { name: /Send message/i });
    fireEvent.click(sendButton);

    expect(screen.getByText('Thinking...')).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
    });

    const user = userEvent.setup();
    render(<CVFollowUpChat analysisId="123" />);

    const input = screen.getByPlaceholderText('Ask a question...');
    await user.type(input, 'Message');

    const sendButton = screen.getByRole('button', { name: /Send message/i });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText(/Failed to get response from Claude/)).toBeInTheDocument();
    });
  });

  it('sends Enter key to submit message', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ response: 'Response' }),
    });

    const user = userEvent.setup();
    render(<CVFollowUpChat analysisId="123" />);

    const input = screen.getByPlaceholderText('Ask a question...');
    await user.type(input, 'Message{Enter}');

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled();
    });
  });

  it('does not submit when Shift+Enter is pressed', async () => {
    (global.fetch as jest.Mock).mockClear();
    const user = userEvent.setup();
    render(<CVFollowUpChat analysisId="123" />);

    const input = screen.getByPlaceholderText('Ask a question...');
    await user.type(input, 'Message');
    await user.keyboard('{Shift>}{Enter}{/Shift}');

    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('has correct accessibility attributes', () => {
    render(<CVFollowUpChat analysisId="123" />);
    expect(screen.getByLabelText('Chat message input')).toBeInTheDocument();
    expect(screen.getByLabelText('Send message')).toBeInTheDocument();
  });
});
