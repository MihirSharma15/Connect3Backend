# tests/conftest.py
from unittest.mock import MagicMock
from fastapi import Request
import pytest
from fastapi.testclient import TestClient
from neo4j import GraphDatabase
import requests
from app.main import app
import time
import logging
import subprocess
import threading

from app.schemas.users import UserInDb
from app.services.auth import create_access_token, get_current_user
from app.services.neo4j_db import get_neo4j_session
from app.services.twilio import get_twilio_client, get_twilio_service

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def wait_for_neo4j(url="http://localhost:7474", timeout=60):
    """Poll the Neo4j HTTP endpoint until it responds with an expected status code."""
    start_time = time.time()
    while True:
        try:
            response = requests.get(url)
            # Neo4j may respond with a redirect or a login page
            if response.status_code in (200, 302, 401):
                logger.info("Neo4j is ready with status code: %s", response.status_code)
                return
        except requests.exceptions.RequestException as e:
            logger.debug("Waiting for Neo4j: %s", e)
        time.sleep(1)
        if time.time() - start_time > timeout:
            raise TimeoutError("Timed out waiting for Neo4j to become available.")


@pytest.fixture(scope="session")
def neo4j_container():
    """
    Start a Neo4j Docker container for the duration of the test session.
    """
    logger.info("Starting Neo4j container...")
    # Build the docker run command
    # Using "--rm" ensures the container is removed after stopping.
    cmd = [
        "docker",
        "run",
        "--rm",
        "--name",
        "neo4j-test",
        "-p",
        "7687:7687",  # Bolt port for Neo4j driver
        "-p",
        "7474:7474",  # HTTP port for browser/API
        "-e",
        "NEO4J_AUTH=none",  # Disable auth for testing
        "neo4j:latest",
    ]

    # Start the container
    logger.info("Starting NEO4J Docker container...")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Wait until Neo4j HTTP endpoint is ready.
    wait_for_neo4j()
    logger.info("Neo4j container is up and running.")

    # Run tests after the container is confirmed to be up.
    yield

    logger.info("Stopping Neo4j container...")

    # Stop the container. With "--rm", the container will be automatically removed.
    def stop_container():
        subprocess.run(["docker", "stop", "neo4j-test"], check=True)

    threading.Thread(target=stop_container, daemon=True).start()
    logger.info("Neo4j container stopped.")


@pytest.fixture(scope="session")
def test_neo4j_session(neo4j_container):
    """Provide a neo4j session pointing at our Docker container. The 'neo4j_container' fixture ensures the DB is already up."""

    driver = GraphDatabase.driver("bolt://localhost:7687", auth=None)

    with driver.session() as session:
        yield session
    driver.close()


@pytest.fixture(scope="function", autouse=True)
def clear_neo4j_db(test_neo4j_session):
    """Clear the Neo4j database before each test to ensure a clean state"""
    test_neo4j_session.run("MATCH (n) DETACH DELETE n")
    yield
    test_neo4j_session.run("MATCH (n) DETACH DELETE n")  # Clean up after each test


@pytest.fixture(scope="session")
def client(test_neo4j_session):
    """Create a TestClient for the FastAPI app with overridden dependencies for Twilio & Neo4J."""

    # --- 1) TWILIO MOCK SETUP ---
    fake_twilio_client = MagicMock()
    fake_twilio_service = MagicMock()

    # Configure the fake service for sending OTP texts
    fake_twilio_service.verifications.create.return_value = MagicMock(
        to="+11234567890",
        channel="sms",
        status="pending",
        date_created="2023-03-20T00:00:00Z",
        date_updated="2023-03-20T00:00:00Z",
    )

    verification_token = create_access_token(data={"sub": "+11234567890"})
    # Configure the fake service for verifying OTPs
    fake_twilio_service.verification_checks.create.return_value = MagicMock(
        to="+11234567890",
        channel="sms",
        status="approved",
        date_created="2023-03-20T00:00:00Z",
        date_updated="2023-03-20T00:00:00Z",
        phone_verification_token={"access_token": "", "token_type": ""},
    )
    # Make the fake client return the fake service
    fake_twilio_client.verify.v2.services.return_value = fake_twilio_service

    # Define dependency override functions
    def fake_get_twilio_client(request: Request):
        return fake_twilio_client

    def fake_get_twilio_service(request: Request):
        return fake_twilio_service

    # --- 2) NEO4J SESSION OVERRIDE ---

    def override_get_neo4j_session(request: Request):
        return test_neo4j_session

    # --- 3) MOCK CURRENT USER ---

    def fake_get_current_user(token: str = None, session=None):
        """For every method that calls get_current_user, we will return this user:
        "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
        "name": "John Doe",
        "phonenumber": "+19999999999",
        "hashed_password": "fakehashedpassword",
        "created_at": "1-1-1970",
        "remaining_connections": 3,
        "is_verified": True,
        "invite_code": "ABCDE"
        """
        data = {
            "user_id": "db5d23a7-c5b8-4ec1-be46-2028a30261d2",
            "name": "John Doe",
            "phonenumber": "+19999999999",
            "hashed_password": "fakehashedpassword",
            "created_at": "1-1-1970",
            "remaining_connections": 3,
            "is_verified": True,
            "invite_code": "ABCDE",
        }
        return UserInDb(**data)

    # --- 4) APPLY ALL DEPENDENCY OVERRIDES AT ONCE ---

    app.dependency_overrides[get_twilio_client] = fake_get_twilio_client
    app.dependency_overrides[get_twilio_service] = fake_get_twilio_service
    app.dependency_overrides[get_neo4j_session] = override_get_neo4j_session
    app.dependency_overrides[get_current_user] = fake_get_current_user

    # --- 5) BUILD AND YIELD THE TEST CLIENT---

    test_client = TestClient(app)
    yield test_client

    # Reset dependency overrides after the test
    app.dependency_overrides = {}
