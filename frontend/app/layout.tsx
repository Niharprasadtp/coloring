import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Upload your photo",
  description: "Upload the photo for your color-by-number order.",
  robots: { index: false },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-stone-50 text-stone-900 antialiased">{children}</body>
    </html>
  );
}
