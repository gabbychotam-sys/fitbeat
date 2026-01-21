import { useState, useEffect, useCallback, useRef } from "react";
import "@/App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Color definitions
const COLOR_HEX = [
  "#00FF00", // Green
  "#00FFFF", // Cyan
  "#0000FF", // Blue
  "#FF00FF", // Purple
  "#FF0000", // Red
  "#FFA500", // Orange
  "#FFFF00", // Yellow
  "#FF69B4", // Pink
  "#ADFF2F", // Lime
  "#FFFFFF", // White
];

const COLOR_NAMES = [
  ["Green", "ירוק", "Verde", "Vert", "Grün", "绿色"],
  ["Cyan", "טורקיז", "Cian", "Cyan", "Cyan", "青色"],
  ["Blue", "כחול", "Azul", "Bleu", "Blau", "蓝色"],
  ["Purple", "סגול", "Púrpura", "Violet", "Lila", "紫色"],
  ["Red", "אדום", "Rojo", "Rouge", "Rot", "红色"],
  ["Orange", "כתום", "Naranja", "Orange", "Orange", "橙色"],
  ["Yellow", "צהוב", "Amarillo", "Jaune", "Gelb", "黄色"],
  ["Pink", "ורוד", "Rosa", "Rose", "Rosa", "粉色"],
  ["Lime", "ליים", "Lima", "Citron", "Limette", "青柠"],
  ["White", "לבן", "Blanco", "Blanc", "Weiß", "白色"],
];

const LANG_NAMES = ["English", "עברית", "Español", "Français", "Deutsch", "中文"];
const LANG_NAMES_MENU = ["English", "Hebrew", "Spanish", "French", "German", "Chinese"];
const LANG_UNITS = ["mi", "km", "km", "km", "km", "km"];

const TR_MINUTES = ["min", "דקות", "min", "min", "min", "分"];
const TR_WELL_DONE = ["Well done", "כל הכבוד", "¡Bien hecho!", "Bravo", "Gut gemacht", "干得好"];
const TR_HALF_WAY = ["Halfway there", "עברת חצי מהדרך", "A mitad de camino", "À mi-chemin", "Halb geschafft", "到一半了"];
const TR_GOAL_DONE_LINE1 = ["Great job", "יפה מאוד", "Excelente", "Super", "Sehr gut", "太棒了"];
const TR_GOAL_DONE_LINE2 = ["Goal completed", "סיימת את היעד", "Objetivo completado", "Objectif atteint", "Ziel erreicht", "完成目标"];

// Keyboards for each language
const KEYBOARDS = {
  0: [["P","O","I","U","Y","T","R","E","W","Q"],["L","K","J","H","G","F","D","S","A"],["M","N","B","V","C","X","Z"]],
  1: [["ק","ר","א","ט","ו","ן","ם","פ"],["ש","ד","ג","כ","ע","י","ח","ל","ך","ף"],["ז","ס","ב","ה","נ","מ","צ","ת","ץ"]],
  2: [["P","O","I","U","Y","T","R","E","W","Q"],["Ñ","L","K","J","H","G","F","D","S","A"],["M","N","B","V","C","X","Z"]],
  3: [["P","O","I","U","Y","T","R","E","W","Q"],["À","L","K","J","H","G","F","D","S","A"],["M","N","B","V","C","X","Z","É","È"]],
  4: [["P","O","I","U","Y","T","R","E","W","Q"],["Ü","L","K","J","H","G","F","D","S","A"],["M","N","B","V","C","X","Z","Ä","Ö"]],
  5: [["李","王","张","刘","陈","杨"],["赵","黄","周","吴","徐","孙"],["朱","马","胡","郭","林","何"]],
};

// Main Watch Display Component
function WatchDisplay({ state, onZoneClick }) {
  const { lang, color, distanceCm, elapsedWalkSec, goalDist, goalTimeMin } = state;
  const mainColor = COLOR_HEX[color];
  const unit = LANG_UNITS[lang];
  
  // Calculate distance display
  const distKm = lang === 0 ? distanceCm / 160934 : distanceCm / 100000;
  const distStr = distKm.toFixed(2);
  
  // Calculate time display
  const elapsedMin = Math.floor(elapsedWalkSec / 60);
  
  // Progress calculations
  const goalCm = lang === 0 ? goalDist * 160934 : goalDist * 100000;
  const distFrac = goalCm > 0 ? Math.min(distanceCm / goalCm, 1) : 0;
  const goalSec = goalTimeMin * 60;
  const timeFrac = goalSec > 0 ? Math.min(elapsedWalkSec / goalSec, 1) : 0;
  
  // Current time
  const now = new Date();
  const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
  
  // Heart rate (simulated)
  const [heartRate, setHeartRate] = useState(72);
  useEffect(() => {
    const interval = setInterval(() => {
      setHeartRate(prev => Math.max(60, Math.min(180, prev + Math.floor(Math.random() * 11) - 5)));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  // Staircase bar component (RTL)
  const StaircaseBar = ({ frac }) => {
    const filled = Math.ceil(frac * 5);
    const heights = [100, 80, 60, 40, 20];
    return (
      <div className="flex gap-[2px] h-3 items-end justify-end" dir="rtl">
        {heights.map((h, i) => (
          <div
            key={i}
            className="w-8 rounded-sm transition-colors"
            style={{
              height: `${h}%`,
              backgroundColor: i < filled ? mainColor : '#333',
            }}
          />
        ))}
      </div>
    );
  };

  // Runner icon
  const RunnerIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill={mainColor}>
      <circle cx="12" cy="4" r="2" />
      <path d="M13 7h-2v6h2V7z" />
      <path d="M10 13l-2 5h2l2-5h-2z" />
      <path d="M14 11l2 5h-2l-2-5h2z" />
      <path d="M9 9h6v2H9V9z" />
    </svg>
  );

  // Clock icon
  const ClockIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" stroke={mainColor} fill="none" strokeWidth="2">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 6v6" />
      <path d="M12 12h4" />
    </svg>
  );

  // Heart icon
  const HeartIcon = () => (
    <svg width="28" height="28" viewBox="0 0 24 24" fill={mainColor}>
      <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
    </svg>
  );

  return (
    <div 
      className="w-[280px] h-[280px] rounded-full bg-black flex flex-col items-center relative overflow-hidden"
      style={{ boxShadow: `0 0 20px ${mainColor}40` }}
    >
      {/* Time Zone - clickable */}
      <div 
        className="mt-2 cursor-pointer hover:opacity-80 transition-opacity"
        onClick={() => onZoneClick('time')}
        data-testid="time-zone"
      >
        <span className="text-4xl font-bold" style={{ color: mainColor }}>{timeStr}</span>
      </div>
      
      {/* Distance Zone - clickable */}
      <div 
        className="w-full px-5 mt-2 cursor-pointer hover:opacity-80 transition-opacity"
        onClick={() => onZoneClick('distance')}
        data-testid="distance-zone"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-semibold" style={{ color: mainColor }}>{distStr}</span>
            <span className="text-sm" style={{ color: mainColor }}>{unit}</span>
          </div>
          <RunnerIcon />
        </div>
        <div className="mt-1">
          <StaircaseBar frac={distFrac} />
        </div>
      </div>
      
      {/* Time Goal Zone - clickable */}
      <div 
        className="w-full px-5 mt-3 cursor-pointer hover:opacity-80 transition-opacity"
        onClick={() => onZoneClick('timeGoal')}
        data-testid="time-goal-zone"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-semibold" style={{ color: mainColor }}>{elapsedMin}</span>
            <span className="text-sm" style={{ color: mainColor }}>{TR_MINUTES[lang]}</span>
          </div>
          <ClockIcon />
        </div>
        <div className="mt-1">
          <StaircaseBar frac={timeFrac} />
        </div>
      </div>
      
      {/* Heart Rate Zone - clickable */}
      <div 
        className="absolute bottom-8 flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity"
        onClick={() => onZoneClick('hr')}
        data-testid="hr-zone"
      >
        <HeartIcon />
        <span className="text-4xl font-bold" style={{ color: mainColor }}>{heartRate}</span>
      </div>
    </div>
  );
}

// Settings View
function SettingsView({ state, onUpdate, onClose }) {
  const mainColor = COLOR_HEX[state.color];
  
  return (
    <div className="w-[280px] h-[280px] rounded-full bg-black flex flex-col items-center p-4 overflow-hidden">
      <h2 className="text-lg font-bold mb-2" style={{ color: mainColor }}>Settings</h2>
      
      <div className="w-full space-y-2 text-sm px-4">
        {/* Language Row */}
        <div 
          className="flex justify-between items-center py-1 border-b border-gray-700 cursor-pointer hover:bg-gray-900"
          onClick={() => onUpdate('showLangMenu', true)}
          data-testid="settings-language"
        >
          <span className="text-white">Language</span>
          <span className="text-gray-400">{LANG_NAMES_MENU[state.lang]} &gt;</span>
        </div>
        
        {/* Name Row */}
        <div 
          className="flex justify-between items-center py-1 border-b border-gray-700 cursor-pointer hover:bg-gray-900"
          onClick={() => onUpdate('showNameEntry', true)}
          data-testid="settings-name"
        >
          <span className="text-white">Name</span>
          <span className="text-gray-400">{state.userName || '-'} &gt;</span>
        </div>
        
        {/* Color Row */}
        <div 
          className="flex justify-between items-center py-1 border-b border-gray-700 cursor-pointer hover:bg-gray-900"
          onClick={() => onUpdate('showColorMenu', true)}
          data-testid="settings-color"
        >
          <span className="text-white">Color</span>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: mainColor }} />
            <span className="text-gray-400">{COLOR_NAMES[state.color][0]} &gt;</span>
          </div>
        </div>
      </div>
      
      <button 
        className="mt-4 px-8 py-2 rounded-full font-bold text-black"
        style={{ backgroundColor: mainColor }}
        onClick={onClose}
        data-testid="settings-save"
      >
        Save
      </button>
    </div>
  );
}

// Language Menu
function LanguageMenu({ state, onSelect, onClose }) {
  const mainColor = COLOR_HEX[state.color];
  
  return (
    <div className="w-[280px] h-[280px] rounded-full bg-black flex flex-col items-center p-4 overflow-hidden">
      <h2 className="text-lg font-bold mb-2" style={{ color: mainColor }}>Language</h2>
      <div className="w-full space-y-1 text-sm px-4 overflow-y-auto max-h-[200px]">
        {LANG_NAMES_MENU.map((name, i) => (
          <div 
            key={i}
            className={`py-2 px-3 cursor-pointer rounded ${state.lang === i ? 'bg-gray-800' : 'hover:bg-gray-900'}`}
            onClick={() => onSelect(i)}
            data-testid={`lang-option-${i}`}
          >
            <span className="text-white">{name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Color Menu
function ColorMenu({ state, onSelect, onClose }) {
  const mainColor = COLOR_HEX[state.color];
  
  return (
    <div className="w-[280px] h-[280px] rounded-full bg-black flex flex-col items-center p-4 overflow-hidden">
      <h2 className="text-lg font-bold mb-2" style={{ color: mainColor }}>Color</h2>
      <div className="w-full space-y-1 text-sm px-4 overflow-y-auto max-h-[200px]">
        {COLOR_NAMES.map((names, i) => (
          <div 
            key={i}
            className={`py-2 px-3 cursor-pointer rounded flex items-center gap-2 ${state.color === i ? 'bg-gray-800' : 'hover:bg-gray-900'}`}
            onClick={() => onSelect(i)}
            data-testid={`color-option-${i}`}
          >
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: COLOR_HEX[i] }} />
            <span className="text-white">{names[0]}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Max HR Menu
function MaxHRMenu({ state, onSelect, onClose }) {
  const mainColor = COLOR_HEX[state.color];
  const options = ['Auto', '50%', '55%', '60%', '65%', '70%', '75%', '80%', '85%', '90%'];
  
  return (
    <div className="w-[280px] h-[280px] rounded-full bg-black flex flex-col items-center p-4 overflow-hidden">
      <h2 className="text-lg font-bold mb-2" style={{ color: mainColor }}>Max HR</h2>
      <div className="w-full space-y-1 text-sm px-4 overflow-y-auto max-h-[200px]">
        {options.map((opt, i) => (
          <div 
            key={i}
            className={`py-2 px-3 cursor-pointer rounded ${state.hrMode === i ? 'bg-gray-800' : 'hover:bg-gray-900'}`}
            onClick={() => onSelect(i)}
            data-testid={`hr-option-${i}`}
          >
            <span className="text-white">{opt}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Goal Picker (Distance)
function GoalPicker({ state, type, onStart, onClose }) {
  const [goal, setGoal] = useState(type === 'distance' ? state.goalDist : state.goalTimeMin);
  const mainColor = COLOR_HEX[state.color];
  const unit = type === 'distance' ? LANG_UNITS[state.lang] : 'min';
  const min = type === 'distance' ? 1 : 10;
  const max = type === 'distance' ? 20 : 120;
  const step = type === 'distance' ? 1 : 10;
  
  return (
    <div className="w-[280px] h-[280px] rounded-full bg-black flex flex-col items-center justify-center p-4">
      <div className="flex items-center gap-4">
        <div className="flex items-baseline gap-1">
          <span className="text-5xl font-bold text-white">{goal}</span>
          <span className="text-xl" style={{ color: mainColor }}>{unit}</span>
        </div>
        <div className="flex flex-col gap-2">
          <button 
            className="w-10 h-10 flex items-center justify-center"
            onClick={() => setGoal(g => Math.min(max, g + step))}
            data-testid="goal-up"
          >
            <div style={{ 
              width: 0, height: 0, 
              borderLeft: '12px solid transparent', 
              borderRight: '12px solid transparent', 
              borderBottom: `16px solid ${mainColor}` 
            }} />
          </button>
          <button 
            className="w-10 h-10 flex items-center justify-center"
            onClick={() => setGoal(g => Math.max(min, g - step))}
            data-testid="goal-down"
          >
            <div style={{ 
              width: 0, height: 0, 
              borderLeft: '12px solid transparent', 
              borderRight: '12px solid transparent', 
              borderTop: `16px solid ${mainColor}` 
            }} />
          </button>
        </div>
      </div>
      
      <button 
        className="mt-6 px-12 py-3 rounded-full font-bold text-black text-lg"
        style={{ backgroundColor: mainColor }}
        onClick={() => onStart(goal)}
        data-testid="goal-start"
      >
        START
      </button>
    </div>
  );
}

// Name Entry View
function NameEntryView({ state, onSave, onClose }) {
  const [name, setName] = useState(state.userName || '');
  const mainColor = COLOR_HEX[state.color];
  const keyboard = KEYBOARDS[state.lang];
  const isRtl = state.lang === 1; // Hebrew
  
  return (
    <div className="w-[280px] h-[280px] rounded-full bg-black flex flex-col items-center p-3 overflow-hidden">
      {/* Name field with checkmark */}
      <div className="flex items-center w-[200px] h-8 border rounded mt-2" style={{ borderColor: mainColor }}>
        <input 
          className="flex-1 bg-transparent text-white text-center outline-none px-2"
          value={name}
          onChange={e => setName(e.target.value.slice(0, 12))}
          data-testid="name-input"
        />
        <button 
          className="h-full w-8 flex items-center justify-center text-black font-bold"
          style={{ backgroundColor: mainColor }}
          onClick={() => onSave(name)}
          data-testid="name-save"
        >
          V
        </button>
      </div>
      
      {/* Keyboard */}
      <div className="mt-2 space-y-1" style={{ direction: isRtl ? 'rtl' : 'ltr' }}>
        {keyboard.map((row, ri) => (
          <div key={ri} className="flex justify-center gap-[2px]">
            {row.map((key, ki) => (
              <button 
                key={ki}
                className="w-6 h-6 bg-gray-700 rounded text-white text-xs hover:bg-gray-600"
                onClick={() => name.length < 12 && setName(n => n + key)}
                data-testid={`key-${key}`}
              >
                {key}
              </button>
            ))}
          </div>
        ))}
        
        {/* Space and Backspace */}
        <div className="flex justify-center gap-1 mt-1">
          <button 
            className="w-24 h-6 bg-gray-700 rounded text-white text-xs hover:bg-gray-600"
            onClick={() => name.length < 12 && setName(n => n + ' ')}
            data-testid="key-space"
          >
            ␣
          </button>
          <button 
            className="w-12 h-6 bg-gray-700 rounded text-white text-xs hover:bg-gray-600"
            onClick={() => setName(n => n.slice(0, -1))}
            data-testid="key-backspace"
          >
            ←
          </button>
        </div>
      </div>
    </div>
  );
}

// Alert View
function AlertView({ line1, line2, onDismiss }) {
  return (
    <div 
      className="w-[280px] h-[280px] rounded-full bg-black flex flex-col items-center justify-center cursor-pointer"
      onClick={onDismiss}
      data-testid="alert-view"
    >
      <span className="text-2xl font-bold text-white mb-4">{line1}</span>
      <span className="text-lg text-gray-300">{line2}</span>
    </div>
  );
}

// Main Simulator Component
function FitBeatSimulator() {
  const [state, setState] = useState({
    lang: 0,
    color: 0,
    userName: '',
    goalDist: 5,
    goalTimeMin: 30,
    hrMode: 0,
    maxHr: 190,
    distGoalActive: false,
    timeGoalActive: false,
    elapsedWalkSec: 0,
    distanceCm: 0,
    distHalfwayShown: false,
    distGoalShown: false,
    timeHalfwayShown: false,
    timeGoalShown: false,
  });
  
  const [view, setView] = useState('main'); // main, settings, langMenu, colorMenu, hrMenu, distPicker, timePicker, nameEntry, alert
  const [alert, setAlert] = useState(null);
  const timerRef = useRef(null);
  
  // Load state from backend
  useEffect(() => {
    axios.get(`${API}/fitbeat/state`).then(res => {
      if (res.data) setState(s => ({ ...s, ...res.data }));
    }).catch(console.error);
  }, []);
  
  // Save state to backend
  const saveState = useCallback(async (newState) => {
    try {
      await axios.post(`${API}/fitbeat/state`, newState);
    } catch (e) {
      console.error('Failed to save state:', e);
    }
  }, []);
  
  // Timer for time goal
  useEffect(() => {
    if (state.timeGoalActive && view === 'main') {
      timerRef.current = setInterval(() => {
        setState(s => {
          const newSec = s.elapsedWalkSec + 1;
          const goalSec = s.goalTimeMin * 60;
          const halfway = goalSec / 2;
          
          let newState = { ...s, elapsedWalkSec: newSec };
          
          // Check 50% alert
          if (!s.timeHalfwayShown && newSec >= halfway && newSec < goalSec) {
            newState.timeHalfwayShown = true;
            setAlert({ 
              line1: TR_WELL_DONE[s.lang] + (s.userName ? ` ${s.userName}!` : '!'),
              line2: TR_HALF_WAY[s.lang]
            });
            setView('alert');
          }
          
          // Check goal completion
          if (!s.timeGoalShown && newSec >= goalSec) {
            newState.timeGoalShown = true;
            newState.timeGoalActive = false;
            newState.elapsedWalkSec = 0;
            setAlert({ 
              line1: TR_GOAL_DONE_LINE1[s.lang] + (s.userName ? ` ${s.userName}!` : '!'),
              line2: TR_GOAL_DONE_LINE2[s.lang]
            });
            setView('alert');
          }
          
          return newState;
        });
      }, 1000);
      
      return () => clearInterval(timerRef.current);
    }
  }, [state.timeGoalActive, view]);
  
  // Handle zone clicks
  const handleZoneClick = (zone) => {
    switch (zone) {
      case 'time': setView('settings'); break;
      case 'distance': setView('distPicker'); break;
      case 'timeGoal': setView('timePicker'); break;
      case 'hr': setView('hrMenu'); break;
      default: break;
    }
  };
  
  // Update state helper
  const updateState = (key, value) => {
    if (key === 'showLangMenu') { setView('langMenu'); return; }
    if (key === 'showColorMenu') { setView('colorMenu'); return; }
    if (key === 'showNameEntry') { setView('nameEntry'); return; }
    
    setState(s => {
      const newState = { ...s, [key]: value };
      saveState(newState);
      return newState;
    });
  };
  
  // Start distance goal
  const startDistanceGoal = (goal) => {
    setState(s => {
      const newState = {
        ...s,
        goalDist: goal,
        distGoalActive: true,
        distanceCm: 0,
        distHalfwayShown: false,
        distGoalShown: false,
      };
      saveState(newState);
      return newState;
    });
    setView('main');
  };
  
  // Start time goal
  const startTimeGoal = (goal) => {
    setState(s => {
      const newState = {
        ...s,
        goalTimeMin: goal,
        timeGoalActive: true,
        elapsedWalkSec: 0,
        timeHalfwayShown: false,
        timeGoalShown: false,
      };
      saveState(newState);
      return newState;
    });
    setView('main');
  };
  
  // Test controls
  const addDistance = (cm) => {
    setState(s => {
      const newDist = s.distanceCm + cm;
      const goalCm = s.lang === 0 ? s.goalDist * 160934 : s.goalDist * 100000;
      const halfway = goalCm / 2;
      
      let newState = { ...s, distanceCm: newDist };
      
      // Check 50% alert
      if (s.distGoalActive && !s.distHalfwayShown && newDist >= halfway && newDist < goalCm) {
        newState.distHalfwayShown = true;
        setAlert({ 
          line1: TR_WELL_DONE[s.lang] + (s.userName ? ` ${s.userName}!` : '!'),
          line2: TR_HALF_WAY[s.lang]
        });
        setView('alert');
      }
      
      // Check goal completion
      if (s.distGoalActive && !s.distGoalShown && newDist >= goalCm) {
        newState.distGoalShown = true;
        setAlert({ 
          line1: TR_GOAL_DONE_LINE1[s.lang] + (s.userName ? ` ${s.userName}!` : '!'),
          line2: TR_GOAL_DONE_LINE2[s.lang]
        });
        setView('alert');
        // Distance continues! No reset!
      }
      
      saveState(newState);
      return newState;
    });
  };
  
  const resetAll = () => {
    const defaultState = {
      lang: state.lang,
      color: state.color,
      userName: state.userName,
      goalDist: 5,
      goalTimeMin: 30,
      hrMode: 0,
      maxHr: 190,
      distGoalActive: false,
      timeGoalActive: false,
      elapsedWalkSec: 0,
      distanceCm: 0,
      distHalfwayShown: false,
      distGoalShown: false,
      timeHalfwayShown: false,
      timeGoalShown: false,
    };
    setState(defaultState);
    saveState(defaultState);
    setView('main');
  };
  
  const simulateExit = () => {
    // On exit: Time resets, Distance persists!
    setState(s => {
      const newState = {
        ...s,
        timeGoalActive: false,
        elapsedWalkSec: 0,
        timeHalfwayShown: false,
        timeGoalShown: false,
        // Distance persists!
      };
      saveState(newState);
      return newState;
    });
  };
  
  // Render current view
  const renderView = () => {
    switch (view) {
      case 'settings':
        return <SettingsView state={state} onUpdate={updateState} onClose={() => setView('main')} />;
      case 'langMenu':
        return <LanguageMenu state={state} onSelect={(i) => { updateState('lang', i); setView('settings'); }} onClose={() => setView('settings')} />;
      case 'colorMenu':
        return <ColorMenu state={state} onSelect={(i) => { updateState('color', i); setView('settings'); }} onClose={() => setView('settings')} />;
      case 'hrMenu':
        return <MaxHRMenu state={state} onSelect={(i) => { updateState('hrMode', i); setView('main'); }} onClose={() => setView('main')} />;
      case 'distPicker':
        return <GoalPicker state={state} type="distance" onStart={startDistanceGoal} onClose={() => setView('main')} />;
      case 'timePicker':
        return <GoalPicker state={state} type="time" onStart={startTimeGoal} onClose={() => setView('main')} />;
      case 'nameEntry':
        return <NameEntryView state={state} onSave={(name) => { updateState('userName', name); setView('settings'); }} onClose={() => setView('settings')} />;
      case 'alert':
        return <AlertView line1={alert?.line1} line2={alert?.line2} onDismiss={() => { setAlert(null); setView('main'); }} />;
      default:
        return <WatchDisplay state={state} onZoneClick={handleZoneClick} />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col items-center py-8">
      <h1 className="text-3xl font-bold text-white mb-2">🎽 FitBeat v4.3.2 Simulator</h1>
      <p className="text-gray-400 mb-6">Garmin Fenix 8 Solar 51mm (280×280px)</p>
      
      {/* Watch Display */}
      <div className="mb-8">
        {renderView()}
      </div>
      
      {/* Status Indicators */}
      <div className="flex gap-4 mb-6">
        <div className={`px-3 py-1 rounded-full text-sm ${state.distGoalActive ? 'bg-green-600 text-white' : 'bg-gray-700 text-gray-400'}`}>
          🏃 Distance: {state.distGoalActive ? 'ACTIVE' : 'OFF'}
        </div>
        <div className={`px-3 py-1 rounded-full text-sm ${state.timeGoalActive ? 'bg-green-600 text-white' : 'bg-gray-700 text-gray-400'}`}>
          ⏱️ Time: {state.timeGoalActive ? 'ACTIVE' : 'OFF'}
        </div>
      </div>
      
      {/* Test Controls */}
      <div className="bg-gray-800 rounded-lg p-4 w-[400px]">
        <h3 className="text-white font-bold mb-3">🧪 Test Controls</h3>
        <div className="grid grid-cols-3 gap-2">
          <button 
            className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded text-sm"
            onClick={resetAll}
            data-testid="btn-reset"
          >
            🔄 Reset
          </button>
          <button 
            className="bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded text-sm"
            onClick={() => addDistance(50000)}
            data-testid="btn-add-500m"
          >
            +500m
          </button>
          <button 
            className="bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded text-sm"
            onClick={() => addDistance(100000)}
            data-testid="btn-add-1km"
          >
            +1km
          </button>
          <button 
            className="bg-yellow-600 hover:bg-yellow-700 text-white px-3 py-2 rounded text-sm"
            onClick={() => setState(s => ({ ...s, elapsedWalkSec: s.elapsedWalkSec + 30 }))}
            data-testid="btn-add-30s"
          >
            +30s
          </button>
          <button 
            className="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded text-sm"
            onClick={simulateExit}
            data-testid="btn-exit"
          >
            🚪 Exit App
          </button>
          <button 
            className="bg-purple-600 hover:bg-purple-700 text-white px-3 py-2 rounded text-sm"
            onClick={() => setView('main')}
            data-testid="btn-back"
          >
            ⬅️ Back
          </button>
        </div>
        
        {/* Current State Debug */}
        <div className="mt-4 text-xs text-gray-400 font-mono">
          <div>Distance: {(state.distanceCm / 100000).toFixed(2)} km | Goal: {state.goalDist} {LANG_UNITS[state.lang]}</div>
          <div>Time: {Math.floor(state.elapsedWalkSec / 60)}:{String(state.elapsedWalkSec % 60).padStart(2, '0')} | Goal: {state.goalTimeMin} min</div>
          <div>Lang: {LANG_NAMES_MENU[state.lang]} | Color: {COLOR_NAMES[state.color][0]} | Name: {state.userName || '-'}</div>
        </div>
      </div>
      
      {/* Download Links */}
      <div className="mt-8 bg-gray-800 rounded-lg p-4 w-[400px]">
        <h3 className="text-white font-bold mb-3">📥 Downloads</h3>
        <a 
          href={`${API}/download/fitbeat`}
          className="block bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-center"
          download="fitbeat.zip"
          data-testid="download-zip"
        >
          📦 Download FitBeat.zip
        </a>
        <p className="text-gray-400 text-xs mt-2">Contains all source files (.mc) ready for Garmin SDK build</p>
        
        <div className="mt-4 p-3 bg-gray-900 rounded text-xs text-gray-400 font-mono">
          <p className="text-yellow-400 mb-1">🔨 Build Command (CMD):</p>
          <code className="text-green-400 break-all">
            cd "C:\Users\gabbyc\Desktop\fitbeat\fitbeat"<br/>
            java -jar "%APPDATA%\Garmin\ConnectIQ\Sdks\connectiq-sdk-win-8.4.0-2025-12-03-5122605dc\bin\monkeybrains.jar" -o FitBeat.prg -f monkey.jungle -y developer_key.der -d fenix8solar51mm
          </code>
        </div>
      </div>
      
      {/* Feature Summary */}
      <div className="mt-8 bg-gray-800 rounded-lg p-4 w-[400px]">
        <h3 className="text-white font-bold mb-3">✨ v4.3.2 Features</h3>
        <ul className="text-gray-300 text-sm space-y-1">
          <li>✅ Separate goals - Distance & Time work independently</li>
          <li>✅ Time goal counts every second from START</li>
          <li>✅ Distance goal doesn't reset time</li>
          <li>✅ 50% alerts (🎈) and completion alerts (👏)</li>
          <li>✅ All icons change to selected color</li>
          <li>✅ Language-specific keyboard (Hebrew/English/Spanish/French/German/Chinese)</li>
          <li>✅ Garmin Menu2 for settings</li>
          <li>✅ On exit: Time resets, Distance persists</li>
        </ul>
      </div>
    </div>
  );
}

function App() {
  return <FitBeatSimulator />;
}

export default App;
