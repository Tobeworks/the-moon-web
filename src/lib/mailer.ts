import nodemailer from 'nodemailer';

const smtpUser = process.env.SMTP_USER;
const smtpPass = process.env.SMTP_PASS;

const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST ?? 'localhost',
  port: Number(process.env.SMTP_PORT ?? 1025),
  secure: process.env.SMTP_SECURE === 'true',
  ...(smtpUser && smtpPass ? { auth: { user: smtpUser, pass: smtpPass } } : {}),
});

const FROM = `THE MOON RECORDS <${process.env.SMTP_FROM ?? 'newsletter@the-moon-records.de'}>`;

const baseHtml = (content: string) => `<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0C0C0C;font-family:'Courier New',monospace;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0C0C0C;padding:40px 16px;">
    <tr><td align="center">
      <table width="100%" style="max-width:560px;border:1px solid rgba(196,185,138,0.12);">
        <tr>
          <td style="padding:28px 32px;border-bottom:1px solid rgba(196,185,138,0.12);">
            <div style="color:#C4B98A;font-size:11px;letter-spacing:0.4em;text-transform:uppercase;margin-bottom:12px;">
              // THE MOON RECORDS
            </div>
          </td>
        </tr>
        <tr><td style="padding:32px;">${content}</td></tr>
        <tr>
          <td style="padding:16px 32px;border-top:1px solid rgba(196,185,138,0.12);">
            <p style="margin:0;color:rgba(232,228,216,0.2);font-size:10px;letter-spacing:0.2em;text-transform:uppercase;">
              THE MOON RECORDS &mdash; TRANSMITTING FROM THE DARK SIDE
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body></html>`;

export async function sendConfirmationEmail(to: string, name: string, token: string, siteUrl: string) {
  const confirmUrl = `${siteUrl}/api/newsletter/confirm?token=${token}`;
  const greeting = name ? `${name},` : 'Hey,';

  const html = baseHtml(`
    <h1 style="margin:0 0 16px;color:#E8E4D8;font-size:22px;letter-spacing:0.2em;text-transform:uppercase;font-weight:700;">
      Confirm Subscription
    </h1>
    <p style="margin:0 0 24px;color:rgba(232,228,216,0.6);font-size:13px;letter-spacing:0.08em;line-height:1.8;">
      ${greeting} you requested to join The Moon Records newsletter.
      Click below to confirm your address and get in.
    </p>
    <a href="${confirmUrl}" style="display:inline-block;background:#C4B98A;color:#1A1710;font-size:12px;font-weight:700;letter-spacing:0.3em;text-transform:uppercase;padding:13px 28px;text-decoration:none;">
      CONFIRM SUBSCRIPTION
    </a>
    <p style="margin:28px 0 0;color:rgba(232,228,216,0.25);font-size:11px;letter-spacing:0.08em;line-height:1.7;">
      Link expires in 24&nbsp;hours. If you did not sign up, ignore this email.
    </p>
  `);

  const text = `${greeting}\n\nConfirm your The Moon Records newsletter subscription:\n${confirmUrl}\n\nLink expires in 24 hours.`;

  await transporter.sendMail({ from: FROM, to, subject: 'Confirm your subscription — THE MOON RECORDS', html, text });
}

export async function sendWelcomeEmail(to: string, name: string, unsubscribeToken: string, siteUrl: string) {
  const unsubscribeUrl = `${siteUrl}/api/newsletter/unsubscribe?token=${unsubscribeToken}`;
  const greeting = name ? `${name},` : 'Hey,';

  const html = baseHtml(`
    <h1 style="margin:0 0 16px;color:#E8E4D8;font-size:22px;letter-spacing:0.2em;text-transform:uppercase;font-weight:700;">
      You're in.
    </h1>
    <p style="margin:0 0 24px;color:rgba(232,228,216,0.6);font-size:13px;letter-spacing:0.08em;line-height:1.8;">
      ${greeting} subscription confirmed. You'll receive transmissions when new releases drop
      &mdash; no noise, no filler.
    </p>
    <p style="margin:0;color:rgba(232,228,216,0.25);font-size:11px;letter-spacing:0.08em;line-height:1.7;">
      To unsubscribe at any time:
      <a href="${unsubscribeUrl}" style="color:rgba(196,185,138,0.7);text-decoration:underline;">click here</a>
    </p>
  `);

  const text = `${greeting}\n\nSubscription confirmed. You'll hear from The Moon Records when new releases drop.\n\nUnsubscribe: ${unsubscribeUrl}`;

  await transporter.sendMail({ from: FROM, to, subject: 'You\'re in — THE MOON RECORDS Newsletter', html, text });
}

export async function sendAlreadySubscribedEmail(to: string, name: string, unsubscribeToken: string, siteUrl: string) {
  const unsubscribeUrl = `${siteUrl}/api/newsletter/unsubscribe?token=${unsubscribeToken}`;
  const greeting = name ? `${name},` : 'Hey,';

  const html = baseHtml(`
    <h1 style="margin:0 0 16px;color:#E8E4D8;font-size:22px;letter-spacing:0.2em;text-transform:uppercase;font-weight:700;">
      Already subscribed
    </h1>
    <p style="margin:0 0 24px;color:rgba(232,228,216,0.6);font-size:13px;letter-spacing:0.08em;line-height:1.8;">
      ${greeting} this address is already on the list. No action needed.
    </p>
    <p style="margin:0;color:rgba(232,228,216,0.25);font-size:11px;letter-spacing:0.08em;line-height:1.7;">
      To unsubscribe:
      <a href="${unsubscribeUrl}" style="color:rgba(196,185,138,0.7);text-decoration:underline;">click here</a>
    </p>
  `);

  const text = `${greeting}\n\nThis address is already subscribed to The Moon Records newsletter.\n\nUnsubscribe: ${unsubscribeUrl}`;

  await transporter.sendMail({ from: FROM, to, subject: 'Already subscribed — THE MOON RECORDS', html, text });
}
