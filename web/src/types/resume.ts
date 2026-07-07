/**
 * Resume and versioning type definitions
 */

export type ResumeUploadMethod = 'drag-drop' | 'file-click' | 'paste' | 'linkedin';
export type ResumeFormat = 'pdf' | 'docx' | 'doc' | 'txt';
export type ResumeStatus = 'processing' | 'completed' | 'failed';

export interface ResumeVersion {
  id: string;
  resumeId: string;
  version: number;
  fileName: string;
  format: ResumeFormat;
  fileSize: number;
  uploadMethod: ResumeUploadMethod;
  status: ResumeStatus;
  extractedText: string;
  skills: string[];
  experience_years: number;
  summary: string;
  uploadedAt: string;
  annotation?: string;
  errorMessage?: string;
}

export interface Resume {
  id: string;
  userId: string;
  currentVersionId: string;
  versions: ResumeVersion[];
  createdAt: string;
  updatedAt: string;
  assessmentCount: number;
}

export interface ResumeUploadRequest {
  file?: File;
  pastedContent?: string;
  linkedInUrl?: string;
  uploadMethod: ResumeUploadMethod;
}

export interface ResumeUploadResponse {
  id: string;
  versionId: string;
  version: number;
  status: ResumeStatus;
  fileName?: string;
  resumeId: string;
}

export interface VersionComparison {
  versionA: ResumeVersion;
  versionB: ResumeVersion;
  skillsAdded: string[];
  skillsRemoved: string[];
  experienceYearsDifference: number;
  summaryDifference: string;
  extractedTextDifference: string;
}

export interface ResumeAnnotation {
  versionId: string;
  annotation: string;
  createdAt: string;
  updatedAt: string;
}
