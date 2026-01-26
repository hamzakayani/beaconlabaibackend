import os
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging_config import setup_logging
logger = setup_logging()

from app.api.v1.endpoints import auth, contact, team, jobs, papers, feature_publication, news, upload_image

app = FastAPI(
    title="Beacon Lab AI Backend",
    root_path="/beaconlabai",
    docs_url="/docs",
    openapi_url="/openapi.json",
    swagger_ui_parameters={
        "operationsSorter": "alpha",
        "persistAuthorization": True,
        "url": "/beaconlabai/openapi.json"
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def make_serializable(obj):
    """Recursively convert exception objects to strings for JSON serialization."""
    if isinstance(obj, Exception):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: make_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(make_serializable(item) for item in obj)
    return obj

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Request validation error: {exc}")
    errors = exc.errors()
    serializable_errors = make_serializable(errors)
    return JSONResponse(
        status_code=422,
        content={"detail": serializable_errors, "body": exc.body},
    )

from app.core.config import settings

os.makedirs("images", exist_ok=True)
app.mount("/images", StaticFiles(directory="images"), name="images")

os.makedirs("cv_uploads", exist_ok=True)
app.mount("/cv_uploads", StaticFiles(directory="cv_uploads"), name="cv_uploads")


#  Include API Routes

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(contact.router, prefix="/api/v1/contact", tags=["Contact"])
app.include_router(team.router, prefix="/api/v1/team", tags=["Team"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
app.include_router(papers.router, prefix="/api/v1/papers", tags=["Papers"])
app.include_router(feature_publication.router, prefix="/api/v1/feature_publication", tags=["Feature Publication"])
app.include_router(news.router, prefix="/api/v1/news", tags=["News"])
app.include_router(upload_image.router, prefix="/api/v1/upload_image", tags=["Upload Image"])








@app.get("/", tags=["Health Check"])
async def health_check():
    """
     Health Check Function
    """
    return {'detail': 'Health Check'}