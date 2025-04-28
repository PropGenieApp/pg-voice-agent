from app import App
from api.routes import demo, ws, agency


def setup_routes(app: App) -> None:
    app.include_router(demo.router)
    app.include_router(agency.router)
    app.include_router(ws.router)
