import { NextRequest, NextResponse } from "next/server";

/**
 * DELETE /api/resume/:resumeId/versions/:versionId
 * Delete a specific version of a resume
 */
export async function DELETE(
  request: NextRequest,
  { params }: { params: { resumeId: string; versionId: string } }
) {
  try {
    const { resumeId, versionId } = params;

    if (!versionId) {
      return NextResponse.json(
        { error: "Version ID is required" },
        { status: 400 }
      );
    }

    // TODO: Verify user owns this resume
    // const session = await getSession();
    // const resume = await db.resumes.findById(resumeId);
    // if (resume.userId !== session.user.id) {
    //   return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    // }

    // TODO: Verify version exists and is not current
    // const version = await db.resumeVersions.findById(versionId);
    // if (!version || version.resumeId !== resumeId) {
    //   return NextResponse.json({ error: "Version not found" }, { status: 404 });
    // }
    // if (resume.currentVersionId === versionId) {
    //   return NextResponse.json(
    //     { error: "Cannot delete the current version" },
    //     { status: 400 }
    //   );
    // }

    // TODO: Delete version from database
    // await db.resumeVersions.deleteById(versionId);

    return NextResponse.json({
      success: true,
      versionId,
      deletedAt: new Date().toISOString(),
    });
  } catch (error) {
    console.error("Delete version error:", error);
    return NextResponse.json(
      {
        error:
          error instanceof Error ? error.message : "Failed to delete version",
      },
      { status: 500 }
    );
  }
}
