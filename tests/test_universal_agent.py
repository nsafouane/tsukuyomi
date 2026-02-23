"""
Unit Tests for Universal Agent Runtime
=====================================
"""

import pytest
import json
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock

from tsukuyomi.agents.runtime.standalone_agent import (
    AgentState,
    AgentConfig,
    UniversalAgent,
)
from tsukuyomi.agents.core.identity import AgentIdentity


def create_agent(config=None):
    """Factory function for creating agents."""
    return UniversalAgent(config or AgentConfig())


class TestAgentState:
    """Tests for AgentState enum."""
    
    def test_states_exist(self):
        """Test all states are defined."""
        assert AgentState.IDLE.value == "idle"
        assert AgentState.THINKING.value == "thinking"
        assert AgentState.RESPONDING.value == "responding"
        assert AgentState.ACTING.value == "acting"
        assert AgentState.RESTING.value == "resting"


class TestAgentConfig:
    """Tests for AgentConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = AgentConfig()
        
        assert config.llm_provider == "groq"
        assert config.llm_model == "llama-3.3-70b-versatile"
        assert config.prompt_style == "full"
        assert config.auto_memory is True
        assert config.scenario_name == "unknown"
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = AgentConfig(
            llm_model="gpt-4",
            prompt_style="intense",
            scenario_name="jury"
        )
        
        assert config.llm_model == "gpt-4"
        assert config.prompt_style == "intense"
        assert config.scenario_name == "jury"


class TestUniversalAgentInit:
    """Tests for UniversalAgent initialization."""
    
    def test_init_default(self):
        """Test default initialization."""
        agent = UniversalAgent()
        
        assert agent.state == AgentState.IDLE
        assert agent.current_tick == 0
        assert agent.conversation_history == []
    
    def test_init_with_config(self):
        """Test initialization with config."""
        config = AgentConfig(scenario_name="test_scenario")
        agent = UniversalAgent(config)
        
        assert agent.config.scenario_name == "test_scenario"


class TestUniversalAgentIdentity:
    """Tests for identity loading."""
    
    def test_load_identity_from_dict(self):
        """Test loading identity from dictionary."""
        agent = UniversalAgent()
        
        identity_dict = {
            "name": "John Doe",
            "age": 45,
            "occupation": "Worker",
            "origin_story": "Test story",
            "core_values": [],
            "defining_memories": [],
            "personality": None
        }
        
        agent.load_identity(identity_dict=identity_dict)
        
        assert agent.identity is not None
        assert agent.identity.name == "John Doe"
        assert agent.memory is not None
        assert agent.prompt_builder is not None
    
    def test_load_identity_from_file(self):
        """Test loading identity from file."""
        identity_dict = {
            "name": "Jane Doe",
            "age": 30,
            "occupation": "Doctor",
            "origin_story": "Test story",
            "core_values": [],
            "defining_memories": [],
            "personality": None
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(identity_dict, f)
            temp_path = f.name
        
        try:
            agent = UniversalAgent()
            agent.load_identity(identity_file=temp_path)
            
            assert agent.identity.name == "Jane Doe"
        finally:
            os.unlink(temp_path)
    
    def test_load_identity_no_identity_raises(self):
        """Test that loading without identity raises error."""
        agent = UniversalAgent()
        
        with pytest.raises(ValueError):
            agent.load_identity()


class TestUniversalAgentLLM:
    """Tests for LLM integration."""
    
    def test_set_llm(self):
        """Test setting LLM function."""
        agent = UniversalAgent()
        
        async def mock_llm(prompt, **kwargs):
            return "Mock response"
        
        agent.set_llm(mock_llm)
        
        assert agent._llm_call is not None


class TestUniversalAgentRespond:
    """Tests for response generation."""
    
    @pytest.fixture
    def agent_with_llm(self):
        """Create agent with identity and mock LLM."""
        agent = UniversalAgent()
        
        identity_dict = {
            "name": "Test Agent",
            "age": 40,
            "occupation": "Tester",
            "origin_story": "Test story",
            "core_values": [],
            "defining_memories": [],
            "personality": None
        }
        
        agent.load_identity(identity_dict=identity_dict)
        
        async def mock_llm(prompt, **kwargs):
            return "I am a test response"
        
        agent.set_llm(mock_llm)
        
        return agent
    
    @pytest.mark.asyncio
    async def test_respond_basic(self, agent_with_llm):
        """Test basic response generation."""
        response = await agent_with_llm.respond("Hello")
        
        assert response == "I am a test response"
        assert agent_with_llm.total_responses == 1
    
    @pytest.mark.asyncio
    async def test_respond_stores_history(self, agent_with_llm):
        """Test that responses are stored in history."""
        await agent_with_llm.respond("Test input")
        
        assert len(agent_with_llm.conversation_history) == 2
        assert agent_with_llm.conversation_history[0]["role"] == "user"
        assert agent_with_llm.conversation_history[1]["role"] == "agent"
    
    @pytest.mark.asyncio
    async def test_respond_without_identity_raises(self):
        """Test responding without identity raises error."""
        agent = UniversalAgent()
        
        with pytest.raises(RuntimeError, match="identity not loaded"):
            await agent.respond("Hello")
    
    @pytest.mark.asyncio
    async def test_respond_without_llm_raises(self):
        """Test responding without LLM raises error."""
        agent = UniversalAgent()
        agent.load_identity(identity_dict={"name": "Test", "age": 30})
        
        with pytest.raises(RuntimeError, match="LLM not set"):
            await agent.respond("Hello")


class TestUniversalAgentObserve:
    """Tests for observation/memory."""
    
    @pytest.fixture
    def agent(self):
        """Create agent with identity."""
        agent = UniversalAgent()
        agent.load_identity(identity_dict={"name": "Test", "age": 30})
        return agent
    
    @pytest.mark.asyncio
    async def test_observe_stores_memory(self, agent):
        """Test that observations are stored."""
        memory_id = await agent.observe(
            event="Something happened",
            importance=0.7
        )
        
        assert memory_id is not None
        assert agent.memory.get_memory_count() == 1


class TestUniversalAgentReflect:
    """Tests for reflection."""
    
    @pytest.fixture
    def agent_with_llm(self):
        """Create agent with identity and LLM."""
        agent = UniversalAgent()
        agent.load_identity(identity_dict={"name": "Test", "age": 30})
        
        async def mock_llm(prompt, **kwargs):
            return "I have reflected deeply."
        
        agent.set_llm(mock_llm)
        return agent
    
    @pytest.mark.asyncio
    async def test_reflect_basic(self, agent_with_llm):
        """Test basic reflection."""
        # Store a memory first
        await agent_with_llm.observe("Test event")
        
        reflection = await agent_with_llm.reflect()
        
        assert reflection == "I have reflected deeply."


class TestUniversalAgentState:
    """Tests for state management."""
    
    def test_advance_tick(self):
        """Test tick advancement."""
        agent = UniversalAgent()
        agent.advance_tick(5)
        
        assert agent.current_tick == 5
    
    def test_get_state(self):
        """Test state retrieval."""
        agent = UniversalAgent()
        agent.load_identity(identity_dict={"name": "Test", "age": 30})
        
        state = agent.get_state()
        
        assert state["name"] == "Test"
        assert state["state"] == "idle"
        assert state["tick"] == 0
    
    def test_get_emotional_baseline(self):
        """Test emotional baseline retrieval."""
        agent = UniversalAgent()
        agent.load_identity(identity_dict={
            "name": "Test",
            "age": 30,
            "baseline_valence": 0.5
        })
        
        pad = agent.get_emotional_baseline()
        
        assert "valence" in pad
        assert "arousal" in pad
        assert "dominance" in pad


class TestUniversalAgentSaveLoad:
    """Tests for save/load functionality."""
    
    def test_save_state(self):
        """Test saving agent state."""
        agent = UniversalAgent()
        agent.load_identity(identity_dict={"name": "Test", "age": 30})
        agent.total_responses = 5
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            agent.save_state(temp_path)
            
            assert os.path.exists(temp_path)
            
            with open(temp_path) as f:
                data = json.load(f)
            
            assert data["identity"]["name"] == "Test"
            assert data["total_responses"] == 5
        finally:
            os.unlink(temp_path)
    
    def test_load_state(self):
        """Test loading agent state."""
        # Create and save
        agent = UniversalAgent()
        agent.load_identity(identity_dict={"name": "Saved", "age": 35})
        agent.total_responses = 10
        agent.current_tick = 100
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            agent.save_state(temp_path)
            
            # Load
            loaded = UniversalAgent.load_state(temp_path)
            
            assert loaded.identity.name == "Saved"
            assert loaded.total_responses == 10
            assert loaded.current_tick == 100
        finally:
            os.unlink(temp_path)


class TestCreateAgent:
    """Tests for create_agent helper."""
    
    def test_create_agent_basic(self):
        """Test creating agent with helper."""
        config = AgentConfig(scenario_name="test")
        agent = create_agent(config)
        identity_dict = {
            "name": "Helper Agent",
            "age": 25,
            "occupation": "Assistant",
            "origin_story": "Created for testing",
            "core_values": [{"value": "Helpfulness", "source": "Programming", "intensity": 0.8}],
            "defining_memories": [],
            "personality": {"big_five": {"openness": 0.5}}
        }
        agent.load_identity(identity_dict=identity_dict)
        
        assert agent.identity.name == "Helper Agent"
        assert agent.identity.age == 25
        assert agent.config.scenario_name == "test"
        assert agent.memory is not None


class TestEmotionalStateDescription:
    """Tests for emotional state descriptions."""
    
    def test_positive_high_arousal(self):
        """Test positive high arousal state."""
        agent = UniversalAgent()
        agent.load_identity(identity_dict={
            "name": "Test",
            "age": 30,
            "baseline_pad": {"valence": 0.5, "arousal": 0.8, "dominance": 0.0}
        })
        
        state = agent._get_current_emotional_state()
        
        assert "energetic" in state or "positive" in state
    
    def test_negative_high_arousal(self):
        """Test negative high arousal state."""
        agent = UniversalAgent()
        agent.load_identity(identity_dict={
            "name": "Test",
            "age": 30,
            "baseline_pad": {"valence": -0.5, "arousal": 0.8, "dominance": 0.0}
        })
        
        state = agent._get_current_emotional_state()
        
        assert "agitated" in state or "frustrated" in state


class TestConversationHistory:
    """Tests for conversation history management."""
    
    @pytest.fixture
    def agent_with_llm(self):
        """Create agent with mock LLM."""
        agent = UniversalAgent()
        agent.load_identity(identity_dict={"name": "Test", "age": 30})
        
        async def mock_llm(prompt, **kwargs):
            return "Response"
        
        agent.set_llm(mock_llm)
        return agent
    
    @pytest.mark.asyncio
    async def test_history_truncation(self, agent_with_llm):
        """Test that history is truncated when too long."""
        # Generate 30 interactions (60 messages)
        for i in range(30):
            await agent_with_llm.respond(f"Input {i}")
        
        # Should be truncated to 50
        assert len(agent_with_llm.conversation_history) <= 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])