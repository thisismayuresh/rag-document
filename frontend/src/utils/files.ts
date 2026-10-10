// File checks and display helpers shared by the upload UI.

export function isPdf(file: File): boolean {
  const hasPdfExtension = file.name.toLowerCase().endsWith(".pdf");
  const hasPdfType = file.type === "application/pdf";
  return hasPdfType || hasPdfExtension;
}

export function exceedsSizeLimit(file: File, maxBytes: number): boolean {
  return file.size > maxBytes;
}

export function formatBytes(sizeBytes: number): string {
  if (sizeBytes < 1024) {
    return `${sizeBytes} B`;
  }
  if (sizeBytes < 1024 * 1024) {
    return `${Math.round(sizeBytes / 1024)} KB`;
  }
  return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function validateUpload(file: File, maxBytes: number): string | null {
  if (!isPdf(file)) {
    return `'${file.name}' is not a PDF. Only PDF files can be uploaded.`;
  }
  if (exceedsSizeLimit(file, maxBytes)) {
    return `'${file.name}' is ${formatBytes(file.size)}. The limit is ${formatBytes(maxBytes)}.`;
  }
  return null;
}
