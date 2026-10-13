const BUSINESS_SENDER = 'satisfyforgee@gmail.com';

export function assertBusinessSender(email) {
  const normalized = String(email || '').trim().toLowerCase();
  if (normalized !== BUSINESS_SENDER) {
    const error = new Error('WRONG_SENDER_ACCOUNT');
    error.code = 'WRONG_SENDER_ACCOUNT';
    error.expected = BUSINESS_SENDER;
    error.observed = normalized || null;
    throw error;
  }
  return normalized;
}

export function sanitizeHeader(value) {
  return String(value ?? '').replace(/[\r\n]+/g, ' ').trim();
}

export function buildMimeMessage({ from, to, subject, text }) {
  const safeFrom = sanitizeHeader(assertBusinessSender(from));
  const safeTo = sanitizeHeader(to);
  const safeSubject = sanitizeHeader(subject);
  const body = String(text ?? '').replace(/\r?\n/g, '\r\n');

  if (!safeTo || !safeTo.includes('@')) {
    const error = new Error('INVALID_RECIPIENT');
    error.code = 'INVALID_RECIPIENT';
    throw error;
  }
  if (!safeSubject) {
    const error = new Error('EMPTY_SUBJECT');
    error.code = 'EMPTY_SUBJECT';
    throw error;
  }
  if (!body.trim()) {
    const error = new Error('EMPTY_BODY');
    error.code = 'EMPTY_BODY';
    throw error;
  }

  return [
    `From: SatisfyForge <${safeFrom}>`,
    `To: ${safeTo}`,
    `Subject: ${safeSubject}`,
    'MIME-Version: 1.0',
    'Content-Type: text/plain; charset=UTF-8',
    'Content-Transfer-Encoding: 8bit',
    '',
    body,
  ].join('\r\n');
}

export function toBase64Url(value) {
  return Buffer.from(String(value), 'utf8')
    .toString('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/g, '');
}

export async function sendGmailMessage({ accessToken, from, to, subject, text, fetchImpl = fetch }) {
  if (!accessToken) {
    const error = new Error('GOOGLE_ACCESS_TOKEN_REQUIRED');
    error.code = 'GOOGLE_ACCESS_TOKEN_REQUIRED';
    throw error;
  }

  const mime = buildMimeMessage({ from, to, subject, text });
  const response = await fetchImpl('https://gmail.googleapis.com/gmail/v1/users/me/messages/send', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ raw: toBase64Url(mime) }),
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error('GMAIL_SEND_FAILED');
    error.code = 'GMAIL_SEND_FAILED';
    error.status = response.status;
    error.payload = payload;
    throw error;
  }

  return {
    id: payload.id ?? null,
    threadId: payload.threadId ?? null,
    labelIds: Array.isArray(payload.labelIds) ? payload.labelIds : [],
  };
}

export function buildIdempotencyKey({ to, subject, text }) {
  const input = `${sanitizeHeader(to).toLowerCase()}\n${sanitizeHeader(subject)}\n${String(text ?? '').trim()}`;
  let hash = 2166136261;
  for (let i = 0; i < input.length; i += 1) {
    hash ^= input.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return `sfmail_${(hash >>> 0).toString(16).padStart(8, '0')}`;
}

export const BUSINESS_GMAIL = BUSINESS_SENDER;
