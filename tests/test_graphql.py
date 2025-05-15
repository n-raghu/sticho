"""
Tests for GraphQL endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from service.run import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_session():
    """Mock the session service to return a valid session."""
    with patch("service.auth.session.SessionService.validate_session") as mock:
        mock.return_value = {
            "user_id": "test-user-id",
            "session_id": "test-session-id",
            "authenticated": True
        }
        yield mock


def test_graphql_hello_unauthenticated(client):
    """Test the hello query without authentication."""
    query = """
    query {
        hello {
            ok
            msg
        }
    }
    """

    # Should raise an exception for unauthenticated requests
    response = client.post("/graphql", json={"query": query}, expect_errors=True)

    # Should return 500 with an error message
    assert response.status_code == 500
    assert "Authentication required" in response.text


def test_graphql_hello_authenticated(client, mock_session):
    """Test the hello query with authentication."""
    query = """
    query {
        hello {
            ok
            msg
        }
    }
    """

    # Add a session cookie to simulate authentication
    client.cookies.set("session", "test-session-token")

    response = client.post("/graphql", json={"query": query})

    # Should return 200 with the expected data
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert data["data"]["hello"]["ok"] is True
    assert "Authentication successful" in data["data"]["hello"]["msg"]


def test_graphql_ping_mutation_authenticated(client, mock_session):
    """Test the ping mutation with authentication."""
    mutation = """
    mutation {
        ping {
            ok
            msg
        }
    }
    """

    # Add a session cookie to simulate authentication
    client.cookies.set("session", "test-session-token")

    response = client.post("/graphql", json={"query": mutation})

    # Should return 200 with the expected data
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert data["data"]["ping"]["ok"] is True
    assert "Ping successful" in data["data"]["ping"]["msg"]
