# Tsukuyomi Restructuring - Migration Tracker

**Version:** 1.3 | **Date:** 2026-02-23 | **Status:** In Progress

---

## Progress Overview

| Phase | Description | Status | Completion |
|-------|-------------|--------|------------|
| 1 | Create Directory Structure | ✅ Complete | 100% |
| 2 | Move Files | ✅ Complete | 100% |
| 3 | Refactor Classes | ✅ Complete | 100% |
| 4 | Create Entry Point | ✅ Complete | 100% |
| 5 | Update Tests | ⏳ In Progress | 75% |
| 6 | Cleanup | ⬜ Not Started | 0% |

---

## File Size Compliance - All Files Under 700 Lines ✅

All files now comply with the 700-line limit. The following files were split:

| Original File | Lines | Split Into |
|---------------|-------|------------|
| `agents/social/persuasion.py` | 947 | persuasion.py (576) + persuasion_types.py (209) |
| `agents/internal/personality/drift_monitor.py` | 919 | drift_monitor.py (449) + drift_types.py (53) + evolution_manager.py (154) |
| `agents/cognitive/reasoning/reasoning_validator.py` | 901 | reasoning_validator.py (543) + validation_types.py (160) |
| `agents/cognitive/memory/retrieval.py` | 763 | retrieval.py (252) + retrieval_types.py (81) + memory_store.py (132) |

---

## Test Suite Status

**Current Results:** 525 passed / 139 failed / 39 skipped (74.8% pass rate)

### ✅ Async Event Loop Issues - FIXED (2026-02-23)
- Updated `conftest.py` with proper event loop fixture for Python 3.10+
- All async tests now pass (test_grpc.py: 14/14 passing)

### Test Files by Status:

| Status | Test File | Issue |
|--------|-----------|-------|
| ✅ | test_grpc.py | All 14 tests passing |
| ✅ | test_proposal_window.py | Migrated |
| ✅ | test_working_memory.py | Migrated |
| ⚠️ | test_emotional_expression.py | API signature changes (22 failures) |
| ⚠️ | test_emotional_integration.py | Missing methods (18 failures) |
| ⚠️ | test_drama_enhancements.py | API mismatch (12 failures) |
| ⚠️ | test_belief_plasticity.py | Missing methods (11 failures) |
| ⚠️ | test_statemanager.py | PersonalityBaseline.ANGRY_MAN removed |

---

## Package Exports Updated (2026-02-23):

### `tsukuyomi/__init__.py`
- Updated docstring with correct import paths
- Changed version to "0.1.0" (MVP)

### `tsukuyomi/services/__init__.py`
- Added exports: LLMService, EmbeddingService, VectorStore, DBManager

### `tsukuyomi/agents/__init__.py`
- Simplified to avoid circular imports
- Uses submodule imports pattern

### `tsukuyomi/agents/internal/personality/__init__.py`
- Added: BehaviorSnapshot, DriftReport, PersonalityEvolutionEvent, PersonalityEvolutionManager

### `tsukuyomi/agents/cognitive/reasoning/__init__.py`
- Added: ReasoningViolation, ViolationType, ViolationSeverity

### `tsukuyomi/agents/cognitive/memory/__init__.py`
- Added: RetrievalMode, RetrievalContext, RetrievalWeights, ScoredMemory, MemoryStore

---

## Remaining Work:

1. **Update experiment imports** (27 old import paths in experiments/)
2. **Fix test API mismatches** (~139 failing tests)
3. **Add PersonalityBaseline.ANGRY_MAN** or update tests

---

## Quick Validation Commands
```bash
# Test imports
python -c "from tsukuyomi.agents.cognitive.memory import MemoryRetrieval; print('OK')"

# Check file sizes
find tsukuyomi -name "*.py" -exec wc -l {} \; | sort -rn | head -10

# Run tests
python -m pytest tests/ --tb=no -q
```

---

**Last Updated:** 2026-02-23
