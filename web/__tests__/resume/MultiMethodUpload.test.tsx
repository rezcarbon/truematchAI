import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MultiMethodUpload } from "@/components/resume/MultiMethodUpload";

// Mock the UI components
jest.mock("@/components/ui/card", () => ({
  Card: ({ children }: any) => <div data-testid="card">{children}</div>,
  CardContent: ({ children }: any) => <div data-testid="card-content">{children}</div>,
  CardHeader: ({ children }: any) => <div data-testid="card-header">{children}</div>,
  CardTitle: ({ children }: any) => <div data-testid="card-title">{children}</div>,
}));

jest.mock("@/components/ui/button", () => ({
  Button: ({ children, onClick, disabled, ...props }: any) => (
    <button onClick={onClick} disabled={disabled} {...props}>
      {children}
    </button>
  ),
}));

jest.mock("@/lib/utils", () => ({
  cn: (...args: any[]) => args.filter(Boolean).join(" "),
}));

describe("MultiMethodUpload", () => {
  let mockOnUpload: jest.Mock;

  beforeEach(() => {
    mockOnUpload = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe("Drag and Drop Upload", () => {
    it("should render drag-drop zone by default", () => {
      render(<MultiMethodUpload onUpload={mockOnUpload} />);
      expect(screen.getByText(/Drag & drop your resume/i)).toBeInTheDocument();
    });

    it("should handle file drop", async () => {
      mockOnUpload.mockResolvedValueOnce(undefined);
      render(<MultiMethodUpload onUpload={mockOnUpload} />);

      const dropZone = screen.getByText(/Drag & drop your resume/i).closest("div");
      if (!dropZone) throw new Error("Drop zone not found");

      const file = new File(["content"], "resume.pdf", { type: "application/pdf" });

      fireEvent.drop(dropZone, {
        dataTransfer: { files: [file] },
      });

      await waitFor(() => {
        expect(screen.getByText("resume.pdf")).toBeInTheDocument();
      });
    });

    it("should upload file on button click", async () => {
      mockOnUpload.mockResolvedValueOnce(undefined);
      const { container } = render(<MultiMethodUpload onUpload={mockOnUpload} />);

      const file = new File(["content"], "resume.pdf", { type: "application/pdf" });
      const input = container.querySelector('input[type="file"]') as HTMLInputElement;

      fireEvent.change(input, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText("resume.pdf")).toBeInTheDocument();
      });

      const uploadButton = screen.getByRole("button", {
        name: /Upload Resume/i,
      });

      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(mockOnUpload).toHaveBeenCalledWith(file, "drag-drop");
      });
    });

    it("should disable upload button when no file is selected", () => {
      render(<MultiMethodUpload onUpload={mockOnUpload} />);

      const uploadButton = screen.getByRole("button", {
        name: /Upload Resume/i,
      });

      expect(uploadButton).toBeDisabled();
    });

    it("should clear file selection on X button click", async () => {
      const { container } = render(<MultiMethodUpload onUpload={mockOnUpload} />);

      const file = new File(["content"], "resume.pdf", { type: "application/pdf" });
      const input = container.querySelector('input[type="file"]') as HTMLInputElement;

      fireEvent.change(input, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText("resume.pdf")).toBeInTheDocument();
      });

      const clearButton = screen.getByRole("button", { name: /Remove file/i });
      fireEvent.click(clearButton);

      await waitFor(() => {
        expect(screen.queryByText("resume.pdf")).not.toBeInTheDocument();
      });
    });
  });

  describe("Paste Upload", () => {
    it("should switch to paste tab", async () => {
      render(<MultiMethodUpload onUpload={mockOnUpload} />);

      const pasteTab = screen.getByRole("button", { name: /Paste/i });
      fireEvent.click(pasteTab);

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Paste your resume content/i)).toBeInTheDocument();
      });
    });

    it("should handle pasted content", async () => {
      mockOnUpload.mockResolvedValueOnce(undefined);
      render(<MultiMethodUpload onUpload={mockOnUpload} />);

      const pasteTab = screen.getByRole("button", { name: /Paste/i });
      fireEvent.click(pasteTab);

      const textarea = await screen.findByPlaceholderText(/Paste your resume content/i);
      const resumeContent = "John Doe\nSoftware Engineer\n5 years experience";

      fireEvent.change(textarea, { target: { value: resumeContent } });

      const processButton = screen.getByRole("button", {
        name: /Process Resume/i,
      });

      fireEvent.click(processButton);

      await waitFor(() => {
        expect(mockOnUpload).toHaveBeenCalledWith(resumeContent, "paste");
      });
    });

    it("should disable paste upload button when content is empty", async () => {
      render(<MultiMethodUpload onUpload={mockOnUpload} />);

      const pasteTab = screen.getByRole("button", { name: /Paste/i });
      fireEvent.click(pasteTab);

      const processButton = await screen.findByRole("button", {
        name: /Process Resume/i,
      });

      expect(processButton).toBeDisabled();
    });
  });

  describe("LinkedIn Upload", () => {
    it("should switch to linkedin tab", async () => {
      render(<MultiMethodUpload onUpload={mockOnUpload} />);

      const linkedInTab = screen.getByRole("button", { name: /LinkedIn/i });
      fireEvent.click(linkedInTab);

      await waitFor(() => {
        expect(
          screen.getByPlaceholderText(/https:\/\/www.linkedin.com\/in\/yourprofile/i)
        ).toBeInTheDocument();
      });
    });

    it("should handle linkedin url input", async () => {
      mockOnUpload.mockResolvedValueOnce(undefined);
      render(<MultiMethodUpload onUpload={mockOnUpload} />);

      const linkedInTab = screen.getByRole("button", { name: /LinkedIn/i });
      fireEvent.click(linkedInTab);

      const urlInput = await screen.findByPlaceholderText(/https:\/\/www.linkedin.com/i);
      const linkedInUrl = "https://www.linkedin.com/in/johndoe";

      fireEvent.change(urlInput, { target: { value: linkedInUrl } });

      const processButton = screen.getByRole("button", {
        name: /Process Resume/i,
      });

      fireEvent.click(processButton);

      await waitFor(() => {
        expect(mockOnUpload).toHaveBeenCalledWith(linkedInUrl, "linkedin");
      });
    });

    it("should disable linkedin process button when url is empty", async () => {
      render(<MultiMethodUpload onUpload={mockOnUpload} />);

      const linkedInTab = screen.getByRole("button", { name: /LinkedIn/i });
      fireEvent.click(linkedInTab);

      const processButton = await screen.findByRole("button", {
        name: /Process Resume/i,
      });

      expect(processButton).toBeDisabled();
    });
  });

  describe("Upload Progress and Loading", () => {
    it("should show loading state during upload", async () => {
      mockOnUpload.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      const { container } = render(<MultiMethodUpload onUpload={mockOnUpload} />);

      const file = new File(["content"], "resume.pdf", { type: "application/pdf" });
      const input = container.querySelector('input[type="file"]') as HTMLInputElement;

      fireEvent.change(input, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText("resume.pdf")).toBeInTheDocument();
      });

      const uploadButton = screen.getByRole("button", {
        name: /Upload Resume/i,
      });

      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(screen.getByText(/Uploading/i)).toBeInTheDocument();
      });
    });

    it("should disable all controls when loading", async () => {
      render(<MultiMethodUpload onUpload={mockOnUpload} loading={true} />);

      const pasteTab = screen.getByRole("button", { name: /Paste/i });
      const linkedInTab = screen.getByRole("button", { name: /LinkedIn/i });

      expect(pasteTab).toBeDisabled();
      expect(linkedInTab).toBeDisabled();
    });

    it("should disable controls when disabled prop is true", () => {
      render(<MultiMethodUpload onUpload={mockOnUpload} disabled={true} />);

      const dropZone = screen.getByText(/Drag & drop your resume/i).closest("div");
      expect(dropZone).toHaveClass("opacity-50");
    });
  });

  describe("Tab Navigation", () => {
    it("should maintain active tab state", async () => {
      render(<MultiMethodUpload onUpload={mockOnUpload} />);

      const pasteTab = screen.getByRole("button", { name: /Paste/i });
      fireEvent.click(pasteTab);

      await waitFor(() => {
        expect(
          screen.getByPlaceholderText(/Paste your resume content/i)
        ).toBeInTheDocument();
      });

      expect(pasteTab).toHaveClass("border-primary");
    });

    it("should switch between tabs correctly", async () => {
      render(<MultiMethodUpload onUpload={mockOnUpload} />);

      // Start with drag-drop
      expect(screen.getByText(/Drag & drop your resume/i)).toBeInTheDocument();

      // Switch to paste
      const pasteTab = screen.getByRole("button", { name: /Paste/i });
      fireEvent.click(pasteTab);

      await waitFor(() => {
        expect(
          screen.getByPlaceholderText(/Paste your resume content/i)
        ).toBeInTheDocument();
      });

      // Switch to linkedin
      const linkedInTab = screen.getByRole("button", { name: /LinkedIn/i });
      fireEvent.click(linkedInTab);

      await waitFor(() => {
        expect(
          screen.getByPlaceholderText(/https:\/\/www.linkedin.com/i)
        ).toBeInTheDocument();
      });

      // Switch back to upload
      const uploadTab = screen.getByRole("button", { name: /Upload/i });
      fireEvent.click(uploadTab);

      await waitFor(() => {
        expect(screen.getByText(/Drag & drop your resume/i)).toBeInTheDocument();
      });
    });
  });

  describe("File Validation", () => {
    it("should accept correct file types", async () => {
      const { container } = render(<MultiMethodUpload onUpload={mockOnUpload} />);

      const input = container.querySelector('input[type="file"]') as HTMLInputElement;
      expect(input.accept).toBe(".pdf,.doc,.docx,.txt");
    });

    it("should display file size correctly", async () => {
      const { container } = render(<MultiMethodUpload onUpload={mockOnUpload} />);

      const file = new File(["a".repeat(5120)], "resume.pdf", {
        type: "application/pdf",
      });
      const input = container.querySelector('input[type="file"]') as HTMLInputElement;

      fireEvent.change(input, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText(/5\.0 KB/)).toBeInTheDocument();
      });
    });
  });

  describe("Error Handling", () => {
    it("should handle upload errors gracefully", async () => {
      mockOnUpload.mockRejectedValueOnce(new Error("Upload failed"));
      const { container } = render(<MultiMethodUpload onUpload={mockOnUpload} />);

      const file = new File(["content"], "resume.pdf", { type: "application/pdf" });
      const input = container.querySelector('input[type="file"]') as HTMLInputElement;

      fireEvent.change(input, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText("resume.pdf")).toBeInTheDocument();
      });

      const uploadButton = screen.getByRole("button", {
        name: /Upload Resume/i,
      });

      fireEvent.click(uploadButton);

      await waitFor(() => {
        expect(mockOnUpload).toHaveBeenCalled();
      });
    });
  });
});
