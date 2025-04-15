# external
from fastapi import FastAPI, Depends, HTTPException, status
from typing import Annotated
from neo4j import GraphDatabase
from twilio.rest import Client
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# internal
from app.core.config import settings
from app.routes import auth, status_content, users
from app.services.neo4j_db import get_neo4j_driver


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Controls the lifespan of the app from startup to shutdown and properly manages the neccessary resources"""
    # neo4j
    driver = GraphDatabase.driver(
        settings.NEO4J_URI, auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
    )
    session = driver.session(database="neo4j")
    app.state.neo4j_driver = driver
    app.state.neo4j_session = session

    # twilio
    twilio_client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)
    app.state.twilio_client = twilio_client

    yield
    session.close()
    driver.close()


app = FastAPI(
    lifespan=lifespan,
    title="Connect3",
    description="A social network",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(status_content.status_router)
app.include_router(users.user_router)
app.include_router(auth.auth_router)


@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    return {
        "message": "Welcome to Connect3, a social network for UNC students. Built for UNC Students, by UNC Students"
    }


@app.get("/health", status_code=status.HTTP_200_OK)
async def health(db: Annotated[GraphDatabase, Depends(get_neo4j_driver)]):
    try:
        db.verify_connectivity()
        db_status = "ok"
    except Exception:
        raise HTTPException(
            status_code=status_content.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Neo4j database connectivity error",
        )

    return {"fastapi": "ok", "neo4j_db": db_status}
