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

    // }

    // }


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
