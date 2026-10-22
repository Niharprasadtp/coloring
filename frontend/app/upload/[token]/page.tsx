"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { ALL_OPTIONS, DIGITAL_OPTIONS, STYLE_OPTIONS, type FormatKey, type FormatOption } from "./formats";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const MAX_BYTES = 15 * 1024 * 1024;
const ACCEPTED = ["image/jpeg", "image/png", "image/webp"];
const POLL_MS = 2000;

type OrderStatus = "AWAITING_UPLOAD" | "PROCESSING" | "COMPLETED" | "FAILED";

interface OutputFile {
  label: string;
  format: FormatKey;
  size: number;
  name: string;
  url: string;
}

interface StatusResponse {
  status: OrderStatus;
  error: string | null;
  formats: FormatKey[];
  progress: number;
  progressMessage: string | null;
  files: OutputFile[];
}

type View =
  | { kind: "loading" }
  | { kind: "invalid" }
  | { kind: "form"; error?: string }
  | { kind: "uploading"; percent: number }
  | { kind: "processing"; progress: number; message: string; formats: FormatKey[] }
  | { kind: "done"; files: OutputFile[] };

function viewFor(s: StatusResponse): View {
  switch (s.status) {
    case "COMPLETED":
      return { kind: "done", files: s.files };
    case "PROCESSING":
      return {
        kind: "processing",
        progress: s.progress,
        message: s.progressMessage ?? "Working on it",
        formats: s.formats,
      };
    case "FAILED":
      return { kind: "form", error: s.error ?? "Something went wrong. Please try again." };
    default:
      return { kind: "form" };
  }
}

// fetch() can't report upload progress, so the upload itself uses XHR.
function uploadWithProgress(
  url: string,
  body: FormData,
  onProgress: (percent: number) => void,
): Promise<{ status: number; data: Record<string, unknown> }> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", url);
    xhr.upload.onprogress = (e) => e.lengthComputable && onProgress(Math.round((e.loaded / e.total) * 100));
    xhr.onload = () => {
      let data = {};
      try {
        data = JSON.parse(xhr.responseText);
      } catch {}
      resolve({ status: xhr.status, data });
    };
    xhr.onerror = () => reject(new Error("network error"));
    xhr.send(body);
  });
}

function formatSize(bytes: number): string {
  return bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export default function UploadPage() {
  const { token } = useParams<{ token: string }>();
  const [view, setView] = useState<View>({ kind: "loading" });
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<FormatKey>>(new Set());
  const [dragging, setDragging] = useState(false);
  const pollTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const fetchStatus = useCallback(async (): Promise<View> => {
    const res = await fetch(`${API_URL}/orders/${encodeURIComponent(token)}`, { cache: "no-store" });
    if (res.status === 404) return { kind: "invalid" };
    if (!res.ok) throw new Error(`Status check failed (${res.status})`);
    return viewFor(await res.json());
  }, [token]);

  // Keep polling while the backend is running the Python job.
  const poll = useCallback(() => {
    pollTimer.current = setTimeout(async () => {
      try {
        const next = await fetchStatus();
        setView(next);
        if (next.kind === "processing") poll();
      } catch {
        poll(); // transient network error: keep trying
      }
    }, POLL_MS);
  }, [fetchStatus]);

  // Initial load: the buyer may be returning to a link that's already done or in progress.
  useEffect(() => {
    let cancelled = false;
    fetchStatus()
      .then((next) => {
        if (cancelled) return;
        setView(next);
        if (next.kind === "processing") poll();
      })
      .catch(() => !cancelled && setView({ kind: "form", error: "Couldn't reach the server. Please refresh." }));
    return () => {
      cancelled = true;
      if (pollTimer.current) clearTimeout(pollTimer.current);
    };
  }, [fetchStatus, poll]);

  useEffect(() => {
    if (!file) return setPreview(null);
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  function pickFile(picked: File | null | undefined) {
    if (!picked) return;
    if (!ACCEPTED.includes(picked.type)) {
      return setView({ kind: "form", error: "Please choose a JPG, PNG or WebP image." });
    }
    if (picked.size > MAX_BYTES) {
      return setView({ kind: "form", error: "That image is larger than 15 MB. Please choose a smaller one." });
    }
    setFile(picked);
    setView({ kind: "form" });
  }

  function toggle(key: FormatKey) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  function toggleGroup(options: FormatOption[]) {
    setSelected((prev) => {
      const next = new Set(prev);
      const allOn = options.every((o) => next.has(o.key));
      for (const o of options) {
        if (allOn) next.delete(o.key);
        else next.add(o.key);
      }
      return next;
    });
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file || selected.size === 0) return;
    setView({ kind: "uploading", percent: 0 });

    const body = new FormData();
    // Options first, so the server has them before the (large) image arrives.
    for (const key of selected) body.append("formats", key);
    body.append("image", file);

    try {
      const { status, data } = await uploadWithProgress(
        `${API_URL}/upload/${encodeURIComponent(token)}`,
        body,
        (percent) => setView({ kind: "uploading", percent }),
      );
      if (status === 202) {
        setView({ kind: "processing", progress: 0, message: "Starting", formats: [...selected] });
        return poll();
      }
      if (status === 409) {
        // Already uploaded (e.g. in another tab): show whatever state it's in.
        const next = await fetchStatus();
        setView(next);
        if (next.kind === "processing") poll();
        return;
      }
      const message = (data.message ?? data.error) as string | undefined;
      setView({ kind: "form", error: message ?? "Upload failed. Please try again." });
    } catch {
      setView({ kind: "form", error: "Upload failed. Check your connection and try again." });
    }
  }

  const busy = view.kind === "uploading";

  return (
    <main className="mx-auto max-w-2xl px-4 py-10 sm:py-14">
      <header className="mb-8 text-center">
        <p className="text-sm font-medium tracking-wide text-rose-600 uppercase">Custom color-by-number</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">Let&apos;s make your coloring page</h1>
      </header>

      {view.kind === "loading" && <Card><p className="text-stone-500">Loading your order…</p></Card>}

      {view.kind === "invalid" && (
        <Card>
          <p className="text-stone-600">
            This upload link isn&apos;t valid. Please check the link in your email, or message the shop on Etsy.
          </p>
        </Card>
      )}

      {(view.kind === "form" || view.kind === "uploading") && (
        <form onSubmit={onSubmit} className="space-y-6">
          <Card>
            <SectionTitle step={1} title="Upload your photo" />
            <div
              role="button"
              tabIndex={0}
              aria-label="Choose or drop a photo"
              onClick={() => !busy && inputRef.current?.click()}
              onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && !busy && inputRef.current?.click()}
              onDragOver={(e) => {
                e.preventDefault();
                if (!busy) setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragging(false);
                if (!busy) pickFile(e.dataTransfer.files[0]);
              }}
              className={`mt-4 flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 text-center transition focus:ring-2 focus:ring-rose-400 focus:outline-none ${
                dragging ? "border-rose-500 bg-rose-50" : "border-stone-300 hover:border-stone-400 hover:bg-stone-50"
              }`}
            >
              {preview ? (
                <>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={preview} alt="Your selected photo" className="max-h-64 rounded-lg object-contain" />
                  <p className="mt-3 max-w-full truncate text-sm text-stone-500">
                    {file?.name} · <span className="text-rose-600 underline">change</span>
                  </p>
                </>
              ) : (
                <>
                  <UploadIcon />
                  <p className="mt-3 font-medium">
                    {dragging ? "Drop it here" : "Drag & drop your photo, or click to browse"}
                  </p>
                  <p className="mt-1 text-sm text-stone-500">JPG, PNG or WebP, up to 15 MB</p>
                </>
              )}
              <input
                ref={inputRef}
                type="file"
                accept={ACCEPTED.join(",")}
                onChange={(e) => pickFile(e.target.files?.[0])}
                disabled={busy}
                className="hidden"
              />
            </div>
          </Card>

          <Card>
            <SectionTitle step={2} title="Select your styles & formats" />
            <p className="mt-1 text-sm text-stone-500">Choose as many as you like.</p>

            <OptionGroup
              title="Coloring page styles"
              options={STYLE_OPTIONS}
              selected={selected}
              disabled={busy}
              onToggle={toggle}
              onToggleAll={() => toggleGroup(STYLE_OPTIONS)}
            />
            <OptionGroup
              title="Digital extras"
              options={DIGITAL_OPTIONS}
              selected={selected}
              disabled={busy}
              onToggle={toggle}
              onToggleAll={() => toggleGroup(DIGITAL_OPTIONS)}
            />
          </Card>

          {view.kind === "form" && view.error && (
            <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
              {view.error}
            </p>
          )}

          <div className="space-y-2">
            <button
              type="submit"
              disabled={!file || selected.size === 0 || busy}
              className="relative w-full overflow-hidden rounded-xl bg-stone-900 px-4 py-3.5 font-medium text-white transition-colors hover:bg-stone-700 disabled:cursor-not-allowed disabled:bg-stone-300"
            >
              {busy && (
                <span
                  className="absolute inset-y-0 left-0 bg-rose-600 transition-[width]"
                  style={{ width: `${view.percent}%` }}
                />
              )}
              <span className="relative">
                {busy
                  ? `Uploading… ${view.percent}%`
                  : `Create my files${selected.size ? ` (${selected.size} selected)` : ""}`}
              </span>
            </button>
            {!busy && (!file || selected.size === 0) && (
              <p className="text-center text-sm text-stone-500">
                {!file ? "Add a photo" : "Pick at least one style or format"} to continue.
              </p>
            )}
          </div>
        </form>
      )}

      {view.kind === "processing" && <ProcessingView {...view} />}
      {view.kind === "done" && <FilesView files={view.files} />}
    </main>
  );
}

function Card({ children }: { children: React.ReactNode }) {
  return <section className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm sm:p-6">{children}</section>;
}

function SectionTitle({ step, title }: { step: number; title: string }) {
  return (
    <h2 className="flex items-center gap-3 text-lg font-semibold">
      <span className="flex h-7 w-7 items-center justify-center rounded-full bg-rose-100 text-sm text-rose-700">
        {step}
      </span>
      {title}
    </h2>
  );
}

function OptionGroup(props: {
  title: string;
  options: FormatOption[];
  selected: Set<FormatKey>;
  disabled: boolean;
  onToggle: (key: FormatKey) => void;
  onToggleAll: () => void;
}) {
  const allOn = props.options.every((o) => props.selected.has(o.key));
  return (
    <fieldset className="mt-5" disabled={props.disabled}>
      <div className="mb-2 flex items-center justify-between">
        <legend className="text-sm font-medium text-stone-700">{props.title}</legend>
        <button type="button" onClick={props.onToggleAll} className="text-sm text-rose-600 hover:underline">
          {allOn ? "Clear" : "Select all"}
        </button>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {props.options.map((o) => {
          const on = props.selected.has(o.key);
          return (
            <label
              key={o.key}
              className={`flex cursor-pointer items-start gap-3 rounded-xl border p-3 transition ${
                on ? "border-rose-500 bg-rose-50 ring-1 ring-rose-500" : "border-stone-200 hover:border-stone-300"
              }`}
            >
              <input type="checkbox" checked={on} onChange={() => props.onToggle(o.key)} className="sr-only" />
              <StyleIcon kind={o.key} />
              <span className="min-w-0 flex-1">
                <span className="block text-sm leading-snug font-medium">{o.label}</span>
                <span className="mt-0.5 block text-xs text-stone-500">{o.description}</span>
              </span>
              <span
                aria-hidden
                className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-md border ${
                  on ? "border-rose-600 bg-rose-600 text-white" : "border-stone-300 bg-white"
                }`}
              >
                {on && (
                  <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M3.5 8.5l3 3 6-7" />
                  </svg>
                )}
              </span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}

const SWATCH = ["#e76f51", "#f4a261", "#e9c46a", "#2a9d8f", "#264653", "#8ab17d"];

// Small illustration of each option, drawn inline so there are no image assets.
function StyleIcon({ kind }: { kind: FormatKey }) {
  const box = "h-12 w-12 shrink-0 overflow-hidden rounded-lg border border-stone-200";
  const shapes = (stroke: string, numbers?: string) => (
    <>
      <path d="M4 34 L16 14 L28 34 Z" fill="none" stroke={stroke} strokeWidth="1.5" />
      <circle cx="33" cy="16" r="8" fill="none" stroke={stroke} strokeWidth="1.5" />
      {numbers && (
        <g fill={numbers} fontSize="8" fontFamily="sans-serif" textAnchor="middle">
          <text x="16" y="30">1</text>
          <text x="33" y="19">2</text>
          <text x="38" y="38">3</text>
        </g>
      )}
    </>
  );
  switch (kind) {
    case "dark":
      return <svg viewBox="0 0 44 44" className={`${box} bg-white`}>{shapes("#1c1917", "#1c1917")}</svg>;
    case "light":
      return <svg viewBox="0 0 44 44" className={`${box} bg-white`}>{shapes("#d6d3d1", "#a8a29e")}</svg>;
    case "palette":
      return (
        <svg viewBox="0 0 44 44" className={`${box} bg-white`}>
          {shapes("#44403c", "#44403c")}
          {SWATCH.slice(0, 4).map((c, i) => <rect key={c} x={2 + i * 10} y="38" width="9" height="5" fill={c} />)}
        </svg>
      );
    case "contour":
      return <svg viewBox="0 0 44 44" className={`${box} bg-white`}>{shapes("#44403c")}</svg>;
    case "palette_pdf":
      return (
        <svg viewBox="0 0 44 44" className={`${box} bg-white`}>
          {SWATCH.map((c, i) => <circle key={c} cx={10 + (i % 3) * 12} cy={14 + Math.floor(i / 3) * 16} r="5" fill={c} />)}
        </svg>
      );
    case "procreate":
      return (
        <svg viewBox="0 0 44 44" className={`${box} bg-stone-900`}>
          {SWATCH.map((c, i) => (
            <rect key={c} x={6 + (i % 3) * 11} y={10 + Math.floor(i / 3) * 13} width="9" height="9" rx="2" fill={c} />
          ))}
        </svg>
      );
  }
}

function ProcessingView({ progress, message, formats }: { progress: number; message: string; formats: FormatKey[] }) {
  const pct = Math.max(3, Math.min(100, progress));
  return (
    <Card>
      <div className="flex flex-col items-center py-4 text-center" aria-live="polite">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-rose-100 border-t-rose-600" />
        <h2 className="mt-5 text-lg font-semibold">Creating your files</h2>
        <p className="mt-1 text-sm text-stone-500">{message}…</p>

        <div
          className="mt-5 h-2.5 w-full overflow-hidden rounded-full bg-stone-100"
          role="progressbar"
          aria-valuenow={progress}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div className="h-full rounded-full bg-rose-600 transition-[width] duration-700" style={{ width: `${pct}%` }} />
        </div>
        <p className="mt-2 text-xs text-stone-500">{progress}%</p>
      </div>

      {formats.length > 0 && (
        <div className="mt-4 border-t border-stone-100 pt-4">
          <p className="text-sm font-medium text-stone-700">In your order</p>
          <ul className="mt-2 flex flex-wrap gap-2">
            {formats.map((k) => (
              <li key={k} className="rounded-full bg-stone-100 px-3 py-1 text-xs text-stone-600">
                {ALL_OPTIONS.find((o) => o.key === k)?.label ?? k}
              </li>
            ))}
          </ul>
        </div>
      )}
      <p className="mt-5 text-center text-xs text-stone-500">
        This can take a few minutes. You can leave this page open or come back to your link later.
      </p>
    </Card>
  );
}

function FilesView({ files }: { files: OutputFile[] }) {
  return (
    <Card>
      <div className="text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
          <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M5 12.5l4.5 4.5L19 7.5" />
          </svg>
        </div>
        <h2 className="mt-4 text-lg font-semibold">Your files are ready</h2>
        <p className="mt-1 text-sm text-stone-500">Download each file below. This link keeps working, so you can come back.</p>
      </div>

      <ul className="mt-6 divide-y divide-stone-100 rounded-xl border border-stone-200">
        {files.map((f) => (
          <li key={f.name} className="flex items-center gap-3 p-3">
            <StyleIcon kind={f.format} />
            <div className="min-w-0 flex-1">
              <p className="text-sm leading-snug font-medium">{f.label}</p>
              <p className="text-xs text-stone-500">
                {f.name.split(".").pop()?.toUpperCase()} · {formatSize(f.size)}
              </p>
            </div>
            <a
              href={f.url}
              className="shrink-0 rounded-lg bg-stone-900 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-stone-700"
            >
              Download
            </a>
          </li>
        ))}
      </ul>
    </Card>
  );
}

function UploadIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-10 w-10 text-stone-400" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M12 16V4m0 0l-4 4m4-4l4 4M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
    </svg>
  );
}
