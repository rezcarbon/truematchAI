import { NextRequest, NextResponse } from "next/server";

interface RevertRequest {
  versionId: string;
}

/**
 * POST /api/resume/:resumeId/revert
 * Revert resume to a previous version
 */
export async function POST(
  request: NextRequest,
  { params }: { params: { resumeId: string } }
) {
  try {
    const body: RevertRequest = await request.json();
    const { versionId } = body;

    if (!versionId) {
      return NextResponse.json(
        { error: "Version ID is required" },
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
    // const version = await db.resumeVersions.findById(versionId);
    // if (!version || version.resumeId !== params.resumeId) {
    //   return NextResponse.json({ error: "Version not found" }, { status: 404 });
    // }

    // TODO: Update current version
    // await db.resumes.update(params.resumeId, { currentVersionId: versionId });

    return NextResponse.json({
      success: true,
      versionId,
      updatedAt: new Date().toISOString(),
    });
  } catch (error) {
    console.error("Revert error:", error);
    return NextResponse.json(
      {
        error:
          error instanceof Error ? error.message : "Failed to revert version",
      },
      { status: 500 }
    );
  }
}
