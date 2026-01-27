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
    "about_app": ["About the App", "אודות האפליקציה", "Acerca de la App", "À propos de l'App", "Über die App", "关于应用"],
    "about_text": ["FitBeat helps you exercise safely with real-time heart rate monitoring, GPS tracking, and personalized goals.", "FitBeat עוזרת לך להתאמן בבטחה עם ניטור דופק בזמן אמת, מעקב GPS ויעדים מותאמים אישית.", "FitBeat te ayuda a ejercitarte de forma segura con monitoreo de frecuencia cardiaca, GPS y metas personalizadas.", "FitBeat vous aide à vous exercer en sécurité avec surveillance cardiaque, GPS et objectifs personnalisés.", "FitBeat hilft dir sicher zu trainieren mit Herzfrequenzüberwachung, GPS und personalisierten Zielen.", "FitBeat通过实时心率监测、GPS追踪和个性化目标帮助您安全锻炼。"],
    "download_app": ["Download App", "הורד את האפליקציה", "Descargar App", "Télécharger l'App", "App herunterladen", "下载应用"],
    "save_bookmark": ["Save to Bookmarks", "שמור בסימניות", "Guardar en Favoritos", "Ajouter aux Favoris", "Als Lesezeichen speichern", "添加到书签"],
    "bookmark_tip": ["Tip: Add this page to your bookmarks to access your workouts anytime!", "טיפ: הוסף את הדף לסימניות כדי לגשת לאימונים שלך בכל עת!", "Tip: Añade esta página a favoritos para acceder a tus entrenamientos!", "Conseil: Ajoutez cette page aux favoris pour accéder à vos entraînements!", "Tipp: Füge diese Seite zu Lesezeichen hinzu, um jederzeit auf deine Trainings zuzugreifen!", "提示：将此页面添加到书签，随时查看您的训练！"],
    "welcome_page_title": ["Welcome to FitBeat", "ברוכים הבאים ל-FitBeat", "Bienvenido a FitBeat", "Bienvenue sur FitBeat", "Willkommen bei FitBeat", "欢迎使用FitBeat"],
    "select_language": ["Select your language", "בחר את השפה שלך", "Selecciona tu idioma", "Choisissez votre langue", "Wahle deine Sprache", "选择您的语言"],
    "what_is_fitbeat": ["What is FitBeat?", "מה זה FitBeat?", "Que es FitBeat?", "Qu'est-ce que FitBeat?", "Was ist FitBeat?", "什么是FitBeat？"],
    "fitbeat_desc": ["FitBeat is a smart fitness app for Garmin watches that helps you exercise safely and effectively.", "FitBeat היא אפליקציית כושר חכמה לשעוני Garmin שעוזרת לך להתאמן בבטחה וביעילות.", "FitBeat es una aplicacion inteligente para relojes Garmin que te ayuda a ejercitarte de forma segura.", "FitBeat est une application fitness intelligente pour montres Garmin qui vous aide a vous exercer en securite.", "FitBeat ist eine intelligente Fitness-App fur Garmin-Uhren die dir hilft sicher zu trainieren.", "FitBeat是一款适用于Garmin手表的智能健身应用，帮助您安全有效地锻炼。"],
    "key_features": ["Key Features", "תכונות עיקריות", "Caracteristicas Principales", "Fonctionnalites Principales", "Hauptfunktionen", "主要功能"],
    "feature_hr": ["Real-time heart rate monitoring with alerts", "ניטור דופק בזמן אמת עם התראות", "Monitoreo de frecuencia cardiaca en tiempo real", "Surveillance cardiaque en temps reel avec alertes", "Echtzeit-Herzfrequenzuberwachung mit Benachrichtigungen", "实时心率监测和警报"],
    "feature_gps": ["GPS route tracking", "מעקב מסלול GPS", "Seguimiento de ruta GPS", "Suivi GPS du parcours", "GPS-Streckenverfolgung", "GPS路线追踪"],
    "feature_goals": ["Distance and time goals", "יעדי מרחק וזמן", "Metas de distancia y tiempo", "Objectifs de distance et temps", "Distanz- und Zeitziele", "距离和时间目标"],
    "feature_dashboard": ["Personal web dashboard to view all workouts", "דשבורד אישי לצפייה בכל האימונים", "Panel web personal para ver todos los entrenamientos", "Tableau de bord web pour voir tous les entrainements", "Personliches Web-Dashboard fur alle Trainings", "个人网页仪表板查看所有训练"],
    "feature_share": ["Share achievements on WhatsApp", "שיתוף הישגים ב-WhatsApp", "Compartir logros en WhatsApp", "Partager les reussites sur WhatsApp", "Erfolge auf WhatsApp teilen", "在WhatsApp上分享成就"],
    "how_it_works": ["How Does It Work?", "איך זה עובד?", "Como Funciona?", "Comment ca Marche?", "Wie Funktioniert Es?", "如何使用？"],
    "step1": ["Download FitBeat from the Garmin Connect IQ Store", "הורד את FitBeat מחנות Garmin Connect IQ", "Descarga FitBeat desde la tienda Garmin Connect IQ", "Telechargez FitBeat depuis le store Garmin Connect IQ", "Lade FitBeat aus dem Garmin Connect IQ Store herunter", "从Garmin Connect IQ商店下载FitBeat"],
    "step2": ["Make sure Garmin Connect app is open on your phone", "ודא שאפליקציית Garmin Connect פתוחה בטלפון", "Asegurate de que la app Garmin Connect este abierta en tu telefono", "Assurez-vous que l'app Garmin Connect est ouverte sur votre telephone", "Stelle sicher dass die Garmin Connect App auf deinem Handy offen ist", "确保手机上的Garmin Connect应用已打开"],
    "step3": ["Complete a workout goal on your watch", "סיים יעד אימון בשעון שלך", "Completa una meta de entrenamiento en tu reloj", "Terminez un objectif d'entrainement sur votre montre", "Schliesse ein Trainingsziel auf deiner Uhr ab", "在手表上完成训练目标"],
    "step4": ["Your workout syncs automatically to this dashboard!", "האימון שלך מסתנכרן אוטומטית לדשבורד!", "Tu entrenamiento se sincroniza automaticamente!", "Votre entrainement se synchronise automatiquement!", "Dein Training wird automatisch synchronisiert!", "您的训练会自动同步到仪表板！"],
    "important_note": ["Important", "חשוב", "Importante", "Important", "Wichtig", "重要"],
    "sync_note": ["The app requires your phone with Garmin Connect to be nearby and connected via Bluetooth for workout sync.", "האפליקציה דורשת שהטלפון עם Garmin Connect יהיה בקרבת מקום ומחובר בבלוטות' לסנכרון אימונים.", "La app requiere que tu telefono con Garmin Connect este cerca y conectado por Bluetooth.", "L'app necessite que votre telephone avec Garmin Connect soit a proximite et connecte en Bluetooth.", "Die App benotigt dein Handy mit Garmin Connect in der Nahe und uber Bluetooth verbunden.", "应用需要您的手机上的Garmin Connect在附近并通过蓝牙连接。"],
    "personal_dashboard": ["Your Personal Dashboard", "הדשבורד האישי שלך", "Tu Panel Personal", "Votre Tableau de Bord", "Dein Personliches Dashboard", "您的个人仪表板"],
    "dashboard_info": ["After your first workout, your personal ID will appear on the watch. Use it to access your dashboard:", "אחרי האימון הראשון, המזהה האישי שלך יופיע בשעון. השתמש בו כדי לגשת לדשבורד:", "Despues de tu primer entrenamiento tu ID personal aparecera en el reloj. Usalo para acceder a tu panel:", "Apres votre premier entrainement votre ID personnel apparaitra sur la montre. Utilisez-le pour acceder:", "Nach deinem ersten Training erscheint deine personliche ID auf der Uhr. Nutze sie fur dein Dashboard:", "首次训练后您的个人ID将显示在手表上。使用它访问您的仪表板："],
    "dashboard_url_example": ["https://fitbeat.it.com/api/u/YOUR_ID?lang=0", "https://fitbeat.it.com/api/u/YOUR_ID?lang=1", "https://fitbeat.it.com/api/u/TU_ID?lang=2", "https://fitbeat.it.com/api/u/VOTRE_ID?lang=3", "https://fitbeat.it.com/api/u/DEINE_ID?lang=4", "https://fitbeat.it.com/api/u/YOUR_ID?lang=5"],
    "save_this_page": ["Save This Page!", "שמור את הדף הזה!", "Guarda Esta Pagina!", "Sauvegardez Cette Page!", "Speichere Diese Seite!", "保存此页面！"],
    "colors": ["Colors", "צבעים", "Colores", "Couleurs", "Farben", "颜色"],
    "workouts_title": ["Workouts", "אימונים", "Entrenamientos", "Entrainements", "Trainings", "训练"],
    "total_km": ["Total km", "סה״כ ק״מ", "Total km", "Total km", "Gesamt km", "总公里"],
    "avg_hr_alt": ["Avg HR", "דופק ממוצע", "FC Prom", "FC Moy", "Durchschn. HF", "平均心率"],
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
    local_time: Optional[str] = None  # Local time from watch (ISO format)

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
@api_router.get("/download/server-only")
async def download_server_only():
    """Download server.py only (for GitHub)"""
    file_path = Path("/app/server_py_only.zip")
    if file_path.exists():
        return FileResponse(
            path=file_path,
            filename="server_py_only.zip",
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=server_py_only.zip", "Cache-Control": "no-store"}
        )
    return {"error": "File not found"}

@api_router.get("/download/full-package")
async def download_full_package():
    """Download FitBeat v4.6.9 + server.py (new endpoint)"""
    file_path = Path("/app/fitbeat_complete.zip")
    if file_path.exists():
        return FileResponse(
            path=file_path,
            filename="fitbeat_v469.zip",
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=fitbeat_v469.zip", "Cache-Control": "no-store"}
        )
    return {"error": "File not found"}

@api_router.get("/download/fitbeat")
async def download_fitbeat():
    """Download FitBeat v4.6.9 + server.py"""
    file_path = Path("/app/fitbeat_complete.zip")
    if file_path.exists():
        return FileResponse(
            path=file_path,
            filename="fitbeat_complete.zip",
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=fitbeat_complete.zip"}
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
    """Download updated server.py with local_time fix"""
    file_path = Path("/app/backend/server_v469_final.py")
    if file_path.exists():
        return FileResponse(
            path=file_path,
            filename="server.py",
            media_type="text/plain",
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
    """Download insights markdown"""
    file_path = Path("/app/memory/server_py_content.txt")
    if file_path.exists():
        return FileResponse(
            path=file_path,
            filename="server.py",
            media_type="text/plain",
            headers={"Content-Disposition": "attachment; filename=server.py"}
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
    
    # Use local time from watch if provided, otherwise use server time
    timestamp = datetime.now(timezone.utc)
    if workout.local_time and workout.local_time.strip():
        try:
            # Parse local time from watch (format: YYYY-MM-DDTHH:MM:SS)
            timestamp = datetime.fromisoformat(workout.local_time)
            logger.info(f"Using local time from watch: {workout.local_time}")
        except Exception as e:
            logger.warning(f"Failed to parse local_time '{workout.local_time}': {e}, using server time")
            timestamp = datetime.now(timezone.utc)
    
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
        route=route_data,
        timestamp=timestamp
    )
    
    doc = workout_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.workouts.insert_one(doc)
    
    logger.info(f"Workout saved for user {workout.user_id}: {workout.distance_cm}cm in {workout.duration_sec}s, route points: {len(route_data) if route_data else 0}, time: {doc['timestamp']}")
    
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
        except Exception:
            formatted_datetime = timestamp[:16] if len(timestamp) > 16 else timestamp
    
    # Get base URL
    base_url = os.environ.get('APP_URL', 'https://fitbeat.it.com')
    
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

@api_router.get("/welcome", response_class=HTMLResponse)
async def welcome_page(lang: int = 0):
    """Landing page - clean minimal design with working dashboard link"""
    
    # RTL support for Hebrew
    dir_attr = 'dir="rtl"' if is_rtl(lang) else 'dir="ltr"'
    lang_code = ["en", "he", "es", "fr", "de", "zh"][lang] if lang < 6 else "en"
    
    # Translations for this page
    titles = ["Welcome to FitBeat", "ברוכים הבאים ל-FitBeat", "Bienvenido a FitBeat", "Bienvenue sur FitBeat", "Willkommen bei FitBeat", "欢迎使用FitBeat"]
    slogans = ["Your Personal Fitness Tracker", "מעקב הכושר האישי שלך", "Tu Rastreador de Fitness", "Votre Tracker Fitness", "Dein Fitness Tracker", "您的健身追踪器"]
    
    desc_texts = [
        "FitBeat tracks your walks and runs on your Garmin watch, with heart rate monitoring, GPS routes, and a personal dashboard.",
        "FitBeat עוקבת אחרי ההליכות והריצות שלך בשעון Garmin, עם ניטור דופק, מסלולי GPS ודשבורד אישי.",
        "FitBeat rastrea tus caminatas y carreras en tu reloj Garmin, con monitoreo cardíaco, rutas GPS y panel personal.",
        "FitBeat suit vos marches et courses sur votre montre Garmin, avec suivi cardiaque, parcours GPS et tableau de bord.",
        "FitBeat verfolgt deine Walks und Läufe auf deiner Garmin-Uhr, mit Herzfrequenz, GPS-Routen und Dashboard.",
        "FitBeat在您的Garmin手表上追踪步行和跑步，包括心率监测、GPS路线和个人仪表板。"
    ]
    
    dashboard_titles = ["Your Dashboard", "הדשבורד שלך", "Tu Panel", "Votre Tableau", "Dein Dashboard", "您的仪表板"]
    dashboard_descs = [
        "After your first workout, your ID will appear on the watch. Access your dashboard at:",
        "אחרי האימון הראשון, המזהה שלך יופיע בשעון. גש לדשבורד שלך בכתובת:",
        "Después de tu primer entrenamiento, tu ID aparecerá en el reloj. Accede a tu panel en:",
        "Après votre premier entraînement, votre ID apparaîtra sur la montre. Accédez à:",
        "Nach deinem ersten Training erscheint deine ID auf der Uhr. Dein Dashboard:",
        "首次训练后，您的ID将显示在手表上。访问您的仪表板："
    ]
    
    bookmark_tips = [
        "Save this link! Replace YOUR_ID with your personal ID from the watch.",
        "שמור את הלינק הזה! החלף YOUR_ID במזהה האישי שלך מהשעון.",
        "¡Guarda este enlace! Reemplaza YOUR_ID con tu ID personal del reloj.",
        "Sauvegardez ce lien! Remplacez YOUR_ID par votre ID sur la montre.",
        "Speichere diesen Link! Ersetze YOUR_ID mit deiner ID von der Uhr.",
        "保存此链接！将YOUR_ID替换为手表上的个人ID。"
    ]
    
    download_texts = ["Download from Garmin Store", "הורד מחנות Garmin", "Descargar de Garmin Store", "Télécharger sur Garmin Store", "Im Garmin Store herunterladen", "从Garmin商店下载"]
    
    title = titles[lang] if lang < 6 else titles[0]
    slogan = slogans[lang] if lang < 6 else slogans[0]
    desc = desc_texts[lang] if lang < 6 else desc_texts[0]
    dash_title = dashboard_titles[lang] if lang < 6 else dashboard_titles[0]
    dash_desc = dashboard_descs[lang] if lang < 6 else dashboard_descs[0]
    bookmark_tip = bookmark_tips[lang] if lang < 6 else bookmark_tips[0]
    download_text = download_texts[lang] if lang < 6 else download_texts[0]
    
    # The working dashboard URL (production)
    dashboard_url = "https://fitbeat.it.com/api/u/YOUR_ID"
    
    return f"""
    <!DOCTYPE html>
    <html lang="{lang_code}" {dir_attr}>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FitBeat - {title}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                background: #0d0d14;
                min-height: 100vh; 
                color: #e0e0e0; 
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 2rem 1.5rem;
            }}
            
            .container {{ 
                max-width: 400px; 
                width: 100%;
                text-align: center;
            }}
            
            /* Logo */
            .logo {{ 
                font-size: 4rem; 
                margin-bottom: 0.5rem;
            }}
            
            /* Title */
            h1 {{ 
                color: #00d4ff; 
                font-size: 2rem; 
                font-weight: 700;
                margin-bottom: 0.25rem;
            }}
            
            .slogan {{ 
                color: #666; 
                font-size: 0.95rem;
                margin-bottom: 2rem;
            }}
            
            /* Description */
            .desc {{ 
                color: #888; 
                font-size: 0.9rem;
                line-height: 1.6;
                margin-bottom: 2.5rem;
                padding: 0 0.5rem;
            }}
            
            /* Dashboard Section */
            .dashboard-section {{
                background: linear-gradient(145deg, #151520 0%, #0f0f18 100%);
                border: 1px solid #1a1a2a;
                border-radius: 1rem;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
            }}
            
            .dash-title {{
                color: #00d4ff;
                font-size: 1.1rem;
                font-weight: 600;
                margin-bottom: 0.75rem;
            }}
            
            .dash-desc {{
                color: #777;
                font-size: 0.85rem;
                margin-bottom: 1rem;
                line-height: 1.5;
            }}
            
            /* URL Box */
            .url-box {{
                background: #0a0a10;
                border: 1px solid #00d4ff40;
                border-radius: 0.5rem;
                padding: 1rem;
                margin-bottom: 1rem;
            }}
            
            .url-link {{
                font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
                color: #00d4ff;
                font-size: 0.8rem;
                word-break: break-all;
                display: block;
                text-decoration: none;
            }}
            
            .url-link:hover {{
                text-decoration: underline;
            }}
            
            /* Tip */
            .tip {{
                color: #999;
                font-size: 0.8rem;
                font-style: italic;
            }}
            
            /* Download Button */
            .btn-download {{
                display: block;
                background: linear-gradient(135deg, #00d4ff 0%, #0099bb 100%);
                color: #000;
                font-weight: 700;
                font-size: 1rem;
                padding: 1rem 2rem;
                border-radius: 2rem;
                text-decoration: none;
                margin-bottom: 1rem;
                transition: transform 0.2s, box-shadow 0.2s;
            }}
            
            .btn-download:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(0, 212, 255, 0.3);
            }}
            
            /* Footer */
            .footer {{
                margin-top: 2rem;
                color: #333;
                font-size: 0.75rem;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">🏃‍♂️</div>
            <h1>FitBeat</h1>
            <p class="slogan">{slogan}</p>
            
            <p class="desc">{desc}</p>
            
            <div class="dashboard-section">
                <div class="dash-title">📊 {dash_title}</div>
                <p class="dash-desc">{dash_desc}</p>
                <div class="url-box">
                    <a href="{dashboard_url}" class="url-link" target="_blank">{dashboard_url}</a>
                </div>
                <p class="tip">💡 {bookmark_tip}</p>
            </div>
            
            <a href="https://apps.garmin.com/apps/c303ee47-1ecf-4487-91c9-3de4ca1a74d5" target="_blank" class="btn-download">
                ⬇️ {download_text}
            </a>
            
            <div class="footer">FitBeat © 2026</div>
        </div>
    </body>
    </html>
    """

@api_router.get("/u/{user_id}", response_class=HTMLResponse)
async def dashboard_page(user_id: str, welcome: str = None, lang: int = None):
    """Main dashboard - 50/50 layout: workout data on one side, app info on other"""
    workouts = await db.workouts.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(500)
    
    # Get language from parameter, or from user's latest workout, or default to English
    if lang is None:
        lang = workouts[0].get('lang', 0) if workouts else 0
    
    # RTL support for Hebrew
    is_rtl_lang = is_rtl(lang)
    dir_attr = 'dir="rtl"' if is_rtl_lang else 'dir="ltr"'
    lang_code = ["en", "he", "es", "fr", "de", "zh"][lang] if lang < 6 else "en"
    
    # Group workouts by year
    from collections import defaultdict
    years_data = defaultdict(list)
    for w in workouts:
        year = w.get('timestamp', '')[:4]
        if year:
            years_data[year].append(w)
    
    # Calculate total summary
    total_dist = sum(w.get('distance_cm', 0) for w in workouts) if workouts else 0
    total_km = total_dist / 100000
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
            <div class="folder-arrow">{'←' if is_rtl_lang else '→'}</div>
        </a>
        """
    
    # Get base URL
    base_url = os.environ.get('APP_URL', 'https://fitbeat.it.com')
    dashboard_url = f"{base_url}/api/u/{user_id}?lang={lang}"
    share_text = f"📊 FitBeat%0A🏃 {len(workouts)} {t('workouts', lang)}%0A📍 {total_km:.1f} {t('km', lang)}%0A🔗 {dashboard_url}"
    
    # Detailed app descriptions per language
    app_descriptions = {
        0: """<b>How to use FitBeat:</b>

<b>Main Screen:</b>
• Tap the <b>TIME</b> (top) → Opens Settings (language, name, 10 colors)
• Tap the <b>DISTANCE</b> → Set distance goal (1-20 km/mi)
• Tap the <b>TIMER</b> → Set time goal (10-120 minutes)
• Tap the <b>HEART</b> (bottom) → Heart rate monitoring settings

<b>Smart Heart Rate:</b>
• Choose "Auto" - measures your current HR and sets target +15 BPM
• Or select a percentage (50%-90%) of your max heart rate
• Get alerts when you exceed your target!
• Get notified when you're back in the safe zone

<b>Features:</b>
• GPS route tracking with map display
• Halfway & goal completion alerts with celebration animation
• 10 customizable colors
• 6 languages supported
• Auto-sync to this dashboard

<b>Important:</b> Garmin Connect app must be open on your phone for sync to work.""",

        1: """<b>איך להשתמש ב-FitBeat:</b>

<b>מסך ראשי:</b>
• לחץ על <b>השעה</b> (למעלה) ← הגדרות (שפה, שם, 10 צבעים)
• לחץ על <b>המרחק</b> ← בחר יעד מרחק (1-20 ק"מ)
• לחץ על <b>הטיימר</b> ← בחר יעד זמן (10-120 דקות)
• לחץ על <b>הלב</b> (למטה) ← הגדרות ניטור דופק

<b>ניטור דופק חכם:</b>
• בחר "אוטו" - מודד את הדופק הנוכחי ומגדיר יעד +15 פעימות
• או בחר אחוז (50%-90%) מהדופק המקסימלי שלך
• מקבל התראה כשעוברים את היעד!
• מקבל הודעה כשחוזרים לטווח הבטוח

<b>פיצ'רים:</b>
• מעקב GPS עם תצוגת מפה
• התראות בחצי הדרך ובסיום היעד עם אנימציה
• 10 צבעים לבחירה
• 6 שפות נתמכות
• סנכרון אוטומטי לדשבורד

<b>חשוב:</b> אפליקציית Garmin Connect צריכה להיות פתוחה בטלפון לסנכרון.""",

        2: """<b>Cómo usar FitBeat:</b>

<b>Pantalla principal:</b>
• Toca la <b>HORA</b> (arriba) → Ajustes (idioma, nombre, 10 colores)
• Toca la <b>DISTANCIA</b> → Establecer meta de distancia (1-20 km)
• Toca el <b>TEMPORIZADOR</b> → Establecer meta de tiempo (10-120 min)
• Toca el <b>CORAZÓN</b> (abajo) → Ajustes de frecuencia cardíaca

<b>Monitoreo cardíaco inteligente:</b>
• Elige "Auto" - mide tu FC actual y establece objetivo +15 LPM
• O selecciona un porcentaje (50%-90%) de tu FC máxima
• ¡Recibe alertas cuando superas tu objetivo!
• Te avisa cuando vuelves a la zona segura

<b>Características:</b>
• Seguimiento GPS con visualización de mapa
• Alertas a mitad de camino y al completar meta
• 10 colores personalizables
• 6 idiomas soportados
• Sincronización automática

<b>Importante:</b> Garmin Connect debe estar abierta en tu teléfono.""",

        3: """<b>Comment utiliser FitBeat:</b>

<b>Écran principal:</b>
• Touchez l'<b>HEURE</b> (haut) → Paramètres (langue, nom, 10 couleurs)
• Touchez la <b>DISTANCE</b> → Définir objectif distance (1-20 km)
• Touchez le <b>CHRONO</b> → Définir objectif temps (10-120 min)
• Touchez le <b>CŒUR</b> (bas) → Paramètres fréquence cardiaque

<b>Suivi cardiaque intelligent:</b>
• Choisissez "Auto" - mesure votre FC et définit objectif +15 BPM
• Ou sélectionnez un pourcentage (50%-90%) de votre FC max
• Alertes quand vous dépassez votre objectif!
• Notification quand vous revenez dans la zone sûre

<b>Fonctionnalités:</b>
• Suivi GPS avec affichage carte
• Alertes mi-parcours et fin d'objectif avec animation
• 10 couleurs personnalisables
• 6 langues supportées
• Synchronisation automatique

<b>Important:</b> Garmin Connect doit être ouverte sur votre téléphone.""",

        4: """<b>So verwendest du FitBeat:</b>

<b>Hauptbildschirm:</b>
• Tippe auf die <b>UHRZEIT</b> (oben) → Einstellungen (Sprache, Name, 10 Farben)
• Tippe auf die <b>DISTANZ</b> → Distanzziel setzen (1-20 km)
• Tippe auf den <b>TIMER</b> → Zeitziel setzen (10-120 min)
• Tippe auf das <b>HERZ</b> (unten) → Herzfrequenz-Einstellungen

<b>Intelligente Herzüberwachung:</b>
• Wähle "Auto" - misst deine aktuelle HF und setzt Ziel +15 SPM
• Oder wähle einen Prozentsatz (50%-90%) deiner max. HF
• Alarm wenn du dein Ziel überschreitest!
• Benachrichtigung wenn du wieder im sicheren Bereich bist

<b>Funktionen:</b>
• GPS-Tracking mit Kartenanzeige
• Halbzeit- und Zielalarme mit Animation
• 10 anpassbare Farben
• 6 Sprachen unterstützt
• Automatische Synchronisation

<b>Wichtig:</b> Garmin Connect muss auf deinem Handy geöffnet sein.""",

        5: """<b>如何使用FitBeat：</b>

<b>主屏幕：</b>
• 点击<b>时间</b>（顶部）→ 设置（语言、名称、10种颜色）
• 点击<b>距离</b> → 设置距离目标（1-20公里）
• 点击<b>计时器</b> → 设置时间目标（10-120分钟）
• 点击<b>心脏</b>（底部）→ 心率监测设置

<b>智能心率监测：</b>
• 选择"自动" - 测量当前心率并设置目标+15次/分
• 或选择最大心率的百分比（50%-90%）
• 超过目标时收到警报！
• 回到安全区域时收到通知

<b>功能：</b>
• GPS路线追踪与地图显示
• 半程和目标完成提醒带动画
• 10种可自定义颜色
• 支持6种语言
• 自动同步到仪表板

<b>重要：</b>手机上的Garmin Connect必须打开才能同步。"""
    }
    
    app_desc = app_descriptions.get(lang, app_descriptions[0])
    
    # Bookmark instructions per language
    bookmark_instructions = {
        0: "iOS: Tap Share → Add to Home Screen\\nAndroid: Tap ⋮ → Add to Home screen\\nDesktop: Press Ctrl+D or Cmd+D",
        1: "iOS: לחץ שיתוף ← הוסף למסך הבית\\nAndroid: לחץ ⋮ ← הוסף למסך הבית\\nמחשב: לחץ Ctrl+D או Cmd+D",
        2: "iOS: Toca Compartir → Añadir a inicio\\nAndroid: Toca ⋮ → Añadir a inicio\\nPC: Ctrl+D o Cmd+D",
        3: "iOS: Appuyez Partager → Ajouter à l'écran\\nAndroid: Appuyez ⋮ → Ajouter à l'écran\\nPC: Ctrl+D ou Cmd+D",
        4: "iOS: Teilen → Zum Home-Bildschirm\\nAndroid: ⋮ → Zum Startbildschirm\\nPC: Strg+D oder Cmd+D",
        5: "iOS: 点击分享 → 添加到主屏幕\\nAndroid: 点击 ⋮ → 添加到主屏幕\\n电脑: Ctrl+D 或 Cmd+D",
    }
    bookmark_alert = bookmark_instructions.get(lang, bookmark_instructions[0])
    
    return f"""
    <!DOCTYPE html>
    <html lang="{lang_code}" {dir_attr}>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FitBeat - {user_name or user_id}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                background: #0a0a12;
                min-height: 100vh; 
                color: #e0e0e0; 
            }}
            
            /* 50/50 Two column layout */
            .page-container {{
                display: flex;
                flex-direction: {'row-reverse' if is_rtl_lang else 'row'};
                min-height: 100vh;
            }}
            
            /* Left side - Workout data (50%) */
            .data-section {{
                flex: 1;
                padding: 2rem;
                border-{'left' if is_rtl_lang else 'right'}: 1px solid #1a1a2a;
                overflow-y: auto;
            }}
            
            /* Right side - App info (50%) */
            .info-section {{
                flex: 1;
                padding: 2rem;
                background: linear-gradient(180deg, #0d0d18 0%, #0a0a12 100%);
                overflow-y: auto;
            }}
            
            /* Mobile: stack vertically */
            @media (max-width: 900px) {{
                .page-container {{
                    flex-direction: column;
                }}
                .data-section {{
                    border: none;
                    border-bottom: 1px solid #1a1a2a;
                }}
            }}
            
            /* Header */
            .section-header {{
                text-align: center;
                padding-bottom: 1.5rem;
                margin-bottom: 1.5rem;
                border-bottom: 1px solid #1a1a2a;
            }}
            .section-header h1 {{ color: #00d4ff; font-size: 1.8rem; }}
            .section-header .subtitle {{ color: #666; font-size: 0.9rem; margin-top: 0.5rem; }}
            .user-name {{ color: #888; font-size: 1rem; margin-top: 0.25rem; }}
            
            /* Summary card */
            .summary {{
                background: linear-gradient(145deg, #12121c 0%, #0d0d14 100%);
                border: 1px solid #1a1a2a;
                border-radius: 1rem;
                padding: 1.25rem;
                margin-bottom: 1.5rem;
            }}
            .summary-title {{ color: #555; font-size: 0.85rem; margin-bottom: 1rem; }}
            .summary-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 1rem;
                text-align: center;
            }}
            .summary-value {{ font-size: 2.2rem; font-weight: bold; color: #00d4ff; }}
            .summary-value.green {{ color: #22c55e; }}
            .summary-label {{ color: #555; font-size: 0.8rem; margin-top: 0.25rem; }}
            
            /* Folders */
            .folders {{
                background: linear-gradient(145deg, #12121c 0%, #0d0d14 100%);
                border: 1px solid #1a1a2a;
                border-radius: 1rem;
                padding: 1rem;
                margin-bottom: 1.5rem;
            }}
            .folders-title {{ color: #555; font-size: 0.85rem; margin-bottom: 1rem; }}
            
            .folder-row {{
                display: flex;
                align-items: center;
                padding: 0.875rem;
                background: rgba(0,0,0,0.3);
                border-radius: 0.75rem;
                margin-bottom: 0.5rem;
                text-decoration: none;
                color: white;
                transition: background 0.2s;
            }}
            .folder-row:hover {{ background: rgba(0,212,255,0.1); }}
            .folder-icon {{ font-size: 1.5rem; margin-{'left' if is_rtl_lang else 'right'}: 0.75rem; }}
            .folder-info {{ flex: 1; }}
            .folder-name {{ font-weight: bold; font-size: 1.1rem; }}
            .folder-meta {{ color: #555; font-size: 0.8rem; }}
            .folder-stats {{ color: #22c55e; font-weight: bold; margin-{'right' if is_rtl_lang else 'left'}: 0.75rem; }}
            .folder-arrow {{ color: #00d4ff; font-size: 1.2rem; }}
            
            .no-workouts {{ text-align: center; padding: 2rem 1rem; color: #555; }}
            .no-workouts-icon {{ font-size: 3rem; margin-bottom: 0.75rem; }}
            
            /* Buttons */
            .share-btn {{
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 0.5rem;
                background: linear-gradient(90deg, #25D366 0%, #128C7E 100%);
                color: white;
                padding: 0.875rem 1.5rem;
                border-radius: 2rem;
                font-weight: 600;
                text-decoration: none;
                margin-bottom: 0.75rem;
            }}
            
            .delete-btn {{
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 0.5rem;
                background: transparent;
                color: #ef4444;
                border: 1px solid #ef4444;
                padding: 0.6rem 1.25rem;
                border-radius: 2rem;
                font-size: 0.85rem;
                cursor: pointer;
            }}
            .delete-btn:hover {{ background: #ef4444; color: white; }}
            
            /* Info section styles */
            .info-header {{
                text-align: center;
                padding-bottom: 1.5rem;
                margin-bottom: 1.5rem;
                border-bottom: 1px solid #1a1a2a;
            }}
            .info-header .logo {{ font-size: 3.5rem; }}
            .info-header h2 {{ color: #00d4ff; font-size: 2rem; margin-top: 0.5rem; }}
            .info-header .tagline {{ color: #555; font-size: 0.9rem; margin-top: 0.25rem; }}
            
            .app-description {{
                background: linear-gradient(145deg, #12121c 0%, #0d0d14 100%);
                border: 1px solid #1a1a2a;
                border-radius: 1rem;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
            }}
            .app-description-text {{
                color: #aaa;
                font-size: 0.9rem;
                line-height: 1.7;
                white-space: pre-line;
            }}
            .app-description-text b {{
                color: #00d4ff;
                font-weight: 600;
            }}
            
            .info-buttons {{
                display: flex;
                flex-direction: column;
                gap: 0.75rem;
                margin-bottom: 1.5rem;
            }}
            
            .download-btn {{
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 0.5rem;
                background: linear-gradient(135deg, #00d4ff 0%, #0099bb 100%);
                color: #000;
                font-weight: 700;
                padding: 1rem 1.5rem;
                border-radius: 2rem;
                text-decoration: none;
                font-size: 1rem;
            }}
            
            .bookmark-btn {{
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 0.5rem;
                background: transparent;
                color: #00d4ff;
                border: 1px solid #00d4ff;
                padding: 0.875rem 1.25rem;
                border-radius: 2rem;
                font-size: 0.95rem;
                cursor: pointer;
            }}
            .bookmark-btn:hover {{ background: rgba(0,212,255,0.1); }}
            
            .footer {{
                text-align: center;
                padding-top: 1rem;
                color: #333;
                font-size: 0.75rem;
            }}
            .footer .user-id {{ color: #00d4ff; opacity: 0.5; font-family: monospace; margin-top: 0.25rem; }}
        </style>
    </head>
    <body>
        <div class="page-container">
            <!-- Data Section - Workout Stats -->
            <div class="data-section">
                <div class="section-header">
                    <h1>📊 {t('total_summary', lang)}</h1>
                    {'<p class="user-name">' + user_name + '</p>' if user_name else ''}
                </div>
                
                <div class="summary">
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
                    {years_html if years_html else f'<div class="no-workouts"><div class="no-workouts-icon">🏃‍♂️</div><p>{t("no_workouts", lang)}</p><p style="font-size:0.8rem;margin-top:0.5rem;">{t("finish_goal", lang)}</p></div>'}
                </div>
                
                <a href="https://wa.me/?text={share_text}" target="_blank" class="share-btn">📤 {t('share_whatsapp', lang)}</a>
                {f'<button onclick="deleteAll()" class="delete-btn">🗑️ {t("delete_all", lang)}</button>' if workouts else ''}
            </div>
            
            <!-- Info Section - App Description -->
            <div class="info-section">
                <div class="info-header">
                    <div class="logo">🏃‍♂️</div>
                    <h2>FitBeat</h2>
                    <p class="tagline">{t('about_app', lang)}</p>
                </div>
                
                <div class="app-description">
                    <div class="app-description-text">{app_desc}</div>
                </div>
                
                <div class="info-buttons">
                    <a href="https://apps.garmin.com/apps/c303ee47-1ecf-4487-91c9-3de4ca1a74d5" target="_blank" class="download-btn">⬇️ {t('download_app', lang)}</a>
                </div>
                
                <div class="footer">
                    <div>FitBeat © 2026</div>
                    <div class="user-id">{t('user_id', lang)}: {user_id}</div>
                </div>
            </div>
        </div>
        
        <script>
            async function deleteAll() {{
                if (confirm('{t("confirm_delete_all", lang)}')) {{
                    await fetch('/api/workout/user/{user_id}/all', {{ method: 'DELETE' }});
                    location.reload();
                }}
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
    
    base_url = os.environ.get('APP_URL', 'https://fitbeat.it.com')
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
    base_url = os.environ.get('APP_URL', 'https://fitbeat.it.com')
    
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

# Raw server.py download (no cache)
@api_router.get("/raw-server")
async def get_raw_server():
    from fastapi.responses import PlainTextResponse
    file_path = Path("/app/backend/server_final.py")
    if file_path.exists():
        content = file_path.read_text()
        return PlainTextResponse(content, headers={"Cache-Control": "no-store"})
    return PlainTextResponse("File not found", status_code=404)

@api_router.get("/servercode")
async def get_server_code():
    from fastapi.responses import PlainTextResponse
    file_path = Path("/app/backend/server_v469_final.py")
    if file_path.exists():
        content = file_path.read_text()
        return PlainTextResponse(content, headers={"Cache-Control": "no-store, max-age=0"})
    return PlainTextResponse("File not found", status_code=404)

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
