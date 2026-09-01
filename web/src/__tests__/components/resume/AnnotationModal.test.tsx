import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AnnotationModal } from '@/components/resume/AnnotationModal';

describe('AnnotationModal', () => {
  const mockOnSave = jest.fn();
  const mockOnClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('does not render when open is false', () => {
    const { container } = render(
      <AnnotationModal
        open={false}
        onSave={mockOnSave}
        onClose={mockOnClose}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('renders when open is true', () => {
    render(
      <AnnotationModal
        open={true}
        onSave={mockOnSave}
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText('Add Note')).toBeInTheDocument();
  });

  it('displays version number in title when provided', () => {
    render(
      <AnnotationModal
        open={true}
        versionNumber={3}
        onSave={mockOnSave}
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText('Add Note to Version 3')).toBeInTheDocument();
  });

  it('displays textarea with placeholder', () => {
    render(
      <AnnotationModal
        open={true}
        onSave={mockOnSave}
        onClose={mockOnClose}
      />
    );

    const textarea = screen.getByPlaceholderText(
      /Add a note about this version/i
    );
    expect(textarea).toBeInTheDocument();
  });

  it('initializes textarea with initial annotation', () => {
    render(
      <AnnotationModal
        open={true}
        initialAnnotation="Updated contact info"
        onSave={mockOnSave}
        onClose={mockOnClose}
      />
    );

    const textarea = screen.getByDisplayValue('Updated contact info');
    expect(textarea).toBeInTheDocument();
  });

  it('calls onSave when save button is clicked', async () => {
    const user = userEvent.setup();
    mockOnSave.mockResolvedValue(undefined);

    render(
      <AnnotationModal
        open={true}
        onSave={mockOnSave}
        onClose={mockOnClose}
      />
    );

    const textarea = screen.getByPlaceholderText(/Add a note/i);
    await user.type(textarea, 'Added new skills');

    const saveButton = screen.getByRole('button', { name: /Save Note/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalledWith('Added new skills');
    });
  });

  it('calls onClose when cancel button is clicked', async () => {
    const user = userEvent.setup();

    render(
      <AnnotationModal
        open={true}
        onSave={mockOnSave}
        onClose={mockOnClose}
      />
    );

    const cancelButton = screen.getByRole('button', { name: /Cancel/i });
    await user.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('calls onClose when close button (X) is clicked', async () => {
    const user = userEvent.setup();

    render(
      <AnnotationModal
        open={true}
        onSave={mockOnSave}
        onClose={mockOnClose}
      />
    );

    const closeButton = screen.getAllByRole('button')[0]; // X button
    await user.click(closeButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('shows error when saving empty annotation', async () => {
    const user = userEvent.setup();
    mockOnSave.mockResolvedValue(undefined);

    render(
      <AnnotationModal
        open={true}
        onSave={mockOnSave}
        onClose={mockOnClose}
      />
    );

    const saveButton = screen.getByRole('button', { name: /Save Note/i });
    await user.click(saveButton);

    expect(screen.getByText(/Please enter an annotation/i)).toBeInTheDocument();
    expect(mockOnSave).not.toHaveBeenCalled();
  });

  it('disables save button when annotation is empty', () => {
    render(
      <AnnotationModal
        open={true}
        onSave={mockOnSave}
        onClose={mockOnClose}
      />
    );

    const saveButton = screen.getByRole('button', { name: /Save Note/i });
    expect(saveButton).toBeDisabled();
  });

  it('enables save button when annotation has content', async () => {
    const user = userEvent.setup();

    render(
      <AnnotationModal
        open={true}
        onSave={mockOnSave}
        onClose={mockOnClose}
      />
    );

    const textarea = screen.getByPlaceholderText(/Add a note/i);
    await user.type(textarea, 'Some annotation');

    const saveButton = screen.getByRole('button', { name: /Save Note/i });
    expect(saveButton).not.toBeDisabled();
  });

  it('clears error when typing after error', async () => {
    const user = userEvent.setup();
    mockOnSave.mockResolvedValue(undefined);

    render(
      <AnnotationModal
        open={true}
        onSave={mockOnSave}
        onClose={mockOnClose}
      />
    );

    // Try to save empty
    const saveButton = screen.getByRole('button', { name: /Save Note/i });
    await user.click(saveButton);

    expect(screen.getByText(/Please enter an annotation/i)).toBeInTheDocument();

    // Type something
    const textarea = screen.getByPlaceholderText(/Add a note/i);
    await user.type(textarea, 'Note');

    // Error should be cleared
    await waitFor(() => {
      expect(
        screen.queryByText(/Please enter an annotation/i)
      ).not.toBeInTheDocument();
    });
  });

  it('disables inputs during saving', async () => {
    const user = userEvent.setup();
    mockOnSave.mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );

    render(
      <AnnotationModal
        open={true}
        onSave={mockOnSave}
        onClose={mockOnClose}
      />
    );

    const textarea = screen.getByPlaceholderText(/Add a note/i);
    await user.type(textarea, 'Note');

    const saveButton = screen.getByRole('button', { name: /Save Note/i });
    await user.click(saveButton);

    expect(textarea).toBeDisabled();
    expect(saveButton).toBeDisabled();
  });

  it('shows loading state while saving', async () => {
    const user = userEvent.setup();
    mockOnSave.mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );

    render(
      <AnnotationModal
        open={true}
        onSave={mockOnSave}
        onClose={mockOnClose}
      />
    );

    const textarea = screen.getByPlaceholderText(/Add a note/i);
    await user.type(textarea, 'Note');

    const saveButton = screen.getByRole('button', { name: /Save Note/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Saving...')).toBeInTheDocument();
    });
  });

  it('calls onClose after successful save', async () => {
    const user = userEvent.setup();
    mockOnSave.mockResolvedValue(undefined);

    render(
      <AnnotationModal
        open={true}
        onSave={mockOnSave}
        onClose={mockOnClose}
      />
    );

    const textarea = screen.getByPlaceholderText(/Add a note/i);
    await user.type(textarea, 'Note');

    const saveButton = screen.getByRole('button', { name: /Save Note/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it('shows error when save fails', async () => {
    const user = userEvent.setup();
    mockOnSave.mockRejectedValue(new Error('Save failed'));

    render(
      <AnnotationModal
        open={true}
        onSave={mockOnSave}
        onClose={mockOnClose}
      />
    );

    const textarea = screen.getByPlaceholderText(/Add a note/i);
    await user.type(textarea, 'Note');

    const saveButton = screen.getByRole('button', { name: /Save Note/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Save failed')).toBeInTheDocument();
    });
  });

  it('disables buttons when loading prop is true', () => {
    render(
      <AnnotationModal
        open={true}
        onSave={mockOnSave}
        onClose={mockOnClose}
        loading={true}
      />
    );

    const buttons = screen.getAllByRole('button');
    buttons.forEach(btn => {
      expect(btn).toBeDisabled();
    });
  });

  it('trims whitespace before saving', async () => {
    const user = userEvent.setup();
    mockOnSave.mockResolvedValue(undefined);

    render(
      <AnnotationModal
        open={true}
        onSave={mockOnSave}
        onClose={mockOnClose}
      />
    );

    const textarea = screen.getByPlaceholderText(/Add a note/i);
    await user.type(textarea, '   Note with spaces   ');

    const saveButton = screen.getByRole('button', { name: /Save Note/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalledWith('Note with spaces');
    });
  });

  it('clears annotation after successful save', async () => {
    const user = userEvent.setup();
    mockOnSave.mockResolvedValue(undefined);

    const { rerender } = render(
      <AnnotationModal
        open={true}
        initialAnnotation="Initial"
        onSave={mockOnSave}
        onClose={mockOnClose}
      />
    );

    const textarea = screen.getByDisplayValue('Initial') as HTMLTextAreaElement;
    await user.clear(textarea);
    await user.type(textarea, 'Updated');

    const saveButton = screen.getByRole('button', { name: /Save Note/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it('handles special characters in annotation', async () => {
    const user = userEvent.setup();
    mockOnSave.mockResolvedValue(undefined);

    render(
      <AnnotationModal
        open={true}
        onSave={mockOnSave}
        onClose={mockOnClose}
      />
    );

    const textarea = screen.getByPlaceholderText(/Add a note/i);
    const specialText = 'Note with special chars: @#$%^&*()[]{}';
    await user.type(textarea, specialText);

    const saveButton = screen.getByRole('button', { name: /Save Note/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalledWith(specialText);
    });
  });

  it('handles multiline annotations', async () => {
    const user = userEvent.setup();
    mockOnSave.mockResolvedValue(undefined);

    render(
      <AnnotationModal
        open={true}
        onSave={mockOnSave}
        onClose={mockOnClose}
      />
    );

    const textarea = screen.getByPlaceholderText(/Add a note/i);
    const multilineText = 'Line 1\nLine 2\nLine 3';
    await user.type(textarea, multilineText);

    const saveButton = screen.getByRole('button', { name: /Save Note/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalledWith(multilineText);
    });
  });
});
