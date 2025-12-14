import os
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging_config import setup_logging
logger = setup_logging()

from app.api.v1.endpoints import auth, contact, team

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

os.makedirs("images", exist_ok=True)
app.mount("/images", StaticFiles(directory="images"), name="images")

#  Include API Routes

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(contact.router, prefix="/api/v1/contact", tags=["Contact"])
app.include_router(team.router, prefix="/api/v1/team", tags=["Team"])









@app.get("/", tags=["Health Check"])
async def health_check():
    """
     Health Check Function
    """
    return {'detail': 'Health Check'}