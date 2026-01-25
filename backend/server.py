טוב, אני אציג את הקובץ המלא. בגלל שהוא גדול, אציג אותו בחלקים שתוכל להעתיק אחד אחרי השני.

## 📄 חלק 1 מתוך 4:
Action: file_editor view /app/backend/server.py
Observation: /app/backend/server.py:
1|from fastapi import FastAPI, APIRouter
2|from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
3|from dotenv import load_dotenv
4|from starlette.middleware.cors import CORSMiddleware
5|from motor.motor_asyncio import AsyncIOMotorClient
6|import os
7|import logging
8|from pathlib import Path
9|from pydantic import BaseModel, Field, ConfigDict
10|from typing import List, Optional
11|import uuid
12|from datetime import datetime, timezone
13|import zipfile
14|import io
15|import tempfile
16|import shutil
17|import hashlib
18|import json
19|
20|ROOT_DIR = Path(__file__).parent
21|load_dotenv(ROOT_DIR / '.env')
22|
23|# ═══════════════════════════════════════════════════════════════
24|# TRANSLATIONS - 6 LANGUAGES (matching watch app)
25|# 0=English, 1=Hebrew, 2=Spanish, 3=French, 4=German, 5=Chinese
26|# ═══════════════════════════════════════════════════════════════
27|TRANSLATIONS = {
28|    "welcome_title": ["Welcome to FitBeat!", "ברוכים הבאים ל-FitBeat!", "¡Bienvenido a FitBeat!", "Bienvenue sur FitBeat!", "Willkommen bei FitBeat!", "欢迎使用FitBeat!"],
29|    "your_dashboard": ["This is your personal dashboard", "זהו הדשבורד האישי שלך", "Este es tu panel personal", "Voici votre tableau de bord", "Dies ist dein persönliches Dashboard", "这是您的个人仪表板"],
30|    "send_whatsapp": ["Send to myself via WhatsApp", "שלח לעצמי ב-WhatsApp", "Enviarme por WhatsApp", "M'envoyer via WhatsApp", "Per WhatsApp senden", "通过WhatsApp发送给自己"],
31|    "got_it": ["Got it, thanks!", "הבנתי, תודה!", "¡Entendido, gracias!", "Compris, merci!", "Verstanden, danke!", "明白了，谢谢！"],
32|    "total_summary": ["Total Summary", "סיכום כולל", "Resumen Total", "Résumé Total", "Gesamtübersicht", "总结"],
33|    "yearly_summary": ["Yearly Summary", "סיכום שנתי", "Resumen Anual", "Résumé Annuel", "Jahresübersicht", "年度总结"],
34|    "monthly_summary": ["Monthly Summary", "סיכום חודשי", "Resumen Mensual", "Résumé Mensuel", "Monatsübersicht", "月度总结"],
35|    "workouts": ["workouts", "אימונים", "entrenamientos", "entraînements", "Trainings", "训练"],
36|    "workout": ["Workout", "אימון", "Entrenamiento", "Entraînement", "Training", "训练"],
37|    "km": ["km", "ק\"מ", "km", "km", "km", "公里"],
38|    "km_total": ["km total", "ק\"מ סה\"כ", "km total", "km total", "km gesamt", "公里总计"],
39|    "hours": ["hours", "שעות", "horas", "heures", "Stunden", "小时"],
40|    "minutes": ["minutes", "דקות", "minutos", "minutes", "Minuten", "分钟"],
41|    "avg_hr": ["Avg HR", "דופק ממוצע", "FC Prom", "FC Moy", "Ø HF", "平均心率"],
42|    "max_hr": ["Max HR", "דופק מקסימלי", "FC Máx", "FC Max", "Max HF", "最大心率"],
43|    "elevation_gain": ["Elevation Gain", "עלייה", "Ascenso", "Dénivelé+", "Anstieg", "爬升"],
44|    "elevation_loss": ["Elevation Loss", "ירידה", "Descenso", "Dénivelé-", "Abstieg", "下降"],
45|    "cadence": ["Cadence", "קצב צעדים", "Cadencia", "Cadence", "Kadenz", "步频"],
46|    "steps": ["steps", "צעדים", "pasos", "pas", "Schritte", "步"],
47|    "pace": ["pace", "קצב", "ritmo", "allure", "Tempo", "配速"],
48|    "distance": ["Distance", "מרחק", "Distancia", "Distance", "Distanz", "距离"],
49|    "duration": ["Duration", "משך", "Duración", "Durée", "Dauer", "时长"],
50|    "share_whatsapp": ["Share on WhatsApp", "שתף ב-WhatsApp", "Compartir en WhatsApp", "Partager sur WhatsApp", "Auf WhatsApp teilen", "分享到WhatsApp"],
51|    "delete_workout": ["Delete workout", "מחק אימון", "Eliminar entrenamiento", "Supprimer l'entraînement", "Training löschen", "删除训练"],
52|    "delete_all": ["Delete all", "מחק הכל", "Eliminar todo", "Tout supprimer", "Alles löschen", "删除全部"],
53|    "confirm_delete": ["Delete this workout?", "למחוק את האימון הזה?", "¿Eliminar este entrenamiento?", "Supprimer cet entraînement?", "Dieses Training löschen?", "删除这个训练？"],
54|    "confirm_delete_all": ["Delete all workouts?", "למחוק את כל האימונים?", "¿Eliminar todos los entrenamientos?", "Supprimer tous les entraînements?", "Alle Trainings löschen?", "删除所有训练？"],
55|    "no_workouts": ["No workouts yet", "אין אימונים עדיין", "Sin entrenamientos aún", "Pas encore d'entraînements", "Noch keine Trainings", "还没有训练"],
56|    "finish_goal": ["Finish a goal on your watch and it will appear here!", "סיים יעד בשעון והאימון יופיע כאן!", "¡Completa una meta en tu reloj y aparecerá aquí!", "Terminez un objectif sur votre montre et il apparaîtra ici!", "Schließe ein Ziel auf deiner Uhr ab und es erscheint hier!", "在手表上完成目标，它将显示在这里！"],
57|    "by_years": ["By Years", "לפי שנים", "Por Años", "Par Années", "Nach Jahren", "按年份"],
58|    "all_workouts": ["All Workouts", "כל האימונים", "Todos los Entrenamientos", "Tous les Entraînements", "Alle Trainings", "所有训练"],
59|    "back": ["Back", "חזור", "Volver", "Retour", "Zurück", "返回"],
60|    "user_id": ["ID", "מזהה", "ID", "ID", "ID", "ID"],
61|    "powered_by": ["Powered by Garmin Fenix 8 Solar", "Powered by Garmin Fenix 8 Solar", "Powered by Garmin Fenix 8 Solar", "Powered by Garmin Fenix 8 Solar", "Powered by Garmin Fenix 8 Solar", "Powered by Garmin Fenix 8 Solar"],
62|    "and": ["and", "ו-", "y", "et", "und", "和"],
63|    "total_time": ["Total time", "זמן כולל", "Tiempo total", "Temps total", "Gesamtzeit", "总时间"],
64|    "per_workout": ["per workout", "לאימון", "por entrenamiento", "par entraînement", "pro Training", "每次训练"],
65|    "route": ["Route", "מסלול", "Ruta", "Parcours", "Strecke", "路线"],
66|    "no_route": ["No GPS data", "אין נתוני GPS", "Sin datos GPS", "Pas de données GPS", "Keine GPS-Daten", "无GPS数据"],
67|    "meters": ["m", "מ'", "m", "m", "m", "米"],
68|    "spm": ["spm", "צ'/דק'", "ppm", "ppm", "spm", "步/分"],
69|}
70|
71|# Month names in 6 languages
72|MONTH_NAMES = {
73|    0: ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
74|    1: ["", "ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני", "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"],
75|    2: ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"],
76|    3: ["", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"],
77|    4: ["", "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"],
78|    5: ["", "一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"],
79|}
80|
81|def t(key, lang=0):
82|    """Get translation for key in specified language"""
83|    if key in TRANSLATIONS:
84|        return TRANSLATIONS[key][lang] if lang < len(TRANSLATIONS[key]) else TRANSLATIONS[key][0]
85|    return key
86|
87|def get_month_name(month_num, lang=0):
88|    """Get month name in specified language"""
89|    if lang in MONTH_NAMES and month_num < len(MONTH_NAMES[lang]):
90|        return MONTH_NAMES[lang][month_num]
91|    return MONTH_NAMES[0][month_num]
92|
93|def is_rtl(lang):
94|    """Check if language is right-to-left"""
95|    return lang == 1  # Hebrew
96|
97|# MongoDB connection
98|mongo_url = os.environ['MONGO_URL']
99|client = AsyncIOMotorClient(mongo_url)
100|db = client[os.environ['DB_NAME']]
101|
102|# Create the main app without a prefix
103|app = FastAPI()
104|
105|# Create a router with the /api prefix
106|api_router = APIRouter(prefix="/api")
107|
108|# Configure logging
109|logging.basicConfig(
110|    level=logging.INFO,
111|    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
112|)
113|logger = logging.getLogger(__name__)
114|
115|# Define Models
116|class StatusCheck(BaseModel):
117|    model_config = ConfigDict(extra="ignore")
118|    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
119|    client_name: str
120|    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
121|
122|class StatusCheckCreate(BaseModel):
123|    client_name: str
124|
125|# FitBeat State Model
126|class FitBeatState(BaseModel):
127|    lang: int = 0
128|    color: int = 0
129|    userName: str = ""
130|    goalDist: int = 5
131|    goalTimeMin: int = 30
132|    hrMode: int = 0
133|    maxHr: int = 190
134|    distGoalActive: bool = False
135|    timeGoalActive: bool = False
136|    elapsedWalkSec: int = 0
137|    distanceCm: int = 0
138|    distHalfwayShown: bool = False
139|    distGoalShown: bool = False
140|    timeHalfwayShown: bool = False
141|    timeGoalShown: bool = False
142|
143|# Workout Summary Models
144|class WorkoutPoint(BaseModel):
145|    lat: float
146|    lon: float
147|    timestamp: int  # Unix timestamp in seconds
148|    hr: Optional[int] = None
149|    elevation: Optional[float] = None
150|
151|class WorkoutSubmit(BaseModel):
152|    user_id: str
153|    user_name: str = ""
154|    distance_cm: int
155|    duration_sec: int
156|    avg_hr: Optional[int] = None
157|    max_hr: Optional[int] = None
158|    elevation_gain: Optional[float] = None
159|    elevation_loss: Optional[float] = None
160|    steps: Optional[int] = None
161|    cadence: Optional[int] = None
162|    route: Optional[List[WorkoutPoint]] = None
163|    lang: Optional[int] = 0  # Language: 0=EN, 1=HE, 2=ES, 3=FR, 4=DE, 5=ZH
164|
165|class WorkoutSummary(BaseModel):
166|    model_config = ConfigDict(extra="ignore")
167|    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
168|    user_id: str
169|    user_name: str = ""
170|    distance_cm: int
171|    duration_sec: int
172|    avg_hr: Optional[int] = None
173|    max_hr: Optional[int] = None
174|    elevation_gain: Optional[float] = None
175|    elevation_loss: Optional[float] = None
176|    steps: Optional[int] = None
177|    cadence: Optional[int] = None
178|    route: Optional[List[dict]] = None
179|    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
180|    lang: int = 0  # Language preference
181|
182|def generate_user_id(device_id: str) -> str:
183|    """Generate a short unique user ID from device ID"""
184|    hash_obj = hashlib.sha256(device_id.encode())
185|    return hash_obj.hexdigest()[:8]
186|
187|@api_router.get("/")
188|async def root():
189|    return {"message": "FitBeat API v4.5.0"}
190|
191|@api_router.post("/status", response_model=StatusCheck)
192|async def create_status_check(input: StatusCheckCreate):
193|    status_dict = input.model_dump()
194|    status_obj = StatusCheck(**status_dict)
195|    doc = status_obj.model_dump()
196|    doc['timestamp'] = doc['timestamp'].isoformat()
197|    _ = await db.status_checks.insert_one(doc)
198|    return status_obj
199|
200|@api_router.get("/status", response_model=List[StatusCheck])
201|async def get_status_checks():
202|    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
203|    for check in status_checks:
204|        if isinstance(check['timestamp'], str):
205|            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
206|    return status_checks
207|
208|# FitBeat ZIP Download
209|@api_router.get("/download/fitbeat")
210|async def download_fitbeat():
211|    """Download FitBeat source code as ZIP"""
212|    fitbeat_dir = Path("/app/fitbeat")
213|    
214|    if not fitbeat_dir.exists():
215|        return JSONResponse(status_code=404, content={"error": "FitBeat directory not found"})
216|    
217|    # Create ZIP in memory
218|    zip_buffer = io.BytesIO()
219|    
220|    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
221|        for file_path in fitbeat_dir.rglob('*'):
222|            if file_path.is_file():
223|                # Skip unnecessary files
224|                if '__pycache__' in str(file_path) or '.pyc' in str(file_path):
225|                    continue
226|                arcname = f"fitbeat/{file_path.relative_to(fitbeat_dir)}"
227|                zip_file.write(file_path, arcname)
228|    
229|    zip_buffer.seek(0)
230|    
231|    # Save to temp file for FileResponse
232|    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
233|    temp_file.write(zip_buffer.getvalue())
234|    temp_file.close()
235|    
236|    return FileResponse(
237|        temp_file.name,
238|        media_type='application/zip',
239|        filename='fitbeat.zip',
240|        headers={"Content-Disposition": "attachment; filename=fitbeat.zip"}
241|    )
242|
243|# Store Assets Download
244|@api_router.get("/download/store-assets")
245|async def download_store_assets():
246|    """Download store assets (icons, descriptions) as ZIP"""
247|    store_assets_zip = Path("/app/store_assets.zip")
248|    
249|    if not store_assets_zip.exists():
250|        return JSONResponse(status_code=404, content={"error": "Store assets not found"})
251|    
252|    return FileResponse(
253|        str(store_assets_zip),
254|        media_type='application/zip',
255|        filename='FitBeat_Store_Assets.zip',
256|        headers={"Content-Disposition": "attachment; filename=FitBeat_Store_Assets.zip"}
257|    )
258|
259|# FitBeat State Management
260|@api_router.get("/fitbeat/state")
261|async def get_fitbeat_state():
262|    """Get current FitBeat simulator state from DB"""
263|    state = await db.fitbeat_state.find_one({"_id": "simulator"}, {"_id": 0})
264|    if state is None:
265|        return FitBeatState().model_dump()
266|    return state
267|
268|@api_router.post("/fitbeat/state")
269|async def save_fitbeat_state(state: FitBeatState):
270|    """Save FitBeat simulator state to DB"""
271|    await db.fitbeat_state.update_one(
272|        {"_id": "simulator"},
273|        {"$set": state.model_dump()},
274|        upsert=True
275|    )
276|    return {"status": "saved"}
277|
278|@api_router.post("/fitbeat/reset")
279|async def reset_fitbeat_state():
280|    """Reset FitBeat simulator state"""
281|    default_state = FitBeatState()
282|    await db.fitbeat_state.update_one(
283|        {"_id": "simulator"},
284|        {"$set": default_state.model_dump()},
285|        upsert=True
286|    )
287|    return {"status": "reset", "state": default_state.model_dump()}
288|
289|# ═══════════════════════════════════════════════════════════════
290|# Workout Summary API - For sharing workouts via WhatsApp
291|# ═══════════════════════════════════════════════════════════════
292|
293|@api_router.post("/workout")
294|async def submit_workout(workout: WorkoutSubmit):
295|    """Receive workout data from watch and save to DB"""
296|    workout_obj = WorkoutSummary(
297|        user_id=workout.user_id,
298|        user_name=workout.user_name,
299|        distance_cm=workout.distance_cm,
300|        duration_sec=workout.duration_sec,
301|        avg_hr=workout.avg_hr,
302|        max_hr=workout.max_hr,
303|        elevation_gain=workout.elevation_gain,
304|        elevation_loss=workout.elevation_loss,
305|        steps=workout.steps,
306|        cadence=workout.cadence,
307|        route=[p.model_dump() for p in workout.route] if workout.route else None
308|    )
309|    
310|    doc = workout_obj.model_dump()
311|    doc['timestamp'] = doc['timestamp'].isoformat()
312|    await db.workouts.insert_one(doc)
313|    
314|    logger.info(f"Workout saved for user {workout.user_id}: {workout.distance_cm}cm in {workout.duration_sec}s")
315|    
316|    return {
317|        "status": "saved",
318|        "workout_id": workout_obj.id,
319|        "user_id": workout.user_id
320|    }
321|
322|@api_router.get("/workout/all")
323|async def get_all_workouts(limit: int = 50):
324|    """Get all workouts (for debugging)"""
325|    workouts = await db.workouts.find(
326|        {},
327|        {"_id": 0}
328|    ).sort("timestamp", -1).to_list(limit)
329|    
330|    return {
331|        "workouts": workouts,
332|        "count": len(workouts)
333|    }
334|
335|@api_router.delete("/workout/user/{user_id}/all")
336|async def delete_all_user_workouts(user_id: str):
337|    """Delete all workouts for a user"""
338|    result = await db.workouts.delete_many({"user_id": user_id})
339|    return {
340|        "status": "deleted",
341|        "user_id": user_id,
342|        "deleted_count": result.deleted_count
343|    }
344|
345|@api_router.delete("/workout/{workout_id}")
346|async def delete_single_workout(workout_id: str):
347|    """Delete a single workout by ID"""
348|    result = await db.workouts.delete_one({"id": workout_id})
349|    if result.deleted_count == 0:
350|        return JSONResponse(status_code=404, content={"error": "Workout not found"})
351|    return {
352|        "status": "deleted",
353|        "workout_id": workout_id
354|    }
355|
356|@api_router.get("/workout/user/{user_id}")
357|async def get_user_workouts(user_id: str, limit: int = 10):
358|    """Get workouts for a specific user"""
359|    workouts = await db.workouts.find(
360|        {"user_id": user_id},
361|        {"_id": 0}
362|    ).sort("timestamp", -1).to_list(limit)
363|    
364|    return {
365|        "user_id": user_id,
366|        "workouts": workouts,
367|        "count": len(workouts)
368|    }
369|
370|@api_router.get("/workout/latest/{user_id}")
371|async def get_latest_workout(user_id: str):
372|    """Get the latest workout for a user"""
373|    workout = await db.workouts.find_one(
374|        {"user_id": user_id},
375|        {"_id": 0},
376|        sort=[("timestamp", -1)]
377|    )
378|    
379|    if not workout:
380|        return JSONResponse(status_code=404, content={"error": "No workouts found for this user"})
381|    
382|    return workout
383|
384|@api_router.get("/workout/id/{workout_id}")
385|async def get_workout_by_id(workout_id: str):
386|    """Get a specific workout by ID"""
387|    workout = await db.workouts.find_one(
388|        {"id": workout_id},
389|        {"_id": 0}
390|    )
391|    
392|    if not workout:
393|        return JSONResponse(status_code=404, content={"error": "Workout not found"})
394|    
395|    return workout
396|
397|@api_router.get("/user/{user_id}/stats")
398|async def get_user_stats(user_id: str):
399|    """Get aggregated stats for a user"""
400|    pipeline = [## 📄 חלק 2 מתוך 4:
Action: file_editor view /app/backend/server.py
Observation: /app/backend/server.py:
400|    pipeline = [
401|        {"$match": {"user_id": user_id}},
402|        {"$group": {
403|            "_id": "$user_id",
404|            "total_workouts": {"$sum": 1},
405|            "total_distance_cm": {"$sum": "$distance_cm"},
406|            "total_duration_sec": {"$sum": "$duration_sec"},
407|            "avg_hr": {"$avg": "$avg_hr"},
408|            "user_name": {"$last": "$user_name"}
409|        }}
410|    ]
411|    
412|    result = await db.workouts.aggregate(pipeline).to_list(1)
413|    
414|    if not result:
415|        return {
416|            "user_id": user_id,
417|            "total_workouts": 0,
418|            "total_distance_km": 0,
419|            "total_duration_min": 0
420|        }
421|    
422|    stats = result[0]
423|    return {
424|        "user_id": user_id,
425|        "user_name": stats.get("user_name", ""),
426|        "total_workouts": stats["total_workouts"],
427|        "total_distance_km": round(stats["total_distance_cm"] / 100000, 2),
428|        "total_duration_min": round(stats["total_duration_sec"] / 60, 1),
429|        "avg_hr": round(stats["avg_hr"]) if stats.get("avg_hr") else None
430|    }
431|
432|@api_router.get("/user/{user_id}/monthly")
433|async def get_monthly_stats(user_id: str, year: int = None, month: int = None):
434|    """Get monthly stats for a user"""
435|    from datetime import datetime
436|    
437|    # Default to current month
438|    now = datetime.now(timezone.utc)
439|    if year is None:
440|        year = now.year
441|    if month is None:
442|        month = now.month
443|    
444|    # Calculate date range for the month
445|    start_date = datetime(year, month, 1, tzinfo=timezone.utc)
446|    if month == 12:
447|        end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
448|    else:
449|        end_date = datetime(year, month + 1, 1, tzinfo=timezone.utc)
450|    
451|    # Get previous month for comparison
452|    if month == 1:
453|        prev_year, prev_month = year - 1, 12
454|    else:
455|        prev_year, prev_month = year, month - 1
456|    
457|    prev_start = datetime(prev_year, prev_month, 1, tzinfo=timezone.utc)
458|    prev_end = start_date
459|    
460|    # Aggregate current month
461|    pipeline = [
462|        {"$match": {
463|            "user_id": user_id,
464|            "timestamp": {
465|                "$gte": start_date.isoformat(),
466|                "$lt": end_date.isoformat()
467|            }
468|        }},
469|        {"$group": {
470|            "_id": "$user_id",
471|            "total_workouts": {"$sum": 1},
472|            "total_distance_cm": {"$sum": "$distance_cm"},
473|            "total_duration_sec": {"$sum": "$duration_sec"},
474|            "avg_hr": {"$avg": "$avg_hr"},
475|            "max_hr": {"$max": "$max_hr"},
476|            "total_elevation_gain": {"$sum": "$elevation_gain"},
477|            "total_elevation_loss": {"$sum": "$elevation_loss"},
478|            "total_steps": {"$sum": "$steps"},
479|            "user_name": {"$last": "$user_name"}
480|        }}
481|    ]
482|    
483|    # Aggregate previous month for comparison
484|    prev_pipeline = [
485|        {"$match": {
486|            "user_id": user_id,
487|            "timestamp": {
488|                "$gte": prev_start.isoformat(),
489|                "$lt": prev_end.isoformat()
490|            }
491|        }},
492|        {"$group": {
493|            "_id": "$user_id",
494|            "total_workouts": {"$sum": 1},
495|            "total_distance_cm": {"$sum": "$distance_cm"},
496|            "total_duration_sec": {"$sum": "$duration_sec"}
497|        }}
498|    ]
499|    
500|    result = await db.workouts.aggregate(pipeline).to_list(1)
501|    prev_result = await db.workouts.aggregate(prev_pipeline).to_list(1)
502|    
503|    # Get list of workouts for this month
504|    workouts = await db.workouts.find(
505|        {
506|            "user_id": user_id,
507|            "timestamp": {
508|                "$gte": start_date.isoformat(),
509|                "$lt": end_date.isoformat()
510|            }
511|        },
512|        {"_id": 0}
513|    ).sort("timestamp", -1).to_list(100)
514|    
515|    month_names_he = ["", "ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני", 
516|                      "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"]
517|    
518|    if not result:
519|        return {
520|            "user_id": user_id,
521|            "year": year,
522|            "month": month,
523|            "month_name": month_names_he[month],
524|            "total_workouts": 0,
525|            "total_distance_km": 0,
526|            "total_duration_min": 0,
527|            "avg_hr": None,
528|            "max_hr": None,
529|            "total_elevation_gain": 0,
530|            "total_elevation_loss": 0,
531|            "total_steps": 0,
532|            "workouts": [],
533|            "comparison": None
534|        }
535|    
536|    stats = result[0]
537|    
538|    # Calculate comparison with previous month
539|    comparison = None
540|    if prev_result:
541|        prev_stats = prev_result[0]
542|        prev_dist = prev_stats["total_distance_cm"] / 100000
543|        curr_dist = stats["total_distance_cm"] / 100000
544|        if prev_dist > 0:
545|            dist_change = round(((curr_dist - prev_dist) / prev_dist) * 100, 1)
546|            comparison = {
547|                "distance_change_percent": dist_change,
548|                "workouts_change": stats["total_workouts"] - prev_stats["total_workouts"]
549|            }
550|    
551|    return {
552|        "user_id": user_id,
553|        "user_name": stats.get("user_name", ""),
554|        "year": year,
555|        "month": month,
556|        "month_name": month_names_he[month],
557|        "total_workouts": stats["total_workouts"],
558|        "total_distance_km": round(stats["total_distance_cm"] / 100000, 2),
559|        "total_duration_min": round(stats["total_duration_sec"] / 60, 1),
560|        "avg_hr": round(stats["avg_hr"]) if stats.get("avg_hr") else None,
561|        "max_hr": stats.get("max_hr"),
562|        "total_elevation_gain": round(stats.get("total_elevation_gain") or 0, 1),
563|        "total_elevation_loss": round(stats.get("total_elevation_loss") or 0, 1),
564|        "total_steps": stats.get("total_steps") or 0,
565|        "workouts": workouts,
566|        "comparison": comparison
567|    }
568|
569|class UserRegister(BaseModel):
570|    device_id: str
571|    user_name: str = ""
572|
573|@api_router.post("/user/register")
574|async def register_user(data: UserRegister):
575|    """Register a new user and get their unique ID"""
576|    user_id = generate_user_id(data.device_id)
577|    
578|    # Check if user exists
579|    existing = await db.users.find_one({"user_id": user_id})
580|    
581|    if not existing:
582|        await db.users.insert_one({
583|            "user_id": user_id,
584|            "device_id": data.device_id,
585|            "user_name": data.user_name,
586|            "created_at": datetime.now(timezone.utc).isoformat()
587|        })
588|        logger.info(f"New user registered: {user_id}")
589|    elif data.user_name and data.user_name != existing.get("user_name"):
590|        # Update user name if changed
591|        await db.users.update_one(
592|            {"user_id": user_id},
593|            {"$set": {"user_name": data.user_name}}
594|        )
595|    
596|    return {"user_id": user_id}
597|
598|# ═══════════════════════════════════════════════════════════════
599|# HTML PAGES - Workout Summary Pages
600|# ═══════════════════════════════════════════════════════════════
601|
602|def generate_workout_html(workout, user_id, lang=0):
603|    """Generate HTML page for workout summary with Leaflet map"""
604|    # RTL support
605|    dir_attr = 'dir="rtl"' if is_rtl(lang) else 'dir="ltr"'
606|    lang_code = ["en", "he", "es", "fr", "de", "zh"][lang] if lang < 6 else "en"
607|    
608|    if not workout:
609|        return f"""
610|        <!DOCTYPE html>
611|        <html lang="{lang_code}" {dir_attr}>
612|        <head>
613|            <meta charset="UTF-8">
614|            <meta name="viewport" content="width=device-width, initial-scale=1.0">
615|            <title>FitBeat - {t('no_workouts', lang)}</title>
616|            <style>
617|                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
618|                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; color: white; display: flex; align-items: center; justify-content: center; }}
619|                .container {{ text-align: center; padding: 2rem; }}
620|                .icon {{ font-size: 4rem; margin-bottom: 1rem; }}
621|                h1 {{ color: #00d4ff; margin-bottom: 0.5rem; }}
622|                p {{ color: #888; }}
623|                .user-id {{ font-family: monospace; color: #00d4ff; opacity: 0.6; margin-top: 1rem; font-size: 0.8rem; }}
624|            </style>
625|        </head>
626|        <body>
627|            <div class="container">
628|                <div class="icon">🏃‍♂️</div>
629|                <h1>FitBeat</h1>
630|                <p>{t('no_workouts', lang)}</p>
631|                <p class="user-id">{t('user_id', lang)}: {user_id}</p>
632|            </div>
633|        </body>
634|        </html>
635|        """
636|    
637|    dist_km = workout['distance_cm'] / 100000
638|    duration_sec = workout['duration_sec']
639|    hrs = duration_sec // 3600
640|    mins = (duration_sec % 3600) // 60
641|    secs = duration_sec % 60
642|    duration_str = f"{hrs}:{mins:02d}:{secs:02d}" if hrs > 0 else f"{mins}:{secs:02d}"
643|    
644|    # Calculate pace
645|    if dist_km > 0:
646|        pace_sec = duration_sec / dist_km
647|        pace_min = int(pace_sec // 60)
648|        pace_s = int(pace_sec % 60)
649|        pace_str = f"{pace_min}:{pace_s:02d}"
650|    else:
651|        pace_str = "--:--"
652|    
653|    user_name = workout.get('user_name', '')
654|    avg_hr = workout.get('avg_hr', '')
655|    max_hr = workout.get('max_hr', '')
656|    elevation_gain = workout.get('elevation_gain', 0) or 0
657|    elevation_loss = workout.get('elevation_loss', 0) or 0
658|    steps = workout.get('steps', 0) or 0
659|    cadence = workout.get('cadence', 0) or 0
660|    workout_id = workout.get('id', '')
661|    route = workout.get('route', []) or []
662|    
663|    # Format date
664|    timestamp = workout.get('timestamp', '')
665|    
666|    # Get base URL
667|    base_url = os.environ.get('APP_URL', 'https://exercise-journal-9.preview.emergentagent.com')
668|    
669|    # WhatsApp share text (translated)
670|    share_texts = {
671|        0: f"🏃‍♂️ {user_name} finished a workout!%0A%0A📍 Distance: {dist_km:.2f} km%0A⏱️ Time: {duration_str}%0A⚡ Pace: {pace_str}/km",
672|        1: f"🏃‍♂️ {user_name} סיים אימון!%0A%0A📍 מרחק: {dist_km:.2f} ק״מ%0A⏱️ זמן: {duration_str}%0A⚡ קצב: {pace_str}/ק״מ",
673|        2: f"🏃‍♂️ ¡{user_name} terminó un entrenamiento!%0A%0A📍 Distancia: {dist_km:.2f} km%0A⏱️ Tiempo: {duration_str}%0A⚡ Ritmo: {pace_str}/km",
674|        3: f"🏃‍♂️ {user_name} a terminé un entraînement!%0A%0A📍 Distance: {dist_km:.2f} km%0A⏱️ Temps: {duration_str}%0A⚡ Allure: {pace_str}/km",
675|        4: f"🏃‍♂️ {user_name} hat ein Training beendet!%0A%0A📍 Distanz: {dist_km:.2f} km%0A⏱️ Zeit: {duration_str}%0A⚡ Tempo: {pace_str}/km",
676|        5: f"🏃‍♂️ {user_name}完成了训练!%0A%0A📍 距离: {dist_km:.2f} km%0A⏱️ 时间: {duration_str}%0A⚡ 配速: {pace_str}/km",
677|    }
678|    share_text = share_texts.get(lang, share_texts[0])
679|    if avg_hr:
680|        hr_texts = {0: f"%0A❤️ HR: {avg_hr} BPM", 1: f"%0A❤️ דופק: {avg_hr} BPM", 2: f"%0A❤️ FC: {avg_hr} LPM", 3: f"%0A❤️ FC: {avg_hr} BPM", 4: f"%0A❤️ HF: {avg_hr} SPM", 5: f"%0A❤️ 心率: {avg_hr} BPM"}
681|        share_text += hr_texts.get(lang, hr_texts[0])
682|    share_text += f"%0A%0A🔗 {base_url}/api/u/{user_id}?lang={lang}"
683|    
684|    # Convert route to JSON for JavaScript
685|    route_json = json.dumps([[p['lat'], p['lon']] for p in route]) if route else "[]"
686|    has_route = len(route) > 0
687|    
688|    # Generate map section - Leaflet if route exists, SVG fallback otherwise
689|    if has_route:
690|        map_section = f'''
691|            <div class="map-container">
692|                <div id="map"></div>
693|                <div class="map-badge">
694|                    <span class="value">{dist_km:.2f}</span>
695|                    <span class="unit">{t('km', lang)}</span>
696|                </div>
697|            </div>
698|        '''
699|    else:
700|        map_section = f'''
701|            <div class="map">
702|                <svg viewBox="0 0 400 200">
703|                    <path d="M 40,160 Q 80,140 120,120 T 200,100 T 280,80 T 360,60" fill="none" stroke="#ff6666" stroke-width="6" stroke-linecap="round" opacity="0.3" style="filter: blur(3px);"/>
704|                    <path d="M 40,160 Q 80,140 120,120 T 200,100 T 280,80 T 360,60" fill="none" stroke="#ff3333" stroke-width="3" stroke-linecap="round" style="filter: drop-shadow(0 0 4px rgba(255,50,50,0.8));"/>
705|                    <circle cx="40" cy="160" r="6" fill="#22c55e"/>
706|                    <circle cx="40" cy="160" r="3" fill="white"/>
707|                    <circle cx="360" cy="60" r="6" fill="#ef4444" style="filter: drop-shadow(0 0 4px rgba(239,68,68,0.8));"/>
708|                    <circle cx="360" cy="60" r="3" fill="white"/>
709|                </svg>
710|                <div class="map-badge">
711|                    <span class="value">{dist_km:.2f}</span>
712|                    <span class="unit">{t('km', lang)}</span>
713|                </div>
714|                <div class="no-gps">{t('no_route', lang)}</div>
715|            </div>
716|        '''
717|    
718|    # Build extra stats section with all parameters
719|    extra_stats_html = ""
720|    
721|    # Max HR
722|    if max_hr:
723|        extra_stats_html += f'''
724|            <div class="extra-stat">
725|                <span class="label">💓 {t('max_hr', lang)}</span>
726|                <span class="value" style="color:#ef4444;">{max_hr} BPM</span>
727|            </div>
728|        '''
729|    
730|    # Elevation Gain
731|    if elevation_gain > 0:
732|        extra_stats_html += f'''
733|            <div class="extra-stat">
734|                <span class="label">📈 {t('elevation_gain', lang)}</span>
735|                <span class="value" style="color:#22c55e;">+{elevation_gain:.0f} {t('meters', lang)}</span>
736|            </div>
737|        '''
738|    
739|    # Elevation Loss
740|    if elevation_loss > 0:
741|        extra_stats_html += f'''
742|            <div class="extra-stat">
743|                <span class="label">📉 {t('elevation_loss', lang)}</span>
744|                <span class="value" style="color:#f97316;">-{elevation_loss:.0f} {t('meters', lang)}</span>
745|            </div>
746|        '''
747|    
748|    # Cadence
749|    if cadence > 0:
750|        extra_stats_html += f'''
751|            <div class="extra-stat">
752|                <span class="label">🦶 {t('cadence', lang)}</span>
753|                <span class="value">{cadence} {t('spm', lang)}</span>
754|            </div>
755|        '''
756|    
757|    # Steps
758|    if steps > 0:
759|        extra_stats_html += f'''
760|            <div class="extra-stat">
761|                <span class="label">👟 {t('steps', lang)}</span>
762|                <span class="value">{steps:,}</span>
763|            </div>
764|        '''
765|    
766|    return f"""
767|    <!DOCTYPE html>
768|    <html lang="{lang_code}" {dir_attr}>
769|    <head>
770|        <meta charset="UTF-8">
771|        <meta name="viewport" content="width=device-width, initial-scale=1.0">
772|        <title>FitBeat - {t('workout', lang)}</title>
773|        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
774|        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
775|        <style>
776|            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
777|            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; color: white; padding: 1rem; }}
778|            .container {{ max-width: 480px; margin: 0 auto; }}
779|            header {{ text-align: center; padding: 1.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 1.5rem; }}
780|            h1 {{ color: #00d4ff; font-size: 1.5rem; margin-bottom: 0.25rem; }}
781|            .subtitle {{ color: #888; font-size: 0.9rem; }}
782|            .user-name {{ font-size: 1.1rem; margin-top: 0.5rem; }}
783|            
784|            /* Leaflet Map Container */
785|            .map-container {{ position: relative; border-radius: 1rem; height: 220px; margin-bottom: 1.5rem; overflow: hidden; }}
786|            #map {{ width: 100%; height: 100%; border-radius: 1rem; z-index: 1; }}
787|            .map-container .map-badge {{ position: absolute; top: 0.75rem; {"left" if is_rtl(lang) else "right"}: 0.75rem; background: rgba(0,0,0,0.85); padding: 0.5rem 1rem; border-radius: 0.75rem; border: 1px solid rgba(255,255,255,0.2); z-index: 1000; }}
788|            .map-badge .value {{ font-size: 1.5rem; font-weight: bold; color: #00d4ff; }}
789|            .map-badge .unit {{ font-size: 0.8rem; color: #888; }}
790|            
791|            /* SVG Fallback Map */
792|            .map {{ background: linear-gradient(135deg, #2d4a2d 0%, #1a2f1a 100%); border-radius: 1rem; height: 200px; margin-bottom: 1.5rem; position: relative; overflow: hidden; }}
793|            .map svg {{ position: absolute; inset: 0; width: 100%; height: 100%; }}
794|            .map .map-badge {{ position: absolute; top: 0.75rem; {"left" if is_rtl(lang) else "right"}: 0.75rem; background: rgba(0,0,0,0.8); padding: 0.5rem 1rem; border-radius: 0.75rem; border: 1px solid rgba(255,255,255,0.1); }}
795|            .no-gps {{ position: absolute; bottom: 0.75rem; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,0.7); padding: 0.25rem 0.75rem; border-radius: 0.5rem; font-size: 0.75rem; color: #888; }}
796|            
797|            .stats {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 1.5rem; }}
798|            .stat {{ background: linear-gradient(135deg, #1e1e3f 0%, #151530 100%); border-radius: 0.75rem; padding: 1rem; border: 1px solid rgba(255,255,255,0.05); }}
799|            .stat .icon {{ font-size: 1.25rem; margin-bottom: 0.5rem; }}
800|            .stat .label {{ color: #888; font-size: 0.75rem; margin-bottom: 0.25rem; }}## 📄 חלק 3 מתוך 4:
Action: file_editor view /app/backend/server.py
Observation: /app/backend/server.py:
800|            .stat .label {{ color: #888; font-size: 0.75rem; margin-bottom: 0.25rem; }}
801|            .stat .value {{ font-size: 1.5rem; font-weight: bold; }}
802|            .stat .value.highlight {{ color: #00d4ff; }}
803|            .stat .unit {{ font-size: 0.8rem; color: #888; margin-right: 0.25rem; }}
804|            
805|            .section {{ background: linear-gradient(135deg, #1e1e3f 0%, #151530 100%); border-radius: 0.75rem; padding: 1rem; margin-bottom: 1rem; border: 1px solid rgba(255,255,255,0.05); }}
806|            .section-title {{ color: #888; font-size: 0.8rem; margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem; }}
807|            .hr-stats {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }}
808|            .hr-stat {{ background: rgba(0,0,0,0.2); border-radius: 0.5rem; padding: 0.75rem; text-align: center; }}
809|            .hr-stat .label {{ color: #888; font-size: 0.7rem; }}
810|            .hr-stat .value {{ color: #ef4444; font-size: 1.25rem; font-weight: bold; }}
811|            .hr-stat .value span {{ font-size: 0.7rem; color: #888; }}
812|            
813|            .extra-stats {{ display: flex; flex-direction: column; }}
814|            .extra-stat {{ display: flex; justify-content: space-between; padding: 0.75rem 0; border-bottom: 1px solid rgba(255,255,255,0.05); }}
815|            .extra-stat:last-child {{ border-bottom: none; }}
816|            .extra-stat .label {{ color: #888; display: flex; align-items: center; gap: 0.5rem; }}
817|            .extra-stat .value {{ font-weight: bold; }}
818|            
819|            .share-btn {{ display: flex; align-items: center; justify-content: center; gap: 0.75rem; background: linear-gradient(90deg, #25D366 0%, #128C7E 100%); color: white; border: none; padding: 1rem 2rem; border-radius: 9999px; font-size: 1.1rem; font-weight: bold; cursor: pointer; margin: 2rem auto; box-shadow: 0 4px 15px rgba(37, 211, 102, 0.3); text-decoration: none; }}
820|            .share-btn:hover {{ transform: translateY(-2px); box-shadow: 0 6px 20px rgba(37, 211, 102, 0.4); }}
821|            .share-btn svg {{ width: 1.5rem; height: 1.5rem; }}
822|            .share-hint {{ text-align: center; color: #888; font-size: 0.8rem; margin-bottom: 1rem; }}
823|            .delete-btn {{ display: flex; align-items: center; justify-content: center; gap: 0.5rem; background: transparent; color: #ef4444; border: 1px solid #ef4444; padding: 0.75rem 1.5rem; border-radius: 9999px; font-size: 0.85rem; cursor: pointer; margin: 1rem auto; }}
824|            .delete-btn:hover {{ background: #ef4444; color: white; }}
825|            footer {{ text-align: center; padding: 1.5rem 0; color: #888; font-size: 0.8rem; }}
826|            footer .brand {{ color: #00d4ff; font-weight: bold; font-size: 1rem; }}
827|            footer .user-id {{ font-family: monospace; color: #00d4ff; opacity: 0.6; margin-top: 0.5rem; font-size: 0.7rem; }}
828|        </style>
829|    </head>
830|    <body>
831|        <div class="container">
832|            <header>
833|                <h1>🏃‍♂️ {t('workout', lang)}</h1>
834|                <p class="subtitle">{timestamp[:10] if timestamp else ''}</p>
835|                {'<p class="user-name">' + user_name + '</p>' if user_name else ''}
836|            </header>
837|            
838|            {map_section}
839|            
840|            <div class="stats">
841|                <div class="stat">
842|                    <div class="icon">📍</div>
843|                    <div class="label">{t('distance', lang)}</div>
844|                    <div class="value highlight">{dist_km:.2f}<span class="unit">{t('km', lang)}</span></div>
845|                </div>
846|                <div class="stat">
847|                    <div class="icon">⏱️</div>
848|                    <div class="label">{t('duration', lang)}</div>
849|                    <div class="value">{duration_str}</div>
850|                </div>
851|                <div class="stat">
852|                    <div class="icon">⚡</div>
853|                    <div class="label">{t('pace', lang)}</div>
854|                    <div class="value">{pace_str}<span class="unit">/{t('km', lang)}</span></div>
855|                </div>
856|                {'<div class="stat"><div class="icon">❤️</div><div class="label">' + t("avg_hr", lang) + '</div><div class="value" style="color:#ef4444;">' + str(avg_hr) + '<span class="unit">BPM</span></div></div>' if avg_hr else ''}
857|            </div>
858|            
859|            {f'<div class="section"><div class="section-title">📊 {t("workout", lang)}</div><div class="extra-stats">{extra_stats_html}</div></div>' if extra_stats_html else ''}
860|            
861|            <a href="https://wa.me/?text={share_text}" target="_blank" class="share-btn">
862|                <svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
863|                {t('share_whatsapp', lang)}
864|            </a>
865|            
866|            <button onclick="deleteWorkout()" class="delete-btn">🗑️ {t('delete_workout', lang)}</button>
867|            
868|            <footer>
869|                <div class="brand">FitBeat</div>
870|                <div>{t('powered_by', lang)}</div>
871|                <div class="user-id">{t('user_id', lang)}: {user_id}</div>
872|            </footer>
873|        </div>
874|        
875|        <script>
876|            // Initialize Leaflet map if route data exists
877|            const routeData = {route_json};
878|            if (routeData.length > 0) {{
879|                const map = L.map('map', {{
880|                    zoomControl: true,
881|                    attributionControl: false
882|                }});
883|                
884|                // Add OpenStreetMap tiles
885|                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
886|                    maxZoom: 19
887|                }}).addTo(map);
888|                
889|                // Create polyline from route
890|                const polyline = L.polyline(routeData, {{
891|                    color: '#ff3333',
892|                    weight: 4,
893|                    opacity: 0.9,
894|                    lineCap: 'round',
895|                    lineJoin: 'round'
896|                }}).addTo(map);
897|                
898|                // Add start marker (green)
899|                const startIcon = L.divIcon({{
900|                    html: '<div style="background:#22c55e;width:16px;height:16px;border-radius:50%;border:3px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.4);"></div>',
901|                    className: '',
902|                    iconSize: [16, 16],
903|                    iconAnchor: [8, 8]
904|                }});
905|                L.marker(routeData[0], {{icon: startIcon}}).addTo(map);
906|                
907|                // Add end marker (red)
908|                const endIcon = L.divIcon({{
909|                    html: '<div style="background:#ef4444;width:16px;height:16px;border-radius:50%;border:3px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.4);"></div>',
910|                    className: '',
911|                    iconSize: [16, 16],
912|                    iconAnchor: [8, 8]
913|                }});
914|                L.marker(routeData[routeData.length - 1], {{icon: endIcon}}).addTo(map);
915|                
916|                // Fit map to route bounds with padding
917|                map.fitBounds(polyline.getBounds(), {{
918|                    padding: [30, 30]
919|                }});
920|            }}
921|            
922|            async function deleteWorkout() {{
923|                if (confirm('{t("confirm_delete", lang)}')) {{
924|                    try {{
925|                        const response = await fetch('/api/workout/{workout_id}', {{ method: 'DELETE' }});
926|                        if (response.ok) {{
927|                            window.location.href = '/api/u/{user_id}?lang={lang}';
928|                        }}
929|                    }} catch (e) {{
930|                        console.error(e);
931|                    }}
932|                }}
933|            }}
934|        </script>
935|    </body>
936|    </html>
937|    """
938|
939|@api_router.get("/u/{user_id}", response_class=HTMLResponse)
940|async def dashboard_page(user_id: str, welcome: str = None, lang: int = None):
941|    """Main page - shows years as folders"""
942|    workouts = await db.workouts.find(
943|        {"user_id": user_id},
944|        {"_id": 0}
945|    ).sort("timestamp", -1).to_list(500)
946|    
947|    # Get language from parameter, or from user's latest workout, or default to English
948|    if lang is None:
949|        lang = workouts[0].get('lang', 0) if workouts else 0
950|    
951|    # Check if this is first visit (show welcome banner)
952|    is_first_visit = welcome == "1" or (len(workouts) == 1)
953|    
954|    # RTL support for Hebrew
955|    dir_attr = 'dir="rtl"' if is_rtl(lang) else 'dir="ltr"'
956|    lang_code = ["en", "he", "es", "fr", "de", "zh"][lang] if lang < 6 else "en"
957|    
958|    # Group workouts by year
959|    from collections import defaultdict
960|    years_data = defaultdict(list)
961|    for w in workouts:
962|        year = w.get('timestamp', '')[:4]  # "2026"
963|        if year:
964|            years_data[year].append(w)
965|    
966|    # Calculate total summary
967|    total_dist = sum(w.get('distance_cm', 0) for w in workouts) if workouts else 0
968|    total_time = sum(w.get('duration_sec', 0) for w in workouts) if workouts else 0
969|    total_km = total_dist / 100000
970|    total_hrs = total_time // 3600
971|    total_mins = (total_time % 3600) // 60
972|    time_str = f"{total_hrs} {t('hours', lang)} {t('and', lang)} {total_mins} {t('minutes', lang)}" if total_hrs > 0 else f"{total_mins} {t('minutes', lang)}"
973|    
974|    user_name = workouts[0].get('user_name', '') if workouts else ''
975|    
976|    # Build year folders
977|    years_html = ""
978|    for year in sorted(years_data.keys(), reverse=True):
979|        year_workouts = years_data[year]
980|        y_dist = sum(w.get('distance_cm', 0) for w in year_workouts) / 100000
981|        y_count = len(year_workouts)
982|        
983|        years_html += f"""
984|        <a href="/api/u/{user_id}/year/{year}?lang={lang}" class="folder-row">
985|            <div class="folder-icon">📁</div>
986|            <div class="folder-info">
987|                <div class="folder-name">{year}</div>
988|                <div class="folder-meta">{y_count} {t('workouts', lang)}</div>
989|            </div>
990|            <div class="folder-stats">{y_dist:.1f} {t('km', lang)}</div>
991|            <div class="folder-arrow">{'←' if is_rtl(lang) else '→'}</div>
992|        </a>
993|        """
994|    
995|    # Get base URL from environment or use default
996|    base_url = os.environ.get('APP_URL', 'https://exercise-journal-9.preview.emergentagent.com')
997|    dashboard_url = f"{base_url}/api/u/{user_id}"
998|    
999|    # Welcome message for WhatsApp (translated)
1000|    welcome_wa_text = {
1001|        0: f"🎉 Welcome! My FitBeat dashboard:%0A%0A🔗 {dashboard_url}%0A%0A💾 Save this link!",
1002|        1: f"🎉 שלום! הדשבורד האישי שלי ב-FitBeat:%0A%0A🔗 {dashboard_url}%0A%0A💾 שמור את הלינק הזה!",
1003|        2: f"🎉 ¡Hola! Mi panel FitBeat:%0A%0A🔗 {dashboard_url}%0A%0A💾 ¡Guarda este enlace!",
1004|        3: f"🎉 Bonjour! Mon tableau FitBeat:%0A%0A🔗 {dashboard_url}%0A%0A💾 Sauvegardez ce lien!",
1005|        4: f"🎉 Hallo! Mein FitBeat Dashboard:%0A%0A🔗 {dashboard_url}%0A%0A💾 Speichere diesen Link!",
1006|        5: f"🎉 你好！我的FitBeat仪表板:%0A%0A🔗 {dashboard_url}%0A%0A💾 保存此链接!",
1007|    }
1008|    welcome_text = welcome_wa_text.get(lang, welcome_wa_text[0])
1009|    
1010|    # Welcome banner HTML (shown on first visit)
1011|    welcome_banner = ""
1012|    if is_first_visit and workouts:
1013|        welcome_banner = f"""
1014|        <div class="welcome-banner" id="welcomeBanner">
1015|            <div class="welcome-icon">🎉</div>
1016|            <h2>{t('welcome_title', lang)}</h2>
1017|            <p>{t('your_dashboard', lang)}</p>
1018|            <p class="welcome-link">{dashboard_url}</p>
1019|            <a href="https://wa.me/?text={welcome_text}" target="_blank" class="welcome-btn">
1020|                📲 {t('send_whatsapp', lang)}
1021|            </a>
1022|            <button onclick="closeWelcome()" class="welcome-close">{t('got_it', lang)}</button>
1023|        </div>
1024|        """
1025|    
1026|    # Share text for the main share button
1027|    share_text = f"📊 FitBeat%0A🏃 {len(workouts)} {t('workouts', lang)}%0A📍 {total_km:.1f} {t('km', lang)}%0A%0A🔗 {dashboard_url}"
1028|    
1029|    return f"""
1030|    <!DOCTYPE html>
1031|    <html lang="{lang_code}" {dir_attr}>
1032|    <head>
1033|        <meta charset="UTF-8">
1034|        <meta name="viewport" content="width=device-width, initial-scale=1.0">
1035|        <title>FitBeat - {user_name or user_id}</title>
1036|        <style>
1037|            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
1038|            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; color: white; padding: 1rem; }}
1039|            .container {{ max-width: 480px; margin: 0 auto; }}
1040|            header {{ text-align: center; padding: 1.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 1.5rem; }}
1041|            h1 {{ color: #00d4ff; font-size: 1.8rem; }}
1042|            .user-name {{ font-size: 1.2rem; margin-top: 0.5rem; }}
1043|            
1044|            .summary {{ background: linear-gradient(135deg, #1e1e3f 0%, #151530 100%); border-radius: 1rem; padding: 1.5rem; margin-bottom: 1.5rem; border: 1px solid rgba(0,212,255,0.2); }}
1045|            .summary-title {{ color: #888; font-size: 0.9rem; margin-bottom: 1rem; }}
1046|            .summary-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; text-align: center; }}
1047|            .summary-value {{ font-size: 2.5rem; font-weight: bold; color: #00d4ff; }}
1048|            .summary-value.green {{ color: #22c55e; }}
1049|            .summary-label {{ color: #888; font-size: 0.9rem; margin-top: 0.25rem; }}
1050|            
1051|            .folders {{ background: linear-gradient(135deg, #1e1e3f 0%, #151530 100%); border-radius: 1rem; padding: 1rem; margin-bottom: 1.5rem; }}
1052|            .folders-title {{ color: #888; font-size: 0.9rem; margin-bottom: 1rem; }}
1053|            
1054|            .folder-row {{ display: flex; align-items: center; padding: 1rem; background: rgba(0,0,0,0.2); border-radius: 0.75rem; margin-bottom: 0.5rem; text-decoration: none; color: white; transition: all 0.2s; }}
1055|            .folder-row:hover {{ background: rgba(0,212,255,0.1); transform: translateX(-4px); }}
1056|            .folder-icon {{ font-size: 2rem; margin-left: 1rem; }}
1057|            .folder-info {{ flex: 1; }}
1058|            .folder-name {{ font-weight: bold; font-size: 1.2rem; }}
1059|            .folder-meta {{ color: #888; font-size: 0.85rem; }}
1060|            .folder-stats {{ color: #22c55e; font-weight: bold; font-size: 1.1rem; margin-left: 1rem; }}
1061|            .folder-arrow {{ color: #00d4ff; font-size: 1.5rem; }}
1062|            
1063|            .no-workouts {{ text-align: center; padding: 3rem 1rem; }}
1064|            .no-workouts-icon {{ font-size: 4rem; margin-bottom: 1rem; }}
1065|            
1066|            .welcome-banner {{ position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.95); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 1000; padding: 2rem; text-align: center; }}
1067|            .welcome-icon {{ font-size: 4rem; margin-bottom: 1rem; }}
1068|            .welcome-banner h2 {{ color: #00d4ff; font-size: 1.8rem; margin-bottom: 0.5rem; }}
1069|            .welcome-banner p {{ color: #888; margin-bottom: 0.5rem; }}
1070|            .welcome-link {{ font-family: monospace; color: #00d4ff; font-size: 0.8rem; background: rgba(0,212,255,0.1); padding: 0.5rem 1rem; border-radius: 0.5rem; margin: 1rem 0; word-break: break-all; }}
1071|            .welcome-btn {{ display: flex; align-items: center; justify-content: center; gap: 0.5rem; background: linear-gradient(90deg, #25D366 0%, #128C7E 100%); color: white; padding: 1rem 2rem; border-radius: 9999px; font-size: 1.1rem; font-weight: bold; text-decoration: none; margin: 1rem 0; }}
1072|            .welcome-close {{ background: transparent; color: #888; border: 1px solid #888; padding: 0.5rem 1.5rem; border-radius: 9999px; cursor: pointer; margin-top: 1rem; }}
1073|            .welcome-close:hover {{ color: white; border-color: white; }}
1074|            
1075|            .buttons {{ display: flex; flex-direction: column; gap: 0.75rem; margin: 1.5rem 0; }}
1076|            .share-btn {{ display: flex; align-items: center; justify-content: center; gap: 0.75rem; background: linear-gradient(90deg, #25D366 0%, #128C7E 100%); color: white; border: none; padding: 1rem 2rem; border-radius: 9999px; font-size: 1rem; font-weight: bold; cursor: pointer; text-decoration: none; }}
1077|            .delete-btn {{ display: flex; align-items: center; justify-content: center; gap: 0.5rem; background: transparent; color: #ef4444; border: 1px solid #ef4444; padding: 0.75rem 1.5rem; border-radius: 9999px; font-size: 0.85rem; cursor: pointer; }}
1078|            .delete-btn:hover {{ background: #ef4444; color: white; }}
1079|            
1080|            footer {{ text-align: center; padding: 1.5rem 0; color: #888; font-size: 0.8rem; }}
1081|            footer .brand {{ color: #00d4ff; font-weight: bold; font-size: 1rem; }}
1082|            footer .user-id {{ font-family: monospace; color: #00d4ff; opacity: 0.6; margin-top: 0.5rem; font-size: 0.7rem; }}
1083|        </style>
1084|    </head>
1085|    <body>
1086|        {welcome_banner}
1087|        <div class="container">
1088|            <header>
1089|                <h1>🏃‍♂️ FitBeat</h1>
1090|                {'<p class="user-name">' + user_name + '</p>' if user_name else ''}
1091|            </header>
1092|            
1093|            <div class="summary">
1094|                <div class="summary-title">📊 {t('total_summary', lang)}</div>
1095|                <div class="summary-grid">
1096|                    <div>
1097|                        <div class="summary-value">{len(workouts)}</div>
1098|                        <div class="summary-label">{t('workouts', lang)}</div>
1099|                    </div>
1100|                    <div>
1101|                        <div class="summary-value green">{total_km:.1f}</div>
1102|                        <div class="summary-label">{t('km_total', lang)}</div>
1103|                    </div>
1104|                </div>
1105|            </div>
1106|            
1107|            <div class="folders">
1108|                <div class="folders-title">📁 {t('by_years', lang)}</div>
1109|                {years_html if years_html else f'<div class="no-workouts"><div class="no-workouts-icon">🏃‍♂️</div><p>{t("no_workouts", lang)}</p><p style="font-size:0.8rem;margin-top:0.5rem;color:#888;">{t("finish_goal", lang)}</p></div>'}
1110|            </div>
1111|            
1112|            <div class="buttons">
1113|                <a href="https://wa.me/?text={share_text}" target="_blank" class="share-btn">📤 {t('share_whatsapp', lang)}</a>
1114|                {f'<button onclick="deleteAll()" class="delete-btn">🗑️ {t("delete_all", lang)}</button>' if workouts else ''}
1115|            </div>
1116|            
1117|            <footer>
1118|                <div class="brand">FitBeat</div>
1119|                <div class="user-id">{t('user_id', lang)}: {user_id}</div>
1120|            </footer>
1121|        </div>
1122|        <script>
1123|            async function deleteAll() {{
1124|                if (confirm('{t("confirm_delete_all", lang)}')) {{
1125|                    await fetch('/api/workout/user/{user_id}/all', {{ method: 'DELETE' }});
1126|                    location.reload();
1127|                }}
1128|            }}
1129|            function closeWelcome() {{
1130|                document.getElementById('welcomeBanner').style.display = 'none';
1131|                localStorage.setItem('fitbeat_welcomed_{user_id}', 'true');
1132|            }}
1133|            // Auto-hide if already welcomed
1134|            if (localStorage.getItem('fitbeat_welcomed_{user_id}')) {{
1135|                const banner = document.getElementById('welcomeBanner');
1136|                if (banner) banner.style.display = 'none';
1137|            }}
1138|        </script>
1139|    </body>
1140|    </html>
1141|    """
1142|
1143|@api_router.get("/u/{user_id}/year/{year}", response_class=HTMLResponse)
1144|async def year_page(user_id: str, year: str, lang: int = None):
1145|    """Year page - shows months as folders"""
1146|    workouts = await db.workouts.find(
1147|        {"user_id": user_id, "timestamp": {"$regex": f"^{year}"}},
1148|        {"_id": 0}
1149|    ).sort("timestamp", -1).to_list(500)
1150|    
1151|    # Get language
1152|    if lang is None:
1153|        lang = workouts[0].get('lang', 0) if workouts else 0
1154|    
1155|    # RTL support
1156|    dir_attr = 'dir="rtl"' if is_rtl(lang) else 'dir="ltr"'
1157|    lang_code = ["en", "he", "es", "fr", "de", "zh"][lang] if lang < 6 else "en"
1158|    
1159|    from collections import defaultdict
1160|    months_data = defaultdict(list)
1161|    for w in workouts:
1162|        month = w.get('timestamp', '')[5:7]
1163|        if month:
1164|            months_data[month].append(w)
1165|    
1166|    total_dist = sum(w.get('distance_cm', 0) for w in workouts) / 100000
1167|    total_time = sum(w.get('duration_sec', 0) for w in workouts)
1168|    total_hrs = total_time // 3600
1169|    total_mins = (total_time % 3600) // 60
1170|    time_str = f"{total_hrs}:{total_mins:02d}"
1171|    avg_hr_list = [w.get('avg_hr') for w in workouts if w.get('avg_hr')]
1172|    avg_hr = round(sum(avg_hr_list) / len(avg_hr_list)) if avg_hr_list else 0
1173|    
1174|    months_html = ""
1175|    for month in sorted(months_data.keys(), reverse=True):
1176|        month_workouts = months_data[month]
1177|        m_dist = sum(w.get('distance_cm', 0) for w in month_workouts) / 100000
1178|        m_count = len(month_workouts)
1179|        month_name = get_month_name(int(month), lang)
1180|        
1181|        months_html += f"""
1182|        <a href="/api/u/{user_id}/year/{year}/month/{month}?lang={lang}" class="folder-row">
1183|            <div class="folder-icon">📁</div>
1184|            <div class="folder-info">
1185|                <div class="folder-name">{month_name}</div>
1186|                <div class="folder-meta">{m_count} {t('workouts', lang)}</div>
1187|            </div>
1188|            <div class="folder-stats">{m_dist:.1f} {t('km', lang)}</div>
1189|            <div class="folder-arrow">{'←' if is_rtl(lang) else '→'}</div>
1190|        </a>
1191|        """
1192|    
1193|    return f"""
1194|    <!DOCTYPE html>
1195|    <html lang="{lang_code}" {dir_attr}>
1196|    <head>
1197|        <meta charset="UTF-8">
1198|        <meta name="viewport" content="width=device-width, initial-scale=1.0">
1199|        <title>FitBeat - {year}</title>
1200|        <style>## 📄 חלק 4 מתוך 4 (אחרון):
Action: file_editor view /app/backend/server.py
Observation: /app/backend/server.py:
1200|        <style>
1201|            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
1202|            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; color: white; padding: 1rem; }}
1203|            .container {{ max-width: 480px; margin: 0 auto; }}
1204|            .back {{ display: inline-flex; align-items: center; gap: 0.5rem; color: #00d4ff; text-decoration: none; margin-bottom: 1rem; font-size: 0.9rem; }}
1205|            header {{ text-align: center; padding: 1rem 0; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 1.5rem; }}
1206|            h1 {{ color: #00d4ff; font-size: 1.5rem; }}
1207|            .subtitle {{ color: #888; margin-top: 0.25rem; }}
1208|            
1209|            .summary {{ background: linear-gradient(135deg, #1e1e3f 0%, #151530 100%); border-radius: 1rem; padding: 1.25rem; margin-bottom: 1.5rem; border: 1px solid rgba(0,212,255,0.2); }}
1210|            .summary-title {{ color: #888; font-size: 0.85rem; margin-bottom: 0.75rem; }}
1211|            .summary-row {{ display: flex; justify-content: space-around; text-align: center; }}
1212|            .summary-item {{ }}
1213|            .summary-value {{ font-size: 1.5rem; font-weight: bold; color: #00d4ff; }}
1214|            .summary-value.green {{ color: #22c55e; }}
1215|            .summary-label {{ color: #888; font-size: 0.75rem; }}
1216|            
1217|            .folders {{ background: linear-gradient(135deg, #1e1e3f 0%, #151530 100%); border-radius: 1rem; padding: 1rem; }}
1218|            .folders-title {{ color: #888; font-size: 0.85rem; margin-bottom: 1rem; }}
1219|            
1220|            .folder-row {{ display: flex; align-items: center; padding: 1rem; background: rgba(0,0,0,0.2); border-radius: 0.75rem; margin-bottom: 0.5rem; text-decoration: none; color: white; transition: all 0.2s; }}
1221|            .folder-row:hover {{ background: rgba(0,212,255,0.1); transform: translateX(-4px); }}
1222|            .folder-icon {{ font-size: 1.75rem; {"margin-left" if is_rtl(lang) else "margin-right"}: 0.75rem; }}
1223|            .folder-info {{ flex: 1; }}
1224|            .folder-name {{ font-weight: bold; font-size: 1.1rem; }}
1225|            .folder-meta {{ color: #888; font-size: 0.8rem; }}
1226|            .folder-stats {{ color: #22c55e; font-weight: bold; {"margin-left" if is_rtl(lang) else "margin-right"}: 0.75rem; }}
1227|            .folder-arrow {{ color: #00d4ff; font-size: 1.25rem; }}
1228|            
1229|            footer {{ text-align: center; padding: 1.5rem 0; color: #888; font-size: 0.8rem; }}
1230|        </style>
1231|    </head>
1232|    <body>
1233|        <div class="container">
1234|            <a href="/api/u/{user_id}?lang={lang}" class="back">{'→' if is_rtl(lang) else '←'} {t('back', lang)}</a>
1235|            <header>
1236|                <h1>📁 {year}</h1>
1237|                <p class="subtitle">{len(workouts)} {t('workouts', lang)}</p>
1238|            </header>
1239|            
1240|            <div class="summary">
1241|                <div class="summary-title">📊 {t('yearly_summary', lang)} {year}</div>
1242|                <div class="summary-row">
1243|                    <div class="summary-item">
1244|                        <div class="summary-value">{len(workouts)}</div>
1245|                        <div class="summary-label">{t('workouts', lang)}</div>
1246|                    </div>
1247|                    <div class="summary-item">
1248|                        <div class="summary-value green">{total_dist:.1f}</div>
1249|                        <div class="summary-label">{t('km', lang)}</div>
1250|                    </div>
1251|                    <div class="summary-item">
1252|                        <div class="summary-value">{time_str}</div>
1253|                        <div class="summary-label">{t('hours', lang)}</div>
1254|                    </div>
1255|                    <div class="summary-item">
1256|                        <div class="summary-value" style="color:#ef4444;">{avg_hr}</div>
1257|                        <div class="summary-label">{t('avg_hr', lang)}</div>
1258|                    </div>
1259|                </div>
1260|            </div>
1261|            
1262|            <div class="folders">
1263|                {months_html}
1264|            </div>
1265|            
1266|            <footer>FitBeat</footer>
1267|        </div>
1268|    </body>
1269|    </html>
1270|    """
1271|
1272|@api_router.get("/u/{user_id}/year/{year}/month/{month}", response_class=HTMLResponse)
1273|async def month_page_view(user_id: str, year: str, month: str, lang: int = None):
1274|    """Month page - shows workouts list"""
1275|    workouts = await db.workouts.find(
1276|        {"user_id": user_id, "timestamp": {"$regex": f"^{year}-{month}"}},
1277|        {"_id": 0}
1278|    ).sort("timestamp", -1).to_list(100)
1279|    
1280|    # Get language
1281|    if lang is None:
1282|        lang = workouts[0].get('lang', 0) if workouts else 0
1283|    
1284|    # RTL support
1285|    dir_attr = 'dir="rtl"' if is_rtl(lang) else 'dir="ltr"'
1286|    lang_code = ["en", "he", "es", "fr", "de", "zh"][lang] if lang < 6 else "en"
1287|    
1288|    month_name = get_month_name(int(month), lang)
1289|    
1290|    total_dist = sum(w.get('distance_cm', 0) for w in workouts) / 100000
1291|    total_time = sum(w.get('duration_sec', 0) for w in workouts)
1292|    total_hrs = total_time // 3600
1293|    total_mins = (total_time % 3600) // 60
1294|    time_str = f"{total_hrs}:{total_mins:02d}"
1295|    avg_hr_list = [w.get('avg_hr') for w in workouts if w.get('avg_hr')]
1296|    avg_hr = round(sum(avg_hr_list) / len(avg_hr_list)) if avg_hr_list else 0
1297|    total_steps = sum(w.get('steps', 0) or 0 for w in workouts)
1298|    
1299|    workouts_html = ""
1300|    for w in workouts:
1301|        dist_km = w.get('distance_cm', 0) / 100000
1302|        dur_sec = w.get('duration_sec', 0)
1303|        dur_min = dur_sec // 60
1304|        dur_s = dur_sec % 60
1305|        hr = w.get('avg_hr', '--')
1306|        day = w.get('timestamp', '')[8:10]
1307|        workout_id = w.get('id', '')
1308|        
1309|        if dist_km > 0:
1310|            pace_sec = dur_sec / dist_km
1311|            pace_str = f"{int(pace_sec//60)}:{int(pace_sec%60):02d}"
1312|        else:
1313|            pace_str = "--:--"
1314|        
1315|        workouts_html += f"""
1316|        <a href="/api/u/{user_id}/workout/{workout_id}?lang={lang}" class="workout-row">
1317|            <div class="workout-day">{day}</div>
1318|            <div class="workout-info">
1319|                <div class="workout-dist">{dist_km:.2f} {t('km', lang)}</div>
1320|                <div class="workout-pace">⚡ {pace_str}/{t('km', lang)}</div>
1321|            </div>
1322|            <div class="workout-time">{dur_min}:{dur_s:02d}</div>
1323|            <div class="workout-hr">❤️ {hr}</div>
1324|            <div class="workout-arrow">{'←' if is_rtl(lang) else '→'}</div>
1325|        </a>
1326|        """
1327|    
1328|    base_url = os.environ.get('APP_URL', 'https://exercise-journal-9.preview.emergentagent.com')
1329|    share_text = f"📅 {month_name} {year}%0A🏃 {len(workouts)} {t('workouts', lang)}%0A📍 {total_dist:.1f} {t('km', lang)}%0A⏱️ {time_str} {t('hours', lang)}%0A%0A🔗 {base_url}/api/u/{user_id}/year/{year}/month/{month}?lang={lang}"
1330|    
1331|    return f"""
1332|    <!DOCTYPE html>
1333|    <html lang="{lang_code}" {dir_attr}>
1334|    <head>
1335|        <meta charset="UTF-8">
1336|        <meta name="viewport" content="width=device-width, initial-scale=1.0">
1337|        <title>FitBeat - {month_name} {year}</title>
1338|        <style>
1339|            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
1340|            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; color: white; padding: 1rem; }}
1341|            .container {{ max-width: 480px; margin: 0 auto; }}
1342|            .back {{ display: inline-flex; align-items: center; gap: 0.5rem; color: #00d4ff; text-decoration: none; margin-bottom: 1rem; font-size: 0.9rem; }}
1343|            header {{ text-align: center; padding: 1rem 0; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 1.5rem; }}
1344|            h1 {{ color: #00d4ff; font-size: 1.5rem; }}
1345|            .subtitle {{ color: #888; margin-top: 0.25rem; }}
1346|            
1347|            .summary {{ background: linear-gradient(135deg, #1e1e3f 0%, #151530 100%); border-radius: 1rem; padding: 1.25rem; margin-bottom: 1.5rem; border: 1px solid rgba(0,212,255,0.2); }}
1348|            .summary-title {{ color: #888; font-size: 0.85rem; margin-bottom: 0.75rem; }}
1349|            .summary-row {{ display: flex; justify-content: space-around; text-align: center; }}
1350|            .summary-item {{ }}
1351|            .summary-value {{ font-size: 1.3rem; font-weight: bold; color: #00d4ff; }}
1352|            .summary-value.green {{ color: #22c55e; }}
1353|            .summary-label {{ color: #888; font-size: 0.7rem; }}
1354|            
1355|            .workouts {{ background: linear-gradient(135deg, #1e1e3f 0%, #151530 100%); border-radius: 1rem; padding: 1rem; margin-bottom: 1.5rem; }}
1356|            .workouts-title {{ color: #888; font-size: 0.85rem; margin-bottom: 1rem; }}
1357|            
1358|            .workout-row {{ display: flex; align-items: center; padding: 0.75rem; background: rgba(0,0,0,0.2); border-radius: 0.5rem; margin-bottom: 0.4rem; text-decoration: none; color: white; transition: all 0.2s; }}
1359|            .workout-row:hover {{ background: rgba(0,212,255,0.1); transform: translateX(-4px); }}
1360|            .workout-day {{ background: #00d4ff; color: #1a1a2e; width: 2.25rem; height: 2.25rem; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem; margin-left: 0.75rem; }}
1361|            .workout-info {{ flex: 1; }}
1362|            .workout-dist {{ font-weight: bold; }}
1363|            .workout-pace {{ color: #888; font-size: 0.75rem; }}
1364|            .workout-time {{ color: #00d4ff; font-weight: bold; font-size: 0.9rem; margin: 0 0.75rem; }}
1365|            .workout-hr {{ color: #ef4444; font-size: 0.85rem; }}
1366|            .workout-arrow {{ color: #00d4ff; font-size: 1rem; {"margin-right" if is_rtl(lang) else "margin-left"}: 0.25rem; }}
1367|            
1368|            .share-btn {{ display: flex; align-items: center; justify-content: center; gap: 0.75rem; background: linear-gradient(90deg, #25D366 0%, #128C7E 100%); color: white; border: none; padding: 1rem 2rem; border-radius: 9999px; font-size: 1rem; font-weight: bold; cursor: pointer; text-decoration: none; margin-bottom: 1.5rem; }}
1369|            
1370|            footer {{ text-align: center; padding: 1rem 0; color: #888; font-size: 0.8rem; }}
1371|        </style>
1372|    </head>
1373|    <body>
1374|        <div class="container">
1375|            <a href="/api/u/{user_id}/year/{year}?lang={lang}" class="back">{'→' if is_rtl(lang) else '←'} {t('back', lang)} {year}</a>
1376|            <header>
1377|                <h1>📁 {month_name} {year}</h1>
1378|                <p class="subtitle">{len(workouts)} {t('workouts', lang)}</p>
1379|            </header>
1380|            
1381|            <div class="summary">
1382|                <div class="summary-title">📊 {t('monthly_summary', lang)}</div>
1383|                <div class="summary-row">
1384|                    <div class="summary-item">
1385|                        <div class="summary-value">{len(workouts)}</div>
1386|                        <div class="summary-label">{t('workouts', lang)}</div>
1387|                    </div>
1388|                    <div class="summary-item">
1389|                        <div class="summary-value green">{total_dist:.1f}</div>
1390|                        <div class="summary-label">{t('km', lang)}</div>
1391|                    </div>
1392|                    <div class="summary-item">
1393|                        <div class="summary-value">{time_str}</div>
1394|                        <div class="summary-label">{t('hours', lang)}</div>
1395|                    </div>
1396|                    <div class="summary-item">
1397|                        <div class="summary-value" style="color:#ef4444;">{avg_hr}</div>
1398|                        <div class="summary-label">{t('avg_hr', lang)}</div>
1399|                    </div>
1400|                    <div class="summary-item">
1401|                        <div class="summary-value">{total_steps:,}</div>
1402|                        <div class="summary-label">{t('steps', lang)}</div>
1403|                    </div>
1404|                </div>
1405|            </div>
1406|            
1407|            <div class="workouts">
1408|                {workouts_html}
1409|            </div>
1410|            
1411|            <a href="https://wa.me/?text={share_text}" target="_blank" class="share-btn">📤 {t('share_whatsapp', lang)}</a>
1412|            
1413|            <footer>FitBeat</footer>
1414|        </div>
1415|    </body>
1416|    </html>
1417|    """
1418|
1419|@api_router.get("/u/{user_id}/workout/{workout_id}", response_class=HTMLResponse)
1420|async def single_workout_page(user_id: str, workout_id: str, lang: int = None):
1421|    """Serve single workout HTML page"""
1422|    workout = await db.workouts.find_one(
1423|        {"id": workout_id, "user_id": user_id},
1424|        {"_id": 0}
1425|    )
1426|    # Get language from parameter or workout
1427|    if lang is None:
1428|        lang = workout.get('lang', 0) if workout else 0
1429|    return generate_workout_html(workout, user_id, lang)
1430|
1431|@api_router.get("/u/{user_id}/monthly", response_class=HTMLResponse)
1432|async def monthly_page(user_id: str):
1433|    """Serve monthly summary HTML page with all workouts"""
1434|    workouts = await db.workouts.find(
1435|        {"user_id": user_id},
1436|        {"_id": 0}
1437|    ).sort("timestamp", -1).to_list(100)
1438|    
1439|    if not workouts:
1440|        return f"""
1441|        <!DOCTYPE html>
1442|        <html lang="he" dir="rtl">
1443|        <head>
1444|            <meta charset="UTF-8">
1445|            <meta name="viewport" content="width=device-width, initial-scale=1.0">
1446|            <title>FitBeat - סיכום חודשי</title>
1447|            <style>
1448|                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
1449|                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; color: white; display: flex; align-items: center; justify-content: center; }}
1450|                .container {{ text-align: center; padding: 2rem; }}
1451|                h1 {{ color: #00d4ff; }}
1452|            </style>
1453|        </head>
1454|        <body>
1455|            <div class="container">
1456|                <h1>📅 אין אימונים</h1>
1457|                <p>מזהה: {user_id}</p>
1458|            </div>
1459|        </body>
1460|        </html>
1461|        """
1462|    
1463|    # Calculate totals
1464|    total_dist = sum(w.get('distance_cm', 0) for w in workouts)
1465|    total_time = sum(w.get('duration_sec', 0) for w in workouts)
1466|    total_steps = sum(w.get('steps', 0) or 0 for w in workouts)
1467|    avg_hr_list = [w.get('avg_hr') for w in workouts if w.get('avg_hr')]
1468|    avg_hr = round(sum(avg_hr_list) / len(avg_hr_list)) if avg_hr_list else 0
1469|    
1470|    # Format totals
1471|    total_km = total_dist / 100000
1472|    total_hrs = total_time // 3600
1473|    total_mins = (total_time % 3600) // 60
1474|    time_str = f"{total_hrs} שעות ו-{total_mins} דקות" if total_hrs > 0 else f"{total_mins} דקות"
1475|    
1476|    # Get base URL
1477|    base_url = os.environ.get('APP_URL', 'https://exercise-journal-9.preview.emergentagent.com')
1478|    
1479|    # Build workout rows
1480|    workout_rows = ""
1481|    for w in workouts:
1482|        dist_km = w.get('distance_cm', 0) / 100000
1483|        dur_min = w.get('duration_sec', 0) // 60
1484|        hr = w.get('avg_hr', '--')
1485|        ts = w.get('timestamp', '')[:10]
1486|        workout_id = w.get('id', '')
1487|        workout_rows += f"""
1488|        <a href="/api/u/{user_id}/workout/{workout_id}" class="workout-row">
1489|            <div class="workout-icon">🏃</div>
1490|            <div class="workout-info">
1491|                <div class="workout-dist">{dist_km:.2f} ק"מ</div>
1492|                <div class="workout-date">{ts}</div>
1493|            </div>
1494|            <div class="workout-stats">
1495|                <div class="workout-time">{dur_min} דק'</div>
1496|                <div class="workout-hr">❤️ {hr}</div>
1497|            </div>
1498|            <div class="workout-arrow">←</div>
1499|        </a>
1500|        """
1501|    
1502|    user_name = workouts[0].get('user_name', '') if workouts else ''
1503|    
1504|    return f"""
1505|    <!DOCTYPE html>
1506|    <html lang="he" dir="rtl">
1507|    <head>
1508|        <meta charset="UTF-8">
1509|        <meta name="viewport" content="width=device-width, initial-scale=1.0">
1510|        <title>FitBeat - סיכום חודשי</title>
1511|        <style>
1512|            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
1513|            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; color: white; padding: 1rem; }}
1514|            .container {{ max-width: 480px; margin: 0 auto; }}
1515|            header {{ text-align: center; padding: 1.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 1.5rem; }}
1516|            h1 {{ color: #00d4ff; font-size: 1.5rem; }}
1517|            .subtitle {{ color: #888; margin-top: 0.5rem; }}
1518|            .totals {{ background: linear-gradient(135deg, #1e1e3f 0%, #151530 100%); border-radius: 1rem; padding: 1.5rem; margin-bottom: 1.5rem; }}
1519|            .totals-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; text-align: center; }}
1520|            .total-value {{ font-size: 2.5rem; font-weight: bold; color: #00d4ff; }}
1521|            .total-value.green {{ color: #22c55e; }}
1522|            .total-label {{ color: #888; font-size: 0.9rem; margin-top: 0.25rem; }}
1523|            .stats-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.5rem; margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid rgba(255,255,255,0.1); }}
1524|            .stat-item {{ text-align: center; }}
1525|            .stat-value {{ font-size: 1.1rem; font-weight: bold; }}
1526|            .stat-label {{ color: #888; font-size: 0.7rem; }}
1527|            .workouts-section {{ background: linear-gradient(135deg, #1e1e3f 0%, #151530 100%); border-radius: 1rem; padding: 1rem; margin-bottom: 1.5rem; }}
1528|            .section-title {{ color: #888; font-size: 0.9rem; margin-bottom: 1rem; }}
1529|            .workout-row {{ display: flex; align-items: center; padding: 0.75rem; background: rgba(0,0,0,0.2); border-radius: 0.5rem; margin-bottom: 0.5rem; text-decoration: none; color: white; transition: background 0.2s; }}
1530|            .workout-row:hover {{ background: rgba(0,212,255,0.1); }}
1531|            .workout-icon {{ font-size: 1.5rem; margin-left: 0.75rem; }}
1532|            .workout-info {{ flex: 1; }}
1533|            .workout-dist {{ font-weight: bold; }}
1534|            .workout-date {{ color: #888; font-size: 0.75rem; }}
1535|            .workout-stats {{ text-align: left; margin-left: 1rem; }}
1536|            .workout-time {{ color: #00d4ff; font-weight: bold; }}
1537|            .workout-hr {{ color: #888; font-size: 0.75rem; }}
1538|            .workout-arrow {{ color: #00d4ff; font-size: 1.2rem; margin-right: 0.5rem; }}
1539|            .share-btn {{ display: flex; align-items: center; justify-content: center; gap: 0.75rem; background: linear-gradient(90deg, #25D366 0%, #128C7E 100%); color: white; border: none; padding: 1rem 2rem; border-radius: 9999px; font-size: 1.1rem; font-weight: bold; cursor: pointer; margin: 1.5rem auto; text-decoration: none; }}
1540|            footer {{ text-align: center; padding: 1rem 0; color: #888; font-size: 0.8rem; }}
1541|            footer .brand {{ color: #00d4ff; font-weight: bold; }}
1542|        </style>
1543|    </head>
1544|    <body>
1545|        <div class="container">
1546|            <header>
1547|                <h1>📅 סיכום חודשי</h1>
1548|                <p class="subtitle">{user_name}</p>
1549|            </header>
1550|            
1551|            <div class="totals">
1552|                <div class="totals-grid">
1553|                    <div>
1554|                        <div class="total-value">{len(workouts)}</div>
1555|                        <div class="total-label">אימונים</div>
1556|                    </div>
1557|                    <div>
1558|                        <div class="total-value green">{total_km:.1f}</div>
1559|                        <div class="total-label">ק"מ סה"כ</div>
1560|                    </div>
1561|                </div>
1562|                <div class="stats-row">
1563|                    <div class="stat-item">
1564|                        <div class="stat-value">⏱️</div>
1565|                        <div class="stat-label">{time_str}</div>
1566|                    </div>
1567|                    <div class="stat-item">
1568|                        <div class="stat-value">❤️</div>
1569|                        <div class="stat-label">{avg_hr} BPM</div>
1570|                    </div>
1571|                    <div class="stat-item">
1572|                        <div class="stat-value">👟</div>
1573|                        <div class="stat-label">{total_steps:,}</div>
1574|                    </div>
1575|                    <div class="stat-item">
1576|                        <div class="stat-value">📍</div>
1577|                        <div class="stat-label">{total_km/len(workouts):.1f} ק"מ/אימון</div>
1578|                    </div>
1579|                </div>
1580|            </div>
1581|            
1582|            <div class="workouts-section">
1583|                <div class="section-title">🏃 כל האימונים</div>
1584|                {workout_rows}
1585|            </div>
1586|            
1587|            <a href="https://wa.me/?text=📅 סיכום חודשי%0A🏃 {len(workouts)} אימונים%0A📍 {total_km:.1f} ק״מ סה״כ%0A⏱️ {time_str}%0A%0A🔗 {base_url}/api/u/{user_id}/monthly" class="share-btn">
1588|                📤 שתף ב-WhatsApp
1589|            </a>
1590|            
1591|            <footer>
1592|                <div class="brand">FitBeat</div>
1593|                <div>מזהה: {user_id}</div>
1594|            </footer>
1595|        </div>
1596|    </body>
1597|    </html>
1598|    """
1599|
1600|# Include the router in the main app
1601|app.include_router(api_router)
1602|
1603|app.add_middleware(
1604|    CORSMiddleware,
1605|    allow_credentials=True,
1606|    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
1607|    allow_methods=["*"],
1608|    allow_headers=["*"],
1609|)
1610|
1611|@app.on_event("shutdown")
1612|async def shutdown_db_client():
1613|    client.close()
