import { useState, useEffect } from "react";
import { useParams, useSearchParams } from "react-router-dom";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Format duration to hours and minutes
function formatDurationLong(minutes) {
  const hrs = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);
  
  if (hrs > 0) {
    return `${hrs} שעות ו-${mins} דקות`;
  }
  return `${mins} דקות`;
}

// Format date in Hebrew
function formatDateHebrew(dateStr) {
  const date = new Date(dateStr);
  const day = date.getDate();
  const hours = String(date.getHours()).padStart(2, '0');
  const mins = String(date.getMinutes()).padStart(2, '0');
  return `${day} • ${hours}:${mins}`;
}

export default function MonthlyPage() {
  const { userId } = useParams();
  const [searchParams] = useSearchParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const year = searchParams.get('year');
  const month = searchParams.get('month');
  
  useEffect(() => {
    async function fetchData() {
      try {
        let url = `${API}/user/${userId}/monthly`;
        const params = new URLSearchParams();
        if (year) params.append('year', year);
        if (month) params.append('month', month);
        if (params.toString()) url += `?${params.toString()}`;
        
        const response = await fetch(url);
        
        if (response.status === 404) {
          setError("לא נמצא משתמש");
          setLoading(false);
          return;
        }
        
        const result = await response.json();
        setData(result);
        setLoading(false);
      } catch (err) {
        setError("שגיאה בטעינת הנתונים");
        setLoading(false);
      }
    }
    
    fetchData();
  }, [userId, year, month]);
  
  const shareToWhatsApp = () => {
    if (!data) return;
    
    const userName = data.user_name || "משתמש";
    
    let text = `📅 סיכום חודשי - ${data.month_name} ${data.year}\n`;
    text += `👤 ${userName}\n\n`;
    text += `🏃 ${data.total_workouts} אימונים\n`;
    text += `📍 ${data.total_distance_km} ק"מ סה"כ\n`;
    text += `⏱️ ${formatDurationLong(data.total_duration_min)}\n`;
    
    if (data.total_elevation_gain > 0) {
      text += `⛰️ ${data.total_elevation_gain} מ' עלייה\n`;
    }
    
    if (data.avg_hr) {
      text += `❤️ דופק ממוצע: ${data.avg_hr} BPM\n`;
    }
    
    if (data.total_steps > 0) {
      text += `👟 ${data.total_steps.toLocaleString()} צעדים\n`;
    }
    
    if (data.comparison) {
      const sign = data.comparison.distance_change_percent >= 0 ? '+' : '';
      text += `\n📈 ${sign}${data.comparison.distance_change_percent}% מהחודש הקודם`;
    }
    
    text += `\n\n🔗 צפה בסיכום המלא:\n${window.location.href}`;
    
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
          <div className="text-6xl mb-4">📅</div>
          <h1 className="text-white text-2xl font-bold mb-2">FitBeat</h1>
          <p className="text-gray-400">{error}</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-[#1a1a2e] to-[#16213e] text-white p-4" dir="rtl">
      <div className="max-w-md mx-auto">
        {/* Header */}
        <header className="text-center py-6 border-b border-white/10 mb-6">
          <h1 className="text-2xl font-bold text-cyan-400 mb-1">📅 סיכום חודשי</h1>
          <p className="text-xl text-white">{data.month_name} {data.year}</p>
          {data.user_name && (
            <p className="text-gray-400 mt-2">{data.user_name}</p>
          )}
        </header>
        
        {/* Main Stats */}
        <section className="bg-gradient-to-br from-[#1e1e3f] to-[#151530] rounded-2xl p-6 mb-6 border border-white/5">
          <div className="grid grid-cols-2 gap-6">
            {/* Workouts Count */}
            <div className="text-center">
              <div className="text-5xl font-bold text-cyan-400">{data.total_workouts}</div>
              <div className="text-gray-400 mt-1">אימונים</div>
            </div>
            
            {/* Total Distance */}
            <div className="text-center">
              <div className="text-5xl font-bold text-green-400">{data.total_distance_km}</div>
              <div className="text-gray-400 mt-1">ק"מ סה"כ</div>
            </div>
          </div>
          
          {/* Comparison with previous month */}
          {data.comparison && (
            <div className="mt-6 pt-4 border-t border-white/10 text-center">
              <div className={`text-lg font-bold ${data.comparison.distance_change_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {data.comparison.distance_change_percent >= 0 ? '📈' : '📉'} 
                {data.comparison.distance_change_percent >= 0 ? '+' : ''}{data.comparison.distance_change_percent}%
              </div>
              <div className="text-gray-500 text-sm">בהשוואה לחודש הקודם</div>
            </div>
          )}
        </section>
        
        {/* Detailed Stats Grid */}
        <section className="grid grid-cols-2 gap-3 mb-6">
          <StatCard 
            icon="⏱️" 
            label="זמן כולל" 
            value={formatDurationLong(data.total_duration_min)} 
          />
          <StatCard 
            icon="❤️" 
            label="דופק ממוצע" 
            value={data.avg_hr ? `${data.avg_hr} BPM` : '--'} 
          />
          <StatCard 
            icon="⛰️" 
            label="עלייה כוללת" 
            value={`${data.total_elevation_gain} מ'`} 
          />
          <StatCard 
            icon="👟" 
            label="צעדים" 
            value={data.total_steps > 0 ? data.total_steps.toLocaleString() : '--'} 
          />
        </section>
        
        {/* Workouts List */}
        {data.workouts && data.workouts.length > 0 && (
          <section className="bg-gradient-to-br from-[#1e1e3f] to-[#151530] rounded-xl p-4 mb-6 border border-white/5">
            <h3 className="text-gray-400 text-sm mb-4 flex items-center gap-2">🏃 אימונים בחודש</h3>
            
            <div className="space-y-3">
              {data.workouts.map((workout, index) => (
                <WorkoutRow key={workout.id || index} workout={workout} userId={userId} />
              ))}
            </div>
          </section>
        )}
        
        {/* No workouts message */}
        {data.total_workouts === 0 && (
          <section className="bg-gradient-to-br from-[#1e1e3f] to-[#151530] rounded-xl p-8 mb-6 border border-white/5 text-center">
            <div className="text-4xl mb-3">🏃‍♂️</div>
            <p className="text-gray-400">אין אימונים בחודש זה</p>
            <p className="text-gray-500 text-sm mt-2">צא להתאמן והנתונים יופיעו כאן!</p>
          </section>
        )}
        
        {/* Share Button */}
        {data.total_workouts > 0 && (
          <section className="text-center py-6">
            <button
              onClick={shareToWhatsApp}
              className="bg-gradient-to-r from-[#25D366] to-[#128C7E] text-white px-8 py-4 rounded-full text-lg font-bold flex items-center gap-3 mx-auto shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition-all"
              data-testid="share-monthly-whatsapp-btn"
            >
              <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
              </svg>
              שתף ב-WhatsApp
            </button>
            <p className="text-gray-500 text-sm mt-3">📲 שתף את ההישגים שלך!</p>
          </section>
        )}
        
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
function StatCard({ icon, label, value }) {
  return (
    <div className="bg-gradient-to-br from-[#252550] to-[#1a1a3a] rounded-xl p-4 border border-white/5">
      <div className="text-xl mb-2">{icon}</div>
      <div className="text-gray-400 text-xs mb-1">{label}</div>
      <div className="text-lg font-bold text-white">{value}</div>
    </div>
  );
}

// Workout Row Component
function WorkoutRow({ workout, userId }) {
  const distKm = (workout.distance_cm / 100000).toFixed(2);
  const durationMin = Math.floor(workout.duration_sec / 60);
  
  return (
    <a 
      href={`/u/${userId}`}
      className="flex items-center justify-between p-3 bg-black/20 rounded-lg hover:bg-black/30 transition-colors"
    >
      <div className="flex items-center gap-3">
        <div className="text-2xl">🏃</div>
        <div>
          <div className="font-medium">{distKm} ק"מ</div>
          <div className="text-gray-500 text-xs">{formatDateHebrew(workout.timestamp)}</div>
        </div>
      </div>
      <div className="text-left">
        <div className="text-cyan-400 font-bold">{durationMin} דק'</div>
        {workout.avg_hr && (
          <div className="text-gray-500 text-xs">❤️ {workout.avg_hr}</div>
        )}
      </div>
    </a>
  );
}
