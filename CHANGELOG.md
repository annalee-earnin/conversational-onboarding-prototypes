# Conversational Onboarding Prototype — Work Summary

## Overview

Two HTML/CSS/JS prototypes exploring a conversational (chat-style) onboarding flow for EarnIn's Cash Out product. Both run as single-file static pages served locally at `http://localhost:8090`.

- **v1** — Original baseline prototype
- **v2** — Redesigned version with persistent input, inline OTP, and additional UX improvements

---

## V1 Changes

### Flow & Copy
- Greeting after name changed from "Nice to meet you, [name]" → "Hi [name]! Let's keep going. Next up…"
- Done message updated to numbered steps (1/2/3) instead of bullet points, with a blank line before the list

### Attribution Card
- "Other" text input moved inside the scrollable list (was sticky at bottom) so it scrolls naturally with all options

---

## V2 — Built from scratch / major redesign

### Architecture
- **Persistent input** — `mainInputCard` always visible at the bottom; placeholder always reads "Reply here"
- **No input validation** — user can send any text at any step
- **`flow[]` array** — each step has `botMsg`, optional `card`, `onSubmit`, `postSubmit`
- **`activeCard`** — slot above the main input for cards (OTP, verify, quick replies, attribution)
- **`generation` counter** — cancels stale async chains on restart

### Intro / Hero Steps (Steps 0–3)
Added four intro steps before name collection, matching the v1 script:
1. Hero slide — "You should get paid while you work…"
2. Educational slide 1 — "How is EarnIn changing that?"
3. Educational slide 2 — "Yes, I want my pay faster"
4. Cash Out intro — disclosures link, "Get started with Cash Out"

### Name & Greeting
- Greeting after name: "Hi [first name]! 👋" (removed "Let's keep going.")

### Verify Info Card (after DOB, before phone)
- Card slides up over the input field showing collected name and DOB
- **View mode**: First name / Last name / Date of birth in label-value format; "Edit" + "That's correct" CTAs (small, hugging, right-aligned)
- **Edit mode**: Separate first/last name fields; DOB pre-filled in MM/DD/YYYY format with format hint; DOB auto-formats as user types; deletion-safe (no slash re-injection on backspace); Save + Cancel buttons
- Tapping "That's correct" sends user bubble and advances flow
- Tapping Save sends "[Name] · [Month D, YYYY]" user bubble, bot acks with "Got it — I've updated your info!", then continues

### OTP Cards (Phone & Email)
- Replaces the main input area entirely (hides `mainInputCard`, renders digit boxes in `activeCard`)
- Auto-submits on 4th digit (300ms delay)
- Numeric keyboard (`type="tel"`, `inputmode="numeric"`)
- OTP hidden input moved physically into `activeCard` DOM with `opacity: 0.01` for WebView keyboard compatibility; `focus()` called immediately, at 50ms, and at 300ms; also triggered on `touchstart`
- Resend button with 30s countdown
- "Edit phone number" / "Edit email" pills open bottom-sheet editors
- Phone number included in OTP message copy

### T&C Steps (Steps 11–12)
- Presented as chat messages (not cards) with "Do you agree to…?" phrasing
- Agreement names rendered as **underlined links** using `[label](url)` markdown in typewriter
  - TC1: "…[Electronic Communications Agreement](#) and to receive transactional SMS?"
  - TC2: "…[General Terms of Service](#) and [Privacy Documents](#)?"
- **QRs hidden until scroll-end** — "Yes, I agree" and "Learn more" buttons are invisible until the user scrolls to the bottom of the message; scroll listener reveals them with fade-in animation
- "Learn more" opens the full agreement text in a bottom sheet (does not advance flow)
- TC3 (optional SMS opt-in) and push notifications follow as separate steps

### Disclosures Bottom Sheet
- Triggered by "Learn more" quick reply or `#disclosures` inline links in chat
- Slides up from bottom with handle bar, title, scrollable body, close button
- Contains full Electronic Communications Agreement and Terms/Privacy wording

### Done Screen (matches v1)
- Celebration GIF (giphy) appears first, typed with brief typing indicator
- Bot message: "🎉 Your EarnIn account is created!" + numbered next steps (2 line breaks before list)
- "Continue set up" CTA button (black pill, full width) — same as v1's `renderContinueCard`

### Other Improvements
- **No pen edit icons** — removed `attachEditBtn` calls from all postSubmit callbacks in v2
- **Restart** restores `mainInputCard`, clears `generation`, resets all state
- **`white-space: pre-wrap`** on `.bubble-bot` so single `\n` in messages renders as a line break
- **GIF bubble** (`addGifBubble`) added to v2 with typing indicator, fade-in animation
- **`gifMsg` support** in `runNextStep` — shown before `botMsg` if present

---

## Shared Infrastructure

| Feature | Detail |
|---|---|
| Static file server | `prototypes/serve.py` — Python SimpleHTTPServer with no-cache headers |
| Local URL | `http://localhost:8090/v1/index.html` and `/v2/index.html` |
| Sharing | Netlify Drop (`netlify.com/drop`) for sharing with colleagues |
| Typewriter | Character-by-character with `[label](url)` → underlined `<a>` tag support |
| Bottom sheets | `.sheet-backdrop` + `.disclosures-sheet` with `.visible` class toggle |
| Scroll hint | Chevron button fades in when chat content overflows; fades out at bottom |

---

## Files

```
prototypes/
├── serve.py          — local dev server
├── v1/
│   └── index.html    — baseline prototype
└── v2/
    └── index.html    — redesigned prototype
```
