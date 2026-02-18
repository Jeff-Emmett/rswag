/** Client-side Canvas mockup compositing for design previews. */

export interface MockupConfig {
  template: string;
  designArea: { x: number; y: number; width: number; height: number };
  label: string;
  productType: string;
  price: number;
}

export const MOCKUP_CONFIGS: MockupConfig[] = [
  {
    template: "/mockups/shirt-template.png",
    designArea: { x: 275, y: 300, width: 250, height: 250 },
    label: "T-Shirt",
    productType: "shirt",
    price: 29.99,
  },
  {
    template: "/mockups/sticker-template.png",
    designArea: { x: 130, y: 130, width: 540, height: 540 },
    label: "Sticker",
    productType: "sticker",
    price: 3.50,
  },
  {
    template: "/mockups/print-template.png",
    designArea: { x: 160, y: 160, width: 480, height: 480 },
    label: "Art Print",
    productType: "print",
    price: 12.99,
  },
];

/**
 * Composite a design image onto a product template using Canvas API.
 * Draws the design into the bounding box first, then overlays the template
 * so transparent regions in the template show the design through.
 */
export function generateMockup(
  designDataUrl: string,
  config: MockupConfig
): Promise<string> {
  return new Promise((resolve, reject) => {
    const canvas = document.createElement("canvas");
    canvas.width = 800;
    canvas.height = 800;
    const ctx = canvas.getContext("2d");
    if (!ctx) return reject(new Error("Canvas not supported"));

    const templateImg = new window.Image();
    const designImg = new window.Image();

    templateImg.crossOrigin = "anonymous";
    designImg.crossOrigin = "anonymous";

    let loaded = 0;
    const onBothLoaded = () => {
      loaded++;
      if (loaded < 2) return;

      // Draw design first (underneath template)
      const { x, y, width, height } = config.designArea;

      // Maintain aspect ratio within the bounding box
      const scale = Math.min(width / designImg.width, height / designImg.height);
      const dw = designImg.width * scale;
      const dh = designImg.height * scale;
      const dx = x + (width - dw) / 2;
      const dy = y + (height - dh) / 2;

      ctx.drawImage(designImg, dx, dy, dw, dh);

      // Draw template on top (transparent areas show design through)
      ctx.drawImage(templateImg, 0, 0, 800, 800);

      resolve(canvas.toDataURL("image/png"));
    };

    templateImg.onload = onBothLoaded;
    designImg.onload = onBothLoaded;
    templateImg.onerror = () => reject(new Error(`Failed to load template: ${config.template}`));
    designImg.onerror = () => reject(new Error("Failed to load design image"));

    templateImg.src = config.template;
    designImg.src = designDataUrl;
  });
}
