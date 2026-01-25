from fastapi import FastAPI, APIRouter
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
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

@api_router.get("/workout/all")
async def get_all_workouts(limit: int = 50):
    """Get all workouts (for debugging)"""
    workouts = await db.workouts.find(
        {},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(limit)
    
    return {
        "workouts": workouts,
        "count": len(workouts)
    }

@api_router.delete("/workout/user/{user_id}/all")
async def delete_all_user_workouts(user_id: str):
    """Delete all workouts for a user"""
    result = await db.workouts.delete_many({"user_id": user_id})
    return {
        "status": "deleted",
        "user_id": user_id,
        "deleted_count": result.deleted_count
    }

@api_router.delete("/workout/{workout_id}")
async def delete_single_workout(workout_id: str):
    """Delete a single workout by ID"""
    result = await db.workouts.delete_one({"id": workout_id})
    if result.deleted_count == 0:
        return JSONResponse(status_code=404, content={"error": "Workout not found"})
    return {
        "status": "deleted",
        "workout_id": workout_id
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

@api_router.get("/workout/id/{workout_id}")
async def get_workout_by_id(workout_id: str):
    """Get a specific workout by ID"""
    workout = await db.workouts.find_one(
        {"id": workout_id},
        {"_id": 0}
    )
    
    if not workout:
        return JSONResponse(status_code=404, content={"error": "Workout not found"})
    
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

@api_router.get("/user/{user_id}/monthly")
async def get_monthly_stats(user_id: str, year: int = None, month: int = None):
    """Get monthly stats for a user"""
    from datetime import datetime
    
    # Default to current month
    now = datetime.now(timezone.utc)
    if year is None:
        year = now.year
    if month is None:
        month = now.month
    
    # Calculate date range for the month
    start_date = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end_date = datetime(year, month + 1, 1, tzinfo=timezone.utc)
    
    # Get previous month for comparison
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1
    
    prev_start = datetime(prev_year, prev_month, 1, tzinfo=timezone.utc)
    prev_end = start_date
    
    # Aggregate current month
    pipeline = [
        {"$match": {
            "user_id": user_id,
            "timestamp": {
                "$gte": start_date.isoformat(),
                "$lt": end_date.isoformat()
            }
        }},
        {"$group": {
            "_id": "$user_id",
            "total_workouts": {"$sum": 1},
            "total_distance_cm": {"$sum": "$distance_cm"},
            "total_duration_sec": {"$sum": "$duration_sec"},
            "avg_hr": {"$avg": "$avg_hr"},
            "max_hr": {"$max": "$max_hr"},
            "total_elevation_gain": {"$sum": "$elevation_gain"},
            "total_elevation_loss": {"$sum": "$elevation_loss"},
            "total_steps": {"$sum": "$steps"},
            "user_name": {"$last": "$user_name"}
        }}
    ]
    
    # Aggregate previous month for comparison
    prev_pipeline = [
        {"$match": {
            "user_id": user_id,
            "timestamp": {
                "$gte": prev_start.isoformat(),
                "$lt": prev_end.isoformat()
            }
        }},
        {"$group": {
            "_id": "$user_id",
            "total_workouts": {"$sum": 1},
            "total_distance_cm": {"$sum": "$distance_cm"},
            "total_duration_sec": {"$sum": "$duration_sec"}
        }}
    ]
    
    result = await db.workouts.aggregate(pipeline).to_list(1)
    prev_result = await db.workouts.aggregate(prev_pipeline).to_list(1)
    
    # Get list of workouts for this month
    workouts = await db.workouts.find(
        {
            "user_id": user_id,
            "timestamp": {
                "$gte": start_date.isoformat(),
                "$lt": end_date.isoformat()
            }
        },
        {"_id": 0}
    ).sort("timestamp", -1).to_list(100)
    
    month_names_he = ["", "ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני", 
                      "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"]
    
    if not result:
        return {
            "user_id": user_id,
            "year": year,
            "month": month,
            "month_name": month_names_he[month],
            "total_workouts": 0,
            "total_distance_km": 0,
            "total_duration_min": 0,
            "avg_hr": None,
            "max_hr": None,
            "total_elevation_gain": 0,
            "total_elevation_loss": 0,
            "total_steps": 0,
            "workouts": [],
            "comparison": None
        }
    
    stats = result[0]
    
    # Calculate comparison with previous month
    comparison = None
    if prev_result:
        prev_stats = prev_result[0]
        prev_dist = prev_stats["total_distance_cm"] / 100000
        curr_dist = stats["total_distance_cm"] / 100000
        if prev_dist > 0:
            dist_change = round(((curr_dist - prev_dist) / prev_dist) * 100, 1)
            comparison = {
                "distance_change_percent": dist_change,
                "workouts_change": stats["total_workouts"] - prev_stats["total_workouts"]
            }
    
    return {
        "user_id": user_id,
        "user_name": stats.get("user_name", ""),
        "year": year,
        "month": month,
        "month_name": month_names_he[month],
        "total_workouts": stats["total_workouts"],
        "total_distance_km": round(stats["total_distance_cm"] / 100000, 2),
        "total_duration_min": round(stats["total_duration_sec"] / 60, 1),
        "avg_hr": round(stats["avg_hr"]) if stats.get("avg_hr") else None,
        "max_hr": stats.get("max_hr"),
        "total_elevation_gain": round(stats.get("total_elevation_gain") or 0, 1),
        "total_elevation_loss": round(stats.get("total_elevation_loss") or 0, 1),
        "total_steps": stats.get("total_steps") or 0,
        "workouts": workouts,
        "comparison": comparison
    }

class UserRegister(BaseModel):
    device_id: str
    user_name: str = ""

@api_router.post("/user/register")
async def register_user(data: UserRegister):
    """Register a new user and get their unique ID"""
    user_id = generate_user_id(data.device_id)
    
    # Check if user exists
    existing = await db.users.find_one({"user_id": user_id})
    
    if not existing:
        await db.users.insert_one({
            "user_id": user_id,
            "device_id": data.device_id,
            "user_name": data.user_name,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"New user registered: {user_id}")
    elif data.user_name and data.user_name != existing.get("user_name"):
        # Update user name if changed
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"user_name": data.user_name}}
        )
    
    return {"user_id": user_id}

# ═══════════════════════════════════════════════════════════════
# HTML PAGES - Workout Summary Pages
# ═══════════════════════════════════════════════════════════════

def generate_workout_html(workout, user_id):
    """Generate HTML page for workout summary"""
    if not workout:
        return f"""
        <!DOCTYPE html>
        <html lang="he" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>FitBeat - לא נמצאו אימונים</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; color: white; display: flex; align-items: center; justify-content: center; }}
                .container {{ text-align: center; padding: 2rem; }}
                .icon {{ font-size: 4rem; margin-bottom: 1rem; }}
                h1 {{ color: #00d4ff; margin-bottom: 0.5rem; }}
                p {{ color: #888; }}
                .user-id {{ font-family: monospace; color: #00d4ff; opacity: 0.6; margin-top: 1rem; font-size: 0.8rem; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="icon">🏃‍♂️</div>
                <h1>FitBeat</h1>
                <p>לא נמצאו אימונים עבור משתמש זה</p>
                <p class="user-id">מזהה: {user_id}</p>
            </div>
        </body>
        </html>
        """
    
    dist_km = workout['distance_cm'] / 100000
    duration_sec = workout['duration_sec']
    hrs = duration_sec // 3600
    mins = (duration_sec % 3600) // 60
    secs = duration_sec % 60
    duration_str = f"{hrs}:{mins:02d}:{secs:02d}" if hrs > 0 else f"{mins}:{secs:02d}"
    
    # Calculate pace
    if dist_km > 0:
        pace_sec = duration_sec / dist_km
        pace_min = int(pace_sec // 60)
        pace_s = int(pace_sec % 60)
        pace_str = f"{pace_min}:{pace_s:02d}"
    else:
        pace_str = "--:--"
    
    user_name = workout.get('user_name', '')
    avg_hr = workout.get('avg_hr', '')
    max_hr = workout.get('max_hr', '')
    elevation_gain = workout.get('elevation_gain', 0) or 0
    elevation_loss = workout.get('elevation_loss', 0) or 0
    steps = workout.get('steps', 0) or 0
    cadence = workout.get('cadence', 0) or 0
    workout_id = workout.get('id', '')
    
    # Format date
    timestamp = workout.get('timestamp', '')
    
    # WhatsApp share text
    share_text = f"🏃‍♂️ {user_name} סיים אימון!%0A%0A📍 מרחק: {dist_km:.2f} ק״מ%0A⏱️ זמן: {duration_str}%0A⚡ קצב: {pace_str} /ק״מ"
    if avg_hr:
        share_text += f"%0A❤️ דופק: {avg_hr} BPM"
    share_text += f"%0A%0A🔗 צפה בסיכום:%0Ahttps://web-production-110fc.up.railway.app/u/{user_id}"
    
    return f"""
    <!DOCTYPE html>
    <html lang="he" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FitBeat - סיכום אימון</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; color: white; padding: 1rem; }}
            .container {{ max-width: 480px; margin: 0 auto; }}
            header {{ text-align: center; padding: 1.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 1.5rem; }}
            h1 {{ color: #00d4ff; font-size: 1.5rem; margin-bottom: 0.25rem; }}
            .subtitle {{ color: #888; font-size: 0.9rem; }}
            .user-name {{ font-size: 1.1rem; margin-top: 0.5rem; }}
            .map {{ background: linear-gradient(135deg, #2d4a2d 0%, #1a2f1a 100%); border-radius: 1rem; height: 200px; margin-bottom: 1.5rem; position: relative; overflow: hidden; }}
            .map svg {{ position: absolute; inset: 0; width: 100%; height: 100%; }}
            .map-badge {{ position: absolute; top: 0.75rem; left: 0.75rem; background: rgba(0,0,0,0.8); padding: 0.5rem 1rem; border-radius: 0.75rem; border: 1px solid rgba(255,255,255,0.1); }}
            .map-badge .value {{ font-size: 1.5rem; font-weight: bold; color: #00d4ff; }}
            .map-badge .unit {{ font-size: 0.8rem; color: #888; }}
            .stats {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 1.5rem; }}
            .stat {{ background: linear-gradient(135deg, #1e1e3f 0%, #151530 100%); border-radius: 0.75rem; padding: 1rem; border: 1px solid rgba(255,255,255,0.05); }}
            .stat .icon {{ font-size: 1.25rem; margin-bottom: 0.5rem; }}
            .stat .label {{ color: #888; font-size: 0.75rem; margin-bottom: 0.25rem; }}
            .stat .value {{ font-size: 1.5rem; font-weight: bold; }}
            .stat .value.highlight {{ color: #00d4ff; }}
            .stat .unit {{ font-size: 0.8rem; color: #888; margin-right: 0.25rem; }}
            .section {{ background: linear-gradient(135deg, #1e1e3f 0%, #151530 100%); border-radius: 0.75rem; padding: 1rem; margin-bottom: 1rem; border: 1px solid rgba(255,255,255,0.05); }}
            .section-title {{ color: #888; font-size: 0.8rem; margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem; }}
            .hr-stats {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }}
            .hr-stat {{ background: rgba(0,0,0,0.2); border-radius: 0.5rem; padding: 0.75rem; text-align: center; }}
            .hr-stat .label {{ color: #888; font-size: 0.7rem; }}
            .hr-stat .value {{ color: #ef4444; font-size: 1.25rem; font-weight: bold; }}
            .hr-stat .value span {{ font-size: 0.7rem; color: #888; }}
            .extra-stats {{ display: flex; flex-direction: column; }}
            .extra-stat {{ display: flex; justify-content: space-between; padding: 0.75rem 0; border-bottom: 1px solid rgba(255,255,255,0.05); }}
            .extra-stat:last-child {{ border-bottom: none; }}
            .extra-stat .label {{ color: #888; display: flex; align-items: center; gap: 0.5rem; }}
            .extra-stat .value {{ font-weight: bold; }}
            .share-btn {{ display: flex; align-items: center; justify-content: center; gap: 0.75rem; background: linear-gradient(90deg, #25D366 0%, #128C7E 100%); color: white; border: none; padding: 1rem 2rem; border-radius: 9999px; font-size: 1.1rem; font-weight: bold; cursor: pointer; margin: 2rem auto; box-shadow: 0 4px 15px rgba(37, 211, 102, 0.3); }}
            .share-btn:hover {{ transform: translateY(-2px); box-shadow: 0 6px 20px rgba(37, 211, 102, 0.4); }}
            .share-btn svg {{ width: 1.5rem; height: 1.5rem; }}
            .share-hint {{ text-align: center; color: #888; font-size: 0.8rem; margin-bottom: 1rem; }}
            .delete-btn {{ display: flex; align-items: center; justify-content: center; gap: 0.5rem; background: transparent; color: #ef4444; border: 1px solid #ef4444; padding: 0.75rem 1.5rem; border-radius: 9999px; font-size: 0.85rem; cursor: pointer; margin: 1rem auto; }}
            .delete-btn:hover {{ background: #ef4444; color: white; }}
            footer {{ text-align: center; padding: 1.5rem 0; color: #888; font-size: 0.8rem; }}
            footer .brand {{ color: #00d4ff; font-weight: bold; font-size: 1rem; }}
            footer .user-id {{ font-family: monospace; color: #00d4ff; opacity: 0.6; margin-top: 0.5rem; font-size: 0.7rem; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🏃‍♂️ סיכום אימון</h1>
                <p class="subtitle">{timestamp[:10] if timestamp else ''}</p>
                {'<p class="user-name">' + user_name + ' סיים אימון!</p>' if user_name else ''}
            </header>
            
            <div class="map">
                <svg viewBox="0 0 400 200">
                    <path d="M 40,160 Q 80,140 120,120 T 200,100 T 280,80 T 360,60" fill="none" stroke="#ff6666" stroke-width="6" stroke-linecap="round" opacity="0.3" style="filter: blur(3px);"/>
                    <path d="M 40,160 Q 80,140 120,120 T 200,100 T 280,80 T 360,60" fill="none" stroke="#ff3333" stroke-width="3" stroke-linecap="round" style="filter: drop-shadow(0 0 4px rgba(255,50,50,0.8));"/>
                    <circle cx="40" cy="160" r="6" fill="#22c55e"/>
                    <circle cx="40" cy="160" r="3" fill="white"/>
                    <circle cx="360" cy="60" r="6" fill="#ef4444" style="filter: drop-shadow(0 0 4px rgba(239,68,68,0.8));"/>
                    <circle cx="360" cy="60" r="3" fill="white"/>
                </svg>
                <div class="map-badge">
                    <span class="value">{dist_km:.2f}</span>
                    <span class="unit">ק"מ</span>
                </div>
            </div>
            
            <div class="stats">
                <div class="stat">
                    <div class="icon">📍</div>
                    <div class="label">מרחק</div>
                    <div class="value highlight">{dist_km:.2f}<span class="unit">ק"מ</span></div>
                </div>
                <div class="stat">
                    <div class="icon">⏱️</div>
                    <div class="label">זמן</div>
                    <div class="value">{duration_str}</div>
                </div>
                <div class="stat">
                    <div class="icon">⚡</div>
                    <div class="label">קצב ממוצע</div>
                    <div class="value">{pace_str}<span class="unit">/ק"מ</span></div>
                </div>
                <div class="stat">
                    <div class="icon">🚀</div>
                    <div class="label">קצב מקסימלי</div>
                    <div class="value">{pace_str}<span class="unit">/ק"מ</span></div>
                </div>
            </div>
            
            {'<div class="section"><div class="section-title">⛰️ פרופיל גובה</div><div class="hr-stats"><div class="hr-stat"><div class="label">עלייה</div><div class="value" style="color:#22c55e;">+' + str(int(elevation_gain)) + ' מ׳</div></div><div class="hr-stat"><div class="label">ירידה</div><div class="value" style="color:#ef4444;">-' + str(int(elevation_loss)) + ' מ׳</div></div></div></div>' if elevation_gain or elevation_loss else ''}
            
            {'<div class="section"><div class="section-title">❤️ דופק</div><div class="hr-stats"><div class="hr-stat"><div class="label">ממוצע</div><div class="value">' + str(avg_hr) + ' <span>BPM</span></div></div><div class="hr-stat"><div class="label">מקסימום</div><div class="value">' + str(max_hr) + ' <span>BPM</span></div></div></div></div>' if avg_hr else ''}
            
            <div class="section">
                <div class="section-title">📊 נתונים נוספים</div>
                <div class="extra-stats">
                    {'<div class="extra-stat"><span class="label">👟 צעדים</span><span class="value">' + f'{steps:,}' + '</span></div>' if steps else ''}
                    {'<div class="extra-stat"><span class="label">🦶 קדנס ממוצע</span><span class="value">' + str(cadence) + ' spm</span></div>' if cadence else ''}
                </div>
            </div>
            
            <a href="https://wa.me/?text={share_text}" target="_blank" style="text-decoration: none;">
                <button class="share-btn">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
                    שתף ב-WhatsApp
                </button>
            </a>
            <p class="share-hint">📲 בחר איש קשר או שלח לעצמך</p>
            
            <button onclick="deleteWorkout()" class="delete-btn">🗑️ מחק אימון</button>
            
            <footer>
                <div class="brand">FitBeat</div>
                <div>Powered by Garmin Fenix 8 Solar</div>
                <div class="user-id">מזהה: {user_id}</div>
            </footer>
        </div>
        
        <script>
            async function deleteWorkout() {{
                if (confirm('למחוק את האימון הזה?')) {{
                    try {{
                        const response = await fetch('/api/workout/{workout_id}', {{ method: 'DELETE' }});
                        if (response.ok) {{
                            alert('האימון נמחק!');
                            window.location.href = '/u/{user_id}';
                        }} else {{
                            alert('שגיאה במחיקה');
                        }}
                    }} catch (e) {{
                        alert('שגיאה: ' + e.message);
                    }}
                }}
            }}
        </script>
    </body>
    </html>
    """

@api_router.get("/u/{user_id}", response_class=HTMLResponse)
async def dashboard_page(user_id: str):
    """Main page - shows years as folders"""
    workouts = await db.workouts.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(500)
    
    # Group workouts by year
    from collections import defaultdict
    years_data = defaultdict(list)
    for w in workouts:
        year = w.get('timestamp', '')[:4]  # "2026"
        if year:
            years_data[year].append(w)
    
    # Calculate total summary
    total_dist = sum(w.get('distance_cm', 0) for w in workouts) if workouts else 0
    total_time = sum(w.get('duration_sec', 0) for w in workouts) if workouts else 0
    total_km = total_dist / 100000
    total_hrs = total_time // 3600
    total_mins = (total_time % 3600) // 60
    time_str = f"{total_hrs} שעות ו-{total_mins} דקות" if total_hrs > 0 else f"{total_mins} דקות"
    
    user_name = workouts[0].get('user_name', '') if workouts else ''
    
    # Build year folders
    years_html = ""
    for year in sorted(years_data.keys(), reverse=True):
        year_workouts = years_data[year]
        y_dist = sum(w.get('distance_cm', 0) for w in year_workouts) / 100000
        y_count = len(year_workouts)
        
        years_html += f"""
        <a href="/u/{user_id}/year/{year}" class="folder-row">
            <div class="folder-icon">📁</div>
            <div class="folder-info">
                <div class="folder-name">{year}</div>
                <div class="folder-meta">{y_count} אימונים</div>
            </div>
            <div class="folder-stats">{y_dist:.1f} ק"מ</div>
            <div class="folder-arrow">←</div>
        </a>
        """
    
    share_text = f"📊 FitBeat%0A🏃 {len(workouts)} אימונים%0A📍 {total_km:.1f} ק״מ%0A%0A🔗 https://web-production-110fc.up.railway.app/u/{user_id}"
    
    return f"""
    <!DOCTYPE html>
    <html lang="he" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FitBeat - {user_name or user_id}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; color: white; padding: 1rem; }}
            .container {{ max-width: 480px; margin: 0 auto; }}
            header {{ text-align: center; padding: 1.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 1.5rem; }}
            h1 {{ color: #00d4ff; font-size: 1.8rem; }}
            .user-name {{ font-size: 1.2rem; margin-top: 0.5rem; }}
            
            .summary {{ background: linear-gradient(135deg, #1e1e3f 0%, #151530 100%); border-radius: 1rem; padding: 1.5rem; margin-bottom: 1.5rem; border: 1px solid rgba(0,212,255,0.2); }}
            .summary-title {{ color: #888; font-size: 0.9rem; margin-bottom: 1rem; }}
            .summary-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; text-align: center; }}
            .summary-value {{ font-size: 2.5rem; font-weight: bold; color: #00d4ff; }}
            .summary-value.green {{ color: #22c55e; }}
            .summary-label {{ color: #888; font-size: 0.9rem; margin-top: 0.25rem; }}
            
            .folders {{ background: linear-gradient(135deg, #1e1e3f 0%, #151530 100%); border-radius: 1rem; padding: 1rem; margin-bottom: 1.5rem; }}
            .folders-title {{ color: #888; font-size: 0.9rem; margin-bottom: 1rem; }}
            
            .folder-row {{ display: flex; align-items: center; padding: 1rem; background: rgba(0,0,0,0.2); border-radius: 0.75rem; margin-bottom: 0.5rem; text-decoration: none; color: white; transition: all 0.2s; }}
            .folder-row:hover {{ background: rgba(0,212,255,0.1); transform: translateX(-4px); }}
            .folder-icon {{ font-size: 2rem; margin-left: 1rem; }}
            .folder-info {{ flex: 1; }}
            .folder-name {{ font-weight: bold; font-size: 1.2rem; }}
            .folder-meta {{ color: #888; font-size: 0.85rem; }}
            .folder-stats {{ color: #22c55e; font-weight: bold; font-size: 1.1rem; margin-left: 1rem; }}
            .folder-arrow {{ color: #00d4ff; font-size: 1.5rem; }}
            
            .no-workouts {{ text-align: center; padding: 3rem 1rem; }}
            .no-workouts-icon {{ font-size: 4rem; margin-bottom: 1rem; }}
            
            .buttons {{ display: flex; flex-direction: column; gap: 0.75rem; margin: 1.5rem 0; }}
            .share-btn {{ display: flex; align-items: center; justify-content: center; gap: 0.75rem; background: linear-gradient(90deg, #25D366 0%, #128C7E 100%); color: white; border: none; padding: 1rem 2rem; border-radius: 9999px; font-size: 1rem; font-weight: bold; cursor: pointer; text-decoration: none; }}
            .delete-btn {{ display: flex; align-items: center; justify-content: center; gap: 0.5rem; background: transparent; color: #ef4444; border: 1px solid #ef4444; padding: 0.75rem 1.5rem; border-radius: 9999px; font-size: 0.85rem; cursor: pointer; }}
            .delete-btn:hover {{ background: #ef4444; color: white; }}
            
            footer {{ text-align: center; padding: 1.5rem 0; color: #888; font-size: 0.8rem; }}
            footer .brand {{ color: #00d4ff; font-weight: bold; font-size: 1rem; }}
            footer .user-id {{ font-family: monospace; color: #00d4ff; opacity: 0.6; margin-top: 0.5rem; font-size: 0.7rem; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🏃‍♂️ FitBeat</h1>
                {'<p class="user-name">' + user_name + '</p>' if user_name else ''}
            </header>
            
            <div class="summary">
                <div class="summary-title">📊 סיכום כולל</div>
                <div class="summary-grid">
                    <div>
                        <div class="summary-value">{len(workouts)}</div>
                        <div class="summary-label">אימונים</div>
                    </div>
                    <div>
                        <div class="summary-value green">{total_km:.1f}</div>
                        <div class="summary-label">ק"מ סה"כ</div>
                    </div>
                </div>
            </div>
            
            <div class="folders">
                <div class="folders-title">📁 לפי שנים</div>
                {years_html if years_html else '<div class="no-workouts"><div class="no-workouts-icon">🏃‍♂️</div><p>אין אימונים עדיין</p><p style="font-size:0.8rem;margin-top:0.5rem;color:#888;">סיים יעד בשעון והאימון יופיע כאן!</p></div>'}
            </div>
            
            <div class="buttons">
                <a href="https://wa.me/?text={share_text}" target="_blank" class="share-btn">📤 שתף ב-WhatsApp</a>
                {'<button onclick="deleteAll()" class="delete-btn">🗑️ מחק הכל</button>' if workouts else ''}
            </div>
            
            <footer>
                <div class="brand">FitBeat</div>
                <div class="user-id">מזהה: {user_id}</div>
            </footer>
        </div>
        <script>
            async function deleteAll() {{
                if (confirm('למחוק את כל האימונים?')) {{
                    await fetch('/api/workout/user/{user_id}/all', {{ method: 'DELETE' }});
                    location.reload();
                }}
            }}
        </script>
    </body>
    </html>
    """

@api_router.get("/u/{user_id}/year/{year}", response_class=HTMLResponse)
async def year_page(user_id: str, year: str):
    """Year page - shows months as folders"""
    workouts = await db.workouts.find(
        {"user_id": user_id, "timestamp": {"$regex": f"^{year}"}},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(500)
    
    month_names = ["", "ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני", 
                   "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"]
    
    from collections import defaultdict
    months_data = defaultdict(list)
    for w in workouts:
        month = w.get('timestamp', '')[5:7]
        if month:
            months_data[month].append(w)
    
    total_dist = sum(w.get('distance_cm', 0) for w in workouts) / 100000
    total_time = sum(w.get('duration_sec', 0) for w in workouts)
    total_hrs = total_time // 3600
    total_mins = (total_time % 3600) // 60
    time_str = f"{total_hrs}:{total_mins:02d}"
    avg_hr_list = [w.get('avg_hr') for w in workouts if w.get('avg_hr')]
    avg_hr = round(sum(avg_hr_list) / len(avg_hr_list)) if avg_hr_list else 0
    
    user_name = workouts[0].get('user_name', '') if workouts else ''
    
    months_html = ""
    for month in sorted(months_data.keys(), reverse=True):
        month_workouts = months_data[month]
        m_dist = sum(w.get('distance_cm', 0) for w in month_workouts) / 100000
        m_count = len(month_workouts)
        month_name = month_names[int(month)]
        
        months_html += f"""
        <a href="/u/{user_id}/year/{year}/month/{month}" class="folder-row">
            <div class="folder-icon">📁</div>
            <div class="folder-info">
                <div class="folder-name">{month_name}</div>
                <div class="folder-meta">{m_count} אימונים</div>
            </div>
            <div class="folder-stats">{m_dist:.1f} ק"מ</div>
            <div class="folder-arrow">←</div>
        </a>
        """
    
    return f"""
    <!DOCTYPE html>
    <html lang="he" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FitBeat - {year}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; color: white; padding: 1rem; }}
            .container {{ max-width: 480px; margin: 0 auto; }}
            .back {{ display: inline-flex; align-items: center; gap: 0.5rem; color: #00d4ff; text-decoration: none; margin-bottom: 1rem; font-size: 0.9rem; }}
            header {{ text-align: center; padding: 1rem 0; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 1.5rem; }}
            h1 {{ color: #00d4ff; font-size: 1.5rem; }}
            .subtitle {{ color: #888; margin-top: 0.25rem; }}
            
            .summary {{ background: linear-gradient(135deg, #1e1e3f 0%, #151530 100%); border-radius: 1rem; padding: 1.25rem; margin-bottom: 1.5rem; border: 1px solid rgba(0,212,255,0.2); }}
            .summary-title {{ color: #888; font-size: 0.85rem; margin-bottom: 0.75rem; }}
            .summary-row {{ display: flex; justify-content: space-around; text-align: center; }}
            .summary-item {{ }}
            .summary-value {{ font-size: 1.5rem; font-weight: bold; color: #00d4ff; }}
            .summary-value.green {{ color: #22c55e; }}
            .summary-label {{ color: #888; font-size: 0.75rem; }}
            
            .folders {{ background: linear-gradient(135deg, #1e1e3f 0%, #151530 100%); border-radius: 1rem; padding: 1rem; }}
            .folders-title {{ color: #888; font-size: 0.85rem; margin-bottom: 1rem; }}
            
            .folder-row {{ display: flex; align-items: center; padding: 1rem; background: rgba(0,0,0,0.2); border-radius: 0.75rem; margin-bottom: 0.5rem; text-decoration: none; color: white; transition: all 0.2s; }}
            .folder-row:hover {{ background: rgba(0,212,255,0.1); transform: translateX(-4px); }}
            .folder-icon {{ font-size: 1.75rem; margin-left: 0.75rem; }}
            .folder-info {{ flex: 1; }}
            .folder-name {{ font-weight: bold; font-size: 1.1rem; }}
            .folder-meta {{ color: #888; font-size: 0.8rem; }}
            .folder-stats {{ color: #22c55e; font-weight: bold; margin-left: 0.75rem; }}
            .folder-arrow {{ color: #00d4ff; font-size: 1.25rem; }}
            
            footer {{ text-align: center; padding: 1.5rem 0; color: #888; font-size: 0.8rem; }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/u/{user_id}" class="back">→ חזרה</a>
            <header>
                <h1>📁 {year}</h1>
                <p class="subtitle">{len(workouts)} אימונים</p>
            </header>
            
            <div class="summary">
                <div class="summary-title">📊 סיכום {year}</div>
                <div class="summary-row">
                    <div class="summary-item">
                        <div class="summary-value">{len(workouts)}</div>
                        <div class="summary-label">אימונים</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-value green">{total_dist:.1f}</div>
                        <div class="summary-label">ק"מ</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-value">{time_str}</div>
                        <div class="summary-label">שעות</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-value" style="color:#ef4444;">{avg_hr}</div>
                        <div class="summary-label">דופק</div>
                    </div>
                </div>
            </div>
            
            <div class="folders">
                <div class="folders-title">📁 חודשים</div>
                {months_html}
            </div>
            
            <footer>FitBeat</footer>
        </div>
    </body>
    </html>
    """

@api_router.get("/u/{user_id}/year/{year}/month/{month}", response_class=HTMLResponse)
async def month_page_view(user_id: str, year: str, month: str):
    """Month page - shows workouts list"""
    workouts = await db.workouts.find(
        {"user_id": user_id, "timestamp": {"$regex": f"^{year}-{month}"}},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(100)
    
    month_names = ["", "ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני", 
                   "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"]
    month_name = month_names[int(month)]
    
    total_dist = sum(w.get('distance_cm', 0) for w in workouts) / 100000
    total_time = sum(w.get('duration_sec', 0) for w in workouts)
    total_hrs = total_time // 3600
    total_mins = (total_time % 3600) // 60
    time_str = f"{total_hrs}:{total_mins:02d}"
    avg_hr_list = [w.get('avg_hr') for w in workouts if w.get('avg_hr')]
    avg_hr = round(sum(avg_hr_list) / len(avg_hr_list)) if avg_hr_list else 0
    total_steps = sum(w.get('steps', 0) or 0 for w in workouts)
    
    workouts_html = ""
    for w in workouts:
        dist_km = w.get('distance_cm', 0) / 100000
        dur_sec = w.get('duration_sec', 0)
        dur_min = dur_sec // 60
        dur_s = dur_sec % 60
        hr = w.get('avg_hr', '--')
        day = w.get('timestamp', '')[8:10]
        workout_id = w.get('id', '')
        
        if dist_km > 0:
            pace_sec = dur_sec / dist_km
            pace_str = f"{int(pace_sec//60)}:{int(pace_sec%60):02d}"
        else:
            pace_str = "--:--"
        
        workouts_html += f"""
        <a href="/u/{user_id}/workout/{workout_id}" class="workout-row">
            <div class="workout-day">{day}</div>
            <div class="workout-info">
                <div class="workout-dist">{dist_km:.2f} ק"מ</div>
                <div class="workout-pace">⚡ {pace_str}/ק"מ</div>
            </div>
            <div class="workout-time">{dur_min}:{dur_s:02d}</div>
            <div class="workout-hr">❤️ {hr}</div>
            <div class="workout-arrow">←</div>
        </a>
        """
    
    share_text = f"📅 {month_name} {year}%0A🏃 {len(workouts)} אימונים%0A📍 {total_dist:.1f} ק״מ%0A⏱️ {time_str} שעות%0A%0A🔗 https://web-production-110fc.up.railway.app/u/{user_id}/year/{year}/month/{month}"
    
    return f"""
    <!DOCTYPE html>
    <html lang="he" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FitBeat - {month_name} {year}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; color: white; padding: 1rem; }}
            .container {{ max-width: 480px; margin: 0 auto; }}
            .back {{ display: inline-flex; align-items: center; gap: 0.5rem; color: #00d4ff; text-decoration: none; margin-bottom: 1rem; font-size: 0.9rem; }}
            header {{ text-align: center; padding: 1rem 0; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 1.5rem; }}
            h1 {{ color: #00d4ff; font-size: 1.5rem; }}
            .subtitle {{ color: #888; margin-top: 0.25rem; }}
            
            .summary {{ background: linear-gradient(135deg, #1e1e3f 0%, #151530 100%); border-radius: 1rem; padding: 1.25rem; margin-bottom: 1.5rem; border: 1px solid rgba(0,212,255,0.2); }}
            .summary-title {{ color: #888; font-size: 0.85rem; margin-bottom: 0.75rem; }}
            .summary-row {{ display: flex; justify-content: space-around; text-align: center; }}
            .summary-item {{ }}
            .summary-value {{ font-size: 1.3rem; font-weight: bold; color: #00d4ff; }}
            .summary-value.green {{ color: #22c55e; }}
            .summary-label {{ color: #888; font-size: 0.7rem; }}
            
            .workouts {{ background: linear-gradient(135deg, #1e1e3f 0%, #151530 100%); border-radius: 1rem; padding: 1rem; margin-bottom: 1.5rem; }}
            .workouts-title {{ color: #888; font-size: 0.85rem; margin-bottom: 1rem; }}
            
            .workout-row {{ display: flex; align-items: center; padding: 0.75rem; background: rgba(0,0,0,0.2); border-radius: 0.5rem; margin-bottom: 0.4rem; text-decoration: none; color: white; transition: all 0.2s; }}
            .workout-row:hover {{ background: rgba(0,212,255,0.1); transform: translateX(-4px); }}
            .workout-day {{ background: #00d4ff; color: #1a1a2e; width: 2.25rem; height: 2.25rem; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; margin-left: 0.75rem; }}
            .workout-info {{ flex: 1; }}
            .workout-dist {{ font-weight: bold; }}
            .workout-pace {{ color: #888; font-size: 0.75rem; }}
            .workout-time {{ color: #00d4ff; font-weight: bold; font-size: 0.9rem; margin: 0 0.75rem; }}
            .workout-hr {{ color: #ef4444; font-size: 0.85rem; }}
            .workout-arrow {{ color: #00d4ff; font-size: 1rem; margin-right: 0.25rem; }}
            
            .share-btn {{ display: flex; align-items: center; justify-content: center; gap: 0.75rem; background: linear-gradient(90deg, #25D366 0%, #128C7E 100%); color: white; border: none; padding: 1rem 2rem; border-radius: 9999px; font-size: 1rem; font-weight: bold; cursor: pointer; text-decoration: none; margin-bottom: 1.5rem; }}
            
            footer {{ text-align: center; padding: 1rem 0; color: #888; font-size: 0.8rem; }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/u/{user_id}/year/{year}" class="back">→ חזרה ל-{year}</a>
            <header>
                <h1>📁 {month_name} {year}</h1>
                <p class="subtitle">{len(workouts)} אימונים</p>
            </header>
            
            <div class="summary">
                <div class="summary-title">📊 סיכום {month_name}</div>
                <div class="summary-row">
                    <div class="summary-item">
                        <div class="summary-value">{len(workouts)}</div>
                        <div class="summary-label">אימונים</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-value green">{total_dist:.1f}</div>
                        <div class="summary-label">ק"מ</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-value">{time_str}</div>
                        <div class="summary-label">שעות</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-value" style="color:#ef4444;">{avg_hr}</div>
                        <div class="summary-label">דופק</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-value">{total_steps:,}</div>
                        <div class="summary-label">צעדים</div>
                    </div>
                </div>
            </div>
            
            <div class="workouts">
                <div class="workouts-title">🏃 אימונים</div>
                {workouts_html}
            </div>
            
            <a href="https://wa.me/?text={share_text}" target="_blank" class="share-btn">📤 שתף ב-WhatsApp</a>
            
            <footer>FitBeat</footer>
        </div>
    </body>
    </html>
    """

@api_router.get("/u/{user_id}/workout/{workout_id}", response_class=HTMLResponse)
async def single_workout_page(user_id: str, workout_id: str):
    """Serve single workout HTML page"""
    workout = await db.workouts.find_one(
        {"id": workout_id, "user_id": user_id},
        {"_id": 0}
    )
    return generate_workout_html(workout, user_id)

@api_router.get("/u/{user_id}/monthly", response_class=HTMLResponse)
async def monthly_page(user_id: str):
    """Serve monthly summary HTML page with all workouts"""
    workouts = await db.workouts.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(100)
    
    if not workouts:
        return f"""
        <!DOCTYPE html>
        <html lang="he" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>FitBeat - סיכום חודשי</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; color: white; display: flex; align-items: center; justify-content: center; }}
                .container {{ text-align: center; padding: 2rem; }}
                h1 {{ color: #00d4ff; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📅 אין אימונים</h1>
                <p>מזהה: {user_id}</p>
            </div>
        </body>
        </html>
        """
    
    # Calculate totals
    total_dist = sum(w.get('distance_cm', 0) for w in workouts)
    total_time = sum(w.get('duration_sec', 0) for w in workouts)
    total_steps = sum(w.get('steps', 0) or 0 for w in workouts)
    avg_hr_list = [w.get('avg_hr') for w in workouts if w.get('avg_hr')]
    avg_hr = round(sum(avg_hr_list) / len(avg_hr_list)) if avg_hr_list else 0
    
    # Format totals
    total_km = total_dist / 100000
    total_hrs = total_time // 3600
    total_mins = (total_time % 3600) // 60
    time_str = f"{total_hrs} שעות ו-{total_mins} דקות" if total_hrs > 0 else f"{total_mins} דקות"
    
    # Build workout rows
    workout_rows = ""
    for w in workouts:
        dist_km = w.get('distance_cm', 0) / 100000
        dur_min = w.get('duration_sec', 0) // 60
        hr = w.get('avg_hr', '--')
        ts = w.get('timestamp', '')[:10]
        workout_id = w.get('id', '')
        workout_rows += f"""
        <a href="/u/{user_id}/workout/{workout_id}" class="workout-row">
            <div class="workout-icon">🏃</div>
            <div class="workout-info">
                <div class="workout-dist">{dist_km:.2f} ק"מ</div>
                <div class="workout-date">{ts}</div>
            </div>
            <div class="workout-stats">
                <div class="workout-time">{dur_min} דק'</div>
                <div class="workout-hr">❤️ {hr}</div>
            </div>
            <div class="workout-arrow">←</div>
        </a>
        """
    
    user_name = workouts[0].get('user_name', '') if workouts else ''
    
    return f"""
    <!DOCTYPE html>
    <html lang="he" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FitBeat - סיכום חודשי</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; color: white; padding: 1rem; }}
            .container {{ max-width: 480px; margin: 0 auto; }}
            header {{ text-align: center; padding: 1.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 1.5rem; }}
            h1 {{ color: #00d4ff; font-size: 1.5rem; }}
            .subtitle {{ color: #888; margin-top: 0.5rem; }}
            .totals {{ background: linear-gradient(135deg, #1e1e3f 0%, #151530 100%); border-radius: 1rem; padding: 1.5rem; margin-bottom: 1.5rem; }}
            .totals-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; text-align: center; }}
            .total-value {{ font-size: 2.5rem; font-weight: bold; color: #00d4ff; }}
            .total-value.green {{ color: #22c55e; }}
            .total-label {{ color: #888; font-size: 0.9rem; margin-top: 0.25rem; }}
            .stats-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.5rem; margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid rgba(255,255,255,0.1); }}
            .stat-item {{ text-align: center; }}
            .stat-value {{ font-size: 1.1rem; font-weight: bold; }}
            .stat-label {{ color: #888; font-size: 0.7rem; }}
            .workouts-section {{ background: linear-gradient(135deg, #1e1e3f 0%, #151530 100%); border-radius: 1rem; padding: 1rem; margin-bottom: 1.5rem; }}
            .section-title {{ color: #888; font-size: 0.9rem; margin-bottom: 1rem; }}
            .workout-row {{ display: flex; align-items: center; padding: 0.75rem; background: rgba(0,0,0,0.2); border-radius: 0.5rem; margin-bottom: 0.5rem; text-decoration: none; color: white; transition: background 0.2s; }}
            .workout-row:hover {{ background: rgba(0,212,255,0.1); }}
            .workout-icon {{ font-size: 1.5rem; margin-left: 0.75rem; }}
            .workout-info {{ flex: 1; }}
            .workout-dist {{ font-weight: bold; }}
            .workout-date {{ color: #888; font-size: 0.75rem; }}
            .workout-stats {{ text-align: left; margin-left: 1rem; }}
            .workout-time {{ color: #00d4ff; font-weight: bold; }}
            .workout-hr {{ color: #888; font-size: 0.75rem; }}
            .workout-arrow {{ color: #00d4ff; font-size: 1.2rem; margin-right: 0.5rem; }}
            .share-btn {{ display: flex; align-items: center; justify-content: center; gap: 0.75rem; background: linear-gradient(90deg, #25D366 0%, #128C7E 100%); color: white; border: none; padding: 1rem 2rem; border-radius: 9999px; font-size: 1.1rem; font-weight: bold; cursor: pointer; margin: 1.5rem auto; text-decoration: none; }}
            footer {{ text-align: center; padding: 1rem 0; color: #888; font-size: 0.8rem; }}
            footer .brand {{ color: #00d4ff; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>📅 סיכום חודשי</h1>
                <p class="subtitle">{user_name}</p>
            </header>
            
            <div class="totals">
                <div class="totals-grid">
                    <div>
                        <div class="total-value">{len(workouts)}</div>
                        <div class="total-label">אימונים</div>
                    </div>
                    <div>
                        <div class="total-value green">{total_km:.1f}</div>
                        <div class="total-label">ק"מ סה"כ</div>
                    </div>
                </div>
                <div class="stats-row">
                    <div class="stat-item">
                        <div class="stat-value">⏱️</div>
                        <div class="stat-label">{time_str}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">❤️</div>
                        <div class="stat-label">{avg_hr} BPM</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">👟</div>
                        <div class="stat-label">{total_steps:,}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">📍</div>
                        <div class="stat-label">{total_km/len(workouts):.1f} ק"מ/אימון</div>
                    </div>
                </div>
            </div>
            
            <div class="workouts-section">
                <div class="section-title">🏃 כל האימונים</div>
                {workout_rows}
            </div>
            
            <a href="https://wa.me/?text=📅 סיכום חודשי%0A🏃 {len(workouts)} אימונים%0A📍 {total_km:.1f} ק״מ סה״כ%0A⏱️ {time_str}%0A%0A🔗 https://web-production-110fc.up.railway.app/u/{user_id}/monthly" class="share-btn">
                📤 שתף ב-WhatsApp
            </a>
            
            <footer>
                <div class="brand">FitBeat</div>
                <div>מזהה: {user_id}</div>
            </footer>
        </div>
    </body>
    </html>
    """

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
