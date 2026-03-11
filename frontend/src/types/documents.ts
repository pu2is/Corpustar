export type DocFileType = "doc" | "docx" | "odt" | "txt";

export interface DocItem {
  id: string;
  filename: string;
  displayName: string;
  note: string;
  sourcePath: string;
  textPath: string;
  fileType: DocFileType;
  fileSize: number;
  createdAt: string;
  updatedAt: string;
}
