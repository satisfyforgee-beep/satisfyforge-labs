import test from 'node:test';
import assert from 'node:assert/strict';
import {
  BUSINESS_GMAIL,
  assertBusinessSender,
  buildMimeMessage,
  buildIdempotencyKey,
  sendGmailMessage,
  toBase64Url,
} from '../src/gmail.mjs';

test('business sender is locked to SatisfyForge Gmail', () => {
  assert.equal(assertBusinessSender(BUSINESS_GMAIL), BUSINESS_GMAIL);
  assert.throws(() => assertBusinessSender('cougarboy1999@gmail.com'), /WRONG_SENDER_ACCOUNT/);
});

test('MIME headers cannot be newline-injected', () => {
  const mime = buildMimeMessage({
    from: BUSINESS_GMAIL,
    to: 'advisor@example.org\r\nBcc: attacker@example.org',
    subject: 'Advisor request\nBcc: attacker@example.org',
    text: 'Hello',
  });
  assert.equal(mime.includes('\r\nBcc: attacker@example.org\r\n'), false);
});

test('base64url output contains no plus slash or padding', () => {
  const encoded = toBase64Url('hello?+/=');
  assert.match(encoded, /^[A-Za-z0-9_-]+$/);
});

test('idempotency key is stable for identical message', () => {
  const args = { to: 'x@example.org', subject: 'Hello', text: 'World' };
  assert.equal(buildIdempotencyKey(args), buildIdempotencyKey(args));
});

test('send calls Gmail API once and returns ids', async () => {
  const calls = [];
  const fetchImpl = async (url, init) => {
    calls.push({ url, init });
    return {
      ok: true,
      status: 200,
      async json() { return { id: 'm1', threadId: 't1', labelIds: ['SENT'] }; },
    };
  };
  const result = await sendGmailMessage({
    accessToken: 'token',
    from: BUSINESS_GMAIL,
    to: 'advisor@example.org',
    subject: 'Business advisor request',
    text: 'Hello from SatisfyForge',
    fetchImpl,
  });
  assert.deepEqual(result, { id: 'm1', threadId: 't1', labelIds: ['SENT'] });
  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, 'https://gmail.googleapis.com/gmail/v1/users/me/messages/send');
  assert.equal(calls[0].init.method, 'POST');
});

test('missing token never attempts network send', async () => {
  let called = false;
  await assert.rejects(
    sendGmailMessage({
      accessToken: '',
      from: BUSINESS_GMAIL,
      to: 'advisor@example.org',
      subject: 'Hello',
      text: 'Body',
      fetchImpl: async () => { called = true; },
    }),
    /GOOGLE_ACCESS_TOKEN_REQUIRED/
  );
  assert.equal(called, false);
});
