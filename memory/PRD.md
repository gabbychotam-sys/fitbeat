# FitBeat - Garmin Watch Face Application

## Original Problem Statement
Build a watch face application named "FitBeat" for a Garmin Fenix 8 Solar watch with:
- Main screen displaying Time, Distance, Duration, and Heart Rate
- Separate, independently functioning goals for distance and time
- RTL (Right-to-Left) step-style progress bars
- Color customization for all icons and key elements (10 colors)
- Alerts at 50% (balloons) and 100% (clapping hands) goal completion
- Multi-language support (English, Hebrew, Spanish, French, German, Chinese)
- Time goal resets on app close, Distance goal persists
- Translated units: km/min in selected language

## User's Preferred Language
Hebrew (עברית)

## Current Architecture
```
/app/
├── backend/
│   └── server.py         # FastAPI server - ZIP download API
├── frontend/
│   └── src/
│       └── App.js        # React simulator (source of truth for UI)
└── fitbeat/              # Garmin Monkey C source code
    ├── source/
    │   ├── FitBeatApp.mc # App entry, delegates, menus, settings, COLOR MENU
    │   └── FitBeatView.mc# Main watch face view, drawing, timers
    ├── resources/        # Fonts, strings, drawables
    └── monkey.jungle     # Build configuration
```

## What's Been Implemented (January 22, 2025)

### ✅ Completed Features:
1. **Main Watch Display**: Time (MM:SS), Distance, HR with colored icons
2. **RTL Progress Bars**: Staircase style, right-to-left
3. **10 Colors**: Green, Cyan, Blue, Purple, Red, Orange, Yellow, Pink, Lime, White
4. **6 Languages**: Full translation for UI, alerts, units
5. **Translated Units**: TR_KM (ק״מ in Hebrew), TR_MINUTES (דקות in Hebrew)
6. **3-Line Alerts**: Name, message, details - in selected color, auto-dismiss 3 sec
7. **Goal Pickers**: Distance and Time with translated units
8. **Settings Screen**: Language, Name, Color, Save - all translated
9. **Web Simulator**: Full React implementation matching Garmin code
10. **Color Menu with CustomMenu**: Native smooth scrolling
11. **Alert Animations**: Falling circles for 50%, stars for 100% - NO animations for HR confirmation
12. **Universal Back Button**: X button on all sub-screens
13. **HR Confirmation Alert**: Plain text only (no animations), shows target BPM

### ✅ Latest UI Fixes (January 22, 2025):
- **Goal Pickers**: X button positioned directly ABOVE the START button
- **Settings Screen**: X button on LEFT, Save button on RIGHT (side by side)
- **HR Confirmation Alert**: Fixed bug - no longer shows animations (plain text only)

### 🟡 Color Menu Scrolling - Updated Implementation (Jan 21, 2025):
**User Requirements:**
- NO scrollbar on left side
- Fixed title at top
- Spacing between colors
- Smooth finger scrolling

**NEW Implementation (based on Garmin forum research):**
- `ColorMenuView extends WatchUi.View` (Custom View)
- `ColorMenuDelegate extends WatchUi.BehaviorDelegate`
- **`onNextPage()` / `onPreviousPage()`** - The recommended method from Garmin forums!
  - Handles both swipe gestures AND physical button presses automatically
  - Works consistently across all touchscreen Garmin devices
- `onTap` for selection
- Global reference `gColorMenuView` for delegate access

**Key Change:**
Replaced `onSwipe` + `onKey` with `onNextPage` / `onPreviousPage` - this is the Garmin-recommended approach for scrolling on touch devices.

**Previous Issues:**
1. `CustomMenu` - scrolling works but has mandatory scrollbar (can't remove)
2. `Custom View + InputDelegate` - scrolling didn't work
3. `Custom View + BehaviorDelegate + onSwipe` - scrolling was jerky/stuck
4. **NEW: `onNextPage` / `onPreviousPage`** - Pending user testing

## Key Code Locations

### Color Menu (lines ~820-990 in FitBeatApp.mc):
- `gColorMenuView` - Global reference for delegate access
- `ColorMenuView` - draws colors with item-by-item scrolling
- `ColorMenuDelegate` - handles **onNextPage, onPreviousPage**, onTap
- `mItemHeight = 50`, `mMaxOffset = 265`
- `scrollDown()` / `scrollUp()` - scroll one item at a time

### Translations:
- `COLOR_NAMES` - 10 colors × 6 languages
- `COLOR_HEX` - 10 hex values
- `TR_COLOR_TITLE` - "Color" in 6 languages
- `TR_KM` - uses Hebrew gershayim ״ (U+05F4), not ASCII "

## Build Instructions
```cmd
cd "C:\Users\gabbyc\Desktop\fitbeat\fitbeat"
java -jar "%APPDATA%\Garmin\ConnectIQ\Sdks\connectiq-sdk-win-8.4.0-2025-12-03-5122605dc\bin\monkeybrains.jar" -o FitBeat.prg -f monkey.jungle -y developer_key.der -d fenix8solar51mm
```

## URLs
- **Download ZIP**: https://fitness-goals-30.preview.emergentagent.com/api/download/fitbeat
- **Simulator**: https://fitness-goals-30.preview.emergentagent.com

## Backlog / Future Tasks
1. Final user verification on physical device
2. Add more customization options (e.g., progress bar style)
3. Add step counter display option

## Technical Notes
- Garmin `CustomMenu` has built-in scrollbar that CANNOT be removed
- `BehaviorDelegate.onSwipe()` is the correct way to handle swipe gestures
- Screen size: 280×280 pixels (Fenix 8 Solar 51mm)
- `TR_KM` must use Hebrew gershayim ״ (U+05F4) not ASCII " to avoid compile errors
