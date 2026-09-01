import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import InlineEditor from '@/components/JDOptimizer/InlineEditor';

describe('InlineEditor', () => {
  const mockProps = {
    value: 'Original job description text',
    onChange: jest.fn(),
    onSave: jest.fn(),
    onCancel: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders editor textarea', () => {
    render(<InlineEditor {...mockProps} />);
    expect(screen.getByPlaceholderText('Edit your job description here...')).toBeInTheDocument();
  });

  it('displays initial value in textarea', () => {
    render(<InlineEditor {...mockProps} />);
    const textarea = screen.getByPlaceholderText(
      'Edit your job description here...'
    ) as HTMLTextAreaElement;
    expect(textarea.value).toBe('Original job description text');
  });

  it('calls onChange when text is edited', async () => {
    render(<InlineEditor {...mockProps} />);
    const textarea = screen.getByPlaceholderText(
      'Edit your job description here...'
    );

    await userEvent.clear(textarea);
    await userEvent.type(textarea, 'Updated text');

    expect(mockProps.onChange).toHaveBeenCalledWith('Updated text');
  });

  it('displays word count', () => {
    render(<InlineEditor {...mockProps} />);
    expect(screen.getByText(/words/)).toBeInTheDocument();
  });

  it('displays character count', () => {
    render(<InlineEditor {...mockProps} />);
    expect(screen.getByText(/characters/)).toBeInTheDocument();
  });

  it('enables save button when changes made', async () => {
    const { rerender } = render(<InlineEditor {...mockProps} />);
    const saveButton = screen.getByText('Save Changes');

    expect(saveButton).toBeDisabled();

    // Simulate a change
    rerender(
      <InlineEditor
        {...mockProps}
        value="Modified text"
      />
    );

    await waitFor(() => {
      expect(saveButton).not.toBeDisabled();
    });
  });

  it('keeps save button disabled when no changes', () => {
    render(<InlineEditor {...mockProps} />);
    const saveButton = screen.getByText('Save Changes');
    expect(saveButton).toBeDisabled();
  });

  it('calls onSave when save button clicked', async () => {
    const onChangeMock = jest.fn();
    const { rerender } = render(
      <InlineEditor
        {...mockProps}
        onChange={onChangeMock}
      />
    );

    // Simulate change
    rerender(
      <InlineEditor
        {...mockProps}
        value="Modified text"
        onChange={onChangeMock}
      />
    );

    const saveButton = screen.getByText('Save Changes');
    await userEvent.click(saveButton);

    expect(mockProps.onSave).toHaveBeenCalled();
  });

  it('calls onCancel when cancel button clicked', async () => {
    render(<InlineEditor {...mockProps} />);
    const cancelButton = screen.getByText('Cancel');
    await userEvent.click(cancelButton);

    expect(mockProps.onCancel).toHaveBeenCalled();
  });

  it('reverts to original value on cancel', async () => {
    const onChangeMock = jest.fn();
    const { rerender } = render(
      <InlineEditor
        value="Original text"
        onChange={onChangeMock}
        onSave={jest.fn()}
        onCancel={jest.fn()}
      />
    );

    // Simulate change
    rerender(
      <InlineEditor
        value="Modified text"
        onChange={onChangeMock}
        onSave={jest.fn()}
        onCancel={jest.fn()}
      />
    );

    const cancelButton = screen.getByText('Cancel');
    await userEvent.click(cancelButton);

    expect(onChangeMock).toHaveBeenCalledWith('Original text');
  });

  it('shows unsaved changes indicator', async () => {
    const { rerender } = render(<InlineEditor {...mockProps} />);

    rerender(
      <InlineEditor
        {...mockProps}
        value="Modified text"
      />
    );

    await waitFor(() => {
      expect(screen.getByText('You have unsaved changes')).toBeInTheDocument();
    });
  });

  it('hides unsaved changes indicator when no changes', () => {
    render(<InlineEditor {...mockProps} />);
    expect(screen.queryByText('You have unsaved changes')).not.toBeInTheDocument();
  });

  it('renders label for textarea', () => {
    render(<InlineEditor {...mockProps} />);
    expect(screen.getByText('Edit Job Description')).toBeInTheDocument();
  });

  it('handles large text content', () => {
    const largeText = 'Test'.repeat(1000);
    render(
      <InlineEditor
        {...mockProps}
        value={largeText}
      />
    );

    const textarea = screen.getByPlaceholderText(
      'Edit your job description here...'
    ) as HTMLTextAreaElement;
    expect(textarea.value).toBe(largeText);
  });

  it('counts words correctly', () => {
    render(
      <InlineEditor
        {...mockProps}
        value="One two three four five"
      />
    );
    expect(screen.getByText(/5 words/)).toBeInTheDocument();
  });

  it('updates word and character count on change', async () => {
    const onChangeMock = jest.fn((value) => {});
    const { rerender } = render(
      <InlineEditor
        value="Original"
        onChange={onChangeMock}
        onSave={jest.fn()}
        onCancel={jest.fn()}
      />
    );

    rerender(
      <InlineEditor
        value="Original text added"
        onChange={onChangeMock}
        onSave={jest.fn()}
        onCancel={jest.fn()}
      />
    );

    expect(screen.getByText(/3 words/)).toBeInTheDocument();
  });

  it('renders all action buttons', () => {
    render(<InlineEditor {...mockProps} />);
    expect(screen.getByText('Cancel')).toBeInTheDocument();
    expect(screen.getByText('Save Changes')).toBeInTheDocument();
  });
});
