// Page-number citations for an assistant message, shown as a row of small
// chips below the answer. Pages are grouped per document and deduplicated.

import type { Citation } from "../types/api";

export interface MessageCitationsProps {
  citations: Citation[];
}

interface DocumentPages {
  name: string;
  pages: number[];
}

function groupByDocument(citations: Citation[]): DocumentPages[] {
  const groups: DocumentPages[] = [];
  for (const citation of citations) {
    const existing = groups.find((group) => group.name === citation.document_name);
    if (existing) {
      if (!existing.pages.includes(citation.page_number)) {
        existing.pages.push(citation.page_number);
      }
    } else {
      groups.push({ name: citation.document_name, pages: [citation.page_number] });
    }
  }
  for (const group of groups) {
    group.pages.sort((a, b) => a - b);
  }
  return groups;
}

export function MessageCitations({ citations }: MessageCitationsProps) {
  if (!citations || citations.length === 0) {
    return null;
  }

  const groups = groupByDocument(citations);

  return (
    <div className="message-citations">
      <span className="citations-label">Sources</span>
      {groups.map((group) => (
        <span key={group.name} className="citation-chip">
          <span className="citation-doc">{group.name}</span>
          <span className="citation-pages">
            p. {group.pages.join(", ")}
          </span>
        </span>
      ))}
    </div>
  );
}
