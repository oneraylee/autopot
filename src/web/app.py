from fastapi import FastAPI

from web.dependencies import AppContainer
from web.routes import build_router


def create_app() -> FastAPI:
    app = FastAPI(title="AI Training Platform API", version="0.1.0")
    container = AppContainer()
    app.state.container = container
    app.include_router(build_router(container))
    return app


app = create_app()
