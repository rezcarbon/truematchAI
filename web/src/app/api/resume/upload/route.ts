import { NextRequest, NextResponse } from "next/server";
import type { ResumeUploadMethod, ResumeVersion } from "@/types/resume";

interface UploadRequest {
  file?: File;
  content?: string;
  uploadMethod: ResumeUploadMethod;
}

interface UploadResponse {
  resumeId: string;
  versionId: string;
  userId: string;
  version: ResumeVersion;
}

/**
 * POST /api/resume/upload
 * Handles resume uploads from multiple sources (drag-drop, paste, linkedin)
 */
export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get("file") as File | null;
    const content = formData.get("content") as string | null;
    const linkedInUrl = formData.get("linkedInUrl") as string | null;
    const uploadMethod = formData.get("uploadMethod") as ResumeUploadMethod;

    if (!uploadMethod) {
      return NextResponse.json(
        { error: "Upload method is required" },
        { status: 400 }
      );
    }

    // Validate input based on upload method
    if (uploadMethod === "drag-drop" || uploadMethod === "file-click") {
      if (!file) {
        return NextResponse.json(
          { error: "File is required for drag-drop upload" },
          { status: 400 }
        );
      }
    } else if (uploadMethod === "paste") {
      if (!content || content.trim().length === 0) {
        return NextResponse.json(
          { error: "Content is required for paste upload" },
          { status: 400 }
        );
      }
    } else if (uploadMethod === "linkedin") {
      if (!linkedInUrl || linkedInUrl.trim().length === 0) {
        return NextResponse.json(
          { error: "LinkedIn URL is required" },
          { status: 400 }
        );
      }
    }

    // TODO: Add authentication check
    // const session = await getSession();
    // if (!session?.user?.id) {
    //   return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    // }

    const userId = "user-123"; // Placeholder: should come from session

    // Extract text and metadata based on upload method
    let extractedText = "";
    let fileName = "resume";
    let fileSize = 0;
    let format: ResumeVersion["format"] = "pdf";

    if (uploadMethod === "drag-drop" || uploadMethod === "file-click") {
      fileName = file!.name;
      fileSize = file!.size;
      format = getFormatFromFileName(fileName);
      extractedText = await extractTextFromFile(file!);
    } else if (uploadMethod === "paste") {
      extractedText = content!;
      fileName = "pasted_resume";
      format = "txt";
    } else if (uploadMethod === "linkedin") {
      // TODO: Implement LinkedIn profile scraping
      extractedText = await fetchLinkedInProfile(linkedInUrl!);
      fileName = "linkedin_profile";
      format = "txt";
    }

    // Parse resume content to extract skills and experience
    const { skills, experience_years, summary } = parseResumeContent(extractedText);

    // Create version record
    const resumeVersion: ResumeVersion = {
      id: `v-${Date.now()}`,
      resumeId: `resume-${userId}`,
      version: 1, // TODO: Get actual version number from DB
      fileName,
      format,
      fileSize,
      uploadMethod,
      status: "completed",
      extractedText,
      skills,
      experience_years,
      summary,
      uploadedAt: new Date().toISOString(),
    };

    // TODO: Save to database
    // await db.resumeVersions.create(resumeVersion);

    const response: UploadResponse = {
      resumeId: resumeVersion.resumeId,
      versionId: resumeVersion.id,
      userId,
      version: resumeVersion,
    };

    return NextResponse.json(response);
  } catch (error) {
    console.error("Resume upload error:", error);
    return NextResponse.json(
      {
        error:
          error instanceof Error
            ? error.message
            : "Failed to process resume upload",
      },
      { status: 500 }
    );
  }
}

/**
 * Extract text content from uploaded file
 */
async function extractTextFromFile(file: File): Promise<string> {
  const text = await file.text();
  return text.slice(0, 100000); // Limit to 100KB of text
}

/**
 * Fetch and extract text from LinkedIn profile
 */
async function fetchLinkedInProfile(url: string): Promise<string> {
  // TODO: Implement LinkedIn scraping
  // This would require LinkedIn API access or web scraping
  return "LinkedIn profile data would be extracted here";
}

/**
 * Determine file format from filename
 */
function getFormatFromFileName(
  fileName: string
): ResumeVersion["format"] {
  const extension = fileName.split(".").pop()?.toLowerCase();
  switch (extension) {
    case "pdf":
      return "pdf";
    case "docx":
      return "docx";
    case "doc":
      return "doc";
    case "txt":
      return "txt";
    default:
      return "pdf";
  }
}

/**
 * Parse resume content to extract skills, experience, and summary
 */
function parseResumeContent(
  text: string
): {
  skills: string[];
  experience_years: number;
  summary: string;
} {
  // Common skills to look for
  const commonSkills = [
    "JavaScript",
    "TypeScript",
    "React",
    "Vue",
    "Angular",
    "Node.js",
    "Python",
    "Java",
    "C++",
    "C#",
    "Go",
    "Rust",
    "PHP",
    "Ruby",
    "Swift",
    "Kotlin",
    "PostgreSQL",
    "MySQL",
    "MongoDB",
    "Redis",
    "Docker",
    "Kubernetes",
    "AWS",
    "Azure",
    "GCP",
    "Git",
    "HTML",
    "CSS",
    "SASS",
    "Tailwind",
    "GraphQL",
    "REST",
    "SQL",
    "NoSQL",
    "Agile",
    "Scrum",
    "Leadership",
    "Communication",
    "Project Management",
  ];

  const skills = commonSkills.filter(
    (skill) =>
      new RegExp(`\\b${skill}\\b`, "i").test(text)
  );

  // Extract experience years (look for patterns like "5 years", "5+ years", etc.)
  const experienceMatch = text.match(
    /(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)/i
  );
  const experience_years = experienceMatch ? parseInt(experienceMatch[1], 10) : 0;

  // Extract summary (first 500 characters or first paragraph)
  const summary = text.slice(0, 500).trim();

  return { skills, experience_years, summary };
}

/**
 * GET /api/resume/:resumeId
 * Retrieve resume and its versions
 */
export async function GET(request: NextRequest) {
  const resumeId = request.nextUrl.pathname.split("/").pop();

  if (!resumeId) {
    return NextResponse.json(
      { error: "Resume ID is required" },
      { status: 400 }
    );
  }

  try {
    // TODO: Fetch from database
    // const resume = await db.resumes.findById(resumeId);

    return NextResponse.json(
      {
        error: "Resume not found",
      },
      { status: 404 }
    );
  } catch (error) {
    console.error("Resume fetch error:", error);
    return NextResponse.json(
      { error: "Failed to fetch resume" },
      { status: 500 }
    );
  }
}
