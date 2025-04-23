from app import App
from api.routes import demo, ws


def setup_routes(app: App) -> None:
    app.include_router(demo.router)
    app.include_router(ws.router)

