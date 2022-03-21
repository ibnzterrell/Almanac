from fastapi import FastAPI
from api.headline_route import headlineAPI
from api.search_route import searchAPI
from model.DB import db_startup, db_shutdown
from model.NLP import loadNLP
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "PUT"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    app.state.engine = db_startup()
    app.state.pipelines = loadNLP()

@app.on_event("shutdown")
async def shutdown():
    db_shutdown(app.state.engine)

@app.get("/")
async def healthCheck():
    return {"message": "Visit /docs for documentation"}

@app.get("/health")
async def healthCheck():
    return {"message": "OK"}

app.include_router(headlineAPI)
app.include_router(searchAPI)