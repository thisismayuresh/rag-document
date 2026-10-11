import type { HealthInfo, SessionInfo } from "../types/api";
import { DocumentDropzone } from "./DocumentDropzone";
import { DocumentList } from "./DocumentList";

interface SidebarProps {
  session: SessionInfo | null;
  health: HealthInfo | null;
  maxUploadBytes: number;
  isUploading: boolean;
  isRemoving: boolean;
  onFileAccepted: (file: File) => void;
  onRemoveDocument: (documentName: string) => void;
}

export function Sidebar({
  session,
  health,
  maxUploadBytes,
  isUploading,
  isRemoving,
  onFileAccepted,
  onRemoveDocument,
}: SidebarProps) {
  const documentCount = session?.documents.length ?? 0;
  const maxDocuments = session?.max_documents ?? 0;
  const isFull = session !== null && documentCount >= maxDocuments;

  let disabledReason = "";
  if (session === null) {
    disabledReason = "Waiting for a session...";
  } else if (isUploading) {
    disabledReason = "Waiting for the current upload to finish...";
  } else if (isFull) {
    disabledReason = `A session holds at most ${maxDocuments} documents. Remove one to add another.`;
  }

  return (
    <aside className="sidebar">
      <section>
        <h2>Documents ({documentCount}/{maxDocuments || "?"})</h2>
        <DocumentDropzone
          maxUploadBytes={maxUploadBytes}
          isUploading={isUploading}
          isDisabled={disabledReason !== ""}
          disabledReason={disabledReason}
          onFileAccepted={onFileAccepted}
        />
      </section>

      <section>
        <DocumentList
          documents={session?.documents ?? []}
          isRemoving={isRemoving}
          onRemove={onRemoveDocument}
        />
      </section>

      {health && (
        <section>
          <h2>Models</h2>
          <dl className="model-info">
            <dt>Chat</dt>
            <dd>{health.chat_model}</dd>
            <dt>Embeddings</dt>
            <dd>{health.embedding_model}</dd>
          </dl>
        </section>
      )}
    </aside>
  );
}
