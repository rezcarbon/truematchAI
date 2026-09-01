'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Check, X } from 'lucide-react';

interface JDInlineEditorProps {
  initialText: string;
  onSave: (text: string) => Promise<void>;
  onCancel: () => void;
  placeholder?: string;
  maxLength?: number;
  minLength?: number;
  loading?: boolean;
  autoFocus?: boolean;
}

export function JDInlineEditor({
  initialText,
  onSave,
  onCancel,
  placeholder = 'Enter text here...',
  maxLength = 5000,
  minLength = 1,
  loading = false,
  autoFocus = true,
}: JDInlineEditorProps) {
  const [text, setText] = useState(initialText);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (autoFocus && textareaRef.current) {
      textareaRef.current.focus();
      // Move cursor to end
      textareaRef.current.setSelectionRange(text.length, text.length);
    }
  }, [autoFocus, text.length]);

  const handleSave = async () => {
    setError(null);

    // Validation
    if (text.trim().length < minLength) {
      setError(`Text must be at least ${minLength} character${minLength > 1 ? 's' : ''}`);
      return;
    }

    if (text.length > maxLength) {
      setError(`Text must not exceed ${maxLength} characters`);
      return;
    }

    if (text === initialText) {
      setError('No changes made');
      return;
    }

    try {
      setIsSaving(true);
      await onSave(text.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setText(initialText);
    setError(null);
    onCancel();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      handleCancel();
    } else if (e.ctrlKey && e.key === 'Enter') {
      handleSave();
    }
  };

  const isValid = text.trim().length >= minLength && text.length <= maxLength;
  const isChanged = text !== initialText;
  const charCount = text.length;
  const charPercentage = (charCount / maxLength) * 100;

  return (
    <div className="space-y-3">
      {/* Text Input */}
      <textarea
        ref={textareaRef}
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          setError(null);
        }}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={loading || isSaving}
        className="w-full rounded-lg border bg-background p-3 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50 disabled:cursor-not-allowed resize-vertical min-h-[120px]"
      />

      {/* Character Count */}
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">
            {charCount} / {maxLength} characters
          </span>
          <div className="w-24 h-1.5 bg-muted rounded-full overflow-hidden">
            <div
              className={`h-full transition-all ${
                charPercentage > 90
                  ? 'bg-red-500'
                  : charPercentage > 75
                  ? 'bg-amber-500'
                  : 'bg-primary'
              }`}
              style={{ width: `${Math.min(charPercentage, 100)}%` }}
            />
          </div>
        </div>
        {isChanged && <span className="text-amber-600">Unsaved changes</span>}
      </div>

      {/* Error Message */}
      {error && (
        <div className="text-sm text-destructive bg-destructive/10 rounded p-2">
          {error}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-2 justify-end">
        <Button
          variant="outline"
          size="sm"
          onClick={handleCancel}
          disabled={loading || isSaving}
        >
          <X className="h-4 w-4 mr-1" />
          Cancel
        </Button>
        <Button
          size="sm"
          onClick={handleSave}
          disabled={!isValid || !isChanged || loading || isSaving}
        >
          {isSaving ? (
            <>
              <span className="animate-spin mr-1">○</span>
              Saving...
            </>
          ) : (
            <>
              <Check className="h-4 w-4 mr-1" />
              Save Changes
            </>
          )}
        </Button>
      </div>

      {/* Help Text */}
      <p className="text-xs text-muted-foreground italic">
        Press Escape to cancel or Ctrl+Enter to save
      </p>
    </div>
  );
}
