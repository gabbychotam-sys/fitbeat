from fastapi import FastAPI, APIRouter
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import zipfile
import io
import tempfile
import shutil
import hashlib

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# FitBeat State Model
class FitBeatState(BaseModel):
    lang: int = 0
    color: int = 0
    userName: str = ""
    goalDist: int = 5
    goalTimeMin: int = 30
    hrMode: int = 0
    maxHr: int = 190
    distGoalActive: bool = False
    timeGoalActive: bool = False
    elapsedWalkSec: int = 0
    distanceCm: int = 0
    distHalfwayShown: bool = False
    distGoalShown: bool = False
    timeHalfwayShown: bool = False
    timeGoalShown: bool = False

# Workout Summary Models
class WorkoutPoint(BaseModel):
    lat: float
    lon: float
    timestamp: int  # Unix timestamp in seconds
    hr: Optional[int] = None
    elevation: Optional[float] = None

class WorkoutSubmit(BaseModel):
    user_id: str
    user_name: str = ""
    distance_cm: int
    duration_sec: int
    avg_hr: Optional[int] = None
    max_hr: Optional[int] = None
    elevation_gain: Optional[float] = None
    elevation_loss: Optional[float] = None
    steps: Optional[int] = None
    cadence: Optional[int] = None
    route: Optional[List[WorkoutPoint]] = None

class WorkoutSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_name: str = ""
    distance_cm: int
    duration_sec: int
    avg_hr: Optional[int] = None
    max_hr: Optional[int] = None
    elevation_gain: Optional[float] = None
    elevation_loss: Optional[float] = None
    steps: Optional[int] = None
    cadence: Optional[int] = None
    route: Optional[List[dict]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

def generate_user_id(device_id: str) -> str:
    """Generate a short unique user ID from device ID"""
    hash_obj = hashlib.sha256(device_id.encode())
    return hash_obj.hexdigest()[:8]

@api_router.get("/")
async def root():
    return {"message": "FitBeat API v4.4.0"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    return status_checks

# FitBeat ZIP Download
@api_router.get("/download/fitbeat")
async def download_fitbeat():
    """Download FitBeat source code as ZIP"""
    fitbeat_dir = Path("/app/fitbeat")
    
    if not fitbeat_dir.exists():
        return JSONResponse(status_code=404, content={"error": "FitBeat directory not found"})
    
    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in fitbeat_dir.rglob('*'):
            if file_path.is_file():
                # Skip unnecessary files
                if '__pycache__' in str(file_path) or '.pyc' in str(file_path):
                    continue
                arcname = f"fitbeat/{file_path.relative_to(fitbeat_dir)}"
                zip_file.write(file_path, arcname)
    
    zip_buffer.seek(0)
    
    # Save to temp file for FileResponse
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    temp_file.write(zip_buffer.getvalue())
    temp_file.close()
    
    return FileResponse(
        temp_file.name,
        media_type='application/zip',
        filename='fitbeat.zip',
        headers={"Content-Disposition": "attachment; filename=fitbeat.zip"}
    )

# Store Assets Download
@api_router.get("/download/store-assets")
async def download_store_assets():
    """Download store assets (icons, descriptions) as ZIP"""
    store_assets_zip = Path("/app/store_assets.zip")
    
    if not store_assets_zip.exists():
        return JSONResponse(status_code=404, content={"error": "Store assets not found"})
    
    return FileResponse(
        str(store_assets_zip),
        media_type='application/zip',
        filename='FitBeat_Store_Assets.zip',
        headers={"Content-Disposition": "attachment; filename=FitBeat_Store_Assets.zip"}
    )

# FitBeat State Management
@api_router.get("/fitbeat/state")
async def get_fitbeat_state():
    """Get current FitBeat simulator state from DB"""
    state = await db.fitbeat_state.find_one({"_id": "simulator"}, {"_id": 0})
    if state is None:
        return FitBeatState().model_dump()
    return state

@api_router.post("/fitbeat/state")
async def save_fitbeat_state(state: FitBeatState):
    """Save FitBeat simulator state to DB"""
    await db.fitbeat_state.update_one(
        {"_id": "simulator"},
        {"$set": state.model_dump()},
        upsert=True
    )
    return {"status": "saved"}

@api_router.post("/fitbeat/reset")
async def reset_fitbeat_state():
    """Reset FitBeat simulator state"""
    default_state = FitBeatState()
    await db.fitbeat_state.update_one(
        {"_id": "simulator"},
        {"$set": default_state.model_dump()},
        upsert=True
    )
    return {"status": "reset", "state": default_state.model_dump()}

# ═══════════════════════════════════════════════════════════════
# Workout Summary API - For sharing workouts via WhatsApp
# ═══════════════════════════════════════════════════════════════

@api_router.post("/workout")
async def submit_workout(workout: WorkoutSubmit):
    """Receive workout data from watch and save to DB"""
    workout_obj = WorkoutSummary(
        user_id=workout.user_id,
        user_name=workout.user_name,
        distance_cm=workout.distance_cm,
        duration_sec=workout.duration_sec,
        avg_hr=workout.avg_hr,
        max_hr=workout.max_hr,
        elevation_gain=workout.elevation_gain,
        elevation_loss=workout.elevation_loss,
        steps=workout.steps,
        cadence=workout.cadence,
        route=[p.model_dump() for p in workout.route] if workout.route else None
    )
    
    doc = workout_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.workouts.insert_one(doc)
    
    logger.info(f"Workout saved for user {workout.user_id}: {workout.distance_cm}cm in {workout.duration_sec}s")
    
    return {
        "status": "saved",
        "workout_id": workout_obj.id,
        "user_id": workout.user_id
    }

@api_router.get("/workout/user/{user_id}")
async def get_user_workouts(user_id: str, limit: int = 10):
    """Get workouts for a specific user"""
    workouts = await db.workouts.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(limit)
    
    return {
        "user_id": user_id,
        "workouts": workouts,
        "count": len(workouts)
    }

@api_router.get("/workout/latest/{user_id}")
async def get_latest_workout(user_id: str):
    """Get the latest workout for a user"""
    workout = await db.workouts.find_one(
        {"user_id": user_id},
        {"_id": 0},
        sort=[("timestamp", -1)]
    )
    
    if not workout:
        return JSONResponse(status_code=404, content={"error": "No workouts found for this user"})
    
    return workout

@api_router.get("/user/{user_id}/stats")
async def get_user_stats(user_id: str):
    """Get aggregated stats for a user"""
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": "$user_id",
            "total_workouts": {"$sum": 1},
            "total_distance_cm": {"$sum": "$distance_cm"},
            "total_duration_sec": {"$sum": "$duration_sec"},
            "avg_hr": {"$avg": "$avg_hr"},
            "user_name": {"$last": "$user_name"}
        }}
    ]
    
    result = await db.workouts.aggregate(pipeline).to_list(1)
    
    if not result:
        return {
            "user_id": user_id,
            "total_workouts": 0,
            "total_distance_km": 0,
            "total_duration_min": 0
        }
    
    stats = result[0]
    return {
        "user_id": user_id,
        "user_name": stats.get("user_name", ""),
        "total_workouts": stats["total_workouts"],
        "total_distance_km": round(stats["total_distance_cm"] / 100000, 2),
        "total_duration_min": round(stats["total_duration_sec"] / 60, 1),
        "avg_hr": round(stats["avg_hr"]) if stats.get("avg_hr") else None
    }

@api_router.post("/user/register")
async def register_user(device_id: str, user_name: str = ""):
    """Register a new user and get their unique ID"""
    user_id = generate_user_id(device_id)
    
    # Check if user exists
    existing = await db.users.find_one({"user_id": user_id})
    
    if not existing:
        await db.users.insert_one({
            "user_id": user_id,
            "device_id": device_id,
            "user_name": user_name,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"New user registered: {user_id}")
    elif user_name and user_name != existing.get("user_name"):
        # Update user name if changed
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"user_name": user_name}}
        )
    
    return {"user_id": user_id}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
