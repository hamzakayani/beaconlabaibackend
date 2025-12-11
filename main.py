import os
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from fastapi.middleware.cors import CORSMiddleware

from app.core.logging_config import setup_logging
logger = setup_logging()

from app.api.v1.endpoints import auth

app = FastAPI(
    title="Beacon Lab AI Backend",
    root_path="/backend",
    docs_url="/docs",
    openapi_url="/openapi.json",
    swagger_ui_parameters={
        "operationsSorter": "alpha",
        "persistAuthorization": True,
        "url": "/backend/openapi.json"
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Request validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

#  Include API Routes

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])









@app.get("/", tags=["Health Check"])
async def health_check():
    """
     Health Check Function
    """
    return {'detail': 'Health Check'}