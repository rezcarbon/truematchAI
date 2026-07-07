import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MultiMethodUpload } from '@/components/resume/MultiMethodUpload';

describe('MultiMethodUpload', () => {
  const mockOnUpload = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders with all upload method tabs', () => {
    render(<MultiMethodUpload onUpload={mockOnUpload} />);

    expect(screen.getByRole('button', { name: /Upload/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Paste/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /LinkedIn/i })).toBeInTheDocument();
  });

  it('displays drag-drop zone on default tab', () => {
    render(<MultiMethodUpload onUpload={mockOnUpload} />);

    expect(screen.getByText(/Drag & drop your resume/i)).toBeInTheDocument();
    expect(screen.getByText(/or click to browse/i)).toBeInTheDocument();
  });

  it('switches to paste tab when clicked', async () => {
    const user = userEvent.setup();
    render(<MultiMethodUpload onUpload={mockOnUpload} />);

    const pasteTab = screen.getByRole('button', { name: /Paste/i });
    await user.click(pasteTab);

    expect(screen.getByPlaceholderText(/Paste your resume content/i)).toBeInTheDocument();
  });

  it('switches to LinkedIn tab when clicked', async () => {
    const user = userEvent.setup();
    render(<MultiMethodUpload onUpload={mockOnUpload} />);

    const linkedInTab = screen.getByRole('button', { name: /LinkedIn/i });
    await user.click(linkedInTab);

    expect(screen.getByPlaceholderText(/LinkedIn profile URL/i)).toBeInTheDocument();
  });

  it('handles file selection', async () => {
    const user = userEvent.setup();
    const file = new File(['test'], 'resume.pdf', { type: 'application/pdf' });

    render(<MultiMethodUpload onUpload={mockOnUpload} />);

    const input = screen.getByDisplayValue('');
    await user.upload(input, file);

    // File should be displayed
    await waitFor(() => {
      expect(screen.getByText('resume.pdf')).toBeInTheDocument();
    });
  });

  it('displays file size when file is selected', async () => {
    const user = userEvent.setup();
    const blob = new Blob(['x'.repeat(2048)], { type: 'application/pdf' });
    const file = new File([blob], 'resume.pdf', { type: 'application/pdf' });

    render(<MultiMethodUpload onUpload={mockOnUpload} />);

    const input = screen.getByDisplayValue('');
    await user.upload(input, file);

    await waitFor(() => {
      expect(screen.getByText(/2.0 KB/)).toBeInTheDocument();
    });
  });

  it('calls onUpload with file when upload button is clicked', async () => {
    const user = userEvent.setup();
    mockOnUpload.mockResolvedValue(undefined);

    const file = new File(['test'], 'resume.pdf', { type: 'application/pdf' });

    render(<MultiMethodUpload onUpload={mockOnUpload} />);

    const input = screen.getByDisplayValue('');
    await user.upload(input, file);

    const uploadButton = screen.getByRole('button', { name: /Upload resume/i });
    await user.click(uploadButton);

    await waitFor(() => {
      expect(mockOnUpload).toHaveBeenCalledWith(file, 'drag-drop');
    });
  });

  it('calls onUpload with pasted content', async () => {
    const user = userEvent.setup();
    mockOnUpload.mockResolvedValue(undefined);

    render(<MultiMethodUpload onUpload={mockOnUpload} />);

    const pasteTab = screen.getByRole('button', { name: /Paste/i });
    await user.click(pasteTab);

    const textarea = screen.getByPlaceholderText(/Paste your resume content/i);
    await user.type(textarea, 'John Doe - Senior Engineer');

    const uploadButton = screen.getByRole('button', { name: /Process Resume/i });
    await user.click(uploadButton);

    await waitFor(() => {
      expect(mockOnUpload).toHaveBeenCalledWith('John Doe - Senior Engineer', 'paste');
    });
  });

  it('calls onUpload with LinkedIn URL', async () => {
    const user = userEvent.setup();
    mockOnUpload.mockResolvedValue(undefined);

    render(<MultiMethodUpload onUpload={mockOnUpload} />);

    const linkedInTab = screen.getByRole('button', { name: /LinkedIn/i });
    await user.click(linkedInTab);

    const input = screen.getByPlaceholderText(/LinkedIn profile URL/i);
    await user.type(input, 'https://linkedin.com/in/johndoe');

    const uploadButton = screen.getByRole('button', { name: /Process Resume/i });
    await user.click(uploadButton);

    await waitFor(() => {
      expect(mockOnUpload).toHaveBeenCalledWith('https://linkedin.com/in/johndoe', 'linkedin');
    });
  });

  it('disables upload button when no content is selected', () => {
    render(<MultiMethodUpload onUpload={mockOnUpload} />);

    const uploadButton = screen.getByRole('button', { name: /Upload resume/i });
    expect(uploadButton).toBeDisabled();
  });

  it('disables all inputs when loading is true', () => {
    render(<MultiMethodUpload onUpload={mockOnUpload} loading={true} />);

    const tabs = screen.getAllByRole('button').filter(btn =>
      btn.textContent?.includes('Upload') ||
      btn.textContent?.includes('Paste') ||
      btn.textContent?.includes('LinkedIn')
    );

    tabs.forEach(tab => {
      expect(tab).toBeDisabled();
    });
  });

  it('disables all inputs when disabled prop is true', () => {
    render(<MultiMethodUpload onUpload={mockOnUpload} disabled={true} />);

    const uploadButton = screen.getByRole('button', { name: /Upload resume/i });
    expect(uploadButton).toBeDisabled();
  });

  it('removes selected file when remove button is clicked', async () => {
    const user = userEvent.setup();
    const file = new File(['test'], 'resume.pdf', { type: 'application/pdf' });

    render(<MultiMethodUpload onUpload={mockOnUpload} />);

    const input = screen.getByDisplayValue('');
    await user.upload(input, file);

    await waitFor(() => {
      expect(screen.getByText('resume.pdf')).toBeInTheDocument();
    });

    const removeButton = screen.getByRole('button', { name: '' });
    await user.click(removeButton);

    await waitFor(() => {
      expect(screen.queryByText('resume.pdf')).not.toBeInTheDocument();
    });
  });

  it('shows upload progress', async () => {
    const user = userEvent.setup();
    mockOnUpload.mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );

    const file = new File(['test'], 'resume.pdf', { type: 'application/pdf' });

    render(<MultiMethodUpload onUpload={mockOnUpload} />);

    const input = screen.getByDisplayValue('');
    await user.upload(input, file);

    const uploadButton = screen.getByRole('button', { name: /Upload resume/i });
    await user.click(uploadButton);

    await waitFor(() => {
      expect(screen.getByText(/Uploading/i)).toBeInTheDocument();
    });
  });

  it('handles drag and drop', async () => {
    const user = userEvent.setup();
    const file = new File(['test'], 'resume.pdf', { type: 'application/pdf' });

    render(<MultiMethodUpload onUpload={mockOnUpload} />);

    const dropZone = screen.getByText(/Drag & drop your resume/i).closest('div');

    if (dropZone) {
      const dataTransfer = {
        files: [file],
      };

      await user.pointer({ keys: '[MouseLeft>]', target: dropZone });
      const dragEvent = new DragEvent('dragover', { bubbles: true });
      Object.defineProperty(dragEvent, 'dataTransfer', { value: dataTransfer });
      dropZone.dispatchEvent(dragEvent);

      const dropEvent = new DragEvent('drop', { bubbles: true });
      Object.defineProperty(dropEvent, 'dataTransfer', { value: dataTransfer });
      dropZone.dispatchEvent(dropEvent);

      await waitFor(() => {
        expect(screen.getByText('resume.pdf')).toBeInTheDocument();
      });
    }
  });

  it('accepts custom file types', () => {
    render(
      <MultiMethodUpload
        onUpload={mockOnUpload}
        accept=".doc,.docx,.pdf,.txt"
      />
    );

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input.accept).toBe('.doc,.docx,.pdf,.txt');
  });

  it('validates minimum content length for paste', async () => {
    const user = userEvent.setup();
    mockOnUpload.mockResolvedValue(undefined);

    render(<MultiMethodUpload onUpload={mockOnUpload} />);

    const pasteTab = screen.getByRole('button', { name: /Paste/i });
    await user.click(pasteTab);

    const textarea = screen.getByPlaceholderText(/Paste your resume content/i);
    await user.type(textarea, 'a');

    const uploadButton = screen.getByRole('button', { name: /Process Resume/i });
    expect(uploadButton).toBeDisabled();
  });
});
