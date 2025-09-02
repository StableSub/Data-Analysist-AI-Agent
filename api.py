import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure state is initialized on import
from backend import state
from backend.routes import upload as upload_routes
from backend.routes import chat as chat_routes
from backend.routes import system as system_routes
from backend.routes import profile as profile_routes

os.environ["TOKENIZERS_PARALLELISM"] = "false"

app = FastAPI(title="Data Analysis AI Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Data Analysis AI Agent API"}


# Mount routers
app.include_router(upload_routes.router)
app.include_router(chat_routes.router)
app.include_router(system_routes.router)
app.include_router(profile_routes.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)