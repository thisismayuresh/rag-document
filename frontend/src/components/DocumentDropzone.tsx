import { useRef, useState } from "react";
import type { ChangeEvent, DragEvent } from "react";

import { ErrorBanner } from "./ErrorBanner";
import { validateUpload } from "../utils/files";

interface DocumentDropzoneProps {
  maxUploadBytes: number;
  isUploading: boolean;
  isDisabled: boolean;
  disabledReason: string;
  onFileAccepted: (file: File) => void;
}

export function DocumentDropzone({
  maxUploadBytes,
  isUploading,
  isDisabled,
  disabledReason,
  onFileAccepted,
}: DocumentDropzoneProps) {
  const [isOver, setIsOver] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFiles(files: FileList | null): void {
    if (!files || files.length === 0) {
      return;
    }

    const file = files[0];
    const problem = validateUpload(file, maxUploadBytes);
    if (problem) {
      setLocalError(problem);
      return;
    }

    setLocalError(null);
    onFileAccepted(file);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>): void {
    event.preventDefault();
    setIsOver(false);
    if (isDisabled) {
      return;
    }
    handleFiles(event.dataTransfer.files);
  }

  function handleDragOver(event: DragEvent<HTMLDivElement>): void {
    event.preventDefault();
    setIsOver(true);
  }

  function handleInputChange(event: ChangeEvent<HTMLInputElement>): void {
    handleFiles(event.target.files);
    // Reset so choosing the same file twice still fires a change event.
    event.target.value = "";
  }

  function openFilePicker(): void {
    inputRef.current?.click();
  }

  const dropzoneClass = isOver ? "dropzone is-over" : "dropzone";
  const maxUploadMb = Math.round(maxUploadBytes / (1024 * 1024));

  return (
    <div>
      <div
        className={dropzoneClass}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={() => setIsOver(false)}
      >
        {isDisabled ? (
          <span>{disabledReason}</span>
        ) : (
          <>
            <span>Drag a PDF here, or</span>
            <button type="button" className="pick-link" onClick={openFilePicker}>
              choose a file
            </button>
          </>
        )}
        <span className="hint">PDF, up to {maxUploadMb} MB</span>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleInputChange}
          disabled={isDisabled}
        />
      </div>

      {isUploading && (
        <p className="empty-note">Uploading and indexing... this can take a while for large PDFs.</p>
      )}

      {localError && (
        <ErrorBanner message={localError} onDismiss={() => setLocalError(null)} />
      )}
    </div>
  );
}
