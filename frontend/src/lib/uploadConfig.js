// Mirrors backend/app/config.py SUPPORTED_EXTENSIONS. Kept in one place
// so the dropzone's accept-list and validation message stay in sync with
// what the server will actually accept.
export const config = {
  supportedExtensions: [
    ".pdf", ".docx", ".txt", ".csv", ".xlsx", ".xls", ".json",
    ".png", ".jpg", ".jpeg",
  ],
};
