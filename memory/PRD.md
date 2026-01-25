# FitBeat - Garmin Watch Face Application

## Original Problem Statement
Build a watch face application named "FitBeat" for a Garmin Fenix 8 Solar watch with distance goals, time goals, heart rate monitoring, and smart timer functionality.

## Current Version: v2.0 (Working - January 24, 2025)

## Core Features Implemented

### 1. Main Display
- Time (hours:minutes)
- Distance walked (km)
- Duration (minutes:seconds)
- Heart Rate (BPM)
- Progress bars for distance and time

### 2. Distance Goal
- Select goal (1-20 km)
- Alerts at 50% and 100%
- Progress bar tracks distance
- **RESET button** - resets distance and deactivates goal
- **Continue from same point** - changing goal mid-walk doesn't reset progress
- **Daily reset at midnight**

### 3. Time Goal
- Select goal (10-120 minutes, increments of 10)
- Alerts at 50% and 100%
- Progress bar tracks time
- **RESET button** - resets time and deactivates goal

### 4. Smart Timer (NEW)
- When distance goal is active AND time goal = 0:
  - Timer counts minutes:seconds automatically
  - **Both progress bars advance at same rate** (based on distance progress)
  - Timer resets if no movement for 5 minutes

### 5. Heart Rate Monitoring
- Three modes: Off, Rest, Training
- Alerts when HR exceeds target
- **3 equal lines layout** (15%, 45%, 75%)

### 6. Settings
- Language: English, Hebrew, Spanish, French, German, Chinese
- Color: Red, Blue, Green, Yellow, Orange, Purple
- User name for personalized alerts

## Technical Architecture

```
/app/
├── backend/
│   └── server.py         # FastAPI server, /api/download/fitbeat
├── frontend/
│   └── src/
│       └── App.js        # React simulator (matches native code exactly)
└── fitbeat/              # Garmin app source (Monkey C)
    ├── source/
    │   ├── FitBeatApp.mc  # Menus, delegates, alerts
    │   └── FitBeatView.mc # Main view, state management
    ├── resources/         # Fonts, strings
    └── monkey.jungle      # Build config
```

## Key Functions (Native Code)

### FitBeatView.mc
- `startDistanceGoal()` - Start new distance goal (resets distance)
- `continueDistanceGoal()` - Continue with new goal (keeps distance)
- `resetDistanceGoal()` - Reset distance to 0 and deactivate
- `startTimeGoal()` - Start time goal
- `resetTimeGoal()` - Reset time to 0 and deactivate
- `isDistGoalActive()` - Check if distance goal is active
- `_checkMidnightReset()` - Auto-reset distance at midnight
- `_checkMovementAndReset()` - Reset timer after 5 min no movement

### FitBeatApp.mc
- `GoalPickerView` - Distance goal picker with RESET button
- `TimeGoalPickerView` - Time goal picker with RESET button
- `AlertView` - 3-line alerts with animations

## Progress Bar Logic
```
Distance bar: distanceCm / goalCm
Time bar:
  - If time goal active: elapsedWalkSec / goalSec
  - If distance goal active (no time goal): distanceCm / goalCm (same as distance bar)
  - Otherwise: 0
```

## Build Command
```cmd
cd "C:\Users\gabbyc\Desktop\fitbeat\fitbeat"
java -jar "%APPDATA%\Garmin\ConnectIQ\Sdks\connectiq-sdk-win-8.4.0-2025-12-03-5122605dc\bin\monkeybrains.jar" -o FitBeat.prg -f monkey.jungle -y developer_key.der -d fenix8solar51mm
```

## URLs
- Simulator: https://exercise-journal-9.preview.emergentagent.com
- Download ZIP: https://exercise-journal-9.preview.emergentagent.com/api/download/fitbeat

## App Store
- Published on Garmin Connect IQ Store
- Country restriction: Israel not supported for Garmin Merchant Account (monetization)

## Future Features

### 1. PayPal Donation Link
- Add to app store description

### 2. Workout Summary with SMS Link (Priority Feature)

**Concept:** After each workout, send SMS to user with link to full summary page

**Simple Flow:**
```
Watch completes workout
        ↓
Watch sends data to server (GPS, HR, elevation, etc.)
        ↓
Server creates summary page + unique link
        ↓
Server sends SMS to user's phone:
"🏃 סיימת אימון! 5.2km, 45:32
צפה במסלול: fitbeat.app/r/abc123"
        ↓
User copies link and shares with anyone they want
(WhatsApp, SMS, Email, Telegram, etc.)
```

**Settings needed:**
- Phone number (user's own number for receiving SMS)

**Summary page includes:**
- Satellite map with route (red line)
- Start point (green) / End point (red)
- Distance, Time, Pace (avg/max)
- Elevation profile (ascent/descent/min/max)
- Heart rate (avg/max/min + zones graph)
- Respiration rate
- SpO2
- Training Effect / Training Load / Recovery Time
- Steps / Cadence

**Units by language:**
- Hebrew: km, meters
- English: miles, feet

**Required integrations:**
- Twilio SMS (~$0.05 per message)
- Map service (Mapbox/Google Maps)
- Server (Vercel/Railway - free tier)
- Database (MongoDB - free tier)

**Bonus features:**
- SMS also appears on watch (via Bluetooth notification)
- Link expires after X days (optional)
- Weekly summary email (optional)
