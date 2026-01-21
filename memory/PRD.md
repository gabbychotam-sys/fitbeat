# FitBeat - Garmin Watch Face Application

## Original Problem Statement
Build a watch face application named "FitBeat" for a Garmin Fenix 8 Solar watch with:
- Main screen displaying Time, Distance, Duration, and Heart Rate
- Separate, independently functioning goals for distance and time
- RTL (Right-to-Left) step-style progress bars
- Color customization for all icons and key elements
- Alerts at 50% (balloons) and 100% (clapping hands) goal completion
- Multi-language support (English, Hebrew, Spanish, French, German, Chinese)
- Time goal resets on app close, Distance goal persists

## Current Architecture
```
/app/
├── backend/
│   └── server.py         # FastAPI server - ZIP download & state API
├── frontend/
│   └── src/
│       └── App.js        # React simulator (source of truth)
└── fitbeat/              # Garmin Monkey C source code
    ├── source/
    │   ├── FitBeatApp.mc # App entry, delegates, menus, settings
    │   └── FitBeatView.mc# Main watch face view, drawing, timers
    ├── resources/        # Fonts, strings, drawables
    └── monkey.jungle     # Build configuration
```

## Completed Features (v4.3.2) - January 21, 2025

### Web Simulator (React)
- [x] Full interactive watch face simulator
- [x] All 6 languages with complete translations
- [x] Color menu with colored text per color
- [x] RTL staircase progress bars
- [x] MM:SS time format
- [x] 3-line alerts with selected color, auto-dismiss after 3 seconds
- [x] Separate distance and time goals
- [x] Test controls for simulation

### Native Garmin Code (Monkey C)
- [x] ColorMenuView with colored text per color
- [x] All translations in Settings screen (title, Name, Color, Save)
- [x] Max HR menu title translated
- [x] MM:SS time format in main view
- [x] RTL staircase progress bars
- [x] 3-line AlertView with selected color
- [x] Auto-dismiss alerts after 3 seconds
- [x] Separate distance/time goal tracking
- [x] TR_KEEP_GOING translation added

### Bug Fixes Applied (January 21, 2025)
1. Changed `ColorMenu()` to `ColorMenuView()` in line 696
2. Fixed `TR_COLOR_TITLE` to use existing `TR_COLOR` variable in Settings
3. Added `TR_MAX_HR_TITLE` translation array and used in MaxHRMenu
4. Added `TR_KEEP_GOING` translation for alert messages
5. Updated AlertView to accept 3 parameters and use selected color
6. Updated all `_showFullScreenAlert` calls to 3-line format
7. Changed auto-dismiss timer from 5 to 3 seconds
8. Added MM:SS format in FitBeatView.mc (elapsedMin + elapsedSec)

## Build Instructions
```cmd
cd "C:\Users\gabbyc\Desktop\fitbeat\fitbeat"
java -jar "%APPDATA%\Garmin\ConnectIQ\Sdks\connectiq-sdk-win-8.4.0-2025-12-03-5122605dc\bin\monkeybrains.jar" -o FitBeat.prg -f monkey.jungle -y developer_key.der -d fenix8solar51mm
```

## Download
ZIP available at: `{BACKEND_URL}/api/download/fitbeat`

## Translations Status
| Item | Status |
|------|--------|
| Settings title | ✅ |
| Language item | ✅ (stays "Language") |
| Name item | ✅ |
| Color item | ✅ |
| Save button | ✅ |
| Color menu title | ✅ |
| Color names | ✅ (in color!) |
| Max HR title | ✅ |
| All alerts | ✅ |

## User's Preferred Language
Hebrew (עברית)
