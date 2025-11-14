from fastapi import FastAPI, APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.auth.router import router as auth_router
from app.users.router import router as users_router
from app.events.router import router as events_router
from app.config import settings

api_router = APIRouter(prefix="/api")

templates = Jinja2Templates(directory="app/templates")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(events_router)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

app.include_router(api_router)
app.mount('/static', StaticFiles(directory='app/templates/static'), name='static')

@app.get("/verify")
async def verify_page(request: Request):
    return templates.TemplateResponse(request, "verify_email.html", {'request': request})

if __name__ == "__main__":
    uvicorn.run('app.main:app', host='0.0.0.0', port=8080, reload=True, workers=3)