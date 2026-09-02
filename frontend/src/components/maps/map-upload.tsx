"use client";

import { useRef, useState } from "react";

import { useUploadMap } from "@/hooks/use-map";
import { ApiError } from "@/lib/api/client";

const DEFAULT_GRID_SIZE_PX = 50;

/**
 * Map upload form (backlog Fase 15 história 1, DM only): picks an image,
 * reads its natural pixel dimensions client-side (the backend has no image
 * inspection — `width_px`/`height_px` are trusted from the uploading
 * client, see `app.maps.models.SessionMap`'s docstring), and lets the DM
 * adjust the grid cell size in pixels before submitting.
 */
export function MapUpload({ sessionId }: { sessionId: string }) {
  const uploadMap = useUploadMap(sessionId);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [name, setName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [widthPx, setWidthPx] = useState(0);
  const [heightPx, setHeightPx] = useState(0);
  const [gridSizePx, setGridSizePx] = useState(DEFAULT_GRID_SIZE_PX);
  const [error, setError] = useState<string | null>(null);

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const picked = event.target.files?.[0];
    if (!picked) return;
    setError(null);
    setFile(picked);
    if (!name) setName(picked.name.replace(/\.[^./]+$/, ""));

    const url = URL.createObjectURL(picked);
    const img = new Image();
    img.onload = () => {
      setWidthPx(img.naturalWidth);
      setHeightPx(img.naturalHeight);
    };
    img.src = url;
    setPreviewUrl(url);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!file || !name.trim() || !widthPx || !heightPx || !gridSizePx) return;
    setError(null);
    try {
      await uploadMap.mutateAsync({
        fields: { name: name.trim(), width_px: widthPx, height_px: heightPx, grid_size_px: gridSizePx },
        file,
      });
      setName("");
      setFile(null);
      setPreviewUrl(null);
      setWidthPx(0);
      setHeightPx(0);
      setGridSizePx(DEFAULT_GRID_SIZE_PX);
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Não foi possível enviar o mapa.");
    }
  }

  const cellCols = gridSizePx > 0 ? Math.round(widthPx / gridSizePx) : 0;
  const cellRows = gridSizePx > 0 ? Math.round(heightPx / gridSizePx) : 0;

  return (
    <form onSubmit={handleSubmit} className="space-y-3 rounded-lg border border-border bg-card p-4">
      <h2 className="font-semibold">Subir mapa</h2>

      <div className="space-y-1">
        <label htmlFor="map-name" className="text-xs text-muted-foreground">
          Nome
        </label>
        <input
          id="map-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm"
        />
      </div>

      <div className="space-y-1">
        <label className="cursor-pointer text-sm text-muted-foreground underline hover:text-foreground">
          {file ? "Trocar imagem" : "Escolher imagem"}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            aria-label="Imagem do mapa"
            onChange={handleFileChange}
            className="sr-only"
          />
        </label>
      </div>

      {previewUrl ? (
        <div className="space-y-2">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={previewUrl}
            alt="Prévia do mapa"
            className="max-h-64 w-full rounded-md border border-border object-contain"
          />
          <div className="flex items-end gap-3">
            <div className="space-y-1">
              <label htmlFor="map-grid-size" className="text-xs text-muted-foreground">
                Pixels por célula (5ft)
              </label>
              <input
                id="map-grid-size"
                type="number"
                min={1}
                value={gridSizePx}
                onChange={(e) => setGridSizePx(Number(e.target.value))}
                className="w-24 rounded-md border border-input bg-background px-2 py-1.5 text-sm"
              />
            </div>
            <p className="text-xs text-muted-foreground">
              {widthPx}×{heightPx}px · grid {cellCols}×{cellRows} células
            </p>
          </div>
        </div>
      ) : null}

      {error ? (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={!file || !name.trim() || !gridSizePx || uploadMap.isPending}
        className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
      >
        Enviar mapa
      </button>
    </form>
  );
}
