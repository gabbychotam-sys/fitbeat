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
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# ═══════════════════════════════════════════════════════════════
# TRANSLATIONS - 6 LANGUAGES (matching watch app)
# 0=English, 1=Hebrew, 2=Spanish, 3=French, 4=German, 5=Chinese
# ═══════════════════════════════════════════════════════════════
TRANSLATIONS = {
    "welcome_title": ["Welcome to FitBeat!", "ברוכים הבאים ל-FitBeat!", "¡Bienvenido a FitBeat!", "Bienvenue sur FitBeat!", "Willkommen bei FitBeat!", "欢迎使用FitBeat!"],
    "your_dashboard": ["This is your personal dashboard", "זהו הדשבורד האישי שלך", "Este es tu panel personal", "Voici votre tableau de bord", "Dies ist dein persönliches Dashboard", "这是您的个人仪表板"],
    "send_whatsapp": ["Send to myself via WhatsApp", "שלח לעצמי ב-WhatsApp", "Enviarme por WhatsApp", "M'envoyer via WhatsApp", "Per WhatsApp senden", "通过WhatsApp发送给自己"],
    "got_it": ["Got it, thanks!", "הבנתי, תודה!", "¡Entendido, gracias!", "Compris, merci!", "Verstanden, danke!", "明白了，谢谢！"],
    "total_summary": ["Total Summary", "סיכום כולל", "Resumen Total", "Résumé Total", "Gesamtübersicht", "总结"],
    "yearly_summary": ["Yearly Summary", "סיכום שנתי", "Resumen Anual", "Résumé Annuel", "Jahresübersicht", "年度总结"],
    "monthly_summary": ["Monthly Summary", "סיכום חודשי", "Resumen Mensual", "Résumé Mensuel", "Monatsübersicht", "月度总结"],
    "workouts": ["workouts", "אימונים", "entrenamientos", "entraînements", "Trainings", "训练"],
    "workout": ["Workout", "אימון", "Entrenamiento", "Entraînement", "Training", "训练"],
    "km": ["km", "ק\"מ", "km", "km", "km", "公里"],
    "km_total": ["km total", "ק\"מ סה\"כ", "km total", "km total", "km gesamt", "公里总计"],
    "hours": ["hours", "שעות", "horas", "heures", "Stunden", "小时"],
    "minutes": ["minutes", "דקות", "minutos", "minutes", "Minuten", "分钟"],
    "avg_hr": ["Avg HR", "דופק ממוצע", "FC Prom", "FC Moy", "Ø HF", "平均心率"],
    "max_hr": ["Max HR", "דופק מקסימלי", "FC Máx", "FC Max", "Max HF", "最大心率"],
    "elevation_gain": ["Elevation Gain", "עלייה", "Ascenso", "Dénivelé+", "Anstieg", "爬升"],
    "elevation_loss": ["Elevation Loss", "ירידה", "Descenso", "Dénivelé-", "Abstieg", "下降"],
    "cadence": ["Cadence", "קצב צעדים", "Cadencia", "Cadence", "Kadenz", "步频"],
    "steps": ["steps", "צעדים", "pasos", "pas", "Schritte", "步"],
    "pace": ["pace", "קצב", "ritmo", "allure", "Tempo", "配速"],
    "distance": ["Distance", "מרחק", "Distancia", "Distance", "Distanz", "距离"],
    "duration": ["Duration", "משך", "Duración", "Durée", "Dauer", "时长"],
    "share_whatsapp": ["Share on WhatsApp", "שתף ב-WhatsApp", "Compartir en WhatsApp", "Partager sur WhatsApp", "Auf WhatsApp teilen", "分享到WhatsApp"],
    "delete_workout": ["Delete workout", "מחק אימון", "Eliminar entrenamiento", "Supprimer l'entraînement", "Training löschen", "删除训练"],
    "delete_all": ["Delete all", "מחק הכל", "Eliminar todo", "Tout supprimer", "Alles löschen", "删除全部"],
    "confirm_delete": ["Delete this workout?", "למחוק את האימון הזה?", "¿Eliminar este entrenamiento?", "Supprimer cet entraînement?", "Dieses Training löschen?", "删除这个训练？"],
    "confirm_delete_all": ["Delete all workouts?", "למחוק את כל האימונים?", "¿Eliminar todos los entrenamientos?", "Supprimer tous les entraînements?", "Alle Trainings löschen?", "删除所有训练？"],
    "no_workouts": ["No workouts yet", "אין אימונים עדיין", "Sin entrenamientos aún", "Pas encore d'entraînements", "Noch keine Trainings", "还没有训练"],
    "finish_goal": ["Finish a goal on your watch and it will appear here!", "סיים יעד בשעון והאימון יופיע כאן!", "¡Completa una meta en tu reloj y aparecerá aquí!", "Terminez un objectif sur votre montre et il apparaîtra ici!", "Schließe ein Ziel auf deiner Uhr ab und es erscheint hier!", "在手表上完成目标，它将显示在这里！"],
    "by_years": ["By Years", "לפי שנים", "Por Años", "Par Années", "Nach Jahren", "按年份"],
    "all_workouts": ["All Workouts", "כל האימונים", "Todos los Entrenamientos", "Tous les Entraînements", "Alle Trainings", "所有训练"],
    "back": ["Back", "חזור", "Volver", "Retour", "Zurück", "返回"],
    "user_id": ["ID", "מזהה", "ID", "ID", "ID", "ID"],
    "powered_by": ["Powered by Garmin Fenix 8 Solar", "Powered by Garmin Fenix 8 Solar", "Powered by Garmin Fenix 8 Solar", "Powered by Garmin Fenix 8 Solar", "Powered by Garmin Fenix 8 Solar", "Powered by Garmin Fenix 8 Solar"],
    "and": ["and", "ו-", "y", "et", "und", "和"],
    "total_time": ["Total time", "זמן כולל", "Tiempo total", "Temps total", "Gesamtzeit", "总时间"],
    "per_workout": ["per workout", "לאימון", "por entrenamiento", "par entraînement", "pro Training", "每次训练"],
    "route": ["Route", "מסלול", "Ruta", "Parcours", "Strecke", "路线"],
    "no_route": ["No GPS data", "אין נתוני GPS", "Sin datos GPS", "Pas de données GPS", "Keine GPS-Daten", "无GPS数据"],
    "meters": ["m", "מ'", "m", "m", "m", "米"],
    "spm": ["spm", "צ'/דק'", "ppm", "ppm", "spm", "步/分"],
}

# Month names in 6 languages
MONTH_NAMES = {
    0: ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
    1: ["", "ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני", "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"],
    2: ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"],
    3: ["", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"],
    4: ["", "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"],
    5: ["", "一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"],
}

def t(key, lang=0):
    """Get translation for key in specified language"""
    if key in TRANSLATIONS:
        return TRANSLATIONS[key][lang] if lang < len(TRANSLATIONS[key]) else TRANSLATIONS[key][0]
    return key

def get_month_name(month_num, lang=0):
    """Get month name in specified language"""
    if lang in MONTH_NAMES and month_num < len(MONTH_NAMES[lang]):
        return MONTH_NAMES[lang][month_num]
    return MONTH_NAMES[0][month_num]

def is_rtl(lang):
    """Check if language is right-to-left"""
    return lang == 1  # Hebrew

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
    route_json: Optional[str] = None  # NEW: JSON string from watch (Garmin array bug workaround)
    lang: Optional[int] = 0  # Language: 0=EN, 1=HE, 2=ES, 3=FR, 4=DE, 5=ZH

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
    lang: int = 0  # Language preference

def generate_user_id(device_id: str) -> str:
    """Generate a short unique user ID from device ID"""
    hash_obj = hashlib.sha256(device_id.encode())
    return hash_obj.hexdigest()[:8]

@api_router.get("/")
async def root():
    return {"message": "FitBeat API v4.5.7"}

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
    """Download FitBeat v4.6.7 - Delayed HTTP send (prevents crash!)"""
    file_path = Path("/app/fitbeat_v467.zip")
    if file_path.exists():
        return FileResponse(
            path=file_path,
            filename="fitbeat_v467.zip",
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=fitbeat_v467.zip"}
        )
    return {"error": "File not found"}

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

@api_router.get("/download/server-py")
async def download_server_py():
    """Download updated server.py with Leaflet map"""
    file_path = Path("/app/backend/server.py")
    if file_path.exists():
        return FileResponse(
            path=file_path,
            filename="server.py",
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=server.py"}
        )
    return {"error": "File not found"}


@api_router.get("/download/summary")
async def download_summary():
    """Download FitBeat full summary document"""
    file_path = Path("/app/memory/FITBEAT_FULL_SUMMARY.md")
    if file_path.exists():
        return FileResponse(
            path=file_path,
            filename="FITBEAT_FULL_SUMMARY.md",
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=FITBEAT_FULL_SUMMARY.md"}
        )
    return {"error": "File not found"}


@api_router.get("/download/insights")
async def download_insights():
    """Download FitBeat insights document v4.6.7 FINAL"""
    file_path = Path("/app/FITBEAT_INSIGHTS_FINAL.md")
    if file_path.exists():
        return FileResponse(
            path=file_path,
            filename="FitBeat_Insights_v467.md",
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=FitBeat_Insights_v467.md"}
        )
    return {"error": "File not found"}

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
    
    # Parse route from either route array or route_json string
    route_data = None
    if workout.route:
        route_data = [p.model_dump() for p in workout.route]
    elif workout.route_json and workout.route_json.strip():
        # Parse JSON string from watch (Garmin array bug workaround)
        try:
            route_data = json.loads(workout.route_json)
            logger.info(f"Parsed route_json with {len(route_data)} points")
        except Exception as e:
            logger.warning(f"Failed to parse route_json: {e}")
            route_data = None
    
    workout_obj = WorkoutSummary(
        user_id=workout.user_id,
        user_name=workout.user_name,
        distance_cm=workout.distance_cm,
        duration_sec=workout.duration_sec,
        avg_hr=workout.avg_hr if workout.avg_hr and workout.avg_hr > 0 else None,
        max_hr=workout.max_hr if workout.max_hr and workout.max_hr > 0 else None,
        elevation_gain=workout.elevation_gain,
        elevation_loss=workout.elevation_loss,
        steps=workout.steps if workout.steps and workout.steps > 0 else None,
        cadence=workout.cadence if workout.cadence and workout.cadence > 0 else None,
        route=route_data
    )
    
    doc = workout_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.workouts.insert_one(doc)
    
    logger.info(f"Workout saved for user {workout.user_id}: {workout.distance_cm}cm in {workout.duration_sec}s, route points: {len(route_data) if route_data else 0}")
    
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

def generate_workout_html(workout, user_id, lang=0):
    """Generate HTML page for workout summary with Leaflet map"""
    # RTL support
    dir_attr = 'dir="rtl"' if is_rtl(lang) else 'dir="ltr"'
    lang_code = ["en", "he", "es", "fr", "de", "zh"][lang] if lang < 6 else "en"
    
    if not workout:
        return f"""
        <!DOCTYPE html>
        <html lang="{lang_code}" {dir_attr}>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>FitBeat - {t('no_workouts', lang)}</title>
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
                <p>{t('no_workouts', lang)}</p>
                <p class="user-id">{t('user_id', lang)}: {user_id}</p>
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
    route = workout.get('route', []) or []
    
    # Format date and time
    timestamp = workout.get('timestamp', '')
    formatted_datetime = ''
    if timestamp:
        try:
            # Parse ISO timestamp
            if 'T' in timestamp:
                date_part = timestamp[:10]  # 2026-01-26
                time_part = timestamp[11:16]  # 10:06
                # Format based on language
                if lang == 1:  # Hebrew - DD/MM/YYYY HH:MM
                    day, month, year = date_part[8:10], date_part[5:7], date_part[:4]
                    formatted_datetime = f"{day}/{month}/{year} {time_part}"
                else:  # Other languages - YYYY-MM-DD HH:MM
                    formatted_datetime = f"{date_part} {time_part}"
            else:
                formatted_datetime = timestamp[:16]
        except:
            formatted_datetime = timestamp[:16] if len(timestamp) > 16 else timestamp
    
    # Get base URL
    base_url = os.environ.get('APP_URL', 'https://fitbeat-gps.preview.emergentagent.com')
    
    # WhatsApp share text (translated)
    share_texts = {
        0: f"🏃‍♂️ {user_name} finished a workout!%0A%0A📍 Distance: {dist_km:.2f} km%0A⏱️ Time: {duration_str}%0A⚡ Pace: {pace_str}/km",
        1: f"🏃‍♂️ {user_name} סיים אימון!%0A%0A📍 מרחק: {dist_km:.2f} ק״מ%0A⏱️ זמן: {duration_str}%0A⚡ קצב: {pace_str}/ק״מ",
        2: f"🏃‍♂️ ¡{user_name} terminó un entrenamiento!%0A%0A📍 Distancia: {dist_km:.2f} km%0A⏱️ Tiempo: {duration_str}%0A⚡ Ritmo: {pace_str}/km",
        3: f"🏃‍♂️ {user_name} a terminé un entraînement!%0A%0A📍 Distance: {dist_km:.2f} km%0A⏱️ Temps: {duration_str}%0A⚡ Allure: {pace_str}/km",
        4: f"🏃‍♂️ {user_name} hat ein Training beendet!%0A%0A📍 Distanz: {dist_km:.2f} km%0A⏱️ Zeit: {duration_str}%0A⚡ Tempo: {pace_str}/km",
        5: f"🏃‍♂️ {user_name}完成了训练!%0A%0A📍 距离: {dist_km:.2f} km%0A⏱️ 时间: {duration_str}%0A⚡ 配速: {pace_str}/km",
    }
    share_text = share_texts.get(lang, share_texts[0])
    if avg_hr:
        hr_texts = {0: f"%0A❤️ HR: {avg_hr} BPM", 1: f"%0A❤️ דופק: {avg_hr} BPM", 2: f"%0A❤️ FC: {avg_hr} LPM", 3: f"%0A❤️ FC: {avg_hr} BPM", 4: f"%0A❤️ HF: {avg_hr} SPM", 5: f"%0A❤️ 心率: {avg_hr} BPM"}
        share_text += hr_texts.get(lang, hr_texts[0])
    share_text += f"%0A%0A🔗 {base_url}/api/u/{user_id}?lang={lang}"
    
    # Convert route to JSON for JavaScript
    route_json = json.dumps([[p['lat'], p['lon']] for p in route]) if route else "[]"
    has_route = len(route) > 0
    
    # Generate map section - Leaflet if route exists, SVG fallback otherwise
    if has_route:
        map_section = f'''
            <div class="map-container">
                <div id="map"></div>
                <div class="map-badge">
                    <span class="value">{dist_km:.2f}</span>
                    <span class="unit">{t('km', lang)}</span>
                </div>
            </div>
        '''
    else:
        map_section = f'''
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
                    <span class="unit">{t('km', lang)}</span>
                </div>
                <div class="no-gps">{t('no_route', lang)}</div>
            </div>
        '''
    
    # Build extra stats section with all parameters
    extra_stats_html = ""
    
    # Max HR
    if max_hr:
        extra_stats_html += f'''
            <div class="extra-stat">
                <span class="label">💓 {t('max_hr', lang)}</span>
                <span class="value" style="color:#ef4444;">{max_hr} BPM</span>
            </div>
        '''
    
    # Elevation Gain
    if elevation_gain > 0:
        extra_stats_html += f'''
            <div class="extra-stat">
                <span class="label">📈 {t('elevation_gain', lang)}</span>
                <span class="value" style="color:#22c55e;">+{elevation_gain:.0f} {t('meters', lang)}</span>
            </div>
        '''
    
    # Elevation Loss
    if elevation_loss > 0:
        extra_stats_html += f'''
            <div class="extra-stat">
                <span class="label">📉 {t('elevation_loss', lang)}</span>
                <span class="value" style="color:#f97316;">-{elevation_loss:.0f} {t('meters', lang)}</span>
            </div>
        '''
    
    # Cadence
    if cadence > 0:
        extra_stats_html += f'''
            <div class="extra-stat">
                <span class="label">🦶 {t('cadence', lang)}</span>
                <span class="value">{cadence} {t('spm', lang)}</span>
            </div>
        '''
    
    # Steps
    if steps > 0:
        extra_stats_html += f'''
            <div class="extra-stat">
                <span class="label">👟 {t('steps', lang)}</span>
                <span class="value">{steps:,}</span>
            </div>
        '''
    
    return f"""
    <!DOCTYPE html>
    <html lang="{lang_code}" {dir_attr}>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FitBeat - {t('workout', lang)}</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; color: white; padding: 1rem; }}
            .container {{ max-width: 480px; margin: 0 auto; }}
            header {{ text-align: center; padding: 1.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 1.5rem; }}
            h1 {{ color: #00d4ff; font-size: 1.5rem; margin-bottom: 0.25rem; }}
            .subtitle {{ color: #888; font-size: 0.9rem; }}
            .user-name {{ font-size: 1.1rem; margin-top: 0.5rem; }}
            
            /* Leaflet Map Container */
            .map-container {{ position: relative; border-radius: 1rem; height: 220px; margin-bottom: 1.5rem; overflow: hidden; }}
            #map {{ width: 100%; height: 100%; border-radius: 1rem; z-index: 1; }}
            .map-container .map-badge {{ position: absolute; top: 0.75rem; {"left" if is_rtl(lang) else "right"}: 0.75rem; background: rgba(0,0,0,0.85); padding: 0.5rem 1rem; border-radius: 0.75rem; border: 1px solid rgba(255,255,255,0.2); z-index: 1000; }}
            .map-badge .value {{ font-size: 1.5rem; font-weight: bold; color: #00d4ff; }}
            .map-badge .unit {{ font-size: 0.8rem; color: #888; }}
            
            /* SVG Fallback Map */
            .map {{ background: linear-gradient(135deg, #2d4a2d 0%, #1a2f1a 100%); border-radius: 1rem; height: 200px; margin-bottom: 1.5rem; position: relative; overflow: hidden; }}
            .map svg {{ position: absolute; inset: 0; width: 100%; height: 100%; }}
            .map .map-badge {{ position: absolute; top: 0.75rem; {"left" if is_rtl(lang) else "right"}: 0.75rem; background: rgba(0,0,0,0.8); padding: 0.5rem 1rem; border-radius: 0.75rem; border: 1px solid rgba(255,255,255,0.1); }}
            .no-gps {{ position: absolute; bottom: 0.75rem; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,0.7); padding: 0.25rem 0.75rem; border-radius: 0.5rem; font-size: 0.75rem; color: #888; }}
            
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
            
            .share-btn {{ display: flex; align-items: center; justify-content: center; gap: 0.75rem; background: linear-gradient(90deg, #25D366 0%, #128C7E 100%); color: white; border: none; padding: 1rem 2rem; border-radius: 9999px; font-size: 1.1rem; font-weight: bold; cursor: pointer; margin: 2rem auto; box-shadow: 0 4px 15px rgba(37, 211, 102, 0.3); text-decoration: none; }}
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
                <h1>🏃‍♂️ {t('workout', lang)}</h1>
                <p class="subtitle">{formatted_datetime}</p>
                {'<p class="user-name">' + user_name + '</p>' if user_name else ''}
            </header>
            
            {map_section}
            
            <div class="stats">
                <div class="stat">
                    <div class="icon">📍</div>
                    <div class="label">{t('distance', lang)}</div>
                    <div class="value highlight">{dist_km:.2f}<span class="unit">{t('km', lang)}</span></div>
                </div>
                <div class="stat">
                    <div class="icon">⏱️</div>
                    <div class="label">{t('duration', lang)}</div>
                    <div class="value">{duration_str}</div>
                </div>
                <div class="stat">
                    <div class="icon">⚡</div>
                    <div class="label">{t('pace', lang)}</div>
                    <div class="value">{pace_str}<span class="unit">/{t('km', lang)}</span></div>
                </div>
                {'<div class="stat"><div class="icon">❤️</div><div class="label">' + t("avg_hr", lang) + '</div><div class="value" style="color:#ef4444;">' + str(avg_hr) + '<span class="unit">BPM</span></div></div>' if avg_hr else ''}
            </div>
            
            {f'<div class="section"><div class="section-title">📊 {t("workout", lang)}</div><div class="extra-stats">{extra_stats_html}</div></div>' if extra_stats_html else ''}
            
            <a href="https://wa.me/?text={share_text}" target="_blank" class="share-btn">
                <svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
                {t('share_whatsapp', lang)}
            </a>
            
            <button onclick="deleteWorkout()" class="delete-btn">🗑️ {t('delete_workout', lang)}</button>
            
            <footer>
                <div class="brand">FitBeat</div>
                <div>{t('powered_by', lang)}</div>
                <div class="user-id">{t('user_id', lang)}: {user_id}</div>
            </footer>
        </div>
        
        <script>
            // Initialize Leaflet map if route data exists
            const routeData = {route_json};
            if (routeData.length > 0) {{
                const map = L.map('map', {{
                    zoomControl: true,
                    attributionControl: false
                }});
                
                // Add OpenStreetMap tiles
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    maxZoom: 19
                }}).addTo(map);
                
                // Create polyline from route
                const polyline = L.polyline(routeData, {{
                    color: '#ff3333',
                    weight: 4,
                    opacity: 0.9,
                    lineCap: 'round',
                    lineJoin: 'round'
                }}).addTo(map);
                
                // Add start marker (green)
                const startIcon = L.divIcon({{
                    html: '<div style="background:#22c55e;width:16px;height:16px;border-radius:50%;border:3px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.4);"></div>',
                    className: '',
                    iconSize: [16, 16],
                    iconAnchor: [8, 8]
                }});
                L.marker(routeData[0], {{icon: startIcon}}).addTo(map);
                
                // Add end marker (red)
                const endIcon = L.divIcon({{
                    html: '<div style="background:#ef4444;width:16px;height:16px;border-radius:50%;border:3px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.4);"></div>',
                    className: '',
                    iconSize: [16, 16],
                    iconAnchor: [8, 8]
                }});
                L.marker(routeData[routeData.length - 1], {{icon: endIcon}}).addTo(map);
                
                // Fit map to route bounds with padding
                map.fitBounds(polyline.getBounds(), {{
                    padding: [30, 30]
                }});
            }}
            
            async function deleteWorkout() {{
                if (confirm('{t("confirm_delete", lang)}')) {{
                    try {{
                        const response = await fetch('/api/workout/{workout_id}', {{ method: 'DELETE' }});
                        if (response.ok) {{
                            window.location.href = '/api/u/{user_id}?lang={lang}';
                        }}
                    }} catch (e) {{
                        console.error(e);
                    }}
                }}
            }}
        </script>
    </body>
    </html>
    """

@api_router.get("/u/{user_id}", response_class=HTMLResponse)
async def dashboard_page(user_id: str, welcome: str = None, lang: int = None):
    """Main page - shows years as folders"""
    workouts = await db.workouts.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(500)
    
    # Get language from parameter, or from user's latest workout, or default to English
    if lang is None:
        lang = workouts[0].get('lang', 0) if workouts else 0
    
    # Check if this is first visit (show welcome banner)
    is_first_visit = welcome == "1" or (len(workouts) == 1)
    
    # RTL support for Hebrew
    dir_attr = 'dir="rtl"' if is_rtl(lang) else 'dir="ltr"'
    lang_code = ["en", "he", "es", "fr", "de", "zh"][lang] if lang < 6 else "en"
    
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
    time_str = f"{total_hrs} {t('hours', lang)} {t('and', lang)} {total_mins} {t('minutes', lang)}" if total_hrs > 0 else f"{total_mins} {t('minutes', lang)}"
    
    user_name = workouts[0].get('user_name', '') if workouts else ''
    
    # Build year folders
    years_html = ""
    for year in sorted(years_data.keys(), reverse=True):
        year_workouts = years_data[year]
        y_dist = sum(w.get('distance_cm', 0) for w in year_workouts) / 100000
        y_count = len(year_workouts)
        
        years_html += f"""
        <a href="/api/u/{user_id}/year/{year}?lang={lang}" class="folder-row">
            <div class="folder-icon">📁</div>
            <div class="folder-info">
                <div class="folder-name">{year}</div>
                <div class="folder-meta">{y_count} {t('workouts', lang)}</div>
            </div>
            <div class="folder-stats">{y_dist:.1f} {t('km', lang)}</div>
            <div class="folder-arrow">{'←' if is_rtl(lang) else '→'}</div>
        </a>
        """
    
    # Get base URL from environment or use default
    base_url = os.environ.get('APP_URL', 'https://fitbeat-gps.preview.emergentagent.com')
    dashboard_url = f"{base_url}/api/u/{user_id}"
    
    # Welcome message for WhatsApp (translated)
    welcome_wa_text = {
        0: f"🎉 Welcome! My FitBeat dashboard:%0A%0A🔗 {dashboard_url}%0A%0A💾 Save this link!",
        1: f"🎉 שלום! הדשבורד האישי שלי ב-FitBeat:%0A%0A🔗 {dashboard_url}%0A%0A💾 שמור את הלינק הזה!",
        2: f"🎉 ¡Hola! Mi panel FitBeat:%0A%0A🔗 {dashboard_url}%0A%0A💾 ¡Guarda este enlace!",
        3: f"🎉 Bonjour! Mon tableau FitBeat:%0A%0A🔗 {dashboard_url}%0A%0A💾 Sauvegardez ce lien!",
        4: f"🎉 Hallo! Mein FitBeat Dashboard:%0A%0A🔗 {dashboard_url}%0A%0A💾 Speichere diesen Link!",
        5: f"🎉 你好！我的FitBeat仪表板:%0A%0A🔗 {dashboard_url}%0A%0A💾 保存此链接!",
    }
    welcome_text = welcome_wa_text.get(lang, welcome_wa_text[0])
    
    # Welcome banner HTML (shown on first visit)
    welcome_banner = ""
    if is_first_visit and workouts:
        welcome_banner = f"""
        <div class="welcome-banner" id="welcomeBanner">
            <div class="welcome-icon">🎉</div>
            <h2>{t('welcome_title', lang)}</h2>
            <p>{t('your_dashboard', lang)}</p>
            <p class="welcome-link">{dashboard_url}</p>
            <a href="https://wa.me/?text={welcome_text}" target="_blank" class="welcome-btn">
                📲 {t('send_whatsapp', lang)}
            </a>
            <button onclick="closeWelcome()" class="welcome-close">{t('got_it', lang)}</button>
        </div>
        """
    
    # Share text for the main share button
    share_text = f"📊 FitBeat%0A🏃 {len(workouts)} {t('workouts', lang)}%0A📍 {total_km:.1f} {t('km', lang)}%0A%0A🔗 {dashboard_url}"
    
    return f"""
    <!DOCTYPE html>
    <html lang="{lang_code}" {dir_attr}>
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
            
            .welcome-banner {{ position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.95); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 1000; padding: 2rem; text-align: center; }}
            .welcome-icon {{ font-size: 4rem; margin-bottom: 1rem; }}
            .welcome-banner h2 {{ color: #00d4ff; font-size: 1.8rem; margin-bottom: 0.5rem; }}
            .welcome-banner p {{ color: #888; margin-bottom: 0.5rem; }}
            .welcome-link {{ font-family: monospace; color: #00d4ff; font-size: 0.8rem; background: rgba(0,212,255,0.1); padding: 0.5rem 1rem; border-radius: 0.5rem; margin: 1rem 0; word-break: break-all; }}
            .welcome-btn {{ display: flex; align-items: center; justify-content: center; gap: 0.5rem; background: linear-gradient(90deg, #25D366 0%, #128C7E 100%); color: white; padding: 1rem 2rem; border-radius: 9999px; font-size: 1.1rem; font-weight: bold; text-decoration: none; margin: 1rem 0; }}
            .welcome-close {{ background: transparent; color: #888; border: 1px solid #888; padding: 0.5rem 1.5rem; border-radius: 9999px; cursor: pointer; margin-top: 1rem; }}
            .welcome-close:hover {{ color: white; border-color: white; }}
            
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
        {welcome_banner}
        <div class="container">
            <header>
                <h1>🏃‍♂️ FitBeat</h1>
                {'<p class="user-name">' + user_name + '</p>' if user_name else ''}
            </header>
            
            <div class="summary">
                <div class="summary-title">📊 {t('total_summary', lang)}</div>
                <div class="summary-grid">
                    <div>
                        <div class="summary-value">{len(workouts)}</div>
                        <div class="summary-label">{t('workouts', lang)}</div>
                    </div>
                    <div>
                        <div class="summary-value green">{total_km:.1f}</div>
                        <div class="summary-label">{t('km_total', lang)}</div>
                    </div>
                </div>
            </div>
            
            <div class="folders">
                <div class="folders-title">📁 {t('by_years', lang)}</div>
                {years_html if years_html else f'<div class="no-workouts"><div class="no-workouts-icon">🏃‍♂️</div><p>{t("no_workouts", lang)}</p><p style="font-size:0.8rem;margin-top:0.5rem;color:#888;">{t("finish_goal", lang)}</p></div>'}
            </div>
            
            <div class="buttons">
                <a href="https://wa.me/?text={share_text}" target="_blank" class="share-btn">📤 {t('share_whatsapp', lang)}</a>
                {f'<button onclick="deleteAll()" class="delete-btn">🗑️ {t("delete_all", lang)}</button>' if workouts else ''}
            </div>
            
            <footer>
                <div class="brand">FitBeat</div>
                <div class="user-id">{t('user_id', lang)}: {user_id}</div>
            </footer>
        </div>
        <script>
            async function deleteAll() {{
                if (confirm('{t("confirm_delete_all", lang)}')) {{
                    await fetch('/api/workout/user/{user_id}/all', {{ method: 'DELETE' }});
                    location.reload();
                }}
            }}
            function closeWelcome() {{
                document.getElementById('welcomeBanner').style.display = 'none';
                localStorage.setItem('fitbeat_welcomed_{user_id}', 'true');
            }}
            // Auto-hide if already welcomed
            if (localStorage.getItem('fitbeat_welcomed_{user_id}')) {{
                const banner = document.getElementById('welcomeBanner');
                if (banner) banner.style.display = 'none';
            }}
        </script>
    </body>
    </html>
    """

@api_router.get("/u/{user_id}/year/{year}", response_class=HTMLResponse)
async def year_page(user_id: str, year: str, lang: int = None):
    """Year page - shows months as folders"""
    workouts = await db.workouts.find(
        {"user_id": user_id, "timestamp": {"$regex": f"^{year}"}},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(500)
    
    # Get language
    if lang is None:
        lang = workouts[0].get('lang', 0) if workouts else 0
    
    # RTL support
    dir_attr = 'dir="rtl"' if is_rtl(lang) else 'dir="ltr"'
    lang_code = ["en", "he", "es", "fr", "de", "zh"][lang] if lang < 6 else "en"
    
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
    
    months_html = ""
    for month in sorted(months_data.keys(), reverse=True):
        month_workouts = months_data[month]
        m_dist = sum(w.get('distance_cm', 0) for w in month_workouts) / 100000
        m_count = len(month_workouts)
        month_name = get_month_name(int(month), lang)
        
        months_html += f"""
        <a href="/api/u/{user_id}/year/{year}/month/{month}?lang={lang}" class="folder-row">
            <div class="folder-icon">📁</div>
            <div class="folder-info">
                <div class="folder-name">{month_name}</div>
                <div class="folder-meta">{m_count} {t('workouts', lang)}</div>
            </div>
            <div class="folder-stats">{m_dist:.1f} {t('km', lang)}</div>
            <div class="folder-arrow">{'←' if is_rtl(lang) else '→'}</div>
        </a>
        """
    
    return f"""
    <!DOCTYPE html>
    <html lang="{lang_code}" {dir_attr}>
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
            .folder-icon {{ font-size: 1.75rem; {"margin-left" if is_rtl(lang) else "margin-right"}: 0.75rem; }}
            .folder-info {{ flex: 1; }}
            .folder-name {{ font-weight: bold; font-size: 1.1rem; }}
            .folder-meta {{ color: #888; font-size: 0.8rem; }}
            .folder-stats {{ color: #22c55e; font-weight: bold; {"margin-left" if is_rtl(lang) else "margin-right"}: 0.75rem; }}
            .folder-arrow {{ color: #00d4ff; font-size: 1.25rem; }}
            
            footer {{ text-align: center; padding: 1.5rem 0; color: #888; font-size: 0.8rem; }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/api/u/{user_id}?lang={lang}" class="back">{'→' if is_rtl(lang) else '←'} {t('back', lang)}</a>
            <header>
                <h1>📁 {year}</h1>
                <p class="subtitle">{len(workouts)} {t('workouts', lang)}</p>
            </header>
            
            <div class="summary">
                <div class="summary-title">📊 {t('yearly_summary', lang)} {year}</div>
                <div class="summary-row">
                    <div class="summary-item">
                        <div class="summary-value">{len(workouts)}</div>
                        <div class="summary-label">{t('workouts', lang)}</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-value green">{total_dist:.1f}</div>
                        <div class="summary-label">{t('km', lang)}</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-value">{time_str}</div>
                        <div class="summary-label">{t('hours', lang)}</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-value" style="color:#ef4444;">{avg_hr}</div>
                        <div class="summary-label">{t('avg_hr', lang)}</div>
                    </div>
                </div>
            </div>
            
            <div class="folders">
                {months_html}
            </div>
            
            <footer>FitBeat</footer>
        </div>
    </body>
    </html>
    """

@api_router.get("/u/{user_id}/year/{year}/month/{month}", response_class=HTMLResponse)
async def month_page_view(user_id: str, year: str, month: str, lang: int = None):
    """Month page - shows workouts list"""
    workouts = await db.workouts.find(
        {"user_id": user_id, "timestamp": {"$regex": f"^{year}-{month}"}},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(100)
    
    # Get language
    if lang is None:
        lang = workouts[0].get('lang', 0) if workouts else 0
    
    # RTL support
    dir_attr = 'dir="rtl"' if is_rtl(lang) else 'dir="ltr"'
    lang_code = ["en", "he", "es", "fr", "de", "zh"][lang] if lang < 6 else "en"
    
    month_name = get_month_name(int(month), lang)
    
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
        timestamp = w.get('timestamp', '')
        day = timestamp[8:10] if len(timestamp) >= 10 else ''
        time_of_day = timestamp[11:16] if len(timestamp) >= 16 else ''  # HH:MM
        workout_id = w.get('id', '')
        
        if dist_km > 0:
            pace_sec = dur_sec / dist_km
            pace_str = f"{int(pace_sec//60)}:{int(pace_sec%60):02d}"
        else:
            pace_str = "--:--"
        
        workouts_html += f"""
        <a href="/api/u/{user_id}/workout/{workout_id}?lang={lang}" class="workout-row">
            <div class="workout-day">{day}</div>
            <div class="workout-info">
                <div class="workout-dist">{dist_km:.2f} {t('km', lang)}</div>
                <div class="workout-pace">🕐 {time_of_day} | ⚡ {pace_str}/{t('km', lang)}</div>
            </div>
            <div class="workout-time">{dur_min}:{dur_s:02d}</div>
            <div class="workout-hr">❤️ {hr}</div>
            <div class="workout-arrow">{'←' if is_rtl(lang) else '→'}</div>
        </a>
        """
    
    base_url = os.environ.get('APP_URL', 'https://fitbeat-gps.preview.emergentagent.com')
    share_text = f"📅 {month_name} {year}%0A🏃 {len(workouts)} {t('workouts', lang)}%0A📍 {total_dist:.1f} {t('km', lang)}%0A⏱️ {time_str} {t('hours', lang)}%0A%0A🔗 {base_url}/api/u/{user_id}/year/{year}/month/{month}?lang={lang}"
    
    return f"""
    <!DOCTYPE html>
    <html lang="{lang_code}" {dir_attr}>
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
            .workout-arrow {{ color: #00d4ff; font-size: 1rem; {"margin-right" if is_rtl(lang) else "margin-left"}: 0.25rem; }}
            
            .share-btn {{ display: flex; align-items: center; justify-content: center; gap: 0.75rem; background: linear-gradient(90deg, #25D366 0%, #128C7E 100%); color: white; border: none; padding: 1rem 2rem; border-radius: 9999px; font-size: 1rem; font-weight: bold; cursor: pointer; text-decoration: none; margin-bottom: 1.5rem; }}
            
            footer {{ text-align: center; padding: 1rem 0; color: #888; font-size: 0.8rem; }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/api/u/{user_id}/year/{year}?lang={lang}" class="back">{'→' if is_rtl(lang) else '←'} {t('back', lang)} {year}</a>
            <header>
                <h1>📁 {month_name} {year}</h1>
                <p class="subtitle">{len(workouts)} {t('workouts', lang)}</p>
            </header>
            
            <div class="summary">
                <div class="summary-title">📊 {t('monthly_summary', lang)}</div>
                <div class="summary-row">
                    <div class="summary-item">
                        <div class="summary-value">{len(workouts)}</div>
                        <div class="summary-label">{t('workouts', lang)}</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-value green">{total_dist:.1f}</div>
                        <div class="summary-label">{t('km', lang)}</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-value">{time_str}</div>
                        <div class="summary-label">{t('hours', lang)}</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-value" style="color:#ef4444;">{avg_hr}</div>
                        <div class="summary-label">{t('avg_hr', lang)}</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-value">{total_steps:,}</div>
                        <div class="summary-label">{t('steps', lang)}</div>
                    </div>
                </div>
            </div>
            
            <div class="workouts">
                {workouts_html}
            </div>
            
            <a href="https://wa.me/?text={share_text}" target="_blank" class="share-btn">📤 {t('share_whatsapp', lang)}</a>
            
            <footer>FitBeat</footer>
        </div>
    </body>
    </html>
    """

@api_router.get("/u/{user_id}/workout/{workout_id}", response_class=HTMLResponse)
async def single_workout_page(user_id: str, workout_id: str, lang: int = None):
    """Serve single workout HTML page"""
    workout = await db.workouts.find_one(
        {"id": workout_id, "user_id": user_id},
        {"_id": 0}
    )
    # Get language from parameter or workout
    if lang is None:
        lang = workout.get('lang', 0) if workout else 0
    return generate_workout_html(workout, user_id, lang)

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
    
    # Get base URL
    base_url = os.environ.get('APP_URL', 'https://fitbeat-gps.preview.emergentagent.com')
    
    # Build workout rows
    workout_rows = ""
    for w in workouts:
        dist_km = w.get('distance_cm', 0) / 100000
        dur_min = w.get('duration_sec', 0) // 60
        hr = w.get('avg_hr', '--')
        ts = w.get('timestamp', '')[:10]
        workout_id = w.get('id', '')
        workout_rows += f"""
        <a href="/api/u/{user_id}/workout/{workout_id}" class="workout-row">
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
            
            <a href="https://wa.me/?text=📅 סיכום חודשי%0A🏃 {len(workouts)} אימונים%0A📍 {total_km:.1f} ק״מ סה״כ%0A⏱️ {time_str}%0A%0A🔗 {base_url}/api/u/{user_id}/monthly" class="share-btn">
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
