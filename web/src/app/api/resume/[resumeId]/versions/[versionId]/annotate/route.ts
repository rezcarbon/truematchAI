import { NextRequest, NextResponse } from "next/server";

interface AnnotateRequest {
  annotation: string;
}

/**
 * POST /api/resume/:resumeId/versions/:versionId/annotate
 * Add or update annotation for a resume version
 */
export async function POST(
  request: NextRequest,
  { params }: { params: { resumeId: string; versionId: string } }
) {
  try {
    const body: AnnotateRequest = await request.json();
    const { annotation } = body;

    if (!annotation || annotation.trim().length === 0) {
      return NextResponse.json(
        { error: "Annotation cannot be empty" },
        { status: 400 }
      );
    }

    if (annotation.length > 1000) {
      return NextResponse.json(
        { error: "Annotation cannot exceed 1000 characters" },
        { status: 400 }
      );
    }

    // TODO: Verify user owns this resume
    // const session = await getSession();
    // const resume = await db.resumes.findById(params.resumeId);
    // if (resume.userId !== session.user.id) {
    //   return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    // }

    // TODO: Verify version exists
    // const version = await db.resumeVersions.findById(params.versionId);
    // if (!version || version.resumeId !== params.resumeId) {
    //   return NextResponse.json({ error: "Version not found" }, { status: 404 });
    // }

    // TODO: Update annotation in database
    // await db.resumeVersions.update(params.versionId, {
    //   annotation,
    //   annotatedAt: new Date().toISOString(),
    // });

    return NextResponse.json({
      success: true,
      versionId: params.versionId,
      annotation,
      annotatedAt: new Date().toISOString(),
    });
  } catch (error) {
    console.error("Annotation error:", error);
    return NextResponse.json(
      {
        error:
          error instanceof Error
            ? error.message
            : "Failed to save annotation",
      },
      { status: 500 }
    );
  }
}
