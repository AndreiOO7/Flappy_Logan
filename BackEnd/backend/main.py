from fastapi import FastAPI
from routers import auth_router, shop_router, game_router
from core.database import lifespan

app = FastAPI(title="Flappy Logan API", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(shop_router)
app.include_router(game_router)