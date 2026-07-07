import React from "react";
import { render, screen } from "@testing-library/react";
import { VersionComparison } from "@/components/resume/VersionComparison";
import type { ResumeVersion, VersionComparison as VersionComparisonType } from "@/types/resume";

// Mock UI components
jest.mock("@/components/ui/card", () => ({
  Card: ({ children }: any) => <div data-testid="card">{children}</div>,
  CardContent: ({ children }: any) => <div data-testid="card-content">{children}</div>,
  CardHeader: ({ children }: any) => <div data-testid="card-header">{children}</div>,
  CardTitle: ({ children }: any) => <div>{children}</div>,
}));

jest.mock("@/components/ui/badge", () => ({
  Badge: ({ children, variant, className }: any) => (
    <span data-variant={variant} className={className}>
      {children}
    </span>
  ),
}));

jest.mock("@/lib/utils", () => ({
  cn: (...args: any[]) => args.filter(Boolean).join(" "),
}));

describe("VersionComparison", () => {
  const mockVersionA: ResumeVersion = {
    id: "v1",
    resumeId: "resume1",
    version: 1,
    fileName: "resume_v1.pdf",
    format: "pdf",
    fileSize: 102400,
    uploadMethod: "drag-drop",
    status: "completed",
    extractedText: "John Doe Software Engineer 5 years JavaScript React",
    skills: ["JavaScript", "React"],
    experience_years: 5,
    summary: "Software Engineer with 5 years of experience",
    uploadedAt: new Date(Date.now() - 86400000).toISOString(),
  };

  const mockVersionB: ResumeVersion = {
    id: "v2",
    resumeId: "resume1",
    version: 2,
    fileName: "resume_v2.pdf",
    format: "pdf",
    fileSize: 112640,
    uploadMethod: "paste",
    status: "completed",
    extractedText:
      "John Doe Senior Software Engineer 6 years JavaScript React TypeScript Node.js",
    skills: ["JavaScript", "React", "TypeScript", "Node.js"],
    experience_years: 6,
    summary: "Senior Software Engineer with 6 years of experience and leadership skills",
    uploadedAt: new Date().toISOString(),
  };

  const mockComparison: VersionComparisonType = {
    versionA: mockVersionA,
    versionB: mockVersionB,
    skillsAdded: ["TypeScript", "Node.js"],
    skillsRemoved: [],
    experienceYearsDifference: 1,
    summaryDifference: "Added leadership skills",
    extractedTextDifference:
      "- 5 years\n+ 6 years\n+ Senior\n+ leadership skills",
  };

  describe("Rendering", () => {
    it("should render comparison header with version numbers", () => {
      render(
        <VersionComparison
          versionA={mockVersionA}
          versionB={mockVersionB}
          comparison={mockComparison}
        />
      );

      expect(screen.getByText("Comparing versions")).toBeInTheDocument();
      expect(screen.getByText(/v1/)).toBeInTheDocument();
      expect(screen.getByText(/v2/)).toBeInTheDocument();
    });

    it("should render all comparison sections", () => {
      render(
        <VersionComparison
          versionA={mockVersionA}
          versionB={mockVersionB}
          comparison={mockComparison}
        />
      );

      expect(screen.getByText("Skills Changes")).toBeInTheDocument();
      expect(screen.getByText("Experience Changes")).toBeInTheDocument();
      expect(screen.getByText("Summary Changes")).toBeInTheDocument();
    });
  });

  describe("Skills Comparison", () => {
    it("should display added skills", () => {
      render(
        <VersionComparison
          versionA={mockVersionA}
          versionB={mockVersionB}
          comparison={mockComparison}
        />
      );

      expect(screen.getByText("Skills Added (2)")).toBeInTheDocument();
      expect(screen.getByText("TypeScript")).toBeInTheDocument();
      expect(screen.getByText("Node.js")).toBeInTheDocument();
    });

    it("should display added skills with green badge", () => {
      render(
        <VersionComparison
          versionA={mockVersionA}
          versionB={mockVersionB}
          comparison={mockComparison}
        />
      );

      const addedSkillsBadges = screen.getAllByText(/TypeScript|Node.js/);
      addedSkillsBadges.forEach((badge) => {
        expect(badge.className).toContain("green");
      });
    });

    it("should display removed skills", () => {
      const comparisonWithRemovedSkills: VersionComparisonType = {
        ...mockComparison,
        skillsRemoved: ["Older Skill"],
      };

      render(
        <VersionComparison
          versionA={mockVersionA}
          versionB={mockVersionB}
          comparison={comparisonWithRemovedSkills}
        />
      );

      expect(screen.getByText("Skills Removed (1)")).toBeInTheDocument();
      expect(screen.getByText("Older Skill")).toBeInTheDocument();
    });

    it("should display removed skills with red badge", () => {
      const comparisonWithRemovedSkills: VersionComparisonType = {
        ...mockComparison,
        skillsRemoved: ["Older Skill"],
      };

      render(
        <VersionComparison
          versionA={mockVersionA}
          versionB={mockVersionB}
          comparison={comparisonWithRemovedSkills}
        />
      );

      const removedSkillsBadges = screen.getAllByText("Older Skill");
      removedSkillsBadges.forEach((badge) => {
        expect(badge.className).toContain("red");
      });
    });

    it("should show message when no skill changes", () => {
      const comparisonNoChanges: VersionComparisonType = {
        ...mockComparison,
        skillsAdded: [],
        skillsRemoved: [],
      };

      render(
        <VersionComparison
          versionA={mockVersionA}
          versionB={mockVersionB}
          comparison={comparisonNoChanges}
        />
      );

      expect(screen.queryByText("Skills Changes")).not.toBeInTheDocument();
    });
  });

  describe("Experience Comparison", () => {
    it("should display experience years for both versions", () => {
      render(
        <VersionComparison
          versionA={mockVersionA}
          versionB={mockVersionB}
          comparison={mockComparison}
        />
      );

      expect(screen.getByText("Experience Changes")).toBeInTheDocument();
      expect(screen.getAllByText("5")).toContainEqual(screen.getByText("5"));
      expect(screen.getAllByText("6")).toContainEqual(screen.getByText("6"));
    });

    it("should display experience difference correctly", () => {
      render(
        <VersionComparison
          versionA={mockVersionA}
          versionB={mockVersionB}
          comparison={mockComparison}
        />
      );

      expect(screen.getByText(/\+1 years added/)).toBeInTheDocument();
    });

    it("should show years removed when experience decreases", () => {
      const comparisonDecreased: VersionComparisonType = {
        ...mockComparison,
        experienceYearsDifference: -2,
      };

      render(
        <VersionComparison
          versionA={mockVersionA}
          versionB={mockVersionB}
          comparison={comparisonDecreased}
        />
      );

      expect(screen.getByText(/-2 years removed/)).toBeInTheDocument();
    });

    it("should not show experience section when difference is zero", () => {
      const comparisonNoChange: VersionComparisonType = {
        ...mockComparison,
        experienceYearsDifference: 0,
      };

      render(
        <VersionComparison
          versionA={mockVersionA}
          versionB={mockVersionB}
          comparison={comparisonNoChange}
        />
      );

      // Experience Changes section should not be rendered at all
      const headers = screen.queryAllByText("Experience Changes");
      expect(headers.length).toBe(0);
    });
  });

  describe("Summary Changes", () => {
    it("should display both version summaries", () => {
      render(
        <VersionComparison
          versionA={mockVersionA}
          versionB={mockVersionB}
          comparison={mockComparison}
        />
      );

      expect(screen.getByText("Summary Changes")).toBeInTheDocument();
      expect(
        screen.getByText("Software Engineer with 5 years of experience")
      ).toBeInTheDocument();
      expect(
        screen.getByText(
          "Senior Software Engineer with 6 years of experience and leadership skills"
        )
      ).toBeInTheDocument();
    });

    it("should label summaries with version numbers", () => {
      render(
        <VersionComparison
          versionA={mockVersionA}
          versionB={mockVersionB}
          comparison={mockComparison}
        />
      );

      const versionLabels = screen.getAllByText(/^v[12]$/);
      expect(versionLabels.length).toBeGreaterThanOrEqual(2);
    });

    it("should handle empty summaries", () => {
      const versionNoSummary = { ...mockVersionA, summary: "" };

      render(
        <VersionComparison
          versionA={versionNoSummary}
          versionB={mockVersionB}
          comparison={mockComparison}
        />
      );

      expect(screen.getByText("Summary Changes")).toBeInTheDocument();
    });
  });

  describe("Detailed Changes", () => {
    it("should display detailed text differences when available", () => {
      render(
        <VersionComparison
          versionA={mockVersionA}
          versionB={mockVersionB}
          comparison={mockComparison}
        />
      );

      expect(screen.getByText("Detailed Changes")).toBeInTheDocument();
      expect(
        screen.getByText(/- 5 years\n\+ 6 years\n\+ Senior\n\+ leadership skills/)
      ).toBeInTheDocument();
    });

    it("should not display detailed changes when difference is empty", () => {
      const comparisonNoDiff: VersionComparisonType = {
        ...mockComparison,
        extractedTextDifference: "",
      };

      render(
        <VersionComparison
          versionA={mockVersionA}
          versionB={mockVersionB}
          comparison={comparisonNoDiff}
        />
      );

      const detailedChangeHeaders = screen.queryAllByText("Detailed Changes");
      expect(detailedChangeHeaders.length).toBe(0);
    });
  });

  describe("Layout and Styling", () => {
    it("should render sections as cards", () => {
      const { container } = render(
        <VersionComparison
          versionA={mockVersionA}
          versionB={mockVersionB}
          comparison={mockComparison}
        />
      );

      const cards = container.querySelectorAll('[data-testid="card"]');
      expect(cards.length).toBeGreaterThan(0);
    });

    it("should have proper spacing between sections", () => {
      const { container } = render(
        <VersionComparison
          versionA={mockVersionA}
          versionB={mockVersionB}
          comparison={mockComparison}
        />
      );

      const mainDiv = container.querySelector(".space-y-6");
      expect(mainDiv).toBeInTheDocument();
    });
  });

  describe("Multiple Skills Changes", () => {
    it("should handle multiple added skills", () => {
      const manySkillsComparison: VersionComparisonType = {
        ...mockComparison,
        skillsAdded: ["TypeScript", "Node.js", "PostgreSQL", "Docker", "Kubernetes"],
      };

      render(
        <VersionComparison
          versionA={mockVersionA}
          versionB={mockVersionB}
          comparison={manySkillsComparison}
        />
      );

      expect(screen.getByText("Skills Added (5)")).toBeInTheDocument();
      expect(screen.getByText("TypeScript")).toBeInTheDocument();
      expect(screen.getByText("Docker")).toBeInTheDocument();
      expect(screen.getByText("Kubernetes")).toBeInTheDocument();
    });

    it("should handle both added and removed skills", () => {
      const bidirectionalComparison: VersionComparisonType = {
        ...mockComparison,
        skillsAdded: ["TypeScript", "Node.js"],
        skillsRemoved: ["jQuery", "Flash"],
      };

      render(
        <VersionComparison
          versionA={mockVersionA}
          versionB={mockVersionB}
          comparison={bidirectionalComparison}
        />
      );

      expect(screen.getByText("Skills Added (2)")).toBeInTheDocument();
      expect(screen.getByText("Skills Removed (2)")).toBeInTheDocument();
      expect(screen.getByText("TypeScript")).toBeInTheDocument();
      expect(screen.getByText("jQuery")).toBeInTheDocument();
    });
  });

  describe("Data Integrity", () => {
    it("should display correct version information", () => {
      render(
        <VersionComparison
          versionA={mockVersionA}
          versionB={mockVersionB}
          comparison={mockComparison}
        />
      );

      const versionHeaders = screen.getAllByText(/^v[12]$/);
      expect(versionHeaders).toBeDefined();
    });

    it("should not mutate comparison data", () => {
      const comparisonCopy = { ...mockComparison };
      render(
        <VersionComparison
          versionA={mockVersionA}
          versionB={mockVersionB}
          comparison={mockComparison}
        />
      );

      expect(mockComparison).toEqual(comparisonCopy);
    });
  });
});
