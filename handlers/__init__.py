from .start import router as start_router
from .pets import router as pets_router
from .posts import router as posts_router
from .interactions import router as interactions_router
from .subscriptions import router as subscriptions_router
from .admin import router as admin_router

dp = start_router
dp.include_router(pets_router)
dp.include_router(posts_router)
dp.include_router(interactions_router)
dp.include_router(subscriptions_router)
dp.include_router(admin_router)