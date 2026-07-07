import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { JDInlineEditor } from '@/components/recruiter/JDInlineEditor';

describe('JDInlineEditor', () => {
  const mockOnSave = jest.fn();
  const mockOnCancel = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders with initial text', () => {
    render(
      <JDInlineEditor
        initialText="Initial job description"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    const textarea = screen.getByDisplayValue('Initial job description');
    expect(textarea).toBeInTheDocument();
  });

  it('displays character count', () => {
    const text = 'Test text';
    render(
      <JDInlineEditor
        initialText={text}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        maxLength={100}
      />
    );

    expect(screen.getByText(`${text.length} / 100 characters`)).toBeInTheDocument();
  });

  it('updates character count when text changes', async () => {
    const user = userEvent.setup();
    render(
      <JDInlineEditor
        initialText="Initial"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        maxLength={100}
      />
    );

    const textarea = screen.getByDisplayValue('Initial');
    await user.clear(textarea);
    await user.type(textarea, 'New longer text');

    expect(screen.getByText('15 / 100 characters')).toBeInTheDocument();
  });

  it('calls onSave when save button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <JDInlineEditor
        initialText="Original"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    const textarea = screen.getByDisplayValue('Original');
    await user.clear(textarea);
    await user.type(textarea, 'Updated text');

    const saveButton = screen.getByRole('button', { name: /Save Changes/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalledWith('Updated text');
    });
  });

  it('calls onCancel when cancel button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <JDInlineEditor
        initialText="Original"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    const cancelButton = screen.getByRole('button', { name: /Cancel/i });
    await user.click(cancelButton);

    expect(mockOnCancel).toHaveBeenCalled();
  });

  it('resets text when cancel is clicked', async () => {
    const user = userEvent.setup();
    render(
      <JDInlineEditor
        initialText="Original"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    const textarea = screen.getByDisplayValue('Original');
    await user.clear(textarea);
    await user.type(textarea, 'Modified');

    const cancelButton = screen.getByRole('button', { name: /Cancel/i });
    await user.click(cancelButton);

    // Text should be reset to original
    expect(textarea).toHaveValue('Original');
  });

  it('shows error when text is too short', async () => {
    const user = userEvent.setup();
    render(
      <JDInlineEditor
        initialText="Hello"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        minLength={5}
      />
    );

    const textarea = screen.getByDisplayValue('Hello');
    await user.clear(textarea);
    await user.type(textarea, 'Hi');

    const saveButton = screen.getByRole('button', { name: /Save Changes/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(/at least 5 characters/i)).toBeInTheDocument();
    });
  });

  it('shows error when text exceeds max length', async () => {
    const user = userEvent.setup();
    render(
      <JDInlineEditor
        initialText="Short"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        maxLength={10}
      />
    );

    const textarea = screen.getByDisplayValue('Short');
    await user.clear(textarea);
    await user.type(textarea, 'This is way too long');

    const saveButton = screen.getByRole('button', { name: /Save Changes/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(/must not exceed 10 characters/i)).toBeInTheDocument();
    });
  });

  it('disables save button when text is unchanged', async () => {
    const user = userEvent.setup();
    render(
      <JDInlineEditor
        initialText="Original"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    const saveButton = screen.getByRole('button', { name: /Save Changes/i });
    expect(saveButton).toBeDisabled();
  });

  it('enables save button when text changes', async () => {
    const user = userEvent.setup();
    render(
      <JDInlineEditor
        initialText="Original"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    const textarea = screen.getByDisplayValue('Original');
    await user.clear(textarea);
    await user.type(textarea, 'Modified');

    const saveButton = screen.getByRole('button', { name: /Save Changes/i });
    expect(saveButton).not.toBeDisabled();
  });

  it('shows unsaved changes indicator', async () => {
    const user = userEvent.setup();
    render(
      <JDInlineEditor
        initialText="Original"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    const textarea = screen.getByDisplayValue('Original');
    await user.clear(textarea);
    await user.type(textarea, 'Modified');

    expect(screen.getByText('Unsaved changes')).toBeInTheDocument();
  });

  it('handles Escape key to cancel', async () => {
    const user = userEvent.setup();
    render(
      <JDInlineEditor
        initialText="Original"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    const textarea = screen.getByDisplayValue('Original');
    await user.clear(textarea);
    await user.type(textarea, 'Modified');
    await user.keyboard('{Escape}');

    expect(mockOnCancel).toHaveBeenCalled();
  });

  it('handles Ctrl+Enter to save', async () => {
    const user = userEvent.setup();
    render(
      <JDInlineEditor
        initialText="Original"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    const textarea = screen.getByDisplayValue('Original');
    await user.clear(textarea);
    await user.type(textarea, 'Modified');
    await user.keyboard('{Control>}{Enter}{/Control}');

    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalledWith('Modified');
    });
  });

  it('shows error message when save fails', async () => {
    const user = userEvent.setup();
    mockOnSave.mockRejectedValueOnce(new Error('Save failed'));

    render(
      <JDInlineEditor
        initialText="Original"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    const textarea = screen.getByDisplayValue('Original');
    await user.clear(textarea);
    await user.type(textarea, 'Modified');

    const saveButton = screen.getByRole('button', { name: /Save Changes/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Save failed')).toBeInTheDocument();
    });
  });

  it('disables inputs during saving', async () => {
    const user = userEvent.setup();
    mockOnSave.mockImplementationOnce(() => new Promise(resolve => setTimeout(resolve, 100)));

    render(
      <JDInlineEditor
        initialText="Original"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    const textarea = screen.getByDisplayValue('Original');
    await user.clear(textarea);
    await user.type(textarea, 'Modified');

    const saveButton = screen.getByRole('button', { name: /Save Changes/i });
    await user.click(saveButton);

    expect(textarea).toBeDisabled();
  });

  it('shows placeholder when provided', () => {
    render(
      <JDInlineEditor
        initialText=""
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        placeholder="Custom placeholder"
      />
    );

    const textarea = screen.getByPlaceholderText('Custom placeholder');
    expect(textarea).toBeInTheDocument();
  });

  it('auto-focuses textarea when autoFocus is true', () => {
    const { container } = render(
      <JDInlineEditor
        initialText="Test"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        autoFocus={true}
      />
    );

    const textarea = screen.getByDisplayValue('Test') as HTMLTextAreaElement;
    expect(document.activeElement).toBe(textarea);
  });

  it('shows character count progress bar', () => {
    const { container } = render(
      <JDInlineEditor
        initialText="Test"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        maxLength={100}
      />
    );

    // Progress bar should be visible
    const progressBar = container.querySelector('.h-1\\.5');
    expect(progressBar).toBeInTheDocument();
  });

  it('trims whitespace before saving', async () => {
    const user = userEvent.setup();
    render(
      <JDInlineEditor
        initialText="Original"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    const textarea = screen.getByDisplayValue('Original');
    await user.clear(textarea);
    await user.type(textarea, '  Modified text  ');

    const saveButton = screen.getByRole('button', { name: /Save Changes/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalledWith('Modified text');
    });
  });

  it('shows "no changes" error when text is identical to initial', async () => {
    const user = userEvent.setup();
    render(
      <JDInlineEditor
        initialText="Original"
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    // Save button should be disabled initially
    let saveButton = screen.getByRole('button', { name: /Save Changes/i });
    expect(saveButton).toBeDisabled();

    // Make a change
    const textarea = screen.getByDisplayValue('Original');
    await user.clear(textarea);
    await user.type(textarea, 'Modified');

    // Button should now be enabled
    saveButton = screen.getByRole('button', { name: /Save Changes/i });
    expect(saveButton).not.toBeDisabled();

    // Reset to original
    await user.clear(textarea);
    await user.type(textarea, 'Original');

    // Button should be disabled again
    saveButton = screen.getByRole('button', { name: /Save Changes/i });
    expect(saveButton).toBeDisabled();
  });
});
