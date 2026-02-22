# Tsukuyomi Restructuring - Migration Tracker

**Version:** 1.0 | **Date:** 2026-02-21 | **Status:** Ready to Begin

---

## Progress Overview

| Phase | Description | Status | Completion |
|-------|-------------|--------|------------|
| 1 | Create Directory Structure | ⬜ Not Started | 0% |
| 2 | Move Files | ⬜ Not Started | 0% |
| 3 | Refactor Classes | ⬜ Not Started | 0% |
| 4 | Create Entry Point | ⬜ Not Started | 0% |
| 5 | Update Tests | ⬜ Not Started | 0% |
| 6 | Cleanup | ⬜ Not Started | 0% |

---

## Phase 1: Shared Utilities (Extract Common Code)
- [ ] Create shared/ directory structure.
- [ ] Create shared/config.py and shared/logging.py.
- [ ] Create shared/exceptions.py.
- [ ] Move proto/utils.py logic to shared/utils.py.
- [ ] Extract common 	ypes.py into shared/.
- [ ] Update imports for shared utilities.

## Phase 2: Shared Services & Large Splits
- [ ] Create services/ directory structure.
- [ ] **Split rain/llm_service.py (825L)** into services/llm/ (provider.py, openai_provider.py, groq_provider.py, service.py, prompts.py).
- [ ] Move rain/embedding_service.py to services/embedding/service.py.
- [ ] Move rain/vector_store.py to services/vector/store.py.
- [ ] Move proto/db_manager.py to services/database/manager.py.

## Phase 3: Scenarios Integration
- [ ] Move core/scenarios/scenario_schema.py to scenarios/schema.py.
- [ ] Move core/scenarios/scenario_loader.py to scenarios/loader.py.
- [ ] Verify test suite 	est_scenario_loader.py passes with new paths.

## Phase 4: Transport Layer
- [ ] Create 	ransport/ directory.
- [ ] Move compiled proto files (*.pb2.py, *.pb2_grpc.py).
- [ ] Move proto/grpc_client.py to 	ransport/grpc/client.py.
- [ ] **Split proto/grpc_server.py** into Server core, FateServicer, and GuestServicer.
- [ ] Move root guest_sdk.py to 	ransport/sdk/guest.py.

## Phase 5: Environment System Untangling
- [ ] Create nvironment/ directory structure.
- [ ] **Untangle Fate Engine**: Merge proto/fate_engine.py + tick loop from ate_resolvers.py into nvironment/core/engine.py.
- [ ] Move resolution logic from ate_resolvers.py to nvironment/core/resolution.py.
- [ ] Move core/proposal_window.py to nvironment/core/proposal.py.
- [ ] **Split core/spatial_index.py (857L)** into spatial.py and spatial_query.py.
- [ ] Move rain/spatial_utils.py (Raycaster) to nvironment/physics/raycasting.py.
- [ ] Move proto/physics/spatial_logic.py to nvironment/physics/spatial_logic.py.
- [ ] Move core/world_builder.py and core/affordance.py.
- [ ] Move proto/action_logic.py.

## Phase 6: Narrative System
- [ ] Create 
arrative/ directory structure.
- [ ] Move rain/drama_director.py to 
arrative/core/director.py.
- [ ] Move rain/catalyst_system.py to 
arrative/core/catalyst.py.
- [ ] Move core/drama/event_library.py to 
arrative/events/library.py.
- [ ] Move core/drama/branch_manager.py to 
arrative/flow/branching.py.
- [ ] Move core/drama/context_aware_director.py to 
arrative/context/context_aware.py.

## Phase 7: Agent System
- [ ] Create gents/ structure (core, cognitive, internal, social, 
untime, prompts).
- [ ] Move gent/universal_agent.py to gents/runtime/standalone_agent.py.
- [ ] **Split core/emotion/unified.py (1426L)** into 4 files in gents/internal/.
- [ ] **Move core/belief/** to `agents/internal/beliefs/` and **split system.py (956L)** into 2 files.
- [ ] **Split brain/memory/retrieval.py (763L)** into 2 files in `agents/cognitive/.`
- [ ] **Split rain/perception_channels.py (~800L)** into 2 files in gents/cognitive/.
- [ ] **Split rain/reasoning/reasoning_validator.py (~870L)** into 2 files.
- [ ] **Split rain/personality/drift_monitor.py (~850L)** into 2 files.
- [ ] Copy entire contents of rain/memory/, rain/personality/, and rain/reasoning/ to corresponding cognitive/ and internal/ folders.
- [ ] Populate gents/social/: Move rain/gossip_protocol.py, proto/conversation_manager.py, gent/persuasion.py, gent/influence.py.
- [ ] Refactor rain/agent_brain.py (God Class) into gents/runtime/simulation_agent.py and delegate out responsibilities.
- [ ] Move remaining gent/ modules (ehavior.py, proposal_handler.py, context_manager.py, identity.py).

## Phase 8: Final Integration & Tests
- [ ] Create server.py entry point at project root.
- [ ] Fix all 57 tests in 	ests/ to use new import structures.
- [ ] Verify pytest tests/ has 100% pass rate (note: 9 collection errors existed prior to restructuring, verify they are resolved).
- [ ] Delete rain/, gent/, core/, proto/ old directories after confirming they are empty.
- [ ] Update final documentation.

## Rollback Procedure

If migration fails at any phase:

1. **Preserve Progress:**
   ```bash
   git add -A
   git commit -m "Migration checkpoint: Phase X"
   ```

2. **If Complete Rollback Needed:**
   ```bash
   git checkout backup-pre-migration
   ```

3. **If Partial Rollback:**
   - Identify failing component
   - Revert specific files
   - Keep completed phases

---

## Notes

### Dependencies to Install (if needed)
```
# No new dependencies required for restructuring
# Existing requirements.txt should suffice
```

### Environment Variables
```
LLM_PROVIDER=groq
LLM_API_KEY=your_key
LLM_MODEL=llama-3.3-70b-versatile
```

### Quick Validation Commands
```bash
# Check import structure
python -c "from tsukuyomi.agents.core import BaseAgent"
python -c "from tsukuyomi.environment.core import EnvironmentEngine"
python -c "from tsukuyomi.narrative.core import NarrativeDirector"
python -c "from tsukuyomi.services.llm import LLMProvider"

# Run tests
pytest tests/ -v --tb=short

# Check file sizes
find tsukuyomi -name "*.py" -exec wc -l {} \; | sort -rn | head -20
```

---

**Last Updated:** 2026-02-21  
**Next Review:** After Phase 1 completion
