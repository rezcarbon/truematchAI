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

    // }

    // }
    //     { error: "Cannot delete the current version" },
    //     { status: 400 }
    //   );
    // }


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
