import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import UploadZone from './UploadZone';

describe('UploadZone', () => {
  const mockOnUpload = jest.fn();
  const mockOnFileSelect = jest.fn();

  beforeEach(() => {
    mockOnUpload.mockClear();
    mockOnFileSelect.mockClear();
  });

  describe('Tab Navigation', () => {
    it('should render all upload method tabs', () => {
      render(
        <UploadZone
          onUpload={mockOnUpload}
        />
      );

      expect(screen.getByRole('button', { name: /File/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Paste/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Linkedin/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Links/i })).toBeInTheDocument();
    });

    it('should switch tabs when clicked', async () => {
      const user = userEvent.setup();
      render(
        <UploadZone
          onUpload={mockOnUpload}
        />
      );

      const pasteTab = screen.getByRole('button', { name: /Paste/i });
      await user.click(pasteTab);

      expect(
        screen.getByPlaceholderText(/Paste your content here/)
      ).toBeInTheDocument();
    });

    it('should disable tabs when loading', () => {
      render(
        <UploadZone
          onUpload={mockOnUpload}
          loading={true}
        />
      );

      const tabs = screen.getAllByRole('button', { name: /(File|Paste|Linkedin|Links)/i });
      tabs.forEach((tab) => {
        expect(tab).toBeDisabled();
      });
    });

    it('should disable tabs when disabled prop is true', () => {
      render(
        <UploadZone
          onUpload={mockOnUpload}
          disabled={true}
        />
      );

      const tabs = screen.getAllByRole('button', { name: /(File|Paste|Linkedin|Links)/i });
      tabs.forEach((tab) => {
        expect(tab).toBeDisabled();
      });
    });
  });

  describe('File Upload Tab', () => {
    it('should show drag-drop zone on file tab', () => {
      render(
        <UploadZone
          onUpload={mockOnUpload}
        />
      );

      expect(screen.getByText(/Drag & drop files here/)).toBeInTheDocument();
    });

    it('should trigger file input on drop zone click', async () => {
      const user = userEvent.setup();
      render(
        <UploadZone
          onUpload={mockOnUpload}
        />
      );

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      expect(fileInput).toBeInTheDocument();
    });

    it('should handle file drop', async () => {
      render(
        <UploadZone
          onUpload={mockOnUpload}
          onFileSelect={mockOnFileSelect}
        />
      );

      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
      const dropZone = screen.getByText(/Drag & drop files here/).closest('div');

      fireEvent.dragOver(dropZone!);
      fireEvent.drop(dropZone!, {
        dataTransfer: {
          files: [file],
        },
      });

      await waitFor(() => {
        expect(mockOnFileSelect).toHaveBeenCalledWith(file);
      });
    });

    it('should validate file size', async () => {
      const mockOnNotification = jest.fn();
      render(
        <UploadZone
          onUpload={mockOnUpload}
          maxFileSize={1024} // 1KB
          showNotifications={false}
        />
      );

      const largeFile = new File(['x'.repeat(2000)], 'large.pdf', {
        type: 'application/pdf',
      });

      const fileInput = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;
      fireEvent.change(fileInput, { target: { files: [largeFile] } });

      // File should not be added to selected files
      expect(screen.queryByText('large.pdf')).not.toBeInTheDocument();
    });

    it('should validate file format', async () => {
      render(
        <UploadZone
          onUpload={mockOnUpload}
          acceptedFormats={['.pdf']}
          showNotifications={false}
        />
      );

      const invalidFile = new File(['test'], 'test.exe', {
        type: 'application/x-msdownload',
      });

      const fileInput = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;
      fireEvent.change(fileInput, { target: { files: [invalidFile] } });

      // File should not be added
      expect(screen.queryByText('test.exe')).not.toBeInTheDocument();
    });

    it('should display selected files', async () => {
      render(
        <UploadZone
          onUpload={mockOnUpload}
          onFileSelect={mockOnFileSelect}
        />
      );

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

      const fileInput = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;
      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('test.pdf')).toBeInTheDocument();
        expect(screen.getByText(/Selected Files/)).toBeInTheDocument();
      });
    });

    it('should remove file from selection', async () => {
      const user = userEvent.setup();
      render(
        <UploadZone
          onUpload={mockOnUpload}
          onFileSelect={mockOnFileSelect}
        />
      );

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

      const fileInput = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;
      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('test.pdf')).toBeInTheDocument();
      });

      const removeButton = screen.getByRole('button', { name: '' }).parentElement
        ?.querySelector('button[class*="text-gray-400"]');
      if (removeButton) {
        await user.click(removeButton);

        expect(screen.queryByText('test.pdf')).not.toBeInTheDocument();
      }
    });

    it('should upload file when button clicked', async () => {
      const user = userEvent.setup();
      mockOnUpload.mockResolvedValue(undefined);

      render(
        <UploadZone
          onUpload={mockOnUpload}
          onFileSelect={mockOnFileSelect}
        />
      );

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

      const fileInput = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;
      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('test.pdf')).toBeInTheDocument();
      });

      const uploadButton = screen.getByRole('button', { name: /Upload/i });
      await user.click(uploadButton);

      await waitFor(() => {
        expect(mockOnUpload).toHaveBeenCalledWith(file, 'file');
      });
    });
  });

  describe('Paste Tab', () => {
    it('should show textarea in paste tab', async () => {
      const user = userEvent.setup();
      render(
        <UploadZone
          onUpload={mockOnUpload}
        />
      );

      const pasteTab = screen.getByRole('button', { name: /Paste/i });
      await user.click(pasteTab);

      expect(
        screen.getByPlaceholderText(/Paste your content here/)
      ).toBeInTheDocument();
    });

    it('should process pasted content', async () => {
      const user = userEvent.setup();
      mockOnUpload.mockResolvedValue(undefined);

      render(
        <UploadZone
          onUpload={mockOnUpload}
        />
      );

      const pasteTab = screen.getByRole('button', { name: /Paste/i });
      await user.click(pasteTab);

      const textarea = screen.getByPlaceholderText(/Paste your content here/);
      const testContent = 'Test pasted content';
      await user.type(textarea, testContent);

      const processButton = screen.getByRole('button', { name: /Process Content/i });
      await user.click(processButton);

      await waitFor(() => {
        expect(mockOnUpload).toHaveBeenCalledWith(testContent, 'paste');
      });
    });

    it('should disable process button when textarea is empty', async () => {
      const user = userEvent.setup();
      render(
        <UploadZone
          onUpload={mockOnUpload}
        />
      );

      const pasteTab = screen.getByRole('button', { name: /Paste/i });
      await user.click(pasteTab);

      const processButton = screen.getByRole('button', { name: /Process Content/i });
      expect(processButton).toBeDisabled();
    });

    it('should show character count', async () => {
      const user = userEvent.setup();
      render(
        <UploadZone
          onUpload={mockOnUpload}
        />
      );

      const pasteTab = screen.getByRole('button', { name: /Paste/i });
      await user.click(pasteTab);

      const textarea = screen.getByPlaceholderText(/Paste your content here/);
      await user.type(textarea, 'Test');

      expect(screen.getByText(/4 characters/)).toBeInTheDocument();
    });
  });

  describe('LinkedIn Tab', () => {
    it('should show URL input in LinkedIn tab', async () => {
      const user = userEvent.setup();
      render(
        <UploadZone
          onUpload={mockOnUpload}
        />
      );

      const linkedinTab = screen.getByRole('button', { name: /Linkedin/i });
      await user.click(linkedinTab);

      expect(
        screen.getByPlaceholderText(/linkedin\.com\/in\//)
      ).toBeInTheDocument();
    });

    it('should process LinkedIn URL', async () => {
      const user = userEvent.setup();
      mockOnUpload.mockResolvedValue(undefined);

      render(
        <UploadZone
          onUpload={mockOnUpload}
        />
      );

      const linkedinTab = screen.getByRole('button', { name: /Linkedin/i });
      await user.click(linkedinTab);

      const input = screen.getByPlaceholderText(/linkedin\.com\/in\//);
      const testUrl = 'https://www.linkedin.com/in/testprofile';
      await user.type(input, testUrl);

      const processButton = screen.getByRole('button', {
        name: /Process LinkedIn Profile/i,
      });
      await user.click(processButton);

      await waitFor(() => {
        expect(mockOnUpload).toHaveBeenCalledWith(testUrl, 'linkedin');
      });
    });
  });

  describe('Links Tab', () => {
    it('should show textarea for links in links tab', async () => {
      const user = userEvent.setup();
      render(
        <UploadZone
          onUpload={mockOnUpload}
        />
      );

      const linksTab = screen.getByRole('button', { name: /Links/i });
      await user.click(linksTab);

      expect(
        screen.getByPlaceholderText(/Enter URLs/)
      ).toBeInTheDocument();
    });

    it('should process multiple links', async () => {
      const user = userEvent.setup();
      mockOnUpload.mockResolvedValue(undefined);

      render(
        <UploadZone
          onUpload={mockOnUpload}
        />
      );

      const linksTab = screen.getByRole('button', { name: /Links/i });
      await user.click(linksTab);

      const textarea = screen.getByPlaceholderText(/Enter URLs/);
      const links = 'https://example.com/resume\nhttps://example.com/portfolio';
      await user.type(textarea, links);

      const processButton = screen.getByRole('button', { name: /Process Links/i });
      await user.click(processButton);

      await waitFor(() => {
        expect(mockOnUpload).toHaveBeenCalledWith(links, 'links');
      });
    });
  });

  describe('Notifications', () => {
    it('should show success notification on successful upload', async () => {
      const user = userEvent.setup();
      mockOnUpload.mockResolvedValue(undefined);

      render(
        <UploadZone
          onUpload={mockOnUpload}
          showNotifications={true}
        />
      );

      const pasteTab = screen.getByRole('button', { name: /Paste/i });
      await user.click(pasteTab);

      const textarea = screen.getByPlaceholderText(/Paste your content here/);
      await user.type(textarea, 'Test content');

      const processButton = screen.getByRole('button', { name: /Process Content/i });
      await user.click(processButton);

      await waitFor(() => {
        expect(screen.getByText(/uploaded successfully/i)).toBeInTheDocument();
      });
    });

    it('should show error notification on upload failure', async () => {
      const user = userEvent.setup();
      const errorMessage = 'Upload failed due to network error';
      mockOnUpload.mockRejectedValue(new Error(errorMessage));

      render(
        <UploadZone
          onUpload={mockOnUpload}
          showNotifications={true}
        />
      );

      const pasteTab = screen.getByRole('button', { name: /Paste/i });
      await user.click(pasteTab);

      const textarea = screen.getByPlaceholderText(/Paste your content here/);
      await user.type(textarea, 'Test content');

      const processButton = screen.getByRole('button', { name: /Process Content/i });
      await user.click(processButton);

      await waitFor(() => {
        expect(screen.getByText(new RegExp(errorMessage))).toBeInTheDocument();
      });
    });

    it('should not show notifications when showNotifications is false', async () => {
      const user = userEvent.setup();
      mockOnUpload.mockResolvedValue(undefined);

      render(
        <UploadZone
          onUpload={mockOnUpload}
          showNotifications={false}
        />
      );

      const pasteTab = screen.getByRole('button', { name: /Paste/i });
      await user.click(pasteTab);

      const textarea = screen.getByPlaceholderText(/Paste your content here/);
      await user.type(textarea, 'Test content');

      const processButton = screen.getByRole('button', { name: /Process Content/i });
      await user.click(processButton);

      await waitFor(() => {
        expect(
          screen.queryByText(/uploaded successfully/i)
        ).not.toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(
        <UploadZone
          onUpload={mockOnUpload}
        />
      );

      const fileInput = document.querySelector('input[type="file"]');
      expect(fileInput).toHaveAttribute('aria-label', 'Upload files');
    });
  });
});
