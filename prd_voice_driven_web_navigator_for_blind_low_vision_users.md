# Product Requirements Document (PRD)

## 1) Product Overview
**Product name (working):** Lighthouse.ai

**One‑liner:** Voice‑driven assistant that lets blind and low‑vision users browse and operate websites hands‑free. Users speak; the agent controls the browser (via automation) and announces what’s on screen after every action—reliably and safely.

**Primary user value:** Faster, less frustrating navigation than traditional screen readers when dealing with dynamic, complex web apps (forms, modals, single‑page apps, tables, infinite scroll).

**Secondary value:** Works alongside existing screen readers and improves page comprehension with concise, context‑aware summaries.

---

## 2) Goals & Non‑Goals
### Goals
1. Execute common web tasks by voice: open links, follow results, fill and submit forms, navigate tables, filter/sort, checkout flows.
2. Give clear, succinct descriptions of the current screen (and changes) after each action.
3. Support error recovery and disambiguation (e.g., multiple similar buttons) through follow‑ups.
4. Be robust across modern, dynamic websites (React/Vue/Angular/SPAs).
5. Prioritize privacy and safety: never take destructive actions without explicit confirmation.

### Non‑Goals (v1)
- Desktop/native app control outside the browser.
- Full parity with specialized screen readers for every advanced feature.
- Complex multi‑step automations spanning many sites (keep to ≤5 steps/script in v1).

---

## 3) Personas
- **Priya (Primary)** — Blind screen‑reader user, adept but frustrated by poorly labeled controls and fast‑changing layouts.
- **Luis (Secondary)** — Low‑vision user who magnifies content; prefers concise spoken summaries vs. verbose reading.
- **QA/Support (Internal)** — Needs reproducible logs and deterministic replays to debug failed steps.

---

## 4) User Stories (v1 scope)
1. As a blind user, I can say “Search Amazon for noise‑canceling headphones and open the first Sony result,” and the agent performs the steps, then describes the product page.
2. After any action, I hear: page title, primary heading, main landmarks, focused element, and the top 3 actionable items (with counts), in ≤6 seconds.
3. When the page has many similar elements, I can say “list the buttons/links” and select by number or description.
4. I can fill forms by saying field/value pairs: “Email: priya@…, password: ****, submit.”
5. I can ask “what changed?” after an action; the agent reports diffs (e.g., new modal, error messages, cart count).
6. Before clicking destructive actions (delete, checkout, payment), the agent asks for confirmation.
7. I can say “stop,” “undo last,” or “cancel” anytime.

Out‑of‑scope (v1): complex captchas (offer human/time‑delayed workflows), MFA beyond copying codes from email/SMS inboxes.

---

## 5) Success Metrics
- **Task success rate (TSR):** ≥85% on a v1 task set (search, open, form submit, add to cart) across top 50 sites.
- **Median action‑to‑speech latency:** ≤3.5s (P95 ≤6s).
- **ASR command error rate:** ≤8%.
- **User satisfaction (CSAT):** ≥4.2/5 in pilot.
- **Accessibility coverage:** ≥95% of pages produce a valid semantic summary (no fatal extractor errors).

---

## 6) Functional Requirements
### 6.1 Voice Command Loop
- Hotword ("Lighthouse") or push‑to‑talk.
- ASR transcribes audio in near‑real‑time.
- NLU converts transcript → intents/slots (Navigate, Click, Focus, Type, Submit, Read, Summarize, Describe Changes, List Elements, Scroll, Back, Forward, Tab, Select #n, Confirm/Cancel, Help).
- Planner maps intent to browser actions and generates a **Safety Plan** (dry‑run with confirmations for risky actions).
- Executor runs actions programmatically (Selenium v1; see Tech Stack), tracks focus, waits for network/DOM idle, retries on transient failures.
- Perception module extracts accessibility tree + DOM, computes diffs, and summarizes.
- TTS speaks back; optional braille display output via screen reader bridge.

### 6.2 Screen Description & Diffing
- After each action, produce a **structured snapshot**:
  - Title, URL domain, main region landmarks (header/nav/main/aside/footer), primary H1.
  - Focused element role/name/state; aria‑label/title/innerText.
  - Top actionable elements (up to 5) with ordinal indexing.
  - Notifications/toasts, errors, validation messages.
- **Change detection** between snapshots using DOM + Accessibility Tree diffs (new dialogs, route changes, form errors, count changes, network status).

### 6.3 Disambiguation & Listing
- When multiple matches, read out short numbered list: “I found 4 ‘Add to cart’ buttons: 1) 64GB, 2) 128GB … Say a number.”
- Allow follow‑ups like “the second one,” “the one under the price,” “the blue button.”

### 6.4 Forms & Tables
- Form filling: map labels → inputs (by `for`, proximity, or ARIA). Confirm before submit.
- Tables: announce dimensions, header row/column, allow queries (“read row 3,” “filter status = shipped”).

### 6.5 Error Handling
- Timeouts lead to suggestions (“This page may require scrolling or consent. Try ‘accept cookies’?”).
- Recovery strategies: refresh, re‑query element, alternative selectors, step back.

---

## 7) Non‑Functional Requirements
- **Latency:** streaming ASR; incremental TTS.
- **Reliability:** deterministic replays from intent/action logs.
- **Privacy:** on‑device option for ASR/TTS; redact secrets; never store audio by default.
- **Security:** allowlist domains per mode; confirmations for destructive actions; sandbox profiles.
- **Compatibility:** Chromium (v1), Firefox (v2), Mac/Win/Linux.

---

## 8) Competitive/Standards Context
- Works alongside NVDA/JAWS/VoiceOver; adheres to WAI‑ARIA; uses axe‑core for page accessibility signals to improve summaries.

---

## 9) System Architecture (v1)
**Client (desktop app or headless service)**
- Audio Capture + VAD → ASR → NLU/Planner → Safety Plan → Executor (browser automation) → Perception (AXTree/DOM/OCR/CV) → Summarizer → TTS → Audio Out.

**Browser Control**
- Selenium WebDriver (Chromium) with CDP bridges for robust waits; Page Objects for common sites; Shadow DOM handling; network idle heuristics.

**State**
- Per‑tab session store: current URL, focus, last snapshot hash, breadcrumb of actions, retry budget.

**Observability**
- Structured logs of intents, selectors, timings; redaction of PII; replay harness.

---

## 10) Detailed Components & Tech Choices
### 10.1 Speech‑to‑Text (ASR)
- **On‑device:** OpenAI Whisper (small/base) for privacy; Vosk (lightweight) as fallback.
- **Cloud (opt‑in):** Azure Speech, Google Cloud Speech‑to‑Text for low latency and phone‑quality audio.
- **Extras:** Hotword detection (Picovoice Porcupine), WebRTC or Silero VAD; noise suppression (RNNoise).

### 10.2 NLU & Dialogue/Planning
- Intent/slot model via Rasa or a lightweight rule+LM hybrid.
- LLM planner (few‑shot) with constrained action schema (JSON) and validators.
- Domain ontologies for common sites (Search, E‑commerce, Docs, Email) to bias plans.

### 10.3 Browser Automation (Beyond Selenium)
- **Selenium** (v1) for cross‑browser automation.
- **Chrome DevTools Protocol (CDP)** for: performance timings, accessibility tree (`Accessibility.getFullAXTree`), network events, shadow DOM, interception.
- **Playwright** (v2 candidate) for more resilient selectors, auto‑waits, and accessibility snapshot; or **Puppeteer** if staying Chromium‑only.
- **Accessibility APIs:** Use the **AXTree** via CDP, roles/names/states, and landmarks; honor ARIA. Optionally query OS APIs (UIAutomation on Windows, AX API on macOS) when integrating with native dialogs.

### 10.4 Perception & Summarization
- **DOM/AX extraction** → **Semantic Graph** (landmarks, headings, forms, controls).
- **Diff engine** (pre/post action) highlights added/removed/changed nodes.
- **OCR** for canvas/images (Tesseract or PaddleOCR).
- **Computer Vision** for unlabeled controls (OpenCV + LayoutParser; optional vision‑language model for descriptions).
- **Summarizer**: LLM constrained to short, structured templates to avoid verbosity.

### 10.5 Text‑to‑Speech (TTS)
- **On‑device:** Coqui‑TTS; macOS `say` as baseline.
- **Cloud (opt‑in):** Amazon Polly, Azure Neural TTS, ElevenLabs for naturalness.
- **Output policies:** Rate/verbosity settings; earcons for events; interruptible speech.

### 10.6 Accessibility & Quality
- **axe‑core** to detect issues; use signals to improve summaries (e.g., warn if unlabeled button).
- **ARIA best‑practice heuristics** in the planner (prefer role=button over generic divs).

### 10.7 Data & Storage
- Local, encrypted store of: command logs, snapshots (hashed), configs. No raw audio unless user opts‑in.

---

## 11) UX Spec (Voice Examples)
- “Go to **bbc.com**.”
- “Search for **chess clocks on Amazon**.”
- “Open result **number 2**.”
- “**Describe this page**.” → “Product page: Sony WH‑1000XM5. Main actions: 1) Add to Cart, 2) Buy Now, 3) Compare… There are 5 reviews, average 4.7.”
- “**What changed?**” → “A dialog named ‘Cookies’ appeared with 2 buttons: Accept, Reject.”
- “**Fill form**: email… password… **submit**.”
- “**List buttons**” → “I found 7. Say a number to choose, or say ‘more context’.”
- “**Stop** / **Cancel** / **Undo last**.”

**Speech Output Template (v1):**
- Title + H1; Focus summary; Key actions (≤3); Notifications/errors; Short hint (“Say ‘list buttons’ or ‘what changed’.”)

---

## 12) Safety & Privacy
- **Confirmation gates** for deletes, purchases, payments, account changes.
- **Domain allowlists** and mode (Read‑Only vs. Control). Read‑Only narrates without clicking.
- **Redaction** of secrets in logs; prevent typing passwords unless explicitly dictated.
- **Sandboxed profiles**; optional VPN when testing.

---

## 13) Telemetry & Analytics
- Latency buckets (ASR, plan, execute, perceive, TTS), intent confusion matrix, selector reliability, page types, failure reasons.

---

## 14) Test Plan
- **Unit:** parser, selector builders, diff engine.
- **Integration:** 30 canonical pages (news, ecommerce, docs, forms, tables, modals, infinite scroll).
- **End‑to‑End:** scripted voice tasks with golden transcripts and expected summaries.
- **Accessibility Bench:** axe‑core score deltas before/after actions.
- **Manual screen‑reader parity checks** with NVDA/VoiceOver for critical flows.

---

## 15) Milestones / Roadmap
**M1 (4–6 weeks):**
- CLI prototype: speech → Navigate/Click/Type/Submit on Chromium using Selenium + CDP; basic Describe/What Changed on 10 sites.

**M2 (6–8 weeks):**
- Robust disambiguation lists; form filling; table reading; confirmation gates; telemetry.

**M3 (8–10 weeks):**
- Playwright evaluation; OCR for canvas content; improved summarizer; pilot with 10 users.

**M4 (10–12 weeks):**
- Packaging (desktop app), domain modes, privacy settings, broader site coverage.

---

## 16) Open Questions (for v2 planning)
- How to integrate directly with NVDA/JAWS event streams for richer updates?
- Should we add a small on‑screen overlay for sighted supporters (toggleable)?
- How to share repeatable task macros safely with other users?

---

## 17) Technical Appendix
### 17.1 Minimal Reference Stack (Python‑first)
- **Automation:** Selenium 4 + undetected‑chromedriver; optional Playwright.
- **CDP Access:** `selenium.webdriver.devtools` or `pychrome` for AXTree.
- **ASR:** Whisper (small/base) via `openai-whisper` or `faster-whisper`; VAD via `webrtcvad` or Silero.
- **NLU/Planner:** Rasa (intents) + lightweight LLM (few‑shot with JSON schema) using guardrails/`pydantic` validation.
- **TTS:** Coqui‑TTS or system TTS; adapters for Azure/Polly.
- **CV/OCR:** OpenCV + Tesseract (`pytesseract`) or PaddleOCR for non‑text UI.
- **Accessibility:** axe‑core (via `axe-playwright` for tests), ARIA heuristics library.
- **App Shell:** Electron or Tauri (desktop), or a Flask/FastAPI service with a small UI.
- **Observability:** `structlog`, OpenTelemetry (optional), local SQLite for runs.

### 17.2 Example Action Schema
```json
{
  "intent": "click",
  "target": {
    "by": ["role", "name"],
    "role": "button",
    "name": "Add to cart",
    "ordinal": 1
  },
  "safety": {"confirmation_required": true},
  "retry": {"max": 2, "backoff_ms": 500}
}
```

### 17.3 Pseudocode — Describe Page
```python
ax = cdp.accessibility.get_full_ax_tree()
landmarks = extract_landmarks(ax)
focus = extract_focus(ax)
actions = rank_actionables(ax)[:5]
notif = detect_notifications(ax, dom)
return render_template(title, h1, focus, actions, notif)
```

### 17.4 Example Selenium Selector Strategy
1) Prefer role/name via AXTree → map to CSS/XPath.
2) If ambiguous: constrain by region (main/dialog), proximity to text, and visibility.
3) Fallback: CV/OCR hit‑testing when DOM is inaccessible (canvas apps).

---

## 18) Dependencies Beyond Selenium (Summary)
- **ASR:** Whisper, Azure Speech, Google STT; VAD (WebRTC/Silero); hotword (Porcupine).
- **NLU/Planning:** Rasa or LLM (with guardrails/JSON schema).
- **TTS:** Coqui‑TTS, Azure Neural TTS, Amazon Polly, ElevenLabs.
- **Accessibility & Extraction:** Chrome DevTools Protocol (AXTree), axe‑core, WAI‑ARIA heuristics.
- **Vision & OCR:** OpenCV, Tesseract/PaddleOCR, optional vision‑language model for screen description.
- **Automation Alternatives:** Playwright (preferred long‑term), Puppeteer (Chromium‑only), OS UIAutomation (Windows/macOS) for edge native dialogs.
- **Testing:** axe‑core, Playwright test runner, deterministic replay harness.
- **Audio IO:** PyAudio/SoundDevice; RNNoise for suppression.

---

## 19) Acceptance Criteria (v1)
- From cold start, user can complete: search → navigate → open result → fill login form → submit → read error/success → add item to cart → describe changes.
- Each step produces a spoken summary ≤6s after action.
- All destructive actions require a verbal confirmation.
- Logs contain redacted, reproducible traces of each session.
- Works on at least 80% of the top 50 Alexa/Tranco sites tested, with a documented skip list and reasons.

