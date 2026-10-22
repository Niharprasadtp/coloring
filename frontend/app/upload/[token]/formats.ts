// Keys must match backend/src/lib/formats.ts.
export type FormatKey = "dark" | "light" | "palette" | "contour" | "palette_pdf" | "procreate";

export interface FormatOption {
  key: FormatKey;
  label: string;
  description: string;
}

export const STYLE_OPTIONS: FormatOption[] = [
  { key: "dark", label: "Dark Numbered Version", description: "Bold dark lines and numbers, easy to read" },
  { key: "light", label: "Light Numbered Version", description: "Faint lines that disappear under paint" },
  { key: "palette", label: "Palette Numbered Version", description: "Numbered page with the color key printed on it" },
  {
    key: "contour",
    label: "Contour/Outline Version (Unnumbered)",
    description: "Outlines only, for free-style coloring",
  },
];

export const DIGITAL_OPTIONS: FormatOption[] = [
  {
    key: "palette_pdf",
    label: "Digital + Printable Color Palette (PDF)",
    description: "Every color with its number and hex code",
  },
  {
    key: "procreate",
    label: "Color Palette for Procreate (.swatches)",
    description: "Import straight into Procreate on iPad",
  },
];

export const ALL_OPTIONS = [...STYLE_OPTIONS, ...DIGITAL_OPTIONS];
