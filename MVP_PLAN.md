# Lighthouse.ai MVP Plan

## Finalized v1 Scope & Acceptance Criteria

### Core Features (2-week MVP)
1. **Voice Command Processing**
   - Push-to-talk activation (spacebar)
   - Basic ASR with Whisper (faster-whisper)
   - Simple NLU for 8 core intents: navigate, click, type, submit, describe, list, stop, help

2. **Browser Automation**
   - Selenium 4 + Chromium with CDP access
   - Basic page navigation and element interaction
   - Accessibility tree extraction via CDP
   - Domain allowlist enforcement

3. **Screen Description**
   - Post-action page summaries (title, main heading, focused element, top 3 actions)
   - Change detection between actions
   - Element listing with numbered disambiguation

4. **Safety & Privacy**
   - Destructive action confirmation (delete, purchase, payment)
   - Domain allowlist (configurable)
   - Local processing by default (no cloud unless opt-in)

### Acceptance Criteria
- [ ] User can navigate to allowed domains by voice
- [ ] User can click buttons/links with disambiguation when needed
- [ ] User can fill simple forms (email, password, submit)
- [ ] User gets spoken feedback after each action (≤4 seconds)
- [ ] Destructive actions require confirmation
- [ ] Works on 5 test sites: Google, Amazon, GitHub, Wikipedia, a form site
- [ ] CLI can run headless or with browser visible
- [ ] FastAPI service provides REST endpoints for testing

### Out of Scope (v1)
- Hotword detection
- Complex form handling
- Table navigation
- Multi-step workflows
- Cloud TTS (local only)
- Advanced error recovery

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Lighthouse.ai MVP                        │
├─────────────────────────────────────────────────────────────┤
│  CLI Runner  │  FastAPI Service  │  Browser Automation     │
│              │                   │                         │
│  ┌─────────┐ │  ┌─────────────┐  │  ┌─────────────────────┐ │
│  │ Voice   │ │  │ REST API    │  │  │ Selenium + CDP      │ │
│  │ Handler │ │  │ Endpoints   │  │  │ - Navigation        │ │
│  └─────────┘ │  └─────────────┘  │  │ - Element Finding  │ │
│              │                   │  │ - AX Tree Access   │ │
│  ┌─────────┐ │  ┌─────────────┐  │  └─────────────────────┘ │
│  │ ASR     │ │  │ Session     │  │                         │
│  │ (Whisper)│ │  │ Manager    │  │  ┌─────────────────────┐ │
│  └─────────┘ │  └─────────────┘  │  │ Safety & Privacy    │ │
│              │                   │  │ - Domain Allowlist  │ │
│  ┌─────────┐ │  ┌─────────────┐  │  │ - Confirmation Gates│ │
│  │ NLU     │ │  │ State Store │  │  └─────────────────────┘ │
│  │ (Simple)│ │  └─────────────┘  │                         │
│  └─────────┘ │                   │                         │
│              │                   │                         │
│  ┌─────────┐ │                   │                         │
│  │ TTS     │ │                   │                         │
│  │ (Coqui) │ │                   │                         │
│  └─────────┘ │                   │                         │
└─────────────────────────────────────────────────────────────┘
```

### Component Boundaries
- **CLI Runner**: Entry point, voice capture, user interaction
- **FastAPI Service**: REST API for testing, session management
- **Browser Automation**: Selenium wrapper with CDP access
- **ASR Module**: Whisper integration with VAD
- **NLU Module**: Simple intent classification
- **TTS Module**: Coqui TTS with cloud abstraction
- **Safety Module**: Domain allowlist, confirmation gates
- **State Module**: Session persistence, action history

---

## File/Folder Structure

```
lighthouse/
├── README.md                          # Quickstart and privacy notes
├── Makefile                           # Build, test, run commands
├── pyproject.toml                     # Pinned dependencies
├── .env.example                       # Environment variables template
├── .gitignore                         # Git ignore patterns
├── cli.py                             # CLI entry point
├── main.py                            # FastAPI service entry point
├── config/
│   ├── __init__.py                    # Configuration module
│   ├── settings.py                    # App settings and constants
│   └── domains.yaml                   # Domain allowlist configuration
├── core/
│   ├── __init__.py                    # Core module
│   ├── asr.py                         # Speech-to-text with Whisper
│   ├── nlu.py                         # Natural language understanding
│   ├── tts.py                         # Text-to-speech with Coqui
│   ├── browser.py                     # Selenium browser automation
│   ├── safety.py                      # Safety and privacy controls
│   └── state.py                       # Session state management
├── api/
│   ├── __init__.py                    # API module
│   ├── routes.py                      # FastAPI route definitions
│   └── models.py                      # Pydantic models
├── utils/
│   ├── __init__.py                    # Utilities module
│   ├── audio.py                       # Audio processing utilities
│   ├── accessibility.py               # Accessibility tree helpers
│   └── logging.py                     # Structured logging setup
├── tests/
│   ├── __init__.py                    # Test module
│   ├── test_cli.py                    # CLI tests
│   ├── test_api.py                    # API tests
│   ├── test_browser.py                # Browser automation tests
│   └── fixtures/                      # Test fixtures and data
└── scripts/
    ├── setup.sh                       # Development setup script
    └── test_sites.py                  # Test site validation script
```

---

## Task List (Ordered by Dependencies)

### Phase 1: Foundation (Days 1-3)
1. **Setup project structure** - Create folders, basic files, git init
2. **Configure dependencies** - pyproject.toml, Makefile, .env.example
3. **Setup logging** - Structured logging with redaction
4. **Create config system** - Settings, domain allowlist, environment handling

### Phase 2: Core Components (Days 4-7)
5. **Implement ASR module** - Whisper integration with VAD
6. **Implement TTS module** - Coqui TTS with cloud abstraction
7. **Create browser automation** - Selenium + CDP wrapper
8. **Implement safety module** - Domain allowlist, confirmation gates

### Phase 3: Intelligence Layer (Days 8-10)
9. **Create simple NLU** - Intent classification for 8 core commands
10. **Implement accessibility helpers** - AX tree extraction, element finding
11. **Create state management** - Session persistence, action history

### Phase 4: Integration (Days 11-12)
12. **Build CLI interface** - Voice capture, command processing loop
13. **Create FastAPI service** - REST endpoints for testing
14. **Implement change detection** - Page diffing, summary generation

### Phase 5: Testing & Polish (Days 13-14)
15. **Write unit tests** - Core module testing
16. **Create integration tests** - End-to-end voice command testing
17. **Test on target sites** - Google, Amazon, GitHub, Wikipedia, forms
18. **Documentation and README** - Quickstart guide, privacy notes

### Dependencies
- Tasks 1-4 can be done in parallel
- Tasks 5-7 depend on task 1
- Task 8 depends on tasks 1, 7
- Tasks 9-11 depend on tasks 5-8
- Tasks 12-14 depend on tasks 9-11
- Tasks 15-18 depend on tasks 12-14

---

## Success Metrics (MVP)
- **Task Success Rate**: ≥80% on 5 test sites
- **Response Time**: ≤4s from command to speech output
- **ASR Accuracy**: ≥90% for clear speech
- **Safety**: 100% confirmation for destructive actions
- **Privacy**: 100% local processing by default
