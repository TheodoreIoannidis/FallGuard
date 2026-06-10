import logging
import sys
import traceback

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fallguard.api.schemas import HealthResponse
from fallguard.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("fallguard.app")

app = FastAPI(
    title=settings.app_name,
    description="ASGI server for processing telemetry data and detecting falls.",
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    )


try:
    from fallguard.api.routes import router

    app.include_router(router)
    logger.info("loaded fallguard routes")
except ImportError as error:
    logger.exception("failed to import routes: %s", error)
    traceback.print_exc(file=sys.stderr)
except Exception as error:
    logger.exception("startup failed while loading routes: %s", error)
    traceback.print_exc(file=sys.stderr)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
