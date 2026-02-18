"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import { getSpaceIdFromCookie } from "@/lib/spaces";
import { MOCKUP_CONFIGS, generateMockup } from "@/lib/mockups";
import type { SpaceConfig } from "@/lib/spaces";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

interface UploadedDesign {
  slug: string;
  name: string;
  image_url: string;
  status: string;
  products: { type: string; price: number }[];
}

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [tags, setTags] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [mockups, setMockups] = useState<Record<string, string>>({});
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadedDesign, setUploadedDesign] = useState<UploadedDesign | null>(null);
  const [isActivating, setIsActivating] = useState(false);
  const [spaceConfig, setSpaceConfig] = useState<SpaceConfig | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const spaceId = getSpaceIdFromCookie();
    fetch(`${API_URL}/spaces/${spaceId}`)
      .then((res) => (res.ok ? res.json() : null))
      .then(setSpaceConfig)
      .catch(() => {});
  }, []);

  // Generate mockups when preview changes
  useEffect(() => {
    if (!preview) {
      setMockups({});
      return;
    }
    MOCKUP_CONFIGS.forEach(async (config) => {
      try {
        const result = await generateMockup(preview, config);
        setMockups((prev) => ({ ...prev, [config.productType]: result }));
      } catch {
        // Template load failure — fallback handled in render
      }
    });
  }, [preview]);

  const handleFile = useCallback((f: File) => {
    if (!f.type.startsWith("image/")) {
      setError("Please select an image file (PNG, JPEG, or WebP)");
      return;
    }
    if (f.size > 10 * 1024 * 1024) {
      setError("File must be under 10 MB");
      return;
    }
    setError(null);
    setFile(f);
    setPreview(URL.createObjectURL(f));
    if (!name) {
      // Auto-fill name from filename
      const baseName = f.name.replace(/\.[^.]+$/, "").replace(/[-_]/g, " ");
      setName(baseName.charAt(0).toUpperCase() + baseName.slice(1));
    }
  }, [name]);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile) handleFile(droppedFile);
    },
    [handleFile]
  );

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !name) return;

    setIsUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("name", name);
      formData.append("space", getSpaceIdFromCookie());
      if (tags) formData.append("tags", tags);

      const response = await fetch(`${API_URL}/design/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Upload failed");
      }

      const design = await response.json();
      setUploadedDesign(design);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsUploading(false);
    }
  };

  const handleActivate = async () => {
    if (!uploadedDesign) return;
    setIsActivating(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/design/${uploadedDesign.slug}/activate`,
        { method: "POST" }
      );
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Failed to activate design");
      }
      setUploadedDesign({ ...uploadedDesign, status: "active" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsActivating(false);
    }
  };

  const handleDelete = async () => {
    if (!uploadedDesign) return;
    try {
      const response = await fetch(
        `${API_URL}/design/${uploadedDesign.slug}`,
        { method: "DELETE" }
      );
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Failed to delete design");
      }
      resetForm();
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    }
  };

  const resetForm = () => {
    setFile(null);
    setPreview(null);
    setName("");
    setTags("");
    setMockups({});
    setUploadedDesign(null);
    setError(null);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">Upload Swag</h1>
        <p className="text-muted-foreground mb-8">
          Upload your own design and preview it on{" "}
          {spaceConfig?.name || "rSwag"} merchandise. See how it looks on
          shirts, stickers, and prints before ordering.
        </p>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Left: Upload Form */}
          <div>
            <form onSubmit={handleUpload} className="space-y-6">
              <div>
                <label
                  htmlFor="name"
                  className="block text-sm font-medium mb-2"
                >
                  Design Name
                </label>
                <input
                  type="text"
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., My Custom Logo"
                  className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                  disabled={isUploading || !!uploadedDesign}
                />
              </div>

              {/* Drag & Drop Zone */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  Design Image
                </label>
                <div
                  onDragOver={(e) => {
                    e.preventDefault();
                    setIsDragging(true);
                  }}
                  onDragLeave={() => setIsDragging(false)}
                  onDrop={handleDrop}
                  onClick={() =>
                    !uploadedDesign && fileInputRef.current?.click()
                  }
                  className={`relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                    isDragging
                      ? "border-primary bg-primary/5"
                      : preview
                        ? "border-primary/50"
                        : "border-muted-foreground/30 hover:border-primary/50"
                  } ${uploadedDesign ? "pointer-events-none opacity-60" : ""}`}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/png,image/jpeg,image/webp"
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (f) handleFile(f);
                    }}
                    className="hidden"
                  />
                  {preview ? (
                    <div className="space-y-3">
                      <img
                        src={preview}
                        alt="Preview"
                        className="max-h-48 mx-auto rounded-md"
                      />
                      <p className="text-sm text-muted-foreground">
                        {file?.name} (
                        {((file?.size || 0) / 1024 / 1024).toFixed(1)} MB)
                      </p>
                      {!uploadedDesign && (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setFile(null);
                            setPreview(null);
                            setMockups({});
                          }}
                          className="text-sm text-red-500 hover:text-red-700"
                        >
                          Remove
                        </button>
                      )}
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <svg
                        className="mx-auto h-12 w-12 text-muted-foreground/50"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={1.5}
                          d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                        />
                      </svg>
                      <p className="text-muted-foreground">
                        Drag & drop your design here, or{" "}
                        <span className="text-primary font-medium">browse</span>
                      </p>
                      <p className="text-xs text-muted-foreground/70">
                        PNG, JPEG, or WebP. Max 10 MB. Min 500x500px.
                      </p>
                    </div>
                  )}
                </div>
              </div>

              <div>
                <label
                  htmlFor="tags"
                  className="block text-sm font-medium mb-2"
                >
                  Tags (optional)
                </label>
                <input
                  type="text"
                  id="tags"
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  placeholder="logo, custom, brand"
                  className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  disabled={isUploading || !!uploadedDesign}
                />
              </div>

              {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-md text-red-700">
                  {error}
                </div>
              )}

              {!uploadedDesign && (
                <button
                  type="submit"
                  disabled={isUploading || !file || !name}
                  className="w-full px-6 py-3 bg-primary text-primary-foreground rounded-md font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isUploading ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg
                        className="animate-spin h-5 w-5"
                        viewBox="0 0 24 24"
                        fill="none"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                      </svg>
                      Uploading...
                    </span>
                  ) : (
                    "Upload & Save Design"
                  )}
                </button>
              )}
            </form>

            {/* Post-upload actions */}
            {uploadedDesign && (
              <div className="mt-6 space-y-4">
                <div className="p-4 bg-muted/50 rounded-lg">
                  <p className="font-medium">{uploadedDesign.name}</p>
                  <p className="text-sm text-muted-foreground">
                    Status:{" "}
                    <span
                      className={
                        uploadedDesign.status === "active"
                          ? "text-green-600"
                          : "text-yellow-600"
                      }
                    >
                      {uploadedDesign.status}
                    </span>
                  </p>
                </div>

                <div className="flex gap-2">
                  {uploadedDesign.status === "draft" ? (
                    <>
                      <button
                        onClick={handleActivate}
                        disabled={isActivating}
                        className="flex-1 px-4 py-2 bg-green-600 text-white rounded-md font-medium hover:bg-green-700 transition-colors disabled:opacity-50"
                      >
                        {isActivating ? "Activating..." : "Add to Store"}
                      </button>
                      <button
                        onClick={handleDelete}
                        className="px-4 py-2 border border-red-300 text-red-600 rounded-md font-medium hover:bg-red-50 transition-colors"
                      >
                        Discard
                      </button>
                    </>
                  ) : (
                    <>
                      <Link
                        href={`/products/${uploadedDesign.slug}`}
                        className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-md font-medium hover:bg-primary/90 transition-colors text-center"
                      >
                        View in Store
                      </Link>
                      <button
                        onClick={resetForm}
                        className="px-4 py-2 border border-muted-foreground/30 text-muted-foreground rounded-md font-medium hover:bg-muted/50 transition-colors"
                      >
                        Upload Another
                      </button>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Right: Mockup Previews */}
          <div>
            <h2 className="text-lg font-semibold mb-4">Product Previews</h2>
            {preview ? (
              <div className="space-y-4">
                {MOCKUP_CONFIGS.map((config) => (
                  <div
                    key={config.productType}
                    className="border rounded-lg overflow-hidden"
                  >
                    <div className="aspect-square bg-muted/20 relative">
                      {mockups[config.productType] ? (
                        <img
                          src={mockups[config.productType]}
                          alt={`${config.label} preview`}
                          className="w-full h-full object-contain"
                        />
                      ) : (
                        <div className="flex items-center justify-center h-full">
                          <div className="animate-spin h-6 w-6 border-2 border-primary border-t-transparent rounded-full" />
                        </div>
                      )}
                    </div>
                    <div className="p-3 flex items-center justify-between">
                      <span className="font-medium">{config.label}</span>
                      <span className="text-muted-foreground">
                        from ${config.price.toFixed(2)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="aspect-square border-2 border-dashed rounded-lg flex items-center justify-center bg-muted/30">
                <p className="text-muted-foreground text-center px-8">
                  Upload a design to see product previews
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Tips */}
        <div className="mt-12 p-6 bg-muted/30 rounded-lg">
          <h3 className="font-semibold mb-3">Upload Tips</h3>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li>
              &bull; Use a high-resolution image (at least 2000x2000px for best
              print quality)
            </li>
            <li>
              &bull; PNG with transparency works best for stickers and shirts
            </li>
            <li>
              &bull; Keep important elements centered — edges may be cropped on
              some products
            </li>
            <li>
              &bull; Designs start as drafts — preview before adding to the
              store
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
