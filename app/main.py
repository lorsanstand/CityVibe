from fastapi import FastAPI, APIRouter
import uvicorn

from auth.router import router as auth_router
from users.router import router as users_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(users_router)

app = FastAPI()

app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run('main:app', host='0.0.0.0', port=8080, reload=True)