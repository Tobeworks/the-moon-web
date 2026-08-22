/**
 * Page scroll lock for full-screen overlays (mobile menu, playlist).
 *
 * Two things make this less trivial than `body { overflow: hidden }`:
 *  - Lenis drives scrolling programmatically and ignores overflow entirely,
 *    so it has to be stopped explicitly.
 *  - iOS Safari ignores overflow on body too; `position: fixed` with a stored
 *    offset is the reliable way, and it needs restoring on unlock.
 */

let locks = 0;
let scrollY = 0;

export function lockScroll(): void {
  if (locks++ > 0) return; // already locked — don't clobber the stored offset

  (window as any).lenis?.stop();
  scrollY = window.scrollY;

  const { style } = document.body;
  style.position = 'fixed';
  style.top = `-${scrollY}px`;
  style.width = '100%';
  style.overflow = 'hidden';
}

export function unlockScroll(): void {
  if (locks === 0) return;
  if (--locks > 0) return; // another overlay is still open

  const { style } = document.body;
  style.position = '';
  style.top = '';
  style.width = '';
  style.overflow = '';

  window.scrollTo(0, scrollY);
  (window as any).lenis?.start();
}
