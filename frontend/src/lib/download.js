/**
 * download.js — fetch-based file download and WhatsApp share helpers.
 * All protected file downloads must go through these helpers so the
 * Authorization header is included. Never use plain <a href> for API files.
 */

/** Replace characters that are illegal in filenames on any OS. */
function sanitizeFilename(name) {
  return name.replace(/[/\\:*?"<>|]/g, '-');
}

/**
 * downloadFile — fetch a protected URL and save the response as a local file.
 * @param {string} url        - API URL (e.g. /api/v1/invoices/5/pdf)
 * @param {string} filename   - Desired filename (will be sanitized)
 * @param {string} token      - Bearer access token
 */
export async function downloadFile(url, filename, token) {
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    let detail = `Download failed (${res.status})`;
    try {
      const json = await res.json();
      if (json.detail) detail = json.detail;
    } catch (_) {
      // non-JSON body, keep the status message
    }
    throw new Error(detail);
  }

  const blob = await res.blob();
  const href = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = href;
  a.download = sanitizeFilename(filename);
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(href), 10_000);
}

/**
 * shareFile — share a protected file via Web Share API (native sheet),
 * falling back to opening a wa.me text link in a new tab.
 * @param {string} url        - API URL
 * @param {string} filename   - Desired filename (will be sanitized)
 * @param {string} token      - Bearer access token
 * @param {string} [text]     - Optional share body text / WhatsApp message
 */
export async function shareFile(url, filename, token, text = '') {
  const safeFilename = sanitizeFilename(filename);

  // Try native share with file (supported in mobile Chrome / Safari 15+)
  if (typeof navigator !== 'undefined' && navigator.share) {
    try {
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`Fetch failed (${res.status})`);
      const blob = await res.blob();
      const file = new File([blob], safeFilename, { type: blob.type });
      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        await navigator.share({ files: [file], title: safeFilename, text });
        return;
      }
    } catch (e) {
      // Fall through to WhatsApp link
      console.warn('Native share failed, falling back to WhatsApp link:', e);
    }
  }

  // Fallback: open WhatsApp with a text message
  const waText = text || safeFilename;
  const waUrl = `https://wa.me/?text=${encodeURIComponent(waText)}`;
  window.open(waUrl, '_blank', 'noopener,noreferrer');
}
