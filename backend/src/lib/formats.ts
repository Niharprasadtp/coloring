// Output options the buyer can pick. Keys are passed to process_image.py as
// --format values; keep in sync with the script and frontend/app/upload/[token]/formats.ts.
export const FORMATS = {
  dark: "Dark Numbered Version",
  light: "Light Numbered Version",
  palette: "Palette Numbered Version",
  contour: "Contour/Outline Version (Unnumbered)",
  palette_pdf: "Digital + Printable Color Palette (PDF)",
  procreate: "Color Palette for Procreate (.swatches)",
} as const;

export type FormatKey = keyof typeof FORMATS;

export function isFormatKey(value: string): value is FormatKey {
  return Object.hasOwn(FORMATS, value);
}

export interface OutputFile {
  file: string;
  label: string;
  format: FormatKey;
  size: number;
}
