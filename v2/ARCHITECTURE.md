# v2 Conversational Onboarding — Architecture Decisions

## Overview

v2 is a single-file HTML prototype (`index.html`) of a conversational onboarding flow for EarnIn's Cash Out product. It runs in both a WKWebView (native dev app) and mobile browsers (Safari/Chrome on iOS). All logic lives in one `<script>` block; there is no build step, no framework, and no external JS dependencies.

---

## Layout & Keyboard Handling

### `.phone` as a fixed flex column

The root `.phone` element uses `position: fixed; inset: 0` so it always fills the layout viewport — not the visual viewport. This sidesteps the Safari/Chrome discrepancy between `100vh` and the actual visible height.

Inside `.phone`, the layout is a vertical flex column:

```
.phone (fixed, flex column)
├── .nav-bar          (flex-shrink: 0)
├── .chat-wrap        (flex: 1, min-height: 0)
│   └── #chatScroll   (flex: 1, overflow-y: auto)
└── .card-area        (flex-shrink: 0)
    ├── #activeCard
    ├── #mainInputCard
    └── .disclaimer
```

### `visualViewport` keyboard sync

When the soft keyboard appears in a browser, `window.innerHeight` stays fixed (layout viewport) but `visualViewport.height` shrinks. The difference is the keyboard height.

`syncToVisualViewport()` listens to `visualViewport resize/scroll` and sets:

```js
phone.style.paddingBottom = (window.innerHeight - visualViewport.height) + 'px';
```

This compresses the flex content upward, pushing the card area above the keyboard without any fixed-position anchoring confusion. In WKWebView the app resizes the WebView itself, so `innerHeight === visualViewport.height` and the padding is always 0 — no behavioural difference.

The `focusin` event also triggers `sync()` + `scrollToLastMsg()` after 300 ms to handle cases where the keyboard was already up and a new focus event doesn't fire a `resize`.

---

## Flow Architecture

### Step array

All steps are defined in a single `flow` array. Each step is either a **text step** (uses the main input field) or a **card step** (renders a custom UI component).

| Field | Purpose |
|---|---|
| `botMsg` | Primary bot message (supports `\n\n`, `[label](url)`, and `**bold**`) |
| `preBotMsg` | Short message shown before `botMsg` in the same step |
| `followUp` | Message shown after `botMsg`, before the card renders |
| `botMsgStyle` | `'hero'` renders a large headline + body paragraph layout |
| `botMsgBody` | Body text for hero-style messages |
| `gifMsg` | URL of a GIF shown before `botMsg` |
| `card` | `'quick'` \| `'otp'` \| `'verify'` \| `'attribution'` \| `'continue'` |
| `options` | Array of quick-reply labels; `{ label, primary, agreeText, noAdvance }` |
| `inputmode` | Sets `inputmode` attribute on the main input for that step |
| `placeholder` | Overrides the default "Reply here" placeholder |
| `skipable` | Renders a Skip quick-reply chip above the input |
| `validate` | Function that returns `false` to block advance and show `errorMsg` |
| `errorMsg` | String or function returning the retry message |
| `onSubmit` | Called with the user's value when the step is completed |
| `postSubmit` | Called after `onSubmit`; used to capture bubble element refs |
| `requireScrollEnd` | Hides QR buttons until the user has scrolled to the end of the bot message |
| `requestPermission` | Requests browser push notification permission before advancing |
| `learnMore` | Inline expand: shows a bot message and re-renders only the primary option |

### Step execution (`runNextStep`)

```
state.step++
  → show gifMsg (if any)
  → show preBotMsg (if any)
  → show botMsg (if any)
  → show followUp (if any)
  → 150 ms delay
  → if card: renderCard(step)
     else: applyStepToInput(step)
```

The 150 ms delay after messages gives the last bot bubble time to finish animating before the card area changes height.

### Text step advance (`advanceText`)

1. Clear input, lock send button
2. Add user bubble to chat
3. Clear `activeCard` (removes any skip QR — done after `addUserMsg` so layout is stable for the `scrollToBubbleTop` rAF)
4. `requestAnimationFrame → scrollToBubbleTop(lastUserBubble)`
5. Run `step.validate`; on failure show error message and force-scroll to it after 350 ms (gives keyboard time to reopen)
6. `step.onSubmit` → `step.postSubmit` → `runNextStep`

### Card step advance (`advanceFromCard`)

Skips validation entirely. Calls `step.onSubmit` → `addUserMsg` → `scrollToBubbleTop` → `runNextStep`.

---

## Current Flow Sequence

| Step | Type | Description |
|---|---|---|
| 0 | Quick card | Hero intro — "Yes, pay faster" skips the education turns |
| 1 | Quick card | Education: why paychecks are biweekly |
| 2 | Quick card | Education: how EarnIn works |
| 3 | Quick card | Cash Out intro + disclosures link |
| 4 | Text (skipable) | Attribution — "Before we dive in, how did you hear about us?" |
| 5 | Text | Legal name (validates ≥ 2 words) |
| 6 | Text | Date of birth (loose parsing via `parseDOB`, validates age ≥ 18) |
| 7 | Text | Phone number (`inputmode: tel`, validates 10 digits) |
| 8 | OTP card | Phone OTP — 4-digit code, 60 s resend timer |
| 9 | Text | Email address (validates format) |
| 10 | Verify card | Confirm collected info (name, DOB, phone, email) — inline edit |
| 11 | Quick card | TC: Electronic Communications Agreement |
| 12 | Quick card | TC: Terms of Service + Privacy |
| 13 | Quick card | Optional SMS marketing opt-in |
| 14 | Quick card | GIF + success message + push notification ask |
| 15 | Quick card | Transitional message + what's next steps + "Ready?" + "Let's go" |
| 16 | Terminal | Restores input field; no further advance |

### Branching

- **Step 0**: Choosing "Yes, I want my pay faster" increments `state.step` by 2, skipping steps 1–2 (the education branch).
- All other steps are strictly linear.

---

## OTP Card

The OTP card reuses `mainInput` (the same `<input>` the user just typed their phone number into) rather than creating a new element. This is critical on iOS: a newly-focused input loses the keyboard when the DOM changes, but `mainInput` retains it because the user has been interacting with it throughout.

Key mechanics:
- `maybePreSwitchOtpInput()` — called **inside the send-button click gesture**, switches `mainInput` to `type=tel` / `inputmode=numeric` before the async bot message plays, so the keyboard transitions smoothly from text to numeric
- `renderOtpCard()` — also re-applies `type=tel` / `inputmode=numeric` explicitly so re-renders (e.g. after editing) also show the numeric keyboard
- `mainInputCard.classList.add('otp-mode')` — collapses the input card to `height:1px; opacity:0; overflow:hidden` so it's invisible but still in the DOM (keeps the keyboard alive)
- Four visual digit boxes in `activeCard` are purely decorative; tapping them calls `mainInput.focus()`

### OTP edit (phone or email)

Tapping "Edit phone number" / "Edit email" renders an inline edit card directly in `activeCard`:
- `eInp.focus()` is called **synchronously** within the click handler (keeps keyboard alive on iOS)
- **X**: calls `renderOtpCard(step)` and `mainInput.focus()` to restore the OTP UI
- **Save**: removes the original OTP intro bot bubble, updates `state.phone/email`, patches the user's chat bubble, sends a new bot message, and re-renders the OTP card
- Scroll: after save, `chatScroll.scrollTop` is set **synchronously** right after the DOM removal (before any repaint) so there's no visible scroll jump

---

## Verify Card

Shown after email collection (step 10). Renders a summary of name, DOB, phone, and email.

- **View mode**: shows all four fields with edit pencil buttons
- **Edit mode**: inline form within the card; Save calls `addBotMsg("Got it — I've updated your info!")` and re-runs `runNextStep` before restoring the view
- The card hides `mainInputCard` while active

---

## Typewriter Rendering

`typeText(el, text)` tokenizes the message string and replays it character-by-character:

| Token | Syntax | Output |
|---|---|---|
| `c` | any character | appended to last text node |
| `br` | `\n\n` | two `<br>` elements |
| `a` | `[label](url)` | `<a>` with underline style |
| `b` | `**text**` | `<strong>` element (added instantly, not char-by-char) |

Speed adapts to message length: `msPerChar = clamp(3, 10, 1500 / charCount)`.

Auto-scroll during typing tracks the bottom of the growing bubble and scrolls `chatScroll` to keep it in view (only when `lastUserBubble` is set, i.e. after the user has interacted).

---

## Scroll Management

Three scroll utilities:

| Function | Behaviour |
|---|---|
| `scrollToBubbleTop(el)` | Instant: `chatScroll.scrollTop = el.offsetTop - 16`. Called after user submits a message to bring their bubble to the top of the visible area. |
| `scrollToLastMsg()` | Smooth: scrolls so the last bot bubble's bottom is 24 px above the chat area bottom. Only scrolls down (guarded by `target > scrollTop`). |
| `updateScrollHint()` | Shows/hides the scroll-down chevron button when the last bot bubble extends below the visible area. |

`scrollToLastMsg` is called:
- After each bot message in a card render (via rAF + 200 ms timeout)
- After the `focusin` event (300 ms delay, after `sync()`)
- After text-step bot messages in `runNextStep`

Force-scroll (no guard) is used in the OTP edit save path and the validation-error path to ensure those messages are always visible regardless of current scroll position.

---

## Quick Replies

Quick reply options are rendered as pill buttons in a `div.quick-replies` (flex column, `align-items: flex-end`), right-aligned to match the chat's user-side convention.

Behaviour:
- `requireScrollEnd: true` — buttons are hidden (`opacity: 0`) until the user has scrolled to the bottom of the bot message; a `scroll` event listener reveals them
- `noAdvance: true` — "Learn more" tap shows expanded detail as a bot message and re-renders only the primary option
- `agreeText` — overrides the chat bubble text so legal agreements show the full consent statement

---

## Restart

`window.location.reload()` — a full page reload is used instead of an in-place `restart()` reset to guarantee a clean state (no stale event listeners, no partial DOM state).

---

## WKWebView Compatibility

- `overflow: hidden` on `html`/`body` prevents the native bounce scroll
- `window.addEventListener('scroll', () => window.scrollTo(0, 0))` suppresses any programmatic scroll on the root
- `padding-top: env(safe-area-inset-top)` on the nav bar handles the notch/Dynamic Island
- `font-size: 16px` on inputs prevents iOS auto-zoom
- All focus calls that must keep the keyboard alive are placed **synchronously inside user-gesture handlers** (click/touchend), never in `setTimeout`
