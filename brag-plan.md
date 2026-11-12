# Second Thought — judge-ready demonstration

## Video brief

- **Format:** landscape, 1920×1080, 30fps, approximately 60 seconds
- **Tone:** polished, calm, human, lightly cinematic
- **Audience:** hackathon judges seeing the product for the first time
- **One-line story:** Second Thought reads a shopper's month, decides whether a purchase fits, and
  explains what happens before money or fulfilment moves.
- **Visual hook:** a checkout that says “not yet” before it lets a shopper overextend.
- **Audio:** original restrained pulse with soft clicks and confirmation tones; no copyrighted music.
- **Truth boundary:** browser demo uses simulated money; configured badges identify the live AI and
  PayPal sandbox. No live PayPal production activity appears in the video.

## Shot list

| Time | Picture | On-screen copy / narration | Sound |
|---|---|---|---|
| 0–4s | Real landing page, badges settled, gentle push-in | “What if checkout knew you get paid Friday?” | Music starts; one soft low pulse |
| 4–14s | Click Ben's month; result resolves in the real UI | “Second Thought checks the whole month — not just the cart.” / “Pay on Sat 07 Nov — and it ships once you've paid.” | Click, short resolving tone |
| 14–27s | Type the real sample sentence and click Read this; show extracted amounts and uncertainty flags | “It reads ordinary money language, then shows what it is unsure about.” | Typing texture, two quiet UI ticks |
| 27–42s | Fast, readable cuts: Ada, Ben, Cleo; each result remains visible long enough to read | “Fits today.” / “Fits on payday.” / “Doesn't fit right now.” | Three soft, distinct answer tones |
| 42–53s | Return to Ben result; show pay-before-ship copy and simulated-money footer | “No approval, no movement. No payment, no shipment.” | Music briefly drops; single confirmation tone |
| 53–60s | Clean final frame with product name, badges, and disclaimer | “Second Thought — a checkout that sometimes says not yet, and tells you why.” / “Sandbox demo · nothing charged” | Music resolves and fades |

## Capture notes

1. Run `product/scripts/serve.py` on a local port with the checked-in product as the source.
2. Capture the real page at 1920×1080, using a clean browser viewport and no browser chrome.
3. Use the existing persona routes and the existing extraction route; do not invent API responses or
   alter the product copy for the video.
4. Keep the badges visible in the opening and closing shots.
5. Capture settled frames and mid-transition frames separately so transitions can be checked before
   rendering.

## Final checks

- First frame is the settled poster frame.
- Duration is less than three minutes; target is about one minute.
- MP4 contains H.264 video and AAC audio at 1920×1080/30fps.
- Every spoken or displayed claim is supported by the product or explicitly labelled sandbox/demo.
- Audio is present, mixed below narration/captions, and has no copyrighted source.
- YouTube handoff: upload as **Unlisted** or **Public**, with no password. The local package is
  upload-ready; publication is a manual account action.
