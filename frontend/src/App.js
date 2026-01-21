import { useState, useEffect, useCallback, useRef } from "react";
import "@/App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Color definitions - exact hex values from spec
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
const LANG_NAMES_MENU = ["English", "עברית", "Español", "Français", "Deutsch", "中文"];
const LANG_UNITS = ["mi", "km", "km", "km", "km", "km"];

const TR_MINUTES = ["min", "דקות", "min", "min", "min", "分钟"];
const TR_KM = ["km", 'ק"מ', "km", "km", "km", "公里"];
const TR_STEPS = ["steps", "צעדים", "pasos", "pas", "Schritte", "步"];

// Alert messages - 3 lines format
// Line 1: Name greeting
// Line 2: Action message
// Line 3: Details
const TR_REST_NOW = ["Take a rest", "תנוח קצת", "Descansa", "Repose-toi", "Ruh dich aus", "休息一下"];
const TR_HR_EXCEEDED = ["Heart rate exceeded", "עברת את הדופק שהגדרת", "FC superada", "FC dépassée", "HF überschritten", "心率超标"];
const TR_KEEP_GOING = ["Keep going!", "המשך!", "¡Sigue!", "Continue!", "Weiter!", "继续!"];
const TR_HALF_WAY = ["Halfway there", "עברת חצי מהדרך", "A mitad de camino", "À mi-chemin", "Halb geschafft", "到一半了"];
const TR_GREAT_JOB = ["Great job!", "יפה מאוד!", "¡Excelente!", "Super!", "Sehr gut!", "太棒了!"];
const TR_GOAL_COMPLETED = ["Goal completed", "סיימת את היעד", "Objetivo completado", "Objectif atteint", "Ziel erreicht", "完成目标"];
const TR_START = ["START", "התחל", "INICIAR", "DÉMARRER", "STARTEN", "开始"];
const TR_MAX_HR = ["Max Heart Rate", "דופק מקסימלי", "FC Máxima", "FC Max", "Max HF", "最大心率"];
const TR_AUTO = ["Auto", "אוטו", "Auto", "Auto", "Auto", "自动"];

// QWERTY REVERSED keyboards for each language (as per Garmin spec!)
const KEYBOARDS = {
  0: [["P","O","I","U","Y","T","R","E","W","Q"],["L","K","J","H","G","F","D","S","A"],["M","N","B","V","C","X","Z"]], // English
  1: [["ק","ר","א","ט","ו","ן","ם","פ"],["ש","ד","ג","כ","ע","י","ח","ל","ך","ף"],["ז","ס","ב","ה","נ","מ","צ","ת","ץ"]], // Hebrew
  2: [["P","O","I","U","Y","T","R","E","W","Q"],["Ñ","L","K","J","H","G","F","D","S","A"],["M","N","B","V","C","X","Z"]], // Spanish
  3: [["P","O","I","U","Y","T","R","E","W","Q"],["À","L","K","J","H","G","F","D","S","A"],["M","N","B","V","C","X","Z","É","È"]], // French
  4: [["P","O","I","U","Y","T","R","E","W","Q"],["Ü","L","K","J","H","G","F","D","S","A"],["M","N","B","V","C","X","Z","Ä","Ö"]], // German
  5: [["李","王","张","刘","陈","杨"],["赵","黄","周","吴","徐","孙"],["朱","马","胡","郭","林","何"]], // Chinese
};

// ═══════════════════════════════════════════════════════════════
// MAIN WATCH DISPLAY - Garmin Font Sizes per spec
// ═══════════════════════════════════════════════════════════════
function WatchDisplay({ state, onZoneClick }) {
  const { lang, color, distanceCm, elapsedWalkSec, goalDist, goalTimeMin } = state;
  const mainColor = COLOR_HEX[color];
  const unit = TR_KM[lang];  // Use translated unit!
  
  // Calculate distance display
  const distKm = lang === 0 ? distanceCm / 160934 : distanceCm / 100000;
  const distStr = distKm.toFixed(2);
  
  // Calculate time display - minutes:seconds format
  const elapsedMin = Math.floor(elapsedWalkSec / 60);
  const elapsedSec = elapsedWalkSec % 60;
  const timeDisplayStr = `${elapsedMin}:${String(elapsedSec).padStart(2, '0')}`;
  
  // Progress calculations
  const goalCm = lang === 0 ? goalDist * 160934 : goalDist * 100000;
  const distFrac = goalCm > 0 ? Math.min(distanceCm / goalCm, 1) : 0;
  const goalSec = goalTimeMin * 60;
  const timeFrac = goalSec > 0 ? Math.min(elapsedWalkSec / goalSec, 1) : 0;
  
  // Current time
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const interval = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);
  const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
  
  // Heart rate (simulated)
  const [heartRate, setHeartRate] = useState(72);
  useEffect(() => {
    const interval = setInterval(() => {
      setHeartRate(prev => Math.max(60, Math.min(180, prev + Math.floor(Math.random() * 11) - 5)));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  // Staircase bar component (RTL - RIGHT to LEFT: tallest on RIGHT, shortest on LEFT)
  // Progress fills from RIGHT to LEFT
  const StaircaseBar = ({ frac }) => {
    const segCount = 5;
    const filled = Math.ceil(frac * segCount);
    // Heights: index 0 = leftmost (shortest), index 4 = rightmost (tallest)
    const heights = [20, 40, 60, 80, 100];
    
    return (
      <div className="flex gap-[4px] h-[12px] items-end" style={{ width: '220px', direction: 'ltr' }}>
        {heights.map((h, i) => {
          // Fill from RIGHT to LEFT: segment 4 fills first, then 3, 2, 1, 0
          const segmentIndex = segCount - 1 - i; // reverse index for fill check
          const isFilled = segmentIndex < filled;
          
          return (
            <div
              key={i}
              className="flex-1 rounded-sm transition-colors"
              style={{
                height: `${h}%`,
                backgroundColor: isFilled ? mainColor : '#444',
              }}
            />
          );
        })}
      </div>
    );
  };

  // Runner icon 🏃 - SVG that uses mainColor
  const RunnerIcon = () => (
    <svg width="28" height="28" viewBox="0 0 24 24" fill={mainColor}>
      <circle cx="14" cy="4" r="2.5"/>
      <path d="M16.5 7.5l-3 3-2-2-4 4 1.5 1.5 2.5-2.5 2 2 4.5-4.5z"/>
      <path d="M8 14l-2 8h2.5l1.5-6 2 2v4h2.5v-6l-3-3-1-4"/>
    </svg>
  );

  // Clock icon ⏱️ - SVG that uses mainColor
  const ClockIcon = () => (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke={mainColor} strokeWidth="2">
      <circle cx="12" cy="12" r="9"/>
      <path d="M12 6v6l4 2"/>
    </svg>
  );

  return (
    <div 
      className="relative bg-black overflow-hidden"
      style={{ 
        width: '280px', 
        height: '280px', 
        borderRadius: '50%',
        boxShadow: `0 0 30px ${mainColor}40`
      }}
    >
      {/* TIME ZONE - top: 3%, FONT_NUMBER_MEDIUM: 69px */}
      <div 
        className="absolute left-1/2 -translate-x-1/2 cursor-pointer hover:opacity-80"
        style={{ top: '3%', zIndex: 10 }}
        onClick={() => onZoneClick('time')}
        data-testid="time-zone"
      >
        <span style={{ 
          fontSize: '52px', 
          fontWeight: 'bold', 
          color: mainColor,
          fontFamily: 'monospace'
        }}>
          {timeStr}
        </span>
      </div>
      
      {/* DISTANCE + TIME BARS - centered at 52% (moved down to be closer together) */}
      <div 
        className="absolute left-1/2 -translate-x-1/2 -translate-y-1/2"
        style={{ top: '52%', width: '220px' }}
        onClick={() => onZoneClick('distance')}
        data-testid="distance-zone"
      >
        {/* Distance row */}
        <div className="flex items-center justify-between mb-1 cursor-pointer" onClick={() => onZoneClick('distance')}>
          <div className="flex items-baseline gap-1">
            {/* FONT_MEDIUM: 32px for numbers */}
            <span style={{ fontSize: '32px', fontWeight: '600', color: mainColor }}>{distStr}</span>
            {/* FONT_XTINY: 18px for labels */}
            <span style={{ fontSize: '18px', color: '#888' }}>{unit}</span>
          </div>
          <RunnerIcon />
        </div>
        <StaircaseBar frac={distFrac} />
        
        {/* Time row - closer to distance (mt-1 instead of mt-2) */}
        <div 
          className="flex items-center justify-between mt-1 mb-1 cursor-pointer"
          onClick={(e) => { e.stopPropagation(); onZoneClick('timeGoal'); }}
          data-testid="time-goal-zone"
        >
          <div className="flex items-baseline gap-1">
            {/* Show minutes:seconds format */}
            <span style={{ fontSize: '32px', fontWeight: '600', color: mainColor }}>{timeDisplayStr}</span>
            <span style={{ fontSize: '18px', color: '#888' }}>{TR_MINUTES[lang]}</span>
          </div>
          <ClockIcon />
        </div>
        <StaircaseBar frac={timeFrac} />
      </div>
      
      {/* HEART RATE - bottom: 2% (moved down), number also colored! */}
      <div 
        className="absolute left-1/2 -translate-x-1/2 flex items-center gap-2 cursor-pointer hover:opacity-80"
        style={{ bottom: '2%' }}
        onClick={() => onZoneClick('hr')}
        data-testid="hr-zone"
      >
        {/* Heart SVG icon - uses mainColor */}
        <svg width="32" height="32" viewBox="0 0 24 24" fill={mainColor}>
          <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
        </svg>
        {/* Heart rate NUMBER also uses mainColor! */}
        <span style={{ fontSize: '48px', fontWeight: 'bold', color: mainColor }}>{heartRate}</span>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// SETTINGS VIEW - fully translated to selected language
// ═══════════════════════════════════════════════════════════════
function SettingsView({ state, onUpdate, onClose }) {
  const mainColor = COLOR_HEX[state.color];
  const lang = state.lang;
  
  // Translations for Settings
  const TR_SETTINGS = ["Settings", "הגדרות", "Ajustes", "Paramètres", "Einstellungen", "设置"];
  const TR_NAME = ["Name", "שם", "Nombre", "Nom", "Name", "名称"];
  const TR_COLOR = ["Color", "צבע", "Color", "Couleur", "Farbe", "颜色"];
  const TR_SAVE = ["Save", "שמור", "Guardar", "Sauvegarder", "Speichern", "保存"];
  
  return (
    <div 
      className="relative bg-black overflow-hidden flex flex-col items-center"
      style={{ width: '280px', height: '280px', borderRadius: '50%' }}
    >
      {/* Title - translated */}
      <div style={{ marginTop: '5%' }}>
        <span style={{ fontSize: '26px', fontWeight: 'bold', color: mainColor }}>{TR_SETTINGS[lang]}</span>
      </div>
      
      {/* Settings list */}
      <div 
        className="absolute left-1/2 -translate-x-1/2"
        style={{ top: '18%', width: '200px' }}
      >
        {/* Language Row - always "Language" for accessibility */}
        <div 
          className="flex justify-between items-center py-1 border-b border-gray-700 cursor-pointer hover:bg-gray-900 rounded"
          onClick={() => onUpdate('showLangMenu', true)}
          data-testid="settings-language"
        >
          <span style={{ fontSize: '20px', color: '#fff' }}>Language</span>
          <span style={{ fontSize: '16px', color: '#888' }}>{LANG_NAMES_MENU[lang]} &gt;</span>
        </div>
        
        {/* Name Row - translated */}
        <div 
          className="flex justify-between items-center py-1 border-b border-gray-700 cursor-pointer hover:bg-gray-900 rounded"
          onClick={() => onUpdate('showNameEntry', true)}
          data-testid="settings-name"
        >
          <span style={{ fontSize: '20px', color: '#fff' }}>{TR_NAME[lang]}</span>
          <span style={{ fontSize: '16px', color: '#888' }}>{state.userName || '-'} &gt;</span>
        </div>
        
        {/* Color Row - translated */}
        <div 
          className="flex justify-between items-center py-1 border-b border-gray-700 cursor-pointer hover:bg-gray-900 rounded"
          onClick={() => onUpdate('showColorMenu', true)}
          data-testid="settings-color"
        >
          <span style={{ fontSize: '20px', color: '#fff' }}>{TR_COLOR[lang]}</span>
          <div className="flex items-center gap-2">
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: mainColor }} />
            {/* Color name in selected language */}
            <span style={{ fontSize: '16px', color: '#888' }}>{COLOR_NAMES[state.color][lang]} &gt;</span>
          </div>
        </div>
      </div>
      
      {/* Save button - translated */}
      <button 
        className="absolute left-1/2 -translate-x-1/2"
        style={{ 
          bottom: '12%',
          fontSize: '18px',
          fontWeight: 'bold',
          backgroundColor: mainColor,
          color: '#000',
          padding: '6px 24px',
          borderRadius: '20px',
          border: 'none',
          cursor: 'pointer'
        }}
        onClick={onClose}
        data-testid="settings-save"
      >
        {TR_SAVE[lang]} ✓
      </button>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// LANGUAGE MENU - per spec
// ═══════════════════════════════════════════════════════════════
function LanguageMenu({ state, onSelect, onClose }) {
  const mainColor = COLOR_HEX[state.color];
  
  return (
    <div 
      className="relative bg-black overflow-hidden flex flex-col items-center"
      style={{ width: '280px', height: '280px', borderRadius: '50%' }}
    >
      {/* Title - top: 8%, FONT_XTINY: 22px */}
      <div style={{ marginTop: '8%' }}>
        <span style={{ fontSize: '22px', color: mainColor }}>Language</span>
      </div>
      
      {/* Language list - centered at 58% */}
      <div 
        className="absolute left-1/2 -translate-x-1/2 -translate-y-1/2 overflow-y-auto"
        style={{ top: '58%', width: '200px', maxHeight: '180px', textAlign: 'center' }}
      >
        {LANG_NAMES_MENU.map((name, i) => (
          <div 
            key={i}
            className="cursor-pointer border-b"
            style={{ 
              padding: '5px 0',
              borderColor: '#333',
              fontSize: '22px',
              color: state.lang === i ? mainColor : '#888',
              fontWeight: state.lang === i ? 'bold' : 'normal'
            }}
            onClick={() => onSelect(i)}
            data-testid={`lang-option-${i}`}
          >
            {name}
          </div>
        ))}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// COLOR MENU - each color name displayed in its own color!
// Swipe/drag scrolling (no arrows), centered layout
// ═══════════════════════════════════════════════════════════════
function ColorMenu({ state, onSelect, onClose }) {
  const mainColor = COLOR_HEX[state.color];
  const lang = state.lang;
  const [scrollOffset, setScrollOffset] = useState(0);
  const visibleItems = 5;
  const containerRef = useRef(null);
  
  // Translations for "Color" title
  const TR_COLOR_TITLE = ["Color", "צבע", "Color", "Couleur", "Farbe", "颜色"];
  
  // Start with current color visible
  useEffect(() => {
    if (state.color > 4) {
      setScrollOffset(Math.min(state.color - 2, 5)); // Center current color
    } else {
      setScrollOffset(0);
    }
  }, [state.color]);
  
  // Mouse drag state
  const [isDragging, setIsDragging] = useState(false);
  const [dragStartY, setDragStartY] = useState(0);
  const [dragAccum, setDragAccum] = useState(0);
  
  // Handle mouse wheel
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    
    const handleWheel = (e) => {
      e.preventDefault();
      if (e.deltaY > 0 && scrollOffset + visibleItems < 10) {
        setScrollOffset(prev => Math.min(prev + 1, 5));
      } else if (e.deltaY < 0 && scrollOffset > 0) {
        setScrollOffset(prev => Math.max(prev - 1, 0));
      }
    };
    
    container.addEventListener('wheel', handleWheel, { passive: false });
    return () => container.removeEventListener('wheel', handleWheel);
  }, [scrollOffset, visibleItems]);
  
  // Mouse drag handlers
  const handleMouseDown = (e) => {
    setIsDragging(true);
    setDragStartY(e.clientY);
    setDragAccum(0);
  };
  
  const handleMouseMove = (e) => {
    if (!isDragging) return;
    const diff = dragStartY - e.clientY;
    const newAccum = dragAccum + diff;
    
    if (Math.abs(newAccum) > 40) { // Threshold for scroll
      if (newAccum > 0 && scrollOffset + visibleItems < 10) {
        setScrollOffset(prev => Math.min(prev + 1, 5));
      } else if (newAccum < 0 && scrollOffset > 0) {
        setScrollOffset(prev => Math.max(prev - 1, 0));
      }
      setDragAccum(0);
      setDragStartY(e.clientY);
    } else {
      setDragAccum(newAccum);
      setDragStartY(e.clientY);
    }
  };
  
  const handleMouseUp = () => {
    setIsDragging(false);
    setDragAccum(0);
  };
  
  // Touch handling for swipe
  const [touchStart, setTouchStart] = useState(null);
  
  const handleTouchStart = (e) => {
    setTouchStart(e.touches[0].clientY);
  };
  
  const handleTouchMove = (e) => {
    if (!touchStart) return;
    const touchEnd = e.touches[0].clientY;
    const diff = touchStart - touchEnd;
    
    if (Math.abs(diff) > 30) { // Threshold for swipe
      if (diff > 0 && scrollOffset + visibleItems < 10) {
        setScrollOffset(prev => Math.min(prev + 1, 5));
      } else if (diff < 0 && scrollOffset > 0) {
        setScrollOffset(prev => Math.max(prev - 1, 0));
      }
      setTouchStart(touchEnd);
    }
  };
  
  // Get visible colors based on scroll offset
  const visibleColors = COLOR_NAMES.slice(scrollOffset, scrollOffset + visibleItems);
  
  return (
    <div 
      className="relative bg-black overflow-hidden flex flex-col items-center"
      style={{ width: '280px', height: '280px', borderRadius: '50%' }}
      onWheel={handleWheel}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      ref={containerRef}
    >
      {/* Title - centered */}
      <div style={{ marginTop: '8%', borderBottom: `2px solid ${mainColor}`, paddingBottom: '4px' }}>
        <span style={{ fontSize: '22px', color: mainColor }}>
          {TR_COLOR_TITLE[lang]}
        </span>
      </div>
      
      {/* Color list - centered, swipe to scroll */}
      <div 
        className="absolute left-1/2 -translate-x-1/2 flex flex-col items-center"
        style={{ top: '20%', width: '220px' }}
      >
        {visibleColors.map((names, i) => {
          const actualIndex = i + scrollOffset;
          return (
            <div 
              key={actualIndex}
              className="flex items-center justify-center gap-[12px] cursor-pointer w-full"
              style={{ 
                padding: '6px 0',
                fontSize: '24px',
                backgroundColor: state.color === actualIndex ? 'rgba(255,255,255,0.15)' : 'transparent',
                borderRadius: '8px',
              }}
              onClick={() => onSelect(actualIndex)}
              data-testid={`color-option-${actualIndex}`}
            >
              <div style={{ 
                width: '16px', 
                height: '16px', 
                borderRadius: '50%', 
                backgroundColor: COLOR_HEX[actualIndex] 
              }} />
              {/* Color name in its own color - centered */}
              <span style={{ color: COLOR_HEX[actualIndex], minWidth: '80px', textAlign: 'center' }}>
                {names[lang] || names[0]}
              </span>
            </div>
          );
        })}
      </div>
      
      {/* Scroll indicator dots at bottom */}
      <div 
        className="absolute flex gap-1"
        style={{ bottom: '8%', left: '50%', transform: 'translateX(-50%)' }}
      >
        {[0, 1, 2, 3, 4, 5].map((i) => (
          <div 
            key={i}
            style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              backgroundColor: i === Math.floor(scrollOffset / 2) ? mainColor : '#444'
            }}
          />
        ))}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// MAX HR MENU - per spec
// ═══════════════════════════════════════════════════════════════
function MaxHRMenu({ state, onSelect, onClose }) {
  const mainColor = COLOR_HEX[state.color];
  const lang = state.lang;
  const options = ['Auto', '50%', '55%', '60%', '65%', '70%', '75%', '80%', '85%', '90%'];
  
  return (
    <div 
      className="relative bg-black overflow-hidden flex flex-col items-center"
      style={{ width: '280px', height: '280px', borderRadius: '50%' }}
    >
      {/* Title - top: 5%, FONT_XTINY: 22px, white-space: nowrap */}
      <div style={{ marginTop: '5%', whiteSpace: 'nowrap' }}>
        <span style={{ fontSize: '22px', color: mainColor }}>{TR_MAX_HR[lang]}</span>
      </div>
      
      {/* Options list - top: 22% */}
      <div 
        className="absolute left-1/2 -translate-x-1/2 overflow-y-auto"
        style={{ top: '22%', width: '200px', maxHeight: '200px' }}
      >
        {options.map((opt, i) => (
          <div 
            key={i}
            className="cursor-pointer text-center"
            style={{ 
              padding: '6px 20px',
              fontSize: '24px',
              color: '#fff',
              backgroundColor: state.hrMode === i ? 'rgba(0, 255, 102, 0.3)' : 'transparent',
              border: state.hrMode === i ? `2px solid ${mainColor}` : '2px solid transparent',
              borderRadius: '5px',
              marginBottom: '4px'
            }}
            onClick={() => onSelect(i)}
            data-testid={`hr-option-${i}`}
          >
            {state.hrMode === i ? '✓ ' : ''}{i === 0 ? TR_AUTO[lang] : opt}
          </div>
        ))}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// GOAL PICKER - per spec (arrows at top/bottom)
// ═══════════════════════════════════════════════════════════════
function GoalPicker({ state, type, onStart, onClose }) {
  const [goal, setGoal] = useState(type === 'distance' ? state.goalDist : state.goalTimeMin);
  const mainColor = COLOR_HEX[state.color];
  const lang = state.lang;
  // Use translated units!
  const unit = type === 'distance' ? TR_KM[lang] : TR_MINUTES[lang];
  const min = type === 'distance' ? 1 : 10;
  const max = type === 'distance' ? 20 : 120;
  const step = type === 'distance' ? 1 : 10;
  
  return (
    <div 
      className="relative bg-black overflow-hidden flex flex-col items-center"
      style={{ width: '280px', height: '280px', borderRadius: '50%' }}
    >
      {/* UP Arrow - top: 5% */}
      <div 
        className="absolute left-1/2 -translate-x-1/2 cursor-pointer"
        style={{ top: '5%' }}
        onClick={() => setGoal(g => Math.min(max, g + step))}
        data-testid="goal-up"
      >
        <div style={{ 
          width: 0, height: 0, 
          borderLeft: '20px solid transparent', 
          borderRight: '20px solid transparent', 
          borderBottom: `25px solid ${mainColor}` 
        }} />
      </div>
      
      {/* Number + Unit - top: 24%, Unit on LEFT of number! */}
      <div 
        className="absolute left-[42%] -translate-x-1/2 flex items-baseline gap-2"
        style={{ top: '24%', flexDirection: 'row-reverse' }}
      >
        {/* Number - 80px */}
        <span style={{ fontSize: '80px', fontWeight: 'bold', color: '#fff' }}>{goal}</span>
        {/* Unit - FONT_TINY: 30px */}
        <span style={{ fontSize: '30px', color: mainColor }}>{unit}</span>
      </div>
      
      {/* START button - top: 65% */}
      <button 
        className="absolute left-1/2 -translate-x-1/2"
        style={{ 
          top: '65%',
          fontSize: '18px',
          fontWeight: 'bold',
          backgroundColor: mainColor,
          color: '#000',
          padding: '6px 25px',
          borderRadius: '20px',
          border: 'none',
          cursor: 'pointer'
        }}
        onClick={() => onStart(goal)}
        data-testid="goal-start"
      >
        {TR_START[lang]}
      </button>
      
      {/* DOWN Arrow - bottom: 5% */}
      <div 
        className="absolute left-1/2 -translate-x-1/2 cursor-pointer"
        style={{ bottom: '5%' }}
        onClick={() => setGoal(g => Math.max(min, g - step))}
        data-testid="goal-down"
      >
        <div style={{ 
          width: 0, height: 0, 
          borderLeft: '20px solid transparent', 
          borderRight: '20px solid transparent', 
          borderTop: `25px solid ${mainColor}` 
        }} />
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// NAME ENTRY VIEW - translated to selected language
// ═══════════════════════════════════════════════════════════════
function NameEntryView({ state, onSave, onClose }) {
  const [name, setName] = useState(state.userName || '');
  const mainColor = COLOR_HEX[state.color];
  const lang = state.lang;
  const keyboard = KEYBOARDS[lang];
  const isRtl = lang === 1; // Hebrew
  
  // Translations
  const TR_NAME_TITLE = ["Name", "שם", "Nombre", "Nom", "Name", "名称"];
  const TR_CONFIRM = ["Confirm", "אישור", "Confirmar", "Confirmer", "Bestätigen", "确认"];
  
  return (
    <div 
      className="relative bg-black overflow-hidden flex flex-col items-center"
      style={{ width: '280px', height: '280px', borderRadius: '50%' }}
    >
      {/* Title - translated */}
      <div style={{ marginTop: '8%' }}>
        <span style={{ fontSize: '22px', color: '#fff' }}>{TR_NAME_TITLE[lang]}</span>
      </div>
      
      {/* Input + Confirm - top: 38%, flex-direction: column, gap: 12px */}
      <div 
        className="absolute left-1/2 -translate-x-1/2 -translate-y-1/2 flex flex-col items-center"
        style={{ top: '38%', gap: '12px' }}
      >
        {/* Input box - 150px × 35px */}
        <input 
          className="text-center outline-none"
          style={{ 
            width: '150px', 
            height: '35px', 
            border: `2px solid ${mainColor}`,
            backgroundColor: 'transparent',
            color: '#fff',
            fontSize: '18px',
            borderRadius: '4px'
          }}
          value={name}
          onChange={e => setName(e.target.value.slice(0, 12))}
          data-testid="name-input"
        />
        
        {/* Confirm button - 100px width (smaller than input!) */}
        <button 
          style={{ 
            width: '100px',
            padding: '6px 10px',
            backgroundColor: mainColor,
            color: '#000',
            fontSize: '14px',
            fontWeight: 'bold',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
          onClick={() => onSave(name)}
          data-testid="name-save"
        >
          ✓ {TR_CONFIRM[lang]}
        </button>
      </div>
      
      {/* Keyboard - top: 58%, width: 240px */}
      <div 
        className="absolute left-1/2 -translate-x-1/2"
        style={{ top: '58%', width: '240px' }}
      >
        {/* Letter rows */}
        {keyboard.map((row, ri) => (
          <div 
            key={ri} 
            className="flex justify-center"
            style={{ gap: '4px', marginBottom: '4px', direction: isRtl ? 'rtl' : 'ltr' }}
          >
            {row.map((key, ki) => (
              <button 
                key={ki}
                style={{ 
                  width: '22px', 
                  height: '22px', 
                  fontSize: '12px',
                  backgroundColor: '#333',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '2px',
                  cursor: 'pointer'
                }}
                onClick={() => name.length < 12 && setName(n => n + key)}
                data-testid={`key-${key}`}
              >
                {key}
              </button>
            ))}
          </div>
        ))}
        
        {/* Control row: ✓ | ␣ | ⌫ */}
        <div className="flex justify-center" style={{ gap: '4px', marginTop: '4px' }}>
          {/* Confirm key */}
          <button 
            style={{ 
              width: '34px', 
              height: '22px', 
              fontSize: '12px',
              backgroundColor: '#444',
              color: '#fff',
              border: 'none',
              borderRadius: '2px',
              cursor: 'pointer'
            }}
            onClick={() => onSave(name)}
          >
            ✓
          </button>
          
          {/* Space key */}
          <button 
            style={{ 
              width: '55px', 
              height: '22px', 
              fontSize: '12px',
              backgroundColor: '#333',
              color: '#fff',
              border: 'none',
              borderRadius: '2px',
              cursor: 'pointer'
            }}
            onClick={() => name.length < 12 && setName(n => n + ' ')}
            data-testid="key-space"
          >
            ␣
          </button>
          
          {/* Backspace key */}
          <button 
            style={{ 
              width: '34px', 
              height: '22px', 
              fontSize: '12px',
              backgroundColor: '#444',
              color: '#fff',
              border: 'none',
              borderRadius: '2px',
              cursor: 'pointer'
            }}
            onClick={() => setName(n => n.slice(0, -1))}
            data-testid="key-backspace"
          >
            ⌫
          </button>
          
          {/* ABC/אבג toggle for Hebrew */}
          {lang === 1 && (
            <button 
              style={{ 
                width: '34px', 
                height: '22px', 
                fontSize: '10px',
                backgroundColor: '#444',
                color: '#fff',
                border: 'none',
                borderRadius: '2px',
                cursor: 'pointer'
              }}
            >
              ABC
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// ALERT VIEW - 3 LINES, selected color, auto-dismiss after 3 seconds
// ═══════════════════════════════════════════════════════════════
function AlertView({ line1, line2, line3, alertType, color, onDismiss }) {
  const mainColor = color || '#00FF00';
  
  // Auto-dismiss after 3 seconds
  useEffect(() => {
    const timer = setTimeout(() => {
      onDismiss();
    }, 3000);
    return () => clearTimeout(timer);
  }, [onDismiss]);
  
  return (
    <div 
      className="relative flex flex-col items-center justify-center cursor-pointer overflow-hidden"
      style={{ 
        width: '280px', 
        height: '280px', 
        borderRadius: '50%',
        backgroundColor: '#000'
      }}
      onClick={onDismiss}
      data-testid="alert-view"
    >
      {/* Line 1 - Name (e.g., "גבי,") */}
      <span style={{ 
        fontSize: '28px', 
        fontWeight: 'bold', 
        color: mainColor, 
        marginBottom: '8px',
        textAlign: 'center'
      }}>
        {line1}
      </span>
      
      {/* Line 2 - Message (e.g., "תנוח קצת") */}
      <span style={{ 
        fontSize: '24px', 
        fontWeight: 'bold',
        color: mainColor,
        textAlign: 'center',
        marginBottom: '8px'
      }}>
        {line2}
      </span>
      
      {/* Line 3 - Details (e.g., "עברת את הדופק שהגדרת") */}
      {line3 && (
        <span style={{ 
          fontSize: '18px', 
          color: mainColor,
          textAlign: 'center',
          padding: '0 20px'
        }}>
          {line3}
        </span>
      )}
    </div>
  );
}
// ═══════════════════════════════════════════════════════════════
// MAIN SIMULATOR COMPONENT
// ═══════════════════════════════════════════════════════════════
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
  
  const [view, setView] = useState('main');
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
          
          // Check 50% alert - 3 lines format
          if (!s.timeHalfwayShown && newSec >= halfway && newSec < goalSec) {
            newState.timeHalfwayShown = true;
            const name = s.userName || '';
            setAlert({ 
              line1: name ? `${name},` : '',
              line2: TR_KEEP_GOING[s.lang],
              line3: TR_HALF_WAY[s.lang],
              color: COLOR_HEX[s.color]
            });
            setView('alert');
          }
          
          // Check goal completion - TIME RESETS! - 3 lines format
          if (!s.timeGoalShown && newSec >= goalSec) {
            newState.timeGoalShown = true;
            newState.timeGoalActive = false;
            newState.elapsedWalkSec = 0;
            const name = s.userName || '';
            setAlert({ 
              line1: name ? `${name},` : '',
              line2: TR_GREAT_JOB[s.lang],
              line3: TR_GOAL_COMPLETED[s.lang],
              color: COLOR_HEX[s.color]
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
  
  // Start distance goal - DOES NOT reset time!
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
  
  // Start time goal - DOES NOT reset distance!
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
      
      // Check 50% alert - 3 lines format
      if (s.distGoalActive && !s.distHalfwayShown && newDist >= halfway && newDist < goalCm) {
        newState.distHalfwayShown = true;
        const name = s.userName || '';
        setAlert({ 
          line1: name ? `${name},` : '',
          line2: TR_KEEP_GOING[s.lang],
          line3: TR_HALF_WAY[s.lang],
          color: COLOR_HEX[s.color]
        });
        setView('alert');
      }
      
      // Check goal completion - 3 lines format, DISTANCE CONTINUES!
      if (s.distGoalActive && !s.distGoalShown && newDist >= goalCm) {
        newState.distGoalShown = true;
        const name = s.userName || '';
        setAlert({ 
          line1: name ? `${name},` : '',
          line2: TR_GREAT_JOB[s.lang],
          line3: TR_GOAL_COMPLETED[s.lang],
          color: COLOR_HEX[s.color]
        });
        setView('alert');
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
  
  // Simulate app exit - Time RESETS, Distance PERSISTS, HR monitoring STOPS!
  const simulateExit = () => {
    setState(s => {
      const newState = {
        ...s,
        timeGoalActive: false,
        elapsedWalkSec: 0,
        timeHalfwayShown: false,
        timeGoalShown: false,
        // HR monitoring stops on exit!
        hrMode: 0,
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
        return <AlertView 
          line1={alert?.line1} 
          line2={alert?.line2} 
          line3={alert?.line3}
          color={alert?.color}
          onDismiss={() => { setAlert(null); setView('main'); }} 
        />;
      default:
        return <WatchDisplay state={state} onZoneClick={handleZoneClick} />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col items-center py-8">
      <h1 className="text-3xl font-bold text-white mb-2">🏃 FitBeat v4.3.2 Simulator</h1>
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
          <button className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded text-sm" onClick={resetAll} data-testid="btn-reset">🔄 Reset</button>
          <button className="bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded text-sm" onClick={() => addDistance(50000)} data-testid="btn-add-500m">+500m</button>
          <button className="bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded text-sm" onClick={() => addDistance(100000)} data-testid="btn-add-1km">+1km</button>
          <button className="bg-yellow-600 hover:bg-yellow-700 text-white px-3 py-2 rounded text-sm" onClick={() => setState(s => ({ ...s, elapsedWalkSec: s.elapsedWalkSec + 30 }))} data-testid="btn-add-30s">+30s</button>
          <button className="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded text-sm" onClick={simulateExit} data-testid="btn-exit">🚪 Exit App</button>
          <button className="bg-purple-600 hover:bg-purple-700 text-white px-3 py-2 rounded text-sm" onClick={() => setView('main')} data-testid="btn-back">⬅️ Back</button>
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
          <code className="text-green-400 break-all text-[10px]">
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
          <li>✅ QWERTY reversed keyboard (P-Q on top)</li>
          <li>✅ 6 languages with native keyboards</li>
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
