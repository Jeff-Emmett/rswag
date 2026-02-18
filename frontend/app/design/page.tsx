"use client";

import { useState } from "react";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

interface GeneratedDesign {
  slug: string;
  name: string;
  image_url: string;
  status: string;
}

export default function DesignPage() {
  const [name, setName] = useState("");
  const [concept, setConcept] = useState("");
  const [tags, setTags] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generatedDesign, setGeneratedDesign] = useState<GeneratedDesign | null>(null);
  const [isActivating, setIsActivating] = useState(false);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsGenerating(true);
    setError(null);
    setGeneratedDesign(null);

    try {
      const response = await fetch(`${API_URL}/design/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name,
          concept,
          tags: tags.split(",").map((t) => t.trim()).filter(Boolean),
          product_type: "sticker",
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Failed to generate design");
      }

      const design = await response.json();
      setGeneratedDesign(design);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleActivate = async () => {
    if (!generatedDesign) return;

    setIsActivating(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/design/${generatedDesign.slug}/activate`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Failed to activate design");
      }

      setGeneratedDesign({ ...generatedDesign, status: "active" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsActivating(false);
    }
  };

  const handleDelete = async () => {
    if (!generatedDesign) return;

    try {
      const response = await fetch(
        `${API_URL}/design/${generatedDesign.slug}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Failed to delete design");
      }

      setGeneratedDesign(null);
      setName("");
      setConcept("");
      setTags("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">Design Swag</h1>
        <p className="text-muted-foreground mb-8">
          Create custom rSpace merchandise using AI. Describe your vision and
          we&apos;ll generate a unique design.
        </p>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Form */}
          <div>
            <form onSubmit={handleGenerate} className="space-y-6">
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
                  placeholder="e.g., Commons Builder"
                  className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                  disabled={isGenerating}
                />
              </div>

              <div>
                <label
                  htmlFor="concept"
                  className="block text-sm font-medium mb-2"
                >
                  Design Concept
                </label>
                <textarea
                  id="concept"
                  value={concept}
                  onChange={(e) => setConcept(e.target.value)}
                  placeholder="Describe your design idea... e.g., Interconnected nodes forming a spatial web, symbolizing collaborative infrastructure for the commons. Include the phrase 'BUILD TOGETHER' in bold letters."
                  rows={4}
                  className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                  required
                  disabled={isGenerating}
                />
              </div>

              <div>
                <label
                  htmlFor="tags"
                  className="block text-sm font-medium mb-2"
                >
                  Tags (comma-separated)
                </label>
                <input
                  type="text"
                  id="tags"
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  placeholder="rspace, commons, spatial, collaboration"
                  className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  disabled={isGenerating}
                />
              </div>

              {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-md text-red-700">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={isGenerating || !name || !concept}
                className="w-full px-6 py-3 bg-primary text-primary-foreground rounded-md font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isGenerating ? (
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
                    Generating Design...
                  </span>
                ) : (
                  "Generate Design"
                )}
              </button>
            </form>
          </div>

          {/* Preview */}
          <div>
            <h2 className="text-lg font-semibold mb-4">Preview</h2>
            <div className="aspect-square border-2 border-dashed rounded-lg flex items-center justify-center bg-muted/30">
              {generatedDesign ? (
                <img
                  src={`${API_URL.replace("/api", "")}${generatedDesign.image_url}`}
                  alt={generatedDesign.name}
                  className="w-full h-full object-contain rounded-lg"
                />
              ) : isGenerating ? (
                <div className="text-center text-muted-foreground">
                  <svg
                    className="animate-spin h-12 w-12 mx-auto mb-4"
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
                  <p>Creating your design...</p>
                  <p className="text-sm">This may take a moment</p>
                </div>
              ) : (
                <p className="text-muted-foreground">
                  Your design will appear here
                </p>
              )}
            </div>

            {generatedDesign && (
              <div className="mt-4 space-y-4">
                <div className="p-4 bg-muted/50 rounded-lg">
                  <p className="font-medium">{generatedDesign.name}</p>
                  <p className="text-sm text-muted-foreground">
                    Status:{" "}
                    <span
                      className={
                        generatedDesign.status === "active"
                          ? "text-green-600"
                          : "text-yellow-600"
                      }
                    >
                      {generatedDesign.status}
                    </span>
                  </p>
                </div>

                <div className="flex gap-2">
                  {generatedDesign.status === "draft" ? (
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
                    <Link
                      href="/products"
                      className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-md font-medium hover:bg-primary/90 transition-colors text-center"
                    >
                      View in Store
                    </Link>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Tips */}
        <div className="mt-12 p-6 bg-muted/30 rounded-lg">
          <h3 className="font-semibold mb-3">Design Tips</h3>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li>
              • Be specific about text you want included - the AI will try to
              render it in the design
            </li>
            <li>
              • Mention colors, mood, and style preferences in your concept
            </li>
            <li>
              • rSpace themes work great: spatial webs, interconnected nodes,
              commons, collaboration, community tools
            </li>
            <li>
              • Generated designs start as drafts - preview before adding to the
              store
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
