import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { VersionTimeline } from "@/components/resume/VersionTimeline";
import type { ResumeVersion } from "@/types/resume";

// Mock UI components
jest.mock("@/components/ui/card", () => ({
  Card: ({ children }: any) => <div data-testid="card">{children}</div>,
  CardContent: ({ children }: any) => <div data-testid="card-content">{children}</div>,
  CardHeader: ({ children }: any) => <div data-testid="card-header">{children}</div>,
  CardTitle: ({ children }: any) => <div>{children}</div>,
}));

jest.mock("@/components/ui/button", () => ({
  Button: ({ children, onClick, disabled, ...props }: any) => (
    <button onClick={onClick} disabled={disabled} {...props}>
      {children}
    </button>
  ),
}));

jest.mock("@/components/ui/badge", () => ({
  Badge: ({ children, variant }: any) => <span data-variant={variant}>{children}</span>,
}));

jest.mock("@/lib/utils", () => ({
  cn: (...args: any[]) => args.filter(Boolean).join(" "),
}));

describe("VersionTimeline", () => {
  const mockResumeVersions: ResumeVersion[] = [
    {
      id: "v1",
      resumeId: "resume1",
      version: 1,
      fileName: "resume_v1.pdf",
      format: "pdf",
      fileSize: 102400,
      uploadMethod: "drag-drop",
      status: "completed",
      extractedText: "John Doe Software Engineer",
      skills: ["JavaScript", "React", "TypeScript"],
      experience_years: 5,
      summary: "Experienced software engineer",
      uploadedAt: new Date(Date.now() - 86400000).toISOString(),
    },
    {
      id: "v2",
      resumeId: "resume1",
      version: 2,
      fileName: "resume_v2.pdf",
      format: "pdf",
      fileSize: 112640,
      uploadMethod: "paste",
      status: "completed",
      extractedText: "John Doe Senior Software Engineer",
      skills: ["JavaScript", "React", "TypeScript", "Node.js"],
      experience_years: 6,
      summary: "Senior software engineer with leadership experience",
      uploadedAt: new Date(Date.now() - 3600000).toISOString(),
    },
  ];

  const mockRevert = jest.fn();
  const mockDelete = jest.fn();
  const mockCompare = jest.fn();
  const mockAnnotate = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Rendering", () => {
    it("should render version timeline with all versions", () => {
      render(
        <VersionTimeline
          versions={mockResumeVersions}
          currentVersionId="v2"
          onRevert={mockRevert}
          onDelete={mockDelete}
          onCompare={mockCompare}
          onAnnotate={mockAnnotate}
        />
      );

      expect(screen.getByText("Version History")).toBeInTheDocument();
      expect(screen.getByText(/2 versions/)).toBeInTheDocument();
      expect(screen.getByText("resume_v1.pdf")).toBeInTheDocument();
      expect(screen.getByText("resume_v2.pdf")).toBeInTheDocument();
    });

    it("should render empty state when no versions exist", () => {
      render(
        <VersionTimeline
          versions={[]}
          currentVersionId="v1"
          onRevert={mockRevert}
          onDelete={mockDelete}
          onCompare={mockCompare}
          onAnnotate={mockAnnotate}
        />
      );

      expect(
        screen.getByText(/No resume versions yet/i)
      ).toBeInTheDocument();
    });

    it("should mark current version with badge", () => {
      render(
        <VersionTimeline
          versions={mockResumeVersions}
          currentVersionId="v2"
          onRevert={mockRevert}
          onDelete={mockDelete}
          onCompare={mockCompare}
          onAnnotate={mockAnnotate}
        />
      );

      const currentBadges = screen.getAllByText("Current");
      expect(currentBadges.length).toBeGreaterThan(0);
    });
  });

  describe("Version Details Display", () => {
    it("should display version number and upload method", () => {
      render(
        <VersionTimeline
          versions={mockResumeVersions}
          currentVersionId="v1"
          onRevert={mockRevert}
          onDelete={mockDelete}
          onCompare={mockCompare}
          onAnnotate={mockAnnotate}
        />
      );

      expect(screen.getByText(/v1/)).toBeInTheDocument();
      expect(screen.getByText(/v2/)).toBeInTheDocument();
      expect(screen.getByText(/Drag & Drop/)).toBeInTheDocument();
      expect(screen.getByText(/Pasted Content/)).toBeInTheDocument();
    });

    it("should display skills count, experience years, and file size", () => {
      render(
        <VersionTimeline
          versions={mockResumeVersions}
          currentVersionId="v1"
          onRevert={mockRevert}
          onDelete={mockDelete}
          onCompare={mockCompare}
          onAnnotate={mockAnnotate}
        />
      );

      expect(screen.getByText("3")).toBeInTheDocument(); // skills count
      expect(screen.getByText("5y")).toBeInTheDocument(); // experience years
      expect(screen.getByText(/100\.0KB/)).toBeInTheDocument(); // file size
    });

    it("should display upload date and time", () => {
      render(
        <VersionTimeline
          versions={mockResumeVersions}
          currentVersionId="v1"
          onRevert={mockRevert}
          onDelete={mockDelete}
          onCompare={mockCompare}
          onAnnotate={mockAnnotate}
        />
      );

      // Check that date is displayed (exact format may vary)
      const dateElements = screen.getAllByText(/Jul/i);
      expect(dateElements.length).toBeGreaterThan(0);
    });
  });

  describe("Version Annotations", () => {
    it("should display annotation when present", () => {
      const versionsWithAnnotation = [
        {
          ...mockResumeVersions[0],
          annotation: "Updated with recent projects",
        },
      ];

      render(
        <VersionTimeline
          versions={versionsWithAnnotation}
          currentVersionId="v1"
          onRevert={mockRevert}
          onDelete={mockDelete}
          onCompare={mockCompare}
          onAnnotate={mockAnnotate}
        />
      );

      expect(screen.getByText("Updated with recent projects")).toBeInTheDocument();
      expect(screen.getByText("Annotation:")).toBeInTheDocument();
    });

    it("should call onAnnotate when Add Note button is clicked", async () => {
      render(
        <VersionTimeline
          versions={mockResumeVersions}
          currentVersionId="v2"
          onRevert={mockRevert}
          onDelete={mockDelete}
          onCompare={mockCompare}
          onAnnotate={mockAnnotate}
        />
      );

      const addNoteButtons = screen.getAllByText(/Add Note/);
      fireEvent.click(addNoteButtons[0]);

      await waitFor(() => {
        expect(mockAnnotate).toHaveBeenCalledWith(mockResumeVersions[1].id);
      });
    });
  });

  describe("Error Display", () => {
    it("should display error message for failed uploads", () => {
      const failedVersion: ResumeVersion = {
        ...mockResumeVersions[0],
        status: "failed",
        errorMessage: "File size exceeds limit",
      };

      render(
        <VersionTimeline
          versions={[failedVersion]}
          currentVersionId="v1"
          onRevert={mockRevert}
          onDelete={mockDelete}
          onCompare={mockCompare}
          onAnnotate={mockAnnotate}
        />
      );

      expect(screen.getByText("File size exceeds limit")).toBeInTheDocument();
      expect(screen.getByText("Error:")).toBeInTheDocument();
    });
  });

  describe("Action Buttons", () => {
    it("should show Revert button for non-current versions", () => {
      render(
        <VersionTimeline
          versions={mockResumeVersions}
          currentVersionId="v2"
          onRevert={mockRevert}
          onDelete={mockDelete}
          onCompare={mockCompare}
          onAnnotate={mockAnnotate}
        />
      );

      const revertButtons = screen.getAllByRole("button", { name: /Revert/i });
      expect(revertButtons.length).toBeGreaterThan(0);
    });

    it("should NOT show Revert button for current version", () => {
      render(
        <VersionTimeline
          versions={mockResumeVersions}
          currentVersionId="v1"
          onRevert={mockRevert}
          onDelete={mockDelete}
          onCompare={mockCompare}
          onAnnotate={mockAnnotate}
        />
      );

      // First version is current, should not have revert button in first card
      const cards = screen.getAllByTestId("card");
      const firstCard = cards[cards.length - 1]; // Last card is the oldest (v1)

      const revertButtonInFirstCard = firstCard.querySelector(
        'button:has-text("Revert")'
      );
      expect(revertButtonInFirstCard).not.toBeInTheDocument();
    });

    it("should call onRevert when Revert button is clicked", async () => {
      render(
        <VersionTimeline
          versions={mockResumeVersions}
          currentVersionId="v2"
          onRevert={mockRevert}
          onDelete={mockDelete}
          onCompare={mockCompare}
          onAnnotate={mockAnnotate}
        />
      );

      const revertButtons = screen.getAllByRole("button", { name: /Revert/i });
      fireEvent.click(revertButtons[0]);

      await waitFor(() => {
        expect(mockRevert).toHaveBeenCalledWith(mockResumeVersions[1].id);
      });
    });

    it("should call onDelete when Delete button is clicked", async () => {
      render(
        <VersionTimeline
          versions={mockResumeVersions}
          currentVersionId="v2"
          onRevert={mockRevert}
          onDelete={mockDelete}
          onCompare={mockCompare}
          onAnnotate={mockAnnotate}
        />
      );

      const deleteButtons = screen.getAllByRole("button", { name: /Delete/i });
      fireEvent.click(deleteButtons[0]);

      await waitFor(() => {
        expect(mockDelete).toHaveBeenCalledWith(mockResumeVersions[1].id);
      });
    });

    it("should NOT show Delete button for current version", () => {
      render(
        <VersionTimeline
          versions={mockResumeVersions}
          currentVersionId="v1"
          currentVersionId="v1"
          onRevert={mockRevert}
          onDelete={mockDelete}
          onCompare={mockCompare}
          onAnnotate={mockAnnotate}
        />
      );

      // The Delete button for current version should be disabled
      const deleteButtons = screen.getAllByRole("button", { name: /Delete/i });
      const currentVersionDeleteButton = deleteButtons[deleteButtons.length - 1];

      expect(currentVersionDeleteButton).toBeDisabled();
    });

    it("should show Compare button for completed versions", () => {
      render(
        <VersionTimeline
          versions={mockResumeVersions}
          currentVersionId="v2"
          onRevert={mockRevert}
          onDelete={mockDelete}
          onCompare={mockCompare}
          onAnnotate={mockAnnotate}
        />
      );

      const compareButtons = screen.getAllByRole("button", { name: /Compare/i });
      expect(compareButtons.length).toBeGreaterThan(0);
    });

    it("should call onCompare with correct versions when Compare button is clicked", async () => {
      render(
        <VersionTimeline
          versions={mockResumeVersions}
          currentVersionId="v2"
          onRevert={mockRevert}
          onDelete={mockDelete}
          onCompare={mockCompare}
          onAnnotate={mockAnnotate}
        />
      );

      const compareButtons = screen.getAllByRole("button", { name: /Compare/i });
      fireEvent.click(compareButtons[0]);

      await waitFor(() => {
        expect(mockCompare).toHaveBeenCalledWith(
          mockResumeVersions[1].id,
          mockResumeVersions[0].id
        );
      });
    });
  });

  describe("Loading State", () => {
    it("should disable all buttons when loading", () => {
      render(
        <VersionTimeline
          versions={mockResumeVersions}
          currentVersionId="v2"
          onRevert={mockRevert}
          onDelete={mockDelete}
          onCompare={mockCompare}
          onAnnotate={mockAnnotate}
          loading={true}
        />
      );

      const allButtons = screen.getAllByRole("button");
      const actionButtons = allButtons.filter(
        (btn) =>
          btn.textContent?.includes("Revert") ||
          btn.textContent?.includes("Delete") ||
          btn.textContent?.includes("Compare")
      );

      actionButtons.forEach((btn) => {
        if (!btn.textContent?.includes("Add Note")) {
          expect(btn).toBeDisabled();
        }
      });
    });
  });

  describe("Version Sorting", () => {
    it("should display versions in reverse chronological order", () => {
      render(
        <VersionTimeline
          versions={mockResumeVersions}
          currentVersionId="v1"
          onRevert={mockRevert}
          onDelete={mockDelete}
          onCompare={mockCompare}
          onAnnotate={mockAnnotate}
        />
      );

      const versionLabels = screen.getAllByText(/^v\d+/);
      // Most recent should be first
      expect(versionLabels[0].textContent).toContain("v2");
      expect(versionLabels[1].textContent).toContain("v1");
    });
  });

  describe("Upload Method Labels", () => {
    it("should correctly label all upload methods", () => {
      const allMethods: ResumeVersion[] = [
        {
          ...mockResumeVersions[0],
          uploadMethod: "drag-drop",
        },
        {
          ...mockResumeVersions[0],
          id: "v2",
          uploadMethod: "paste",
        },
        {
          ...mockResumeVersions[0],
          id: "v3",
          uploadMethod: "linkedin",
        },
        {
          ...mockResumeVersions[0],
          id: "v4",
          uploadMethod: "file-click",
        },
      ];

      render(
        <VersionTimeline
          versions={allMethods}
          currentVersionId="v1"
          onRevert={mockRevert}
          onDelete={mockDelete}
          onCompare={mockCompare}
          onAnnotate={mockAnnotate}
        />
      );

      expect(screen.getByText(/Drag & Drop/)).toBeInTheDocument();
      expect(screen.getByText(/Pasted Content/)).toBeInTheDocument();
      expect(screen.getByText(/LinkedIn/)).toBeInTheDocument();
      expect(screen.getByText(/File Click/)).toBeInTheDocument();
    });
  });
});
