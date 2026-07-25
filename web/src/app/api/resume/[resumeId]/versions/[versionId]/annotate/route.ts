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

    // }

    // }

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
