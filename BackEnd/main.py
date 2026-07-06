from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth_router, shop_router, game_router
from core.database import lifespan


app = FastAPI(title="Flappy Logan API", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(shop_router)
app.include_router(game_router)

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5500",
    "https://your-frontend-domain.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)