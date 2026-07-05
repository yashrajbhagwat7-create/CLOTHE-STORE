from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes.pages import router

app = FastAPI()

# Static Folder
app.mount("/static", StaticFiles(directory="static"), name="static")

# Page routes
app.include_router(router)

