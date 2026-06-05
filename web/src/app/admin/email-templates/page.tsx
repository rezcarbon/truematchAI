'use client';

import { useState } from 'react';
import { Save, Eye, Plus, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/shared/AppShell';
import { useToast } from '@/components/providers/ToastProvider';

interface EmailTemplate {
  id: string;
  name: string;
  type: string;
  subject: string;
  body: string;
  variables: string[];
  createdAt: string;
  updatedAt: string;
}

const DEFAULT_TEMPLATES = [
  {
    type: 'interview_scheduled',
    name: 'Interview Scheduled',
    subject: 'Interview Scheduled for {candidate_name}',
    body: `Dear {recruiter_name},

We're pleased to confirm that an interview has been scheduled.

Candidate: {candidate_name}
Position: {position_title}
Date & Time: {scheduled_at}
Location/Platform: {meeting_platform}
Meeting Link: {meeting_link}

Please confirm your attendance by clicking the link below:
{action_url}

If you have any questions, please reply to this email.

Best regards,
TrueMatch Team`,
  },
  {
    type: 'scorecard_request',
    name: 'Scorecard Request',
    subject: 'Scorecard Needed for {candidate_name}',
    body: `Dear {interviewer_name},

Please complete the interview scorecard for:

Candidate: {candidate_name}
Position: {position_title}
Interview Date: {interview_date}

Your feedback is important. Please complete the scorecard here:
{action_url}

Thank you for your time.

Best regards,
TrueMatch Team`,
  },
  {
    type: 'candidate_advanced',
    name: 'Candidate Advanced',
    subject: '{candidate_name} Advanced to {new_stage}',
    body: `Dear {recruiter_name},

Good news! A candidate has advanced in the pipeline:

Candidate: {candidate_name}
Position: {position_title}
Previous Stage: {old_stage}
New Stage: {new_stage}
Date: {stage_date}

View candidate profile:
{action_url}

Next steps: Review the candidate's materials and schedule next interview.

Best regards,
TrueMatch Team`,
  },
];

export default function EmailTemplatesPage() {
  const { addToast } = useToast();
  const [templates, setTemplates] = useState<EmailTemplate[]>(
    DEFAULT_TEMPLATES.map((t, i) => ({
      id: `default-${i}`,
      name: t.name,
      type: t.type,
      subject: t.subject,
      body: t.body,
      variables: extractVariables(t.subject + '\n' + t.body),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }))
  );

  const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate | null>(
    templates[0]
  );
  const [editMode, setEditMode] = useState(false);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);

  function extractVariables(text: string): string[] {
    const regex = /\{([^}]+)\}/g;
    const matches = text.matchAll(regex);
    return Array.from(matches)
      .map((m) => m[1])
      .filter((v, i, arr) => arr.indexOf(v) === i); // Deduplicate
  }

  const handleSave = async () => {
    if (!selectedTemplate) return;

    try {
      // In production, this would save to backend
      const variables = extractVariables(
        selectedTemplate.subject + '\n' + selectedTemplate.body
      );

      setTemplates(
        templates.map((t) =>
          t.id === selectedTemplate.id
            ? {
                ...selectedTemplate,
                variables,
                updatedAt: new Date().toISOString(),
              }
            : t
        )
      );

      setSelectedTemplate({
        ...selectedTemplate,
        variables,
        updatedAt: new Date().toISOString(),
      });

      addToast('Template saved successfully', 'success');
    } catch (err) {
      addToast('Failed to save template', 'error');
    }
  };

  const handleDelete = (id: string) => {
    if (templates.length === 1) {
      addToast('Cannot delete the last template', 'error');
      return;
    }

    setTemplates(templates.filter((t) => t.id !== id));
    setSelectedTemplate(
      selectedTemplate?.id === id ? templates[0] : selectedTemplate
    );
    addToast('Template deleted', 'success');
  };

  const handleCreateNew = () => {
    const newTemplate: EmailTemplate = {
      id: `custom-${Date.now()}`,
      name: 'New Template',
      type: 'custom',
      subject: '',
      body: '',
      variables: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    setTemplates([...templates, newTemplate]);
    setSelectedTemplate(newTemplate);
    setEditMode(true);
  };

  if (!selectedTemplate) {
    return null;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Email Templates"
        subtitle="Customize email notifications sent to your team"
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Template List */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Templates</CardTitle>
              <Button size="sm" onClick={handleCreateNew}>
                <Plus className="h-4 w-4 mr-1" /> New
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            {templates.map((template) => (
              <button
                key={template.id}
                onClick={() => {
                  setSelectedTemplate(template);
                  setEditMode(false);
                }}
                className={`w-full text-left p-3 rounded-lg transition-colors ${
                  selectedTemplate.id === template.id
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-gray-100'
                }`}
              >
                <p className="font-medium text-sm">{template.name}</p>
                <p className="text-xs text-muted-foreground">{template.type}</p>
              </button>
            ))}
          </CardContent>
        </Card>

        {/* Template Editor */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>{selectedTemplate.name}</CardTitle>
                <p className="text-xs text-muted-foreground mt-1">
                  {selectedTemplate.type}
                </p>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setIsPreviewOpen(!isPreviewOpen)}
                >
                  <Eye className="h-4 w-4 mr-1" /> Preview
                </Button>
                {editMode ? (
                  <>
                    <Button size="sm" onClick={handleSave}>
                      <Save className="h-4 w-4 mr-1" /> Save
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setEditMode(false)}
                    >
                      Cancel
                    </Button>
                  </>
                ) : (
                  <>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setEditMode(true)}
                    >
                      Edit
                    </Button>
                    {!selectedTemplate.id.startsWith('default-') && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDelete(selectedTemplate.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </>
                )}
              </div>
            </div>
          </CardHeader>

          <CardContent className="space-y-6">
            {editMode ? (
              <>
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Template Name
                  </label>
                  <input
                    type="text"
                    value={selectedTemplate.name}
                    onChange={(e) =>
                      setSelectedTemplate({
                        ...selectedTemplate,
                        name: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Subject Line
                  </label>
                  <input
                    type="text"
                    value={selectedTemplate.subject}
                    onChange={(e) =>
                      setSelectedTemplate({
                        ...selectedTemplate,
                        subject: e.target.value,
                      })
                    }
                    placeholder="Use {variable_name} for dynamic content"
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Email Body
                  </label>
                  <textarea
                    value={selectedTemplate.body}
                    onChange={(e) =>
                      setSelectedTemplate({
                        ...selectedTemplate,
                        body: e.target.value,
                      })
                    }
                    placeholder="Use {variable_name} for dynamic content"
                    rows={12}
                    className="w-full px-3 py-2 border rounded-lg font-mono text-sm"
                  />
                </div>
              </>
            ) : (
              <>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Subject:
                  </p>
                  <p className="mt-1 text-sm">{selectedTemplate.subject}</p>
                </div>

                <div>
                  <p className="text-sm font-medium text-muted-foreground">
                    Body:
                  </p>
                  <p className="mt-1 text-sm whitespace-pre-wrap">
                    {selectedTemplate.body}
                  </p>
                </div>
              </>
            )}

            {/* Variables List */}
            {selectedTemplate.variables.length > 0 && (
              <div className="border-t pt-4">
                <p className="text-sm font-medium text-muted-foreground mb-2">
                  Available Variables:
                </p>
                <div className="grid grid-cols-2 gap-2">
                  {selectedTemplate.variables.map((variable) => (
                    <code
                      key={variable}
                      className="text-xs bg-gray-100 px-2 py-1 rounded"
                    >
                      {`{${variable}}`}
                    </code>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Preview Modal */}
      {isPreviewOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-full max-w-2xl max-h-96 overflow-y-auto">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Email Preview</CardTitle>
                <button
                  onClick={() => setIsPreviewOpen(false)}
                  className="text-muted-foreground hover:text-foreground"
                >
                  ✕
                </button>
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              <div>
                <p className="text-xs font-medium text-muted-foreground">
                  FROM:
                </p>
                <p className="text-sm">noreply@truematch.ai (TrueMatch)</p>
              </div>

              <div>
                <p className="text-xs font-medium text-muted-foreground">
                  SUBJECT:
                </p>
                <p className="text-sm font-semibold">
                  {selectedTemplate.subject}
                </p>
              </div>

              <div className="border-t pt-4">
                <p className="text-xs font-medium text-muted-foreground mb-2">
                  BODY:
                </p>
                <div className="bg-gray-50 p-4 rounded-lg text-sm whitespace-pre-wrap font-mono">
                  {selectedTemplate.body}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
