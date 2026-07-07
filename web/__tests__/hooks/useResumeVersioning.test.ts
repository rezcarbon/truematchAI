import { renderHook, act, waitFor } from "@testing-library/react";
import { useResumeVersioning } from "@/hooks/useResumeVersioning";
import type { Resume, ResumeVersion } from "@/types/resume";

// Mock fetch globally
global.fetch = jest.fn();

describe("useResumeVersioning", () => {
  const mockVersion: ResumeVersion = {
    id: "v1",
    resumeId: "resume1",
    version: 1,
    fileName: "resume.pdf",
    format: "pdf",
    fileSize: 102400,
    uploadMethod: "drag-drop",
    status: "completed",
    extractedText: "John Doe Software Engineer",
    skills: ["JavaScript", "React"],
    experience_years: 5,
    summary: "Software Engineer",
    uploadedAt: new Date().toISOString(),
  };

  const mockResume: Resume = {
    id: "resume1",
    userId: "user1",
    currentVersionId: "v1",
    versions: [mockVersion],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    assessmentCount: 0,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockClear();
  });

  describe("Initialization", () => {
    it("should initialize with null resume when no initial resume provided", () => {
      const { result } = renderHook(() => useResumeVersioning());

      expect(result.current.resume).toBeNull();
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it("should initialize with provided resume", () => {
      const { result } = renderHook(() => useResumeVersioning(mockResume));

      expect(result.current.resume).toEqual(mockResume);
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });

  describe("uploadResume", () => {
    it("should upload file and update resume state", async () => {
      const mockFile = new File(["content"], "resume.pdf", {
        type: "application/pdf",
      });

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          resumeId: "resume1",
          versionId: "v1",
          userId: "user1",
          version: mockVersion,
        }),
      });

      const { result } = renderHook(() => useResumeVersioning());

      let uploadedVersion;
      await act(async () => {
        uploadedVersion = await result.current.uploadResume(mockFile, "drag-drop");
      });

      await waitFor(() => {
        expect(result.current.resume).not.toBeNull();
      });

      expect(result.current.resume?.versions).toHaveLength(1);
      expect(uploadedVersion).toEqual(mockVersion);
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it("should upload pasted content", async () => {
      const pastedContent = "John Doe\nSoftware Engineer";

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          resumeId: "resume1",
          versionId: "v1",
          userId: "user1",
          version: mockVersion,
        }),
      });

      const { result } = renderHook(() => useResumeVersioning());

      await act(async () => {
        await result.current.uploadResume(pastedContent, "paste");
      });

      await waitFor(() => {
        expect(result.current.resume).not.toBeNull();
      });

      expect(result.current.loading).toBe(false);
    });

    it("should handle upload errors", async () => {
      const mockFile = new File(["content"], "resume.pdf");

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ error: "Upload failed" }),
      });

      const { result } = renderHook(() => useResumeVersioning());

      await act(async () => {
        try {
          await result.current.uploadResume(mockFile, "drag-drop");
        } catch (error) {
          // Error expected
        }
      });

      expect(result.current.error).toBe("Upload failed");
      expect(result.current.loading).toBe(false);
    });

    it("should append new version to existing resume versions", async () => {
      const mockFile = new File(["content"], "resume.pdf");
      const newVersion: ResumeVersion = {
        ...mockVersion,
        id: "v2",
        version: 2,
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          resumeId: "resume1",
          versionId: "v2",
          userId: "user1",
          version: newVersion,
        }),
      });

      const { result } = renderHook(() => useResumeVersioning(mockResume));

      expect(result.current.resume?.versions).toHaveLength(1);

      await act(async () => {
        await result.current.uploadResume(mockFile, "drag-drop");
      });

      await waitFor(() => {
        expect(result.current.resume?.versions).toHaveLength(2);
      });

      expect(result.current.resume?.versions[0].id).toBe("v2");
      expect(result.current.resume?.currentVersionId).toBe("v2");
    });

    it("should set loading state during upload", async () => {
      const mockFile = new File(["content"], "resume.pdf");

      let resolveUpload: () => void;
      (global.fetch as jest.Mock).mockReturnValueOnce(
        new Promise((resolve) => {
          resolveUpload = () => {
            resolve({
              ok: true,
              json: async () => ({
                resumeId: "resume1",
                versionId: "v1",
                userId: "user1",
                version: mockVersion,
              }),
            });
          };
        })
      );

      const { result } = renderHook(() => useResumeVersioning());

      let uploadPromise: Promise<any>;
      act(() => {
        uploadPromise = result.current.uploadResume(mockFile, "drag-drop");
      });

      expect(result.current.loading).toBe(true);

      resolveUpload!();

      await act(async () => {
        await uploadPromise!;
      });

      expect(result.current.loading).toBe(false);
    });
  });

  describe("revertToVersion", () => {
    it("should revert to specified version", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

      const { result } = renderHook(() => useResumeVersioning(mockResume));

      await act(async () => {
        await result.current.revertToVersion("v1");
      });

      expect(result.current.resume?.currentVersionId).toBe("v1");
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it("should throw error if no resume is loaded", async () => {
      const { result } = renderHook(() => useResumeVersioning());

      await act(async () => {
        await expect(result.current.revertToVersion("v1")).rejects.toThrow(
          "No resume loaded"
        );
      });
    });

    it("should handle revert errors", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ error: "Revert failed" }),
      });

      const { result } = renderHook(() => useResumeVersioning(mockResume));

      await act(async () => {
        try {
          await result.current.revertToVersion("v1");
        } catch (error) {
          // Error expected
        }
      });

      expect(result.current.error).toBe("Revert failed");
    });

    it("should update the updatedAt timestamp", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

      const { result } = renderHook(() => useResumeVersioning(mockResume));
      const originalUpdatedAt = result.current.resume?.updatedAt;

      await act(async () => {
        await result.current.revertToVersion("v1");
      });

      expect(result.current.resume?.updatedAt).not.toBe(originalUpdatedAt);
    });
  });

  describe("deleteVersion", () => {
    it("should delete specified version", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

      const resumeWithMultipleVersions: Resume = {
        ...mockResume,
        versions: [
          mockVersion,
          { ...mockVersion, id: "v2", version: 2 },
        ],
      };

      const { result } = renderHook(() =>
        useResumeVersioning(resumeWithMultipleVersions)
      );

      expect(result.current.resume?.versions).toHaveLength(2);

      await act(async () => {
        await result.current.deleteVersion("v1");
      });

      expect(result.current.resume?.versions).toHaveLength(1);
      expect(result.current.resume?.versions[0].id).toBe("v2");
      expect(result.current.error).toBeNull();
    });

    it("should throw error if no resume is loaded", async () => {
      const { result } = renderHook(() => useResumeVersioning());

      await act(async () => {
        await expect(result.current.deleteVersion("v1")).rejects.toThrow(
          "No resume loaded"
        );
      });
    });

    it("should handle delete errors", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ error: "Delete failed" }),
      });

      const { result } = renderHook(() => useResumeVersioning(mockResume));

      await act(async () => {
        try {
          await result.current.deleteVersion("v1");
        } catch (error) {
          // Error expected
        }
      });

      expect(result.current.error).toBe("Delete failed");
    });
  });

  describe("annotateVersion", () => {
    it("should add annotation to version", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          annotation: "Updated with new skills",
        }),
      });

      const { result } = renderHook(() => useResumeVersioning(mockResume));

      await act(async () => {
        await result.current.annotateVersion("v1", "Updated with new skills");
      });

      expect(
        result.current.resume?.versions[0].annotation
      ).toBe("Updated with new skills");
      expect(result.current.error).toBeNull();
    });

    it("should throw error if no resume is loaded", async () => {
      const { result } = renderHook(() => useResumeVersioning());

      await act(async () => {
        await expect(
          result.current.annotateVersion("v1", "Test annotation")
        ).rejects.toThrow("No resume loaded");
      });
    });

    it("should handle annotation errors", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ error: "Annotation failed" }),
      });

      const { result } = renderHook(() => useResumeVersioning(mockResume));

      await act(async () => {
        try {
          await result.current.annotateVersion("v1", "Test");
        } catch (error) {
          // Error expected
        }
      });

      expect(result.current.error).toBe("Annotation failed");
    });
  });

  describe("compareVersions", () => {
    it("should compare two versions", async () => {
      const mockComparison = {
        versionA: mockVersion,
        versionB: { ...mockVersion, id: "v2", version: 2 },
        skillsAdded: ["TypeScript"],
        skillsRemoved: [],
        experienceYearsDifference: 1,
        summaryDifference: "Added TypeScript",
        extractedTextDifference: "+ TypeScript",
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockComparison,
      });

      const { result } = renderHook(() => useResumeVersioning(mockResume));

      let comparison;
      await act(async () => {
        comparison = await result.current.compareVersions("v1", "v2");
      });

      expect(comparison).toEqual(mockComparison);
      expect(result.current.error).toBeNull();
    });

    it("should throw error if no resume is loaded", async () => {
      const { result } = renderHook(() => useResumeVersioning());

      await act(async () => {
        await expect(
          result.current.compareVersions("v1", "v2")
        ).rejects.toThrow("No resume loaded");
      });
    });

    it("should handle comparison errors", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ error: "Comparison failed" }),
      });

      const { result } = renderHook(() => useResumeVersioning(mockResume));

      await act(async () => {
        try {
          await result.current.compareVersions("v1", "v2");
        } catch (error) {
          // Error expected
        }
      });

      expect(result.current.error).toBe("Comparison failed");
    });
  });

  describe("Error Handling", () => {
    it("should clear error on successful operation after error", async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: false,
          json: async () => ({ error: "First error" }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({}),
        });

      const { result } = renderHook(() => useResumeVersioning(mockResume));

      // First call - error
      await act(async () => {
        try {
          await result.current.revertToVersion("v1");
        } catch (error) {
          // Expected
        }
      });

      expect(result.current.error).toBe("First error");

      // Second call - success
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

      await act(async () => {
        await result.current.revertToVersion("v1");
      });

      expect(result.current.error).toBeNull();
    });

    it("should handle network errors", async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(
        new Error("Network error")
      );

      const { result } = renderHook(() => useResumeVersioning());

      await act(async () => {
        try {
          const file = new File(["content"], "resume.pdf");
          await result.current.uploadResume(file, "drag-drop");
        } catch (error) {
          // Expected
        }
      });

      expect(result.current.error).toBe("Network error");
    });
  });

  describe("Loading State Management", () => {
    it("should set loading to false after successful operation", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ version: mockVersion }),
      });

      const { result } = renderHook(() => useResumeVersioning());

      await act(async () => {
        const file = new File(["content"], "resume.pdf");
        await result.current.uploadResume(file, "drag-drop");
      });

      expect(result.current.loading).toBe(false);
    });

    it("should set loading to false after failed operation", async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ error: "Upload failed" }),
      });

      const { result } = renderHook(() => useResumeVersioning());

      await act(async () => {
        try {
          const file = new File(["content"], "resume.pdf");
          await result.current.uploadResume(file, "drag-drop");
        } catch (error) {
          // Expected
        }
      });

      expect(result.current.loading).toBe(false);
    });
  });
});
