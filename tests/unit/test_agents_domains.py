"""
Unit tests for optimization_core.agents.domains re-exports and agent instantiations.
"""

import pytest
from optimization_core.agents.domains import (
    CodeInterpreterAgent,
    DataAnalysisAgent,
    RLAgent,
    MathAgent,
    MarketingAgent,
    ResearchAgent,
    SystemAgent,
    BlockchainAgent,
)
from optimization_core.agents.framework.models import AgentConfig


def test_domains_exports():
    assert CodeInterpreterAgent is not None
    assert DataAnalysisAgent is not None
    assert RLAgent is not None
    assert MathAgent is not None
    assert MarketingAgent is not None
    assert ResearchAgent is not None
    assert SystemAgent is not None
    assert BlockchainAgent is not None


def test_code_interpreter_agent_instantiation():
    cfg = AgentConfig(agent_id="code_test", model_name="test_model")
    agent = CodeInterpreterAgent(config=cfg)
    assert agent.name == "CodeInterpreterAgent"


def test_data_analysis_agent_instantiation():
    cfg = AgentConfig(agent_id="data_test", model_name="test_model")
    agent = DataAnalysisAgent(config=cfg)
    assert agent.name == "DataAnalysisAgent"


def test_rl_agent_instantiation():
    cfg = AgentConfig(agent_id="rl_test", model_name="test_model")
    agent = RLAgent(config=cfg)
    assert agent.name == "EmbodiedRLAgent"


def test_math_agent_instantiation():
    agent = MathAgent(name="MathTest")
    assert agent.name == "MathTest"


def test_marketing_agent_instantiation():
    cfg = AgentConfig(agent_id="marketing_test", model_name="test_model")
    agent = MarketingAgent(config=cfg)
    assert agent.name == "MarketingAgent"
