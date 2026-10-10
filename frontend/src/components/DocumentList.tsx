import type { DocumentInfo } from "../types/api";
import { formatBytes } from "../utils/files";

interface DocumentListProps {
  documents: DocumentInfo[];
  isRemoving: boolean;
  onRemove: (documentName: string) => void;
}

export function DocumentList({ documents, isRemoving, onRemove }: DocumentListProps) {
  if (documents.length === 0) {
    return <p className="empty-note">No documents in this session yet.</p>;
  }

  return (
    <ul className="document-list">
      {documents.map((document) => (
        <li key={document.name}>
          <span className="doc-name">{document.name}</span>
          <span className="doc-meta">
            {document.page_count} pages, {document.chunk_count} chunks,{" "}
            {formatBytes(document.size_bytes)}
          </span>
          <button
            type="button"
            className="remove-button"
            onClick={() => onRemove(document.name)}
            disabled={isRemoving}
          >
            Remove
          </button>
        </li>
      ))}
    </ul>
  );
}
