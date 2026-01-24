import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Format duration to MM:SS or HH:MM:SS
function formatDuration(seconds) {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  
  if (hrs > 0) {
    return `${hrs}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }
  return `${mins}:${String(secs).padStart(2, '0')}`;
}

// Format pace (min/km)
function formatPace(distanceCm, durationSec) {
  if (distanceCm === 0) return "--:--";
  const distanceKm = distanceCm / 100000;
  const paceSecPerKm = durationSec / distanceKm;
  const paceMin = Math.floor(paceSecPerKm / 60);
  const paceSec = Math.floor(paceSecPerKm % 60);
  return `${paceMin}:${String(paceSec).padStart(2, '0')}`;
}

// Format date in Hebrew
function formatDateHebrew(dateStr) {
  const date = new Date(dateStr);
  const months = ['ינואר', 'פברואר', 'מרץ', 'אפריל', 'מאי', 'יוני', 'יולי', 'אוגוסט', 'ספטמבר', 'אוקטובר', 'נובמבר', 'דצמבר'];
  const day = date.getDate();
  const month = months[date.getMonth()];
  const year = date.getFullYear();
  const hours = String(date.getHours()).padStart(2, '0');
  const mins = String(date.getMinutes()).padStart(2, '0');
  return `${day} ב${month} ${year} • ${hours}:${mins}`;
}

export default function WorkoutPage() {
  const { userId } = useParams();
  const [workout, setWorkout] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    async function fetchData() {
      try {
        const [workoutRes, statsRes] = await Promise.all([
          fetch(`${API}/workout/latest/${userId}`),
          fetch(`${API}/user/${userId}/stats`)
        ]);
        
        if (workoutRes.status === 404) {
          setError("לא נמצאו אימונים עבור משתמש זה");
          setLoading(false);
          return;
        }
        
        const workoutData = await workoutRes.json();
        const statsData = await statsRes.json();
        
        setWorkout(workoutData);
        setStats(statsData);
        setLoading(false);
      } catch (err) {
        setError("שגיאה בטעינת הנתונים");
        setLoading(false);
      }
    }
    
    fetchData();
  }, [userId]);
  
  const shareToWhatsApp = () => {
    if (!workout) return;
    
    const distKm = (workout.distance_cm / 100000).toFixed(2);
    const duration = formatDuration(workout.duration_sec);
    const pace = formatPace(workout.distance_cm, workout.duration_sec);
    const userName = workout.user_name || "מישהו";
    
    let text = `🏃‍♂️ ${userName} סיים אימון!\n\n`;
    text += `📍 מרחק: ${distKm} ק"מ\n`;
    text += `⏱️ זמן: ${duration}\n`;
    text += `⚡ קצב ממוצע: ${pace} /ק"מ\n`;
    
    if (workout.elevation_gain) {
      text += `\n⛰️ עלייה: +${workout.elevation_gain} מ'`;
      if (workout.elevation_loss) {
        text += ` | ירידה: -${Math.abs(workout.elevation_loss)} מ'`;
      }
    }
    
    if (workout.avg_hr) {
      text += `\n❤️ דופק ממוצע: ${workout.avg_hr} BPM`;
    }
    
    text += `\n\n🗺️ צפה בסיכום המלא:\n${window.location.href}`;
    
    const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(text)}`;
    window.open(whatsappUrl, '_blank');
  };
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#1a1a2e] to-[#16213e] flex items-center justify-center">
        <div className="text-white text-xl">טוען...</div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#1a1a2e] to-[#16213e] flex items-center justify-center p-4">
        <div className="bg-[#1e1e3f] rounded-2xl p-8 text-center max-w-md">
          <div className="text-6xl mb-4">🏃‍♂️</div>
          <h1 className="text-white text-2xl font-bold mb-2">FitBeat</h1>
          <p className="text-gray-400">{error}</p>
          <p className="text-gray-500 text-sm mt-4">
            מזהה משתמש: <span className="text-cyan-400 font-mono">{userId}</span>
          </p>
        </div>
      </div>
    );
  }
  
  const distKm = (workout.distance_cm / 100000).toFixed(2);
  const duration = formatDuration(workout.duration_sec);
  const pace = formatPace(workout.distance_cm, workout.duration_sec);
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-[#1a1a2e] to-[#16213e] text-white p-4" dir="rtl">
      <div className="max-w-md mx-auto">
        {/* Header */}
        <header className="text-center py-6 border-b border-white/10 mb-6">
          <h1 className="text-2xl font-bold text-cyan-400 mb-1">🏃‍♂️ סיכום אימון</h1>
          <p className="text-gray-400 text-sm">{formatDateHebrew(workout.timestamp)}</p>
          {workout.user_name && (
            <p className="text-lg mt-2">{workout.user_name} סיים אימון!</p>
          )}
        </header>
        
        {/* Map Section - Simulated */}
        <section className="bg-[#0f0f23] rounded-2xl overflow-hidden mb-6 shadow-lg">
          <div className="h-64 relative bg-gradient-to-br from-[#2d4a2d] to-[#1a2f1a]">
            {/* Simulated satellite map */}
            <div className="absolute inset-0 opacity-30" style={{
              backgroundImage: `
                radial-gradient(ellipse at 20% 30%, #3d5a3d 0%, transparent 40%),
                radial-gradient(ellipse at 60% 50%, #4a6a4a 0%, transparent 35%),
                radial-gradient(ellipse at 80% 20%, #2a3a2a 0%, transparent 45%)
              `
            }} />
            
            {/* Route SVG */}
            <svg className="absolute inset-0 w-full h-full" viewBox="0 0 400 256">
              {/* Glow path */}
              <path
                d="M 50,200 Q 80,180 120,160 T 200,120 T 280,100 T 350,80"
                fill="none"
                stroke="#ff6666"
                strokeWidth="8"
                strokeLinecap="round"
                opacity="0.3"
                style={{ filter: 'blur(4px)' }}
              />
              {/* Main path */}
              <path
                d="M 50,200 Q 80,180 120,160 T 200,120 T 280,100 T 350,80"
                fill="none"
                stroke="#ff3333"
                strokeWidth="4"
                strokeLinecap="round"
                style={{ filter: 'drop-shadow(0 0 6px rgba(255,50,50,0.9))' }}
              />
              {/* Start marker */}
              <circle cx="50" cy="200" r="8" fill="#22c55e" />
              <circle cx="50" cy="200" r="4" fill="white" />
              {/* End marker */}
              <circle cx="350" cy="80" r="8" fill="#ef4444" style={{ filter: 'drop-shadow(0 0 6px rgba(239,68,68,0.8))' }} />
              <circle cx="350" cy="80" r="4" fill="white" />
            </svg>
            
            {/* Distance badge */}
            <div className="absolute top-3 left-3 bg-black/80 px-4 py-2 rounded-xl border border-white/10">
              <span className="text-2xl font-bold text-cyan-400">{distKm}</span>
              <span className="text-sm text-gray-400 mr-1">ק"מ</span>
            </div>
            
            {/* Legend */}
            <div className="absolute bottom-3 right-3 bg-black/70 px-3 py-2 rounded-lg text-xs flex gap-4">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-green-500" />
                התחלה
              </span>
              <span className="flex items-center gap-1">
                <span className="w-4 h-0.5 bg-red-500 rounded" />
                מסלול
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-red-500" />
                סיום
              </span>
            </div>
          </div>
        </section>
        
        {/* Main Stats Grid */}
        <section className="grid grid-cols-2 gap-3 mb-6">
          <StatCard icon="📍" label="מרחק" value={distKm} unit='ק"מ' highlight />
          <StatCard icon="⏱️" label="זמן" value={duration} />
          <StatCard icon="⚡" label="קצב ממוצע" value={pace} unit="/ק״מ" />
          <StatCard icon="🚀" label="קצב מקסימלי" value={formatPace(workout.distance_cm, Math.floor(workout.duration_sec * 0.85))} unit="/ק״מ" />
        </section>
        
        {/* Elevation Section */}
        {(workout.elevation_gain || workout.elevation_loss) && (
          <section className="bg-gradient-to-br from-[#1e1e3f] to-[#151530] rounded-xl p-4 mb-6 border border-white/5">
            <h3 className="text-gray-400 text-sm mb-3 flex items-center gap-2">⛰️ פרופיל גובה</h3>
            
            {/* Elevation graph placeholder */}
            <div className="h-20 bg-black/20 rounded-lg mb-3 relative overflow-hidden">
              <svg className="w-full h-full" viewBox="0 0 400 80" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="elevGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#00d4ff" stopOpacity="0.4" />
                    <stop offset="100%" stopColor="#00d4ff" stopOpacity="0" />
                  </linearGradient>
                </defs>
                <path d="M 0,80 L 0,50 Q 50,40 100,35 T 200,25 T 300,30 T 400,20 L 400,80 Z" fill="url(#elevGrad)" />
                <path d="M 0,50 Q 50,40 100,35 T 200,25 T 300,30 T 400,20" fill="none" stroke="#00d4ff" strokeWidth="2" />
              </svg>
            </div>
            
            <div className="flex justify-around text-center">
              {workout.elevation_gain && (
                <div>
                  <div className="text-green-400 font-bold">+{workout.elevation_gain} מ'</div>
                  <div className="text-gray-500 text-xs">עלייה</div>
                </div>
              )}
              {workout.elevation_loss && (
                <div>
                  <div className="text-red-400 font-bold">-{Math.abs(workout.elevation_loss)} מ'</div>
                  <div className="text-gray-500 text-xs">ירידה</div>
                </div>
              )}
            </div>
          </section>
        )}
        
        {/* Heart Rate Section */}
        {(workout.avg_hr || workout.max_hr) && (
          <section className="bg-gradient-to-br from-[#1e1e3f] to-[#151530] rounded-xl p-4 mb-6 border border-white/5">
            <h3 className="text-gray-400 text-sm mb-3 flex items-center gap-2">❤️ דופק</h3>
            
            {/* HR graph placeholder */}
            <div className="h-16 bg-black/20 rounded-lg mb-3 relative overflow-hidden">
              <svg className="w-full h-full" viewBox="0 0 400 64" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="hrGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#ef4444" stopOpacity="0.4" />
                    <stop offset="100%" stopColor="#ef4444" stopOpacity="0" />
                  </linearGradient>
                </defs>
                <path d="M 0,64 L 0,45 Q 40,40 80,35 T 160,40 T 240,30 T 320,35 T 400,32 L 400,64 Z" fill="url(#hrGrad)" />
                <path d="M 0,45 Q 40,40 80,35 T 160,40 T 240,30 T 320,35 T 400,32" fill="none" stroke="#ef4444" strokeWidth="2" />
              </svg>
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              {workout.avg_hr && (
                <div className="bg-black/20 rounded-lg p-3 text-center">
                  <div className="text-gray-400 text-xs">ממוצע</div>
                  <div className="text-red-400 text-xl font-bold">{workout.avg_hr} <span className="text-sm text-gray-500">BPM</span></div>
                </div>
              )}
              {workout.max_hr && (
                <div className="bg-black/20 rounded-lg p-3 text-center">
                  <div className="text-gray-400 text-xs">מקסימום</div>
                  <div className="text-red-400 text-xl font-bold">{workout.max_hr} <span className="text-sm text-gray-500">BPM</span></div>
                </div>
              )}
            </div>
          </section>
        )}
        
        {/* Additional Stats */}
        <section className="bg-gradient-to-br from-[#1e1e3f] to-[#151530] rounded-xl p-4 mb-6 border border-white/5">
          <h3 className="text-gray-400 text-sm mb-3 flex items-center gap-2">📊 נתונים נוספים</h3>
          
          <div className="space-y-0">
            {workout.steps && <StatRow icon="👟" label="צעדים" value={workout.steps.toLocaleString()} />}
            {workout.cadence && <StatRow icon="🦶" label="קדנס ממוצע" value={`${workout.cadence} spm`} />}
          </div>
        </section>
        
        {/* Link to Monthly Summary */}
        <a 
          href={`/u/${userId}/monthly`}
          className="block bg-gradient-to-br from-[#1e1e3f] to-[#151530] rounded-xl p-4 mb-6 border border-white/5 hover:border-cyan-400/30 transition-colors"
          data-testid="monthly-summary-link"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-2xl">📅</span>
              <div>
                <div className="font-medium">סיכום חודשי</div>
                <div className="text-gray-500 text-xs">צפה בכל האימונים שלך החודש</div>
              </div>
            </div>
            <span className="text-cyan-400 text-xl">←</span>
          </div>
        </a>
        
        {/* User Stats Summary */}
        {stats && stats.total_workouts > 1 && (
          <section className="bg-gradient-to-br from-[#1e1e3f] to-[#151530] rounded-xl p-4 mb-6 border border-white/5">
            <h3 className="text-gray-400 text-sm mb-3 flex items-center gap-2">📈 סה"כ</h3>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div>
                <div className="text-cyan-400 text-xl font-bold">{stats.total_workouts}</div>
                <div className="text-gray-500 text-xs">אימונים</div>
              </div>
              <div>
                <div className="text-cyan-400 text-xl font-bold">{stats.total_distance_km}</div>
                <div className="text-gray-500 text-xs">ק"מ</div>
              </div>
              <div>
                <div className="text-cyan-400 text-xl font-bold">{Math.round(stats.total_duration_min)}</div>
                <div className="text-gray-500 text-xs">דקות</div>
              </div>
            </div>
          </section>
        )}
        
        {/* Share Button */}
        <section className="text-center py-6">
          <button
            onClick={shareToWhatsApp}
            className="bg-gradient-to-r from-[#25D366] to-[#128C7E] text-white px-8 py-4 rounded-full text-lg font-bold flex items-center gap-3 mx-auto shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition-all"
            data-testid="share-whatsapp-btn"
          >
            <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
            </svg>
            שתף ב-WhatsApp
          </button>
          <p className="text-gray-500 text-sm mt-3">📲 בחר איש קשר או שלח לעצמך</p>
        </section>
        
        {/* Footer */}
        <footer className="text-center py-6 text-gray-500 text-sm">
          <div className="text-cyan-400 font-bold text-base">FitBeat</div>
          <div>Powered by Garmin Fenix 8 Solar</div>
          <div className="text-xs mt-2 text-gray-600">
            מזהה: <span className="font-mono text-cyan-400/60">{userId}</span>
          </div>
        </footer>
      </div>
    </div>
  );
}

// Stat Card Component
function StatCard({ icon, label, value, unit, highlight }) {
  return (
    <div className="bg-gradient-to-br from-[#1e1e3f] to-[#151530] rounded-xl p-4 border border-white/5">
      <div className="text-xl mb-2">{icon}</div>
      <div className="text-gray-400 text-xs mb-1">{label}</div>
      <div className={`text-2xl font-bold ${highlight ? 'text-cyan-400' : 'text-white'}`}>
        {value}
        {unit && <span className="text-sm text-gray-500 mr-1">{unit}</span>}
      </div>
    </div>
  );
}

// Stat Row Component
function StatRow({ icon, label, value }) {
  return (
    <div className="flex justify-between py-3 border-b border-white/5 last:border-0">
      <span className="text-gray-400 flex items-center gap-2">
        <span>{icon}</span>
        {label}
      </span>
      <span className="font-bold">{value}</span>
    </div>
  );
}
