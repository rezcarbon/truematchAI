"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Plus, Minus } from "lucide-react";
import type { ResumeVersion, VersionComparison as VersionComparisonType } from "@/types/resume";
import { cn } from "@/lib/utils";

interface VersionComparisonProps {
  versionA: ResumeVersion;
  versionB: ResumeVersion;
  comparison: VersionComparisonType;
}

export function VersionComparison({
  versionA,
  versionB,
  comparison,
}: VersionComparisonProps) {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="text-sm">
          <p className="text-muted-foreground">Comparing versions</p>
          <div className="flex items-center gap-2 mt-1">
            <span className="font-medium">v{versionA.version}</span>
            <ArrowRight className="h-4 w-4 text-muted-foreground" />
            <span className="font-medium">v{versionB.version}</span>
          </div>
        </div>
      </div>

      {/* Skills Comparison */}
      {(comparison.skillsAdded.length > 0 || comparison.skillsRemoved.length > 0) && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Skills Changes</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {comparison.skillsAdded.length > 0 && (
              <div>
                <p className="text-sm font-medium mb-2 flex items-center gap-2">
                  <Plus className="h-4 w-4 text-green-600" />
                  Skills Added ({comparison.skillsAdded.length})
                </p>
                <div className="flex flex-wrap gap-2">
                  {comparison.skillsAdded.map((skill) => (
                    <Badge key={skill} variant="secondary" className="bg-green-100 text-green-800">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {comparison.skillsRemoved.length > 0 && (
              <div>
                <p className="text-sm font-medium mb-2 flex items-center gap-2">
                  <Minus className="h-4 w-4 text-red-600" />
                  Skills Removed ({comparison.skillsRemoved.length})
                </p>
                <div className="flex flex-wrap gap-2">
                  {comparison.skillsRemoved.map((skill) => (
                    <Badge key={skill} variant="secondary" className="bg-red-100 text-red-800">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {comparison.skillsAdded.length === 0 && comparison.skillsRemoved.length === 0 && (
              <p className="text-sm text-muted-foreground">No skill changes detected.</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Experience Comparison */}
      {comparison.experienceYearsDifference !== 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Experience Changes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-lg bg-muted p-3">
                <p className="text-xs text-muted-foreground mb-1">v{versionA.version}</p>
                <p className="text-2xl font-bold">{versionA.experience_years}</p>
                <p className="text-xs text-muted-foreground">years experience</p>
              </div>
              <div className="rounded-lg bg-muted p-3">
                <p className="text-xs text-muted-foreground mb-1">v{versionB.version}</p>
                <p className="text-2xl font-bold">{versionB.experience_years}</p>
                <p className="text-xs text-muted-foreground">years experience</p>
              </div>
            </div>
            <div className="mt-3 p-2 bg-blue-50 dark:bg-blue-900/20 rounded">
              <p className="text-sm">
                {comparison.experienceYearsDifference > 0 ? (
                  <span className="text-green-600 font-medium">
                    +{comparison.experienceYearsDifference} years added
                  </span>
                ) : (
                  <span className="text-red-600 font-medium">
                    {comparison.experienceYearsDifference} years removed
                  </span>
                )}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary Comparison */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Summary Changes</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4">
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-2">v{versionA.version}</p>
              <div className="p-3 rounded-lg bg-muted text-sm max-h-[150px] overflow-y-auto">
                {versionA.summary || "No summary available"}
              </div>
            </div>
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-2">v{versionB.version}</p>
              <div className="p-3 rounded-lg bg-muted text-sm max-h-[150px] overflow-y-auto">
                {versionB.summary || "No summary available"}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Text Diff */}
      {comparison.extractedTextDifference && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Detailed Changes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="p-3 rounded-lg bg-muted text-sm max-h-[300px] overflow-y-auto font-mono text-xs">
              {comparison.extractedTextDifference}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
