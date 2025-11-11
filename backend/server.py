from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from routes import schools

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')



# Create the main app without a prefix
app = FastAPI(title="School Finder API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Health check endpoint
@api_router.get("/")
async def root():
    return {"message": "School Finder API is running"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is operational"}

# Include school routes
api_router.include_router(schools.router)

# Include the router in the main app
app.include_router(api_router)

# --- THIS IS THE FIX ---
# Define allowed origins for CORS
# We must specify the exact frontend URL because allow_credentials=True
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:3001",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # or ["*"] temporarily in dev
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting School Finder API...")
    logger.info("Loading school data...")

@app.on_event("shutdown")
async def shutdown_db_client():
    #client.close()
    logger.info("School Finder API shutdown complete")