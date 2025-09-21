# Lighthouse.ai MVP - Task List

## Phase 1: Foundation (Days 1-3)

### Issue #1: Setup Project Structure
**Priority**: High | **Estimated**: 2 hours | **Dependencies**: None

Create the basic project structure and initial files:

- [ ] Create directory structure as defined in MVP_PLAN.md
- [ ] Initialize git repository
- [ ] Create empty `__init__.py` files in all packages
- [ ] Setup basic logging configuration
- [ ] Create placeholder files for all modules

**Acceptance Criteria**:
- All directories exist with proper `__init__.py` files
- Git repository initialized with proper `.gitignore`
- Basic logging setup working
- Project structure matches the defined architecture

---

### Issue #2: Configure Dependencies and Build System
**Priority**: High | **Estimated**: 1 hour | **Dependencies**: #1

Setup the build system and dependency management:

- [ ] Verify `pyproject.toml` works with `pip install -e .`
- [ ] Test `make install` and `make dev-install`
- [ ] Verify all pinned dependencies can be installed
- [ ] Setup pre-commit hooks configuration
- [ ] Test build process with `make build`

**Acceptance Criteria**:
- All dependencies install without conflicts
- Development environment setup works
- Pre-commit hooks are configured
- Build process completes successfully

---

### Issue #3: Setup Logging and Configuration System
**Priority**: High | **Estimated**: 3 hours | **Dependencies**: #1

Implement structured logging and configuration management:

- [ ] Create `utils/logging.py` with structured logging setup
- [ ] Create `config/settings.py` with Pydantic settings
- [ ] Implement environment variable loading
- [ ] Add log redaction for PII
- [ ] Create configuration validation

**Acceptance Criteria**:
- Structured logging works with proper formatting
- Configuration loads from environment variables
- PII redaction works in logs
- Settings validation catches configuration errors

---

### Issue #4: Create Domain Allowlist Configuration
**Priority**: Medium | **Estimated**: 2 hours | **Dependencies**: #3

Implement domain security configuration:

- [ ] Create `config/domains.yaml` with allowlist
- [ ] Implement domain validation logic
- [ ] Add restricted actions configuration
- [ ] Create domain checking utilities
- [ ] Add configuration loading for domains

**Acceptance Criteria**:
- Domain allowlist is configurable via YAML
- Domain validation works correctly
- Restricted actions are properly defined
- Configuration can be reloaded without restart

---

## Phase 2: Core Components (Days 4-7)

### Issue #5: Implement ASR Module with Whisper
**Priority**: High | **Estimated**: 6 hours | **Dependencies**: #3

Create speech-to-text functionality using faster-whisper:

- [ ] Install and configure faster-whisper
- [ ] Implement audio capture with PyAudio
- [ ] Add WebRTC VAD for voice activity detection
- [ ] Create ASR service class with streaming support
- [ ] Add model downloading and caching
- [ ] Implement audio preprocessing (noise reduction)

**Acceptance Criteria**:
- Whisper model loads and processes audio correctly
- VAD detects speech start/end accurately
- Audio capture works on target platforms
- Streaming transcription works in real-time
- Model files are cached locally

---

### Issue #6: Implement TTS Module with Coqui
**Priority**: High | **Estimated**: 4 hours | **Dependencies**: #3

Create text-to-speech functionality using Coqui TTS:

- [ ] Install and configure Coqui TTS
- [ ] Implement TTS service class
- [ ] Add audio output with proper device selection
- [ ] Create cloud TTS abstraction layer
- [ ] Implement speech rate and voice controls
- [ ] Add audio queue management

**Acceptance Criteria**:
- Coqui TTS generates natural-sounding speech
- Audio output works on target platforms
- Cloud TTS abstraction is ready for future use
- Speech controls (rate, voice) work correctly
- Audio queue prevents overlapping speech

---

### Issue #7: Create Browser Automation with Selenium + CDP
**Priority**: High | **Estimated**: 8 hours | **Dependencies**: #3

Implement browser automation using Selenium 4 with Chrome DevTools Protocol:

- [ ] Setup Selenium WebDriver with Chrome
- [ ] Implement CDP access for accessibility tree
- [ ] Create element finding strategies (role, name, text)
- [ ] Add page navigation and interaction methods
- [ ] Implement wait strategies for dynamic content
- [ ] Add screenshot and DOM capture capabilities

**Acceptance Criteria**:
- Browser automation works reliably
- CDP provides accessibility tree data
- Element finding works with multiple strategies
- Dynamic content waits work correctly
- Screenshots and DOM capture function properly

---

### Issue #8: Implement Safety and Privacy Controls
**Priority**: High | **Estimated**: 4 hours | **Dependencies**: #4, #7

Create safety mechanisms for destructive actions and privacy:

- [ ] Implement domain allowlist checking
- [ ] Add confirmation gates for restricted actions
- [ ] Create action logging with redaction
- [ ] Implement session isolation
- [ ] Add privacy controls for data handling

**Acceptance Criteria**:
- Domain allowlist prevents navigation to blocked sites
- Destructive actions require explicit confirmation
- All actions are logged with PII redaction
- Sessions are properly isolated
- Privacy controls work as configured

---

## Phase 3: Intelligence Layer (Days 8-10)

### Issue #9: Create Simple NLU for Voice Commands
**Priority**: High | **Estimated**: 6 hours | **Dependencies**: #5

Implement natural language understanding for voice commands:

- [ ] Define intent schema for 8 core commands
- [ ] Implement intent classification logic
- [ ] Add entity extraction for targets and values
- [ ] Create command validation and normalization
- [ ] Add confidence scoring and fallback handling

**Acceptance Criteria**:
- All 8 core intents are recognized correctly
- Entity extraction works for common patterns
- Commands are validated before execution
- Confidence scoring helps with disambiguation
- Fallback handling provides helpful error messages

---

### Issue #10: Implement Accessibility Helpers
**Priority**: High | **Estimated**: 5 hours | **Dependencies**: #7

Create utilities for working with accessibility data:

- [ ] Implement accessibility tree parsing
- [ ] Add element role and state extraction
- [ ] Create landmark and heading detection
- [ ] Implement actionable element ranking
- [ ] Add focus management utilities

**Acceptance Criteria**:
- Accessibility tree is parsed correctly
- Element roles and states are extracted
- Landmarks and headings are identified
- Actionable elements are ranked by importance
- Focus management works reliably

---

### Issue #11: Create State Management System
**Priority**: Medium | **Estimated**: 4 hours | **Dependencies**: #3

Implement session state and action history:

- [ ] Create session state storage
- [ ] Implement action history tracking
- [ ] Add state persistence and recovery
- [ ] Create session cleanup and timeout handling
- [ ] Add state validation and error recovery

**Acceptance Criteria**:
- Session state is maintained correctly
- Action history is tracked and accessible
- State persistence works across restarts
- Session cleanup prevents memory leaks
- State validation catches inconsistencies

---

## Phase 4: Integration (Days 11-12)

### Issue #12: Build CLI Interface
**Priority**: High | **Estimated**: 6 hours | **Dependencies**: #5, #6, #9, #11

Create the command-line interface for voice interaction:

- [ ] Implement voice capture loop
- [ ] Add push-to-talk functionality (spacebar)
- [ ] Create command processing pipeline
- [ ] Add user feedback and status display
- [ ] Implement graceful shutdown handling

**Acceptance Criteria**:
- Voice capture works reliably
- Push-to-talk activation is responsive
- Command processing pipeline works end-to-end
- User feedback is clear and helpful
- Shutdown is graceful and safe

---

### Issue #13: Create FastAPI Service
**Priority**: Medium | **Estimated**: 4 hours | **Dependencies**: #7, #9, #11

Build REST API for testing and integration:

- [ ] Create FastAPI application structure
- [ ] Implement REST endpoints for core functions
- [ ] Add request/response models with Pydantic
- [ ] Create API documentation with OpenAPI
- [ ] Add error handling and validation

**Acceptance Criteria**:
- FastAPI service starts and runs correctly
- REST endpoints work for all core functions
- API documentation is complete and accurate
- Error handling provides helpful responses
- Request/response validation works properly

---

### Issue #14: Implement Change Detection and Summarization
**Priority**: High | **Estimated**: 5 hours | **Dependencies**: #7, #10

Create page change detection and summary generation:

- [ ] Implement DOM diffing between actions
- [ ] Create page summary generation
- [ ] Add change detection for dynamic content
- [ ] Implement element listing with disambiguation
- [ ] Add notification and error detection

**Acceptance Criteria**:
- DOM changes are detected accurately
- Page summaries are concise and helpful
- Dynamic content changes are captured
- Element listing provides clear disambiguation
- Notifications and errors are properly detected

---

## Phase 5: Testing & Polish (Days 13-14)

### Issue #15: Write Unit Tests
**Priority**: High | **Estimated**: 6 hours | **Dependencies**: #5-#14

Create comprehensive unit test suite:

- [ ] Test ASR module with sample audio
- [ ] Test TTS module with sample text
- [ ] Test browser automation with mock pages
- [ ] Test NLU with sample commands
- [ ] Test safety controls with various scenarios

**Acceptance Criteria**:
- All core modules have unit tests
- Test coverage is above 80%
- Tests run reliably in CI environment
- Mock objects are used appropriately
- Edge cases are covered

---

### Issue #16: Create Integration Tests
**Priority**: High | **Estimated**: 4 hours | **Dependencies**: #15

Build end-to-end integration tests:

- [ ] Test complete voice command workflows
- [ ] Test API endpoints with real requests
- [ ] Test browser automation on real sites
- [ ] Test error handling and recovery
- [ ] Test performance under load

**Acceptance Criteria**:
- End-to-end workflows work correctly
- API integration tests pass
- Real site testing works reliably
- Error handling is tested thoroughly
- Performance meets requirements

---

### Issue #17: Test on Target Sites
**Priority**: High | **Estimated**: 4 hours | **Dependencies**: #16

Validate functionality on target websites:

- [ ] Test navigation on Google, Amazon, GitHub, Wikipedia
- [ ] Test form filling on a test form site
- [ ] Validate accessibility on each target site
- [ ] Test error handling on problematic sites
- [ ] Document any site-specific issues

**Acceptance Criteria**:
- All target sites work correctly
- Form filling works on test sites
- Accessibility is properly handled
- Error handling works for edge cases
- Site-specific issues are documented

---

### Issue #18: Documentation and Final Polish
**Priority**: Medium | **Estimated**: 3 hours | **Dependencies**: #17

Complete documentation and final polish:

- [ ] Update README with final instructions
- [ ] Add inline code documentation
- [ ] Create troubleshooting guide
- [ ] Add performance benchmarks
- [ ] Final code review and cleanup

**Acceptance Criteria**:
- Documentation is complete and accurate
- Code is well-documented
- Troubleshooting guide is helpful
- Performance benchmarks are documented
- Code passes final review

---

## Dependencies Summary

```
Phase 1: #1 → #2, #3, #4
Phase 2: #3 → #5, #6, #7 → #8
Phase 3: #5, #7 → #9, #10 → #11
Phase 4: #5, #6, #9, #11 → #12
         #7, #9, #11 → #13
         #7, #10 → #14
Phase 5: #5-#14 → #15 → #16 → #17 → #18
```

## Success Criteria

- [ ] All 18 issues completed
- [ ] 80%+ test coverage
- [ ] Works on 5 target sites
- [ ] Response time ≤4 seconds
- [ ] ASR accuracy ≥90%
- [ ] 100% safety confirmation for destructive actions
- [ ] 100% local processing by default
