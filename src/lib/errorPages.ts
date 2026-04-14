export function promoErrorPage(code: number, headline: string, message: string): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>THE MOON RECORDS // ${code}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Josefin+Sans:wght@300;400;600;700&family=Space+Mono&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #0C0C0C;
      color: #E8E4D8;
      font-family: 'Josefin Sans', 'Futura', Arial, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      gap: 1rem;
      text-align: center;
      padding: 2rem;
    }
    .eyebrow {
      font-family: 'Space Mono', 'Courier New', monospace;
      font-size: 0.6rem;
      letter-spacing: 0.35em;
      text-transform: uppercase;
      color: #C4B98A;
    }
    .headline {
      font-family: 'Josefin Sans', 'Futura', Arial, sans-serif;
      font-size: 1.5rem;
      font-weight: 700;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: #E8E4D8;
      margin: 0;
    }
    .msg {
      font-family: 'Space Mono', 'Courier New', monospace;
      font-size: 0.6rem;
      letter-spacing: 0.2em;
      text-transform: uppercase;
      color: rgba(232,228,216,0.4);
    }
    .rule {
      width: 3rem;
      height: 1px;
      background: rgba(196,185,138,0.3);
      margin: 0.5rem auto;
    }
    .back {
      font-family: 'Space Mono', 'Courier New', monospace;
      font-size: 0.6rem;
      letter-spacing: 0.25em;
      text-transform: uppercase;
      color: rgba(232,228,216,0.35);
      text-decoration: none;
      margin-top: 1.5rem;
      border-bottom: 1px solid rgba(196,185,138,0.2);
      padding-bottom: 0.2rem;
      transition: color 200ms;
    }
    .back:hover { color: rgba(232,228,216,0.6); }
  </style>
</head>
<body>
  <span class="eyebrow">The Moon Records</span>
  <div class="rule"></div>
  <h1 class="headline">${headline}</h1>
  <p class="msg">${message}</p>
  <a href="/" class="back">← Return</a>
</body>
</html>`;
}
