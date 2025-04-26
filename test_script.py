# test_agent.py
import pytest
from agent import Research_Agent

# Optional: to mock web requests
from unittest.mock import patch


@pytest.fixture
def agent():
    return Research_Agent()


def test_normal_query(agent):
    output, news = agent.run("What is Quantum Computing?")
    assert isinstance(output, str)
    assert "Quantum" in output or "computing" in output.lower()
    assert isinstance(news, list)


def test_news_query(agent):
    output, news = agent.run("AI latest news")
    assert isinstance(output, str)
    assert "🔹" in output  # Since your news output uses bullet points
    assert isinstance(news, list)
    assert len(news) > 0


def test_empty_query(agent):
    output, news = agent.run("")
    assert isinstance(output, str)
    assert "Error" in output or "No relevant content" in output or len(output) > 0


@patch('agent.web_scraper')
def test_web_scraper_failure(mock_scraper, agent):
    mock_scraper.side_effect = Exception("Simulated scraping error")
    output, news = agent.run("Python programming basics")
    assert "Error" in output or "No relevant content" in output


def test_conversation_memory(agent):
    query1 = "Explain Machine Learning"
    query2 = "Explain Deep Learning"

    agent.run(query1)
    agent.run(query2)

    memory = agent.get_memory()
    assert isinstance(memory, list)
    assert any("Machine Learning" in msg.content for msg in memory)
    assert any("Deep Learning" in msg.content for msg in memory)

