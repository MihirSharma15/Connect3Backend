# external
from fastapi import FastAPI, Depends, HTTPException, status
from typing import Annotated
from neo4j import GraphDatabase
from twilio.rest import Client
from fastapi.middleware.cors import CORSMiddleware

# internal 
from app.services.auth import get_current_user
from app.core.config import settings
from app.routes.auth import auth_router
from app.routes.users import user_router
from app.schemas.users import UserInDb
from app.services.neo4j_db import get_neo4j_driver

async def lifespan(app: FastAPI):
    """Controls the lifespan of the app from startup to shutdown and properly manages the neccessary resources"""
    # neo4j
    driver = GraphDatabase.driver(settings.NEO4J_URI, auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD))
    session = driver.session(database="neo4j")
    app.state.neo4j_driver = driver
    app.state.neo4j_session = session

    # twilio
    twilio_client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)
    app.state.twilio_client = twilio_client

    yield
    session.close()
    driver.close()



app = FastAPI(lifespan=lifespan,
              title="Connect3",
              description="A social network",
              version="0.1.0",)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(auth_router)

@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    return {"message": "Welcome to Connect3, a social network for UNC students. Built for UNC Students, by UNC Students"}

@app.get("/health", status_code=status.HTTP_200_OK)
async def health(db: Annotated[GraphDatabase, Depends(get_neo4j_driver)]):
    try:
        db.verify_connectivity()
        db_status = "ok"
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Neo4j database connectivity error"
        )

    return {
        "fastapi": "ok",
        "neo4j_db": db_status
        }


@app.get("/localhost", status_code=status.HTTP_200_OK)
async def localhost():
    return {
        "Message": "Hi Localhost! I saw your grant on Linkedin and jumped at the opportunity to apply. I’m creating Connect3.",
        "Problem": "State Schools are massive. Yet, somehow everyone knows everyone. ",
        "Solution" : "We want to visualize the social network. How? Every user gets THREE of their most valuable connections. Those three get their own three. With enough people, the social network becomes visualized. You can see the exact social context that you fit in. ",
        "Advantages":  "Figure out HOW you know someone. On connect3, you can type in someone’s name, and you can see through how many connections you know someone. i.e Me -to- James -to- Ryan -to- Lily.",
        "Bottomline": "This might just be a social experiment, this might be the next Facebook. I don’t know. Regardless, I want to tackle the problem of social networks, and I hope you guys will join me for the ride. "
    }