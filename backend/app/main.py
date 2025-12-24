import uvicorn
import logging

from fastapi import FastAPI, APIRouter, Request, Depends
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.users.router import router as users_router
from app.events.router import router as events_router
from app.config import settings
from app.log_config import set_logging
from app.auth.dependencies import get_current_superuser

set_logging()
log = logging.getLogger(__name__)

templates = Jinja2Templates(directory="app/templates")

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(events_router)

app = FastAPI(
    title="CityVibe API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    response: Response = await call_next(request)
    log.info(
        "method=%s path=%s status=%s",
        request.method,
        request.url.path,
        response.status_code,
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code
        }
    )
    return response


@app.post("/push/send")
async def send_push(message: str, header: str, current_user = Depends(get_current_superuser)) -> dict:
    log.info("Push notification sent", extra={"superuser_id": str(current_user.id), "header": header})
    return {"message": "successfully"}

app.include_router(api_router)
app.mount('/static', StaticFiles(directory='app/templates/static'), name='static')

@app.get("/verify")
async def verify_page(request: Request):
    log.debug("Verify email page accessed")
    return templates.TemplateResponse(request, "verify_email.html", {'request': request})

if __name__ == "__main__":
    if settings.MODE == "PROD":
        UVICORN_PARAMS = dict(
            host=settings.HOST,
            port=settings.PORT,
            reload=False,
            workers=settings.WORKERS,
            access_log=False
        )
    else:
        UVICORN_PARAMS = dict(
            host=settings.HOST,
            port=settings.PORT,
            reload=False,
            workers=settings.WORKERS,
            access_log=False
        )
    log.info("App is starting", extra={
        "host": settings.HOST,
        "port": settings.PORT,
        "workers": settings.WORKERS
    })
    uvicorn.run('app.main:app', **UVICORN_PARAMS)