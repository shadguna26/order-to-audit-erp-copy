/**
 * download.js — fetch-based file download and WhatsApp share helpers.
 * All protected file downloads must go through these helpers so the
 * Authorization header is included. Never use plain <a href> for API files.
 */

/** Replace characters that are illegal in filenames on any OS. */
function sanitizeFilename(name) {
  return String(name || 'download').replace(/[/\\:*?"<>|]/g, '-');
}

function getAuthToken(explicitToken) {
  if (explicitToken) return explicitToken;
  if (typeof localStorage !== 'undefined') {
    return (
      localStorage.getItem('token') ||
      localStorage.getItem('access_token') ||
      ''
    );
  }
  return '';
}

function filenameFromDisposition(headerValue) {
  if (!headerValue) return null;
  const utf8Match = headerValue.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match && utf8Match[1]) {
    try {
      return decodeURIComponent(utf8Match[1].trim().replace(/^["']|["']$/g, ''));
    } catch (_) {
      return utf8Match[1].trim();
    }
  }
  const plainMatch = headerValue.match(/filename=([^;]+)/i);
  if (plainMatch && plainMatch[1]) {
    return plainMatch[1].trim().replace(/^["']|["']$/g, '');
  }
  return null;
}

/**
 * downloadFile — fetch a protected URL and save the response as a local file.
 * @param {string} url          - API URL (e.g. /api/v1/invoices/5/pdf)
 * @param {string} fallbackName - Fallback filename if Content-Disposition is absent
 * @param {string} [token]      - Optional Bearer access token (defaults to localStorage)
 */
export async function downloadFile(url, fallbackName, token) {
  const authToken = getAuthToken(token);
  const headers = authToken ? { Authorization: `Bearer ${authToken}` } : {};
  const res = await fetch(url, { headers });

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

  const contentType = (res.headers.get('content-type') || '').toLowerCase();
  if (contentType.includes('text/html')) {
    throw new Error('Server returned HTML instead of a file');
  }

  const headerFilename = filenameFromDisposition(res.headers.get('content-disposition'));
  const finalName = sanitizeFilename(headerFilename || fallbackName);

  const blob = await res.blob();
  const href = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = href;
  a.download = finalName;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(href), 30_000);
}

/**
 * shareFile — share a protected file via Web Share API (native sheet),
 * falling back to opening a wa.me text link in a new tab.
 * @param {string} url    - API URL
 * @param {string} name   - Desired filename (will be sanitized)
 * @param {string} [text] - Optional share body text / WhatsApp message
 * @param {string} [token] - Optional Bearer access token
 */
export async function shareFile(url, name, text = '', token) {
  const safeFilename = sanitizeFilename(name);
  const authToken = getAuthToken(token);
  const headers = authToken ? { Authorization: `Bearer ${authToken}` } : {};

  if (typeof navigator !== 'undefined' && navigator.share) {
    try {
      const res = await fetch(url, { headers });
      if (!res.ok) throw new Error(`Fetch failed (${res.status})`);
      const contentType = (res.headers.get('content-type') || '').toLowerCase();
      if (contentType.includes('text/html')) {
        throw new Error('Server returned HTML instead of a file');
      }
      const blob = await res.blob();
      const file = new File([blob], safeFilename, { type: blob.type || 'application/pdf' });
      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        await navigator.share({ files: [file], title: safeFilename, text });
        return;
      }
    } catch (e) {
      if (e && e.name === 'AbortError') return;
      console.warn('Native share failed, falling back to WhatsApp link:', e);
    }
  }

  const waText = text || safeFilename;
  const waUrl = `https://wa.me/?text=${encodeURIComponent(waText)}`;
  window.open(waUrl, '_blank', 'noopener,noreferrer');
}
