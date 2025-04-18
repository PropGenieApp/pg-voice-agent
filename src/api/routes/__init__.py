from app import App
from api.routes import demo

def setup_routes(app: App) -> None:
    app.include_router(demo.router)

