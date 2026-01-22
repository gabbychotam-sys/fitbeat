using Toybox.Application;
using Toybox.WatchUi;
using Toybox.System;
using Toybox.Graphics;
using Toybox.Timer;



// ═══ Hebrew custom bitmap fonts (Unicode) ═══
var gHeSmallFont = null;
var gHeLargeFont = null;

function _isHebrew(lang) {
    return (lang == 1);
}

function _getHeSmallFont() {
    if (gHeSmallFont == null) {
        try {
            gHeSmallFont = WatchUi.loadResource(Rez.Fonts.HeSmall);
        } catch(e) {
            gHeSmallFont = Graphics.FONT_TINY;
        }
    }
    return gHeSmallFont;
}

function _getHeLargeFont() {
    if (gHeLargeFont == null) {
        try {
            gHeLargeFont = WatchUi.loadResource(Rez.Fonts.HeLarge);
        } catch(e) {
            gHeLargeFont = Graphics.FONT_SMALL;
        }
    }
    return gHeLargeFont;
}
// ╔════════════════════════════════════════════════════════════╗
// ║  FitBeat v4.3.2 - Garmin Fenix 8 Solar 51mm (280×280)     ║
// ║  6 Languages | 10 Colors | Arrows Goal Picker             ║
// ║  Full Screen Alerts | Custom Settings View                ║
// ║  SEPARATE GOALS: Distance & Time work INDEPENDENTLY!      ║
// ║  ALL ICONS USE SELECTED COLOR!                            ║
// ╚════════════════════════════════════════════════════════════╝

class FitBeatApp extends Application.AppBase {
    function initialize() {
        AppBase.initialize();
    }

    function onStart(state) {
        if (Application.Storage.getValue("lang") == null) {
            Application.Storage.setValue("lang", 0); // English default
        }
        if (Application.Storage.getValue("color") == null) {
            Application.Storage.setValue("color", 0); // Green default
        }
        if (Application.Storage.getValue("hrMode") == null) {
            Application.Storage.setValue("hrMode", 0);
        }
        if (Application.Storage.getValue("goalDist") == null) {
            Application.Storage.setValue("goalDist", 5);
        }
        if (Application.Storage.getValue("goalTimeMin") == null) {
            Application.Storage.setValue("goalTimeMin", 30);
        }
    }

    // ═══ ON STOP - Time resets, Distance persists! ═══
    function onStop(state) {
        // Time goal RESETS on app exit!
        Application.Storage.setValue("timeGoalActive", false);
        Application.Storage.setValue("elapsedWalkSec", 0);
        Application.Storage.setValue("timeHalfwayShown", false);
        Application.Storage.setValue("timeGoalShown", false);
        
        // Distance goal PERSISTS! (no reset)
    }

    function getInitialView() {
        var v = new FitBeatView();
        return [v, new FitBeatDelegate(v)];
    }
}

// Main screen delegate
class FitBeatDelegate extends WatchUi.BehaviorDelegate {
    var mView;

    function initialize(view) {
        BehaviorDelegate.initialize();
        mView = view;
    }

    function onTap(evt) {
        if (mView == null) { return false; }
        
        var coords = evt.getCoordinates();
        if (coords == null) { return false; }
        
        var tapY = coords[1];
        var timeZone = mView.getTimeZone();
        var distZone = mView.getDistZone();
        var timeGoalZone = mView.getTimeGoalZone();
        var hrZone = mView.getHrZone();
        
        // Tap on TIME -> Settings (Custom View)
        if (tapY >= timeZone[0] && tapY <= timeZone[1]) {
            WatchUi.pushView(new SettingsView(), new SettingsViewDelegate(mView), WatchUi.SLIDE_UP);
            return true;
        }
        
        // Tap on DISTANCE -> Goal Picker (with arrows!)
        if (tapY >= distZone[0] && tapY <= distZone[1]) {
            WatchUi.pushView(new GoalPickerView(mView), new GoalPickerDelegate(mView), WatchUi.SLIDE_UP);
            return true;
        }

        // Tap on TIME GOAL -> Time Goal Picker (10..120 minutes)
        if (timeGoalZone != null && tapY >= timeGoalZone[0] && tapY <= timeGoalZone[1]) {
            WatchUi.pushView(new TimeGoalPickerView(mView), new TimeGoalPickerDelegate(mView), WatchUi.SLIDE_UP);
            return true;
        }
        
        // Tap on HR -> Max HR Menu
        if (tapY >= hrZone[0] && tapY <= hrZone[1]) {
            WatchUi.pushView(new MaxHRMenu(), new MaxHRMenuDelegate(mView), WatchUi.SLIDE_UP);
            return true;
        }
        
        return false;
    }
}

// ╔════════════════════════════════════════════════════════════╗
// ║  TRANSLATIONS - 6 LANGUAGES ONLY                          ║
// ║  English, עברית, Español, Français, Deutsch, 中文          ║
// ╚════════════════════════════════════════════════════════════╝

var LANG_NAMES = ["English", "עברית", "Español", "Français", "Deutsch", "中文"];
var LANG_NAMES_MENU = ["English", "Hebrew", "Spanish", "French", "German", "Chinese"];
var LANG_UNITS = ["mi", "km", "km", "km", "km", "km"];

// Color names in 6 languages (10 colors)
var COLOR_NAMES = [
    ["Green", "ירוק", "Verde", "Vert", "Grün", "绿色"],
    ["Cyan", "טורקיז", "Cian", "Cyan", "Cyan", "青色"],
    ["Blue", "כחול", "Azul", "Bleu", "Blau", "蓝色"],
    ["Purple", "סגול", "Púrpura", "Violet", "Lila", "紫色"],
    ["Red", "אדום", "Rojo", "Rouge", "Rot", "红色"],
    ["Orange", "כתום", "Naranja", "Orange", "Orange", "橙色"],
    ["Yellow", "צהוב", "Amarillo", "Jaune", "Gelb", "黄色"],
    ["Pink", "ורוד", "Rosa", "Rose", "Rosa", "粉色"],
    ["Lime", "ליים", "Lima", "Citron", "Limette", "青柠"],
    ["White", "לבן", "Blanco", "Blanc", "Weiß", "白色"]
];

var COLOR_HEX = [0x00FF00, 0x00FFFF, 0x0000FF, 0xFF00FF, 0xFF0000, 0xFFA500, 0xFFFF00, 0xFF69B4, 0xADFF2F, 0xFFFFFF];

var TR_SETTINGS = ["Settings", "הגדרות", "Ajustes", "Paramètres", "Einstellungen", "设置"];
var TR_LANGUAGE = ["Language", "שפה", "Idioma", "Langue", "Sprache", "语言"];
var TR_NAME = ["Name", "שם", "Nombre", "Nom", "Name", "名称"];
var TR_COLOR = ["Color", "צבע", "Color", "Couleur", "Farbe", "颜色"];
var TR_SAVE = ["Save", "שמור", "Guardar", "Sauvegarder", "Speichern", "保存"];
var TR_START = ["START", "התחל", "INICIAR", "DÉMARRER", "STARTEN", "开始"];
var TR_STEPS = ["steps", "צעדים", "pasos", "pas", "Schritte", "步"];
var TR_MINUTES = ["min", "דקות", "min", "min", "min", "分钟"];
var TR_KM = ["km", "ק״מ", "km", "km", "km", "公里"];
var TR_HALFWAY1 = ["Halfway!", "!חצי דרך", "¡Mitad!", "Mi-chemin!", "Halbzeit!", "一半!"];
var TR_HALFWAY2 = ["Keep going!", "!המשך", "¡Sigue!", "Continue!", "Weiter!", "继续!"];
var TR_GOAL1 = ["Goal!", "!יעד", "¡Meta!", "Objectif!", "Ziel!", "目标!"];
var TR_GOAL2 = ["Congrats!", "!כל הכבוד", "¡Felicidades!", "Félicitations!", "Glückwunsch!", "恭喜!"];
var TR_HRHIGH1 = ["HR High!", "!דופק גבוה", "¡FC Alta!", "FC Haute!", "HF Hoch!", "心率高!"];
var TR_HRHIGH2 = ["Slow down", "האט", "Reduce", "Ralentis", "Langsamer", "减速"];
// New full-screen messages
var TR_WELL_DONE = ["Well done", "כל הכבוד", "¡Bien hecho!", "Bravo", "Gut gemacht", "干得好"];
var TR_HALF_WAY = ["Halfway there", "עברת חצי מהדרך", "A mitad de camino", "À mi-chemin", "Halb geschafft", "到一半了"];
var TR_KEEP_GOING = ["Keep going!", "המשך!", "¡Sigue!", "Continue!", "Weiter!", "继续!"];
var TR_GOAL_DONE_LINE1 = ["Great job", "יפה מאוד", "Excelente", "Super", "Sehr gut", "太棒了"];
var TR_GOAL_DONE_LINE2 = ["Goal completed", "סיימת את היעד", "Objetivo completado", "Objectif atteint", "Ziel erreicht", "完成目标"];
var TR_REST_NOW = ["Take a rest", "תנוח קצת", "Descansa", "Repose-toi", "Mach eine Pause", "休息一下"];
var TR_HR_TOO_HIGH = ["Heart rate above target", "עברת את הדופק שהגדרת", "FC por encima del objetivo", "FC au-dessus de l'objectif", "Puls ueber Ziel", "心率超过目标"];
var TR_GO_AHEAD = ["You can continue", "אפשר להמשיך באימון", "Puedes seguir", "Tu peux continuer", "Du kannst weitermachen", "可以继续"];
var TR_HR_OK = ["Back in range", "הדופק ירד, אפשר להמשיך", "De vuelta al rango", "De retour dans la zone", "Wieder im Bereich", "回到范围"];
var TR_AUTO = ["Auto", "אוטו", "Auto", "Auto", "Auto", "自动"];

// HR Target confirmation messages
var TR_HR_TARGET_SET = ["HR target set", "יעד דופק נקבע", "Objetivo FC fijado", "Objectif FC défini", "HF-Ziel gesetzt", "心率目标设定"];
var TR_STAY_BELOW = ["Stay below", "לא לעבור", "Mantente bajo", "Reste en dessous de", "Bleib unter", "保持低于"];
var TR_BPM = ["BPM", "פעימות", "LPM", "BPM", "SPM", "次/分"];

function getLang() {
    var l = Application.Storage.getValue("lang");
    if (l == null || l < 0 || l > 5) { return 0; }
    return l;
}

function getMainColor() {
    var c = Application.Storage.getValue("color");
    if (c == null || c < 0 || c > 9) { return 0x00FF00; }
    return COLOR_HEX[c];
}

function getColorIndex() {
    var c = Application.Storage.getValue("color");
    if (c == null || c < 0 || c > 9) { return 0; }
    return c;
}

// ╔════════════════════════════════════════════════════════════╗
// ║  GOAL PICKER VIEW - WITH ARROWS ▲▼ (NOT A LIST!)          ║
// ║  ALL POSITIONS IN PERCENTAGES OF w AND h                  ║
// ╚════════════════════════════════════════════════════════════╝

class GoalPickerView extends WatchUi.View {
    var mMainView;
    var mGoal = 5;
    var mUpZone = null;
    var mDownZone = null;
    var mStartZone = null;
    var mCancelZone = null;  // X button for cancel/back
    
    function initialize(mainView) {
        View.initialize();
        mMainView = mainView;
        var g = Application.Storage.getValue("goalDist");
        if (g != null && g >= 1 && g <= 20) { mGoal = g; }
    }
    
    function onUpdate(dc) {
        var w = dc.getWidth();
        var h = dc.getHeight();
        var lang = getLang();
        var color = getMainColor();
        var unit = TR_KM[lang];  // Use translated unit!
        
        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        dc.clear();
        
        // ═══ X CANCEL BUTTON (more visible - moved inward) ═══
        var xSize = 28;
        var xMargin = 50;  // More inward from edge
        dc.setColor(Graphics.COLOR_DK_GRAY, Graphics.COLOR_DK_GRAY);
        dc.fillCircle(xMargin, xMargin, xSize / 2 + 6);
        dc.setColor(Graphics.COLOR_LT_GRAY, Graphics.COLOR_LT_GRAY);
        dc.drawCircle(xMargin, xMargin, xSize / 2 + 6);
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        dc.drawText(xMargin, xMargin - 2, Graphics.FONT_SMALL, "X", Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
        mCancelZone = [xMargin - xSize, xMargin + xSize, xMargin - xSize, xMargin + xSize];
        
        // ═══ LAYOUT: Number+Unit on LEFT, Arrows on RIGHT, START at BOTTOM ═══
        var arrowSize = w / 12;
        var centerY = h / 2 - h / 10;
        
        var numFont = Graphics.FONT_NUMBER_HOT;
        var unitFont = Graphics.FONT_SMALL;
        var numH = dc.getFontHeight(numFont);
        
        var numStr = mGoal.toString();
        var numW = dc.getTextWidthInPixels(numStr, numFont);
        
        // LEFT SIDE: Number + Unit
        var leftX = w / 6;
        var numY = centerY - numH / 2;
        
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        dc.drawText(leftX, numY, numFont, numStr, Graphics.TEXT_JUSTIFY_LEFT);
        
        dc.setColor(color, Graphics.COLOR_TRANSPARENT);
        dc.drawText(leftX + numW + w / 30, centerY - dc.getFontHeight(unitFont) / 2, unitFont, unit, Graphics.TEXT_JUSTIFY_LEFT);
        
        // RIGHT SIDE: ▲ and ▼ arrows
        var arrowX = w * 3 / 4;
        var upY = centerY - arrowSize - h / 15;
        var downY = centerY + h / 15;
        
        // ▲ UP ARROW
        dc.setColor(color, Graphics.COLOR_TRANSPARENT);
        dc.fillPolygon([
            [arrowX, upY],
            [arrowX - arrowSize, upY + arrowSize],
            [arrowX + arrowSize, upY + arrowSize]
        ]);
        mUpZone = [upY, upY + arrowSize, arrowX - arrowSize, arrowX + arrowSize];
        
        // ▼ DOWN ARROW
        dc.setColor(color, Graphics.COLOR_TRANSPARENT);
        dc.fillPolygon([
            [arrowX, downY + arrowSize],
            [arrowX - arrowSize, downY],
            [arrowX + arrowSize, downY]
        ]);
        mDownZone = [downY, downY + arrowSize, arrowX - arrowSize, arrowX + arrowSize];

        // BOTTOM: START button
        var btnFont = Graphics.FONT_SMALL;
        var btnH = dc.getFontHeight(btnFont);
        var btnW = w * 4 / 10;
        var btnX = (w - btnW) / 2;
        var btnY = h - btnH - h / 6;
        
        dc.setColor(color, color);
        dc.fillRoundedRectangle(btnX, btnY, btnW, btnH + h / 20, h / 40);
        
        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_TRANSPARENT);
        dc.drawText(w / 2, btnY + h / 60, btnFont, "START", Graphics.TEXT_JUSTIFY_CENTER);
        
        mStartZone = [btnY, btnY + btnH + h / 20, btnX, btnX + btnW];
    }
    
    function getUpZone() { return mUpZone; }
    function getDownZone() { return mDownZone; }
    function getStartZone() { return mStartZone; }
    function getCancelZone() { return mCancelZone; }
    function getGoal() { return mGoal; }
    
    function incrementGoal() {
        if (mGoal < 20) { mGoal++; WatchUi.requestUpdate(); }
    }
    
    function decrementGoal() {
        if (mGoal > 1) { mGoal--; WatchUi.requestUpdate(); }
    }
}

class GoalPickerDelegate extends WatchUi.BehaviorDelegate {
    var mMainView;
    
    function initialize(mainView) {
        BehaviorDelegate.initialize();
        mMainView = mainView;
    }
    
    function onTap(evt) {
        var coords = evt.getCoordinates();
        if (coords == null) { return false; }
        
        var tapX = coords[0];
        var tapY = coords[1];
        
        var picker = WatchUi.getCurrentView()[0];
        if (picker == null || !(picker instanceof GoalPickerView)) { return false; }
        
        var upZone = picker.getUpZone();
        var downZone = picker.getDownZone();
        var startZone = picker.getStartZone();
        var cancelZone = picker.getCancelZone();
        
        // X CANCEL button - go back without saving
        if (cancelZone != null && tapY >= cancelZone[0] && tapY <= cancelZone[1] && tapX >= cancelZone[2] && tapX <= cancelZone[3]) {
            WatchUi.popView(WatchUi.SLIDE_DOWN);
            return true;
        }
        
        // UP arrow
        if (upZone != null && tapY >= upZone[0] && tapY <= upZone[1] && tapX >= upZone[2] && tapX <= upZone[3]) {
            picker.incrementGoal();
            return true;
        }
        
        // DOWN arrow
        if (downZone != null && tapY >= downZone[0] && tapY <= downZone[1] && tapX >= downZone[2] && tapX <= downZone[3]) {
            picker.decrementGoal();
            return true;
        }
        
        // START button - starts DISTANCE goal ONLY, doesn't reset time!
        if (startZone != null && tapY >= startZone[0] && tapY <= startZone[1] && tapX >= startZone[2] && tapX <= startZone[3]) {
            var goal = picker.getGoal();
            Application.Storage.setValue("goalDist", goal);
            if (mMainView != null) {
                mMainView.setGoal(goal);
                mMainView.startDistanceGoal();  // Only starts distance!
            }
            WatchUi.popView(WatchUi.SLIDE_DOWN);
            return true;
        }
        
        return false;
    }
    
    function onBack() {
        WatchUi.popView(WatchUi.SLIDE_DOWN);
        return true;
    }
}

// ╔════════════════════════════════════════════════════════════╗
// ║  TIME GOAL PICKER - 10..120 MINUTES (STEP 10)             ║
// ║  Same layout as Distance Goal Picker                       ║
// ╚════════════════════════════════════════════════════════════╝

class TimeGoalPickerView extends WatchUi.View {
    var mGoalMin = 30;
    var mUpZone = null;
    var mDownZone = null;
    var mStartZone = null;
    var mCancelZone = null;  // X button for cancel/back
    var mMainView;

    function initialize(mainView) {
        View.initialize();
        mMainView = mainView;
        var v = Application.Storage.getValue("goalTimeMin");
        if (v != null) { mGoalMin = v; }
        if (mGoalMin < 10) { mGoalMin = 10; }
        if (mGoalMin > 120) { mGoalMin = 120; }
        mGoalMin = (mGoalMin / 10).toNumber() * 10;
        if (mGoalMin < 10) { mGoalMin = 10; }
        if (mGoalMin > 120) { mGoalMin = 120; }
    }

    function onUpdate(dc) {
        var w = dc.getWidth();
        var h = dc.getHeight();
        var lang = getLang();
        var color = getMainColor();

        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        dc.clear();

        // ═══ X CANCEL BUTTON (more visible - moved inward) ═══
        var xSize = 28;
        var xMargin = 50;  // More inward from edge
        dc.setColor(Graphics.COLOR_DK_GRAY, Graphics.COLOR_DK_GRAY);
        dc.fillCircle(xMargin, xMargin, xSize / 2 + 6);
        dc.setColor(Graphics.COLOR_LT_GRAY, Graphics.COLOR_LT_GRAY);
        dc.drawCircle(xMargin, xMargin, xSize / 2 + 6);
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        dc.drawText(xMargin, xMargin - 2, Graphics.FONT_SMALL, "X", Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
        mCancelZone = [xMargin - xSize, xMargin + xSize, xMargin - xSize, xMargin + xSize];

        // ═══ LAYOUT: Number+Unit on LEFT, Arrows on RIGHT, START at BOTTOM ═══
        var arrowSize = w / 12;
        var centerY = h / 2 - h / 10;
        
        var numFont = Graphics.FONT_NUMBER_HOT;
        var unitFont = Graphics.FONT_SMALL;
        var numH = dc.getFontHeight(numFont);
        
        var numStr = mGoalMin.toString();
        var numW = dc.getTextWidthInPixels(numStr, numFont);
        var unitStr = TR_MINUTES[lang];  // Use translated unit!
        
        // LEFT SIDE: Number + Unit
        var leftX = w / 6;
        var numY = centerY - numH / 2;
        
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        dc.drawText(leftX, numY, numFont, numStr, Graphics.TEXT_JUSTIFY_LEFT);
        
        dc.setColor(color, Graphics.COLOR_TRANSPARENT);
        dc.drawText(leftX + numW + w / 30, centerY - dc.getFontHeight(unitFont) / 2, unitFont, unitStr, Graphics.TEXT_JUSTIFY_LEFT);
        
        // RIGHT SIDE: ▲ and ▼ arrows
        var arrowX = w * 3 / 4;
        var upY = centerY - arrowSize - h / 15;
        var downY = centerY + h / 15;
        
        // ▲ UP ARROW
        dc.setColor(color, Graphics.COLOR_TRANSPARENT);
        dc.fillPolygon([
            [arrowX, upY],
            [arrowX - arrowSize, upY + arrowSize],
            [arrowX + arrowSize, upY + arrowSize]
        ]);
        mUpZone = [upY, upY + arrowSize, arrowX - arrowSize, arrowX + arrowSize];
        
        // ▼ DOWN ARROW
        dc.setColor(color, Graphics.COLOR_TRANSPARENT);
        dc.fillPolygon([
            [arrowX, downY + arrowSize],
            [arrowX - arrowSize, downY],
            [arrowX + arrowSize, downY]
        ]);
        mDownZone = [downY, downY + arrowSize, arrowX - arrowSize, arrowX + arrowSize];

        // BOTTOM: START button
        var btnFont = Graphics.FONT_SMALL;
        var btnH = dc.getFontHeight(btnFont);
        var btnW = w * 4 / 10;
        var btnX = (w - btnW) / 2;
        var btnY = h - btnH - h / 6;
        
        dc.setColor(color, color);
        dc.fillRoundedRectangle(btnX, btnY, btnW, btnH + h / 20, h / 40);
        
        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_TRANSPARENT);
        dc.drawText(w / 2, btnY + h / 60, btnFont, "START", Graphics.TEXT_JUSTIFY_CENTER);
        
        mStartZone = [btnY, btnY + btnH + h / 20, btnX, btnX + btnW];
    }

    function getUpZone() { return mUpZone; }
    function getDownZone() { return mDownZone; }
    function getStartZone() { return mStartZone; }
    function getCancelZone() { return mCancelZone; }
    function getGoalMin() { return mGoalMin; }

    function incrementGoal() {
        if (mGoalMin < 120) { mGoalMin += 10; WatchUi.requestUpdate(); }
    }

    function decrementGoal() {
        if (mGoalMin > 10) { mGoalMin -= 10; WatchUi.requestUpdate(); }
    }
}

class TimeGoalPickerDelegate extends WatchUi.BehaviorDelegate {
    var mMainView;

    function initialize(mainView) {
        BehaviorDelegate.initialize();
        mMainView = mainView;
    }

    function onTap(evt) {
        var coords = evt.getCoordinates();
        if (coords == null) { return false; }

        var tapX = coords[0];
        var tapY = coords[1];

        var picker = WatchUi.getCurrentView()[0];
        if (picker == null || !(picker instanceof TimeGoalPickerView)) { return false; }

        var upZone = picker.getUpZone();
        var downZone = picker.getDownZone();
        var startZone = picker.getStartZone();
        var cancelZone = picker.getCancelZone();

        // X CANCEL button - go back without saving
        if (cancelZone != null && tapY >= cancelZone[0] && tapY <= cancelZone[1] && tapX >= cancelZone[2] && tapX <= cancelZone[3]) {
            WatchUi.popView(WatchUi.SLIDE_DOWN);
            return true;
        }

        if (upZone != null && tapY >= upZone[0] && tapY <= upZone[1] && tapX >= upZone[2] && tapX <= upZone[3]) {
            picker.incrementGoal();
            return true;
        }

        if (downZone != null && tapY >= downZone[0] && tapY <= downZone[1] && tapX >= downZone[2] && tapX <= downZone[3]) {
            picker.decrementGoal();
            return true;
        }

        // START button - starts TIME goal ONLY, doesn't reset distance!
        if (startZone != null && tapY >= startZone[0] && tapY <= startZone[1] && tapX >= startZone[2] && tapX <= startZone[3]) {
            var goalMin = picker.getGoalMin();
            Application.Storage.setValue("goalTimeMin", goalMin);
            if (mMainView != null) {
                mMainView.setTimeGoal(goalMin);
                mMainView.startTimeGoal();  // Only starts time!
            }
            WatchUi.popView(WatchUi.SLIDE_DOWN);
            return true;
        }

        return false;
    }

    function onBack() {
        WatchUi.popView(WatchUi.SLIDE_DOWN);
        return true;
    }
}

// ╔════════════════════════════════════════════════════════════╗
// ║  SETTINGS VIEW - CUSTOM VIEW (NOT Menu2!)                 ║
// ║  Shows: Language, Name, Color + Save button               ║
// ║  TRANSLATED to selected language!                         ║
// ╚════════════════════════════════════════════════════════════╝

// Translations for Settings screen
var TR_SETTINGS_TITLE = ["Settings", "הגדרות", "Ajustes", "Paramètres", "Einstellungen", "设置"];
var TR_NAME_LABEL = ["Name", "שם", "Nombre", "Nom", "Name", "名称"];
var TR_SAVE_BTN = ["Save", "שמור", "Guardar", "Sauvegarder", "Speichern", "保存"];

class SettingsView extends WatchUi.View {
    var mLangZone = null;
    var mNameZone = null;
    var mColorZone = null;
    var mSaveZone = null;
    var mCancelZone = null;  // X button for cancel/back

    function initialize() { View.initialize(); }

    function onUpdate(dc) {
        var w = dc.getWidth();
        var h = dc.getHeight();
        var lang = getLang();
        var color = getMainColor();
        var colorIdx = getColorIndex();

        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        dc.clear();

        var titleFont = Graphics.FONT_SMALL;
        var itemFont  = Graphics.FONT_TINY;
        var valueFont = Graphics.FONT_XTINY;
        var titleH = dc.getFontHeight(titleFont);
        var itemH = dc.getFontHeight(itemFont);

        var padSide = w / 10;
        var y = h / 10;

        // Title: Settings - TRANSLATED!
        dc.setColor(color, Graphics.COLOR_TRANSPARENT);
        dc.drawText(w / 2, y, titleFont, TR_SETTINGS_TITLE[lang], Graphics.TEXT_JUSTIFY_CENTER);
        y += titleH + h / 25;

        // Divider
        dc.setColor(Graphics.COLOR_DK_GRAY, Graphics.COLOR_TRANSPARENT);
        dc.drawLine(padSide, y, w - padSide, y);
        y += h / 40;
        
        // Row 1: Language
        var row1Top = y;
        var valueStr1 = LANG_NAMES_MENU[lang] + " >";

        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        dc.drawText(padSide, y, itemFont, "Language", Graphics.TEXT_JUSTIFY_LEFT);

        dc.setColor(Graphics.COLOR_LT_GRAY, Graphics.COLOR_TRANSPARENT);
        dc.drawText(w - padSide, y, valueFont, valueStr1, Graphics.TEXT_JUSTIFY_RIGHT);

        y += itemH + h / 30;
        mLangZone = [row1Top, y, 0, w];

        // Divider
        dc.setColor(Graphics.COLOR_DK_GRAY, Graphics.COLOR_TRANSPARENT);
        dc.drawLine(padSide, y, w - padSide, y);
        y += h / 40;

        // Row 2: Name - TRANSLATED!
        var row2Top = y;
        var userName = Application.Storage.getValue("userName");
        if (userName == null || userName.equals("")) { userName = "-"; }
        var valueStr2 = userName + " >";

        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        dc.drawText(padSide, y, itemFont, TR_NAME_LABEL[lang], Graphics.TEXT_JUSTIFY_LEFT);

        dc.setColor(Graphics.COLOR_LT_GRAY, Graphics.COLOR_TRANSPARENT);
        dc.drawText(w - padSide, y, valueFont, valueStr2, Graphics.TEXT_JUSTIFY_RIGHT);

        y += itemH + h / 30;
        mNameZone = [row2Top, y, 0, w];

        // Divider
        dc.setColor(Graphics.COLOR_DK_GRAY, Graphics.COLOR_TRANSPARENT);
        dc.drawLine(padSide, y, w - padSide, y);
        y += h / 40;

        // Row 3: Color - TRANSLATED!
        var row3Top = y;
        var dotR = h / 45;
        var colorName = COLOR_NAMES[colorIdx][lang];  // Color name in selected language!
        var valueStr3 = colorName + " >";

        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        dc.drawText(padSide, y, itemFont, TR_COLOR[lang], Graphics.TEXT_JUSTIFY_LEFT);

        // Color dot
        var textW2 = dc.getTextWidthInPixels(valueStr3, valueFont);
        var dotX2 = w - padSide - textW2 - dotR * 2;
        dc.setColor(color, color);
        dc.fillCircle(dotX2, y + itemH / 2, dotR);

        dc.setColor(Graphics.COLOR_LT_GRAY, Graphics.COLOR_TRANSPARENT);
        dc.drawText(w - padSide, y, valueFont, valueStr3, Graphics.TEXT_JUSTIFY_RIGHT);

        y += itemH + h / 30;
        mColorZone = [row3Top, y, 0, w];

        // Divider
        dc.setColor(Graphics.COLOR_DK_GRAY, Graphics.COLOR_TRANSPARENT);
        dc.drawLine(padSide, y, w - padSide, y);

        y += h / 10;

        // Save button - TRANSLATED!
        var btnW = w * 4 / 10;
        var btnH = h / 8;
        var btnX = (w - btnW) / 2;
        var btnY = y;

        dc.setColor(color, color);
        dc.fillRoundedRectangle(btnX, btnY, btnW, btnH, h / 40);

        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_TRANSPARENT);
        var saveTextH = dc.getFontHeight(valueFont);
        var saveTextY = btnY + (btnH - saveTextH) / 2;
        dc.drawText(w / 2, saveTextY, valueFont, TR_SAVE_BTN[lang], Graphics.TEXT_JUSTIFY_CENTER);

        mSaveZone = [btnY, btnY + btnH, btnX, btnX + btnW];
    }

    function getLangZone() { return mLangZone; }
    function getNameZone() { return mNameZone; }
    function getColorZone() { return mColorZone; }
    function getSaveZone() { return mSaveZone; }
    function getCancelZone() { return mCancelZone; }
}

class SettingsViewDelegate extends WatchUi.BehaviorDelegate {
    var mMainView;

    function initialize(mainView) {
        BehaviorDelegate.initialize();
        mMainView = mainView;
    }

    function onTap(evt) {
        var coords = evt.getCoordinates();
        if (coords == null) { return false; }

        var tapX = coords[0];
        var tapY = coords[1];

        var settings = WatchUi.getCurrentView()[0];
        if (settings == null || !(settings instanceof SettingsView)) { return false; }

        var langZone = settings.getLangZone();
        var nameZone = settings.getNameZone();
        var colorZone = settings.getColorZone();
        var saveZone = settings.getSaveZone();
        var cancelZone = settings.getCancelZone();

        // X CANCEL button - go back without saving
        if (cancelZone != null && tapY >= cancelZone[0] && tapY <= cancelZone[1] && tapX >= cancelZone[2] && tapX <= cancelZone[3]) {
            WatchUi.popView(WatchUi.SLIDE_DOWN);
            return true;
        }

        // Language
        if (langZone != null && tapY >= langZone[0] && tapY <= langZone[1]) {
            WatchUi.pushView(new LanguageMenu(), new LanguageMenuDelegate(mMainView), WatchUi.SLIDE_LEFT);
            return true;
        }

        // Name
        if (nameZone != null && tapY >= nameZone[0] && tapY <= nameZone[1]) {
            var currentName = Application.Storage.getValue("userName");
            if (currentName == null) { currentName = ""; }
            WatchUi.pushView(new NameEntryView(currentName), new NameEntryDelegate(), WatchUi.SLIDE_LEFT);
            return true;
        }

        // Color - open CustomMenu (native smooth scrolling!)
        if (colorZone != null && tapY >= colorZone[0] && tapY <= colorZone[1]) {
            WatchUi.pushView(new ColorMenu(), new ColorMenuDelegate(), WatchUi.SLIDE_LEFT);
            return true;
        }

        // Save
        if (saveZone != null && tapY >= saveZone[0] && tapY <= saveZone[1] && tapX >= saveZone[2] && tapX <= saveZone[3]) {
            WatchUi.popView(WatchUi.SLIDE_DOWN);
            WatchUi.requestUpdate();
            return true;
        }

        return false;
    }

    function onBack() {
        WatchUi.popView(WatchUi.SLIDE_DOWN);
        return true;
    }
}

// ╔════════════════════════════════════════════════════════════╗
// ║  ALERT VIEW - FULL SCREEN, 3 LINES, AUTO-DISMISS (3 sec)   ║
// ║  With falling stars/confetti animation!                     ║
// ║  Uses its own Timer for safe auto-dismiss!                 ║
// ╚════════════════════════════════════════════════════════════╝

class AlertView extends WatchUi.View {
    var mLine1;
    var mLine2;
    var mLine3;
    var mColor;
    var mDismissTimer;
    var mAnimTimer;
    var mDismissed = false;
    var mAlertType;  // "halfway" = balloons, "goal" = stars
    
    // Particle animation data
    var mParticles = null;
    var mParticleCount = 8;
    var mAnimFrame = 0;

    function initialize(line1, line2, line3, alertType) {
        WatchUi.View.initialize();
        mLine1 = line1;
        mLine2 = line2;
        mLine3 = line3 != null ? line3 : "";
        mColor = getMainColor();
        mDismissTimer = new Timer.Timer();
        mAnimTimer = new Timer.Timer();
        mDismissed = false;
        mAlertType = alertType != null ? alertType : "halfway";
        
        // Initialize particles with random positions
        mParticles = new [mParticleCount];
        for (var i = 0; i < mParticleCount; i++) {
            mParticles[i] = {
                "x" => (i * 35) % 280,  // Spread across width
                "y" => -20 - (i * 15),   // Start above screen
                "speed" => 8 + (i % 4) * 3
            };
        }
    }
    
    function onShow() {
        // Start 3-second auto-dismiss timer when alert is shown
        mDismissTimer.start(method(:onDismissTimer), 3000, false);
        // Start animation timer (100ms = 10 FPS for smooth animation)
        mAnimTimer.start(method(:onAnimFrame), 100, true);
    }
    
    function onHide() {
        // Stop timers when view is hidden
        if (mDismissTimer != null) { mDismissTimer.stop(); }
        if (mAnimTimer != null) { mAnimTimer.stop(); }
    }
    
    function onAnimFrame() {
        mAnimFrame += 1;
        // Move particles down
        if (mParticles != null) {
            for (var i = 0; i < mParticleCount; i++) {
                var p = mParticles[i];
                p["y"] = p["y"] + p["speed"];
                // Reset particle when it goes off screen
                if (p["y"] > 300) {
                    p["y"] = -20;
                    p["x"] = (p["x"] + 70) % 280;
                }
            }
        }
        WatchUi.requestUpdate();
    }
    
    function onDismissTimer() {
        // Auto-dismiss after 3 seconds
        if (!mDismissed) {
            mDismissed = true;
            if (mAnimTimer != null) { mAnimTimer.stop(); }
            WatchUi.popView(WatchUi.SLIDE_DOWN);
        }
    }
    
    function dismiss() {
        // Manual dismiss
        if (!mDismissed) {
            mDismissed = true;
            if (mDismissTimer != null) { mDismissTimer.stop(); }
            if (mAnimTimer != null) { mAnimTimer.stop(); }
            WatchUi.popView(WatchUi.SLIDE_DOWN);
        }
    }

    function onUpdate(dc) {
        var w = dc.getWidth();
        var h = dc.getHeight();

        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        dc.clear();
        
        // Draw falling particles (stars for goal, circles for halfway)
        if (mParticles != null) {
            var colors = [Graphics.COLOR_YELLOW, Graphics.COLOR_RED, Graphics.COLOR_GREEN, 
                         Graphics.COLOR_BLUE, Graphics.COLOR_ORANGE, Graphics.COLOR_PINK,
                         Graphics.COLOR_WHITE, mColor];
            
            for (var i = 0; i < mParticleCount; i++) {
                var p = mParticles[i];
                var px = p["x"];
                var py = p["y"];
                
                // Only draw if in visible area
                if (py > 0 && py < h) {
                    var pColor = colors[i % 8];
                    dc.setColor(pColor, pColor);
                    
                    if (mAlertType.equals("goal")) {
                        // Draw star shape for goal completion
                        var size = 6 + (i % 3) * 2;
                        // Simple star as filled circle with smaller inner circle
                        dc.fillCircle(px, py, size);
                        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
                        dc.fillCircle(px, py, size / 3);
                    } else {
                        // Draw circle for halfway (balloon-like)
                        var size = 8 + (i % 3) * 3;
                        dc.fillCircle(px, py, size);
                        // Balloon string
                        dc.setColor(pColor, pColor);
                        dc.drawLine(px, py + size, px, py + size + 10);
                    }
                }
            }
        }

        var fBig = (gHeLargeFont != null) ? gHeLargeFont : Graphics.FONT_LARGE;
        var fSmall = (gHeSmallFont != null) ? gHeSmallFont : Graphics.FONT_SMALL;

        // Use selected color for all text!
        dc.setColor(mColor, Graphics.COLOR_TRANSPARENT);

        if (mLine3 != null && !mLine3.equals("")) {
            // 3 lines format
            dc.drawText(w/2, (h*25)/100, fBig, mLine1, Graphics.TEXT_JUSTIFY_CENTER);
            dc.drawText(w/2, (h*45)/100, fBig, mLine2, Graphics.TEXT_JUSTIFY_CENTER);
            dc.drawText(w/2, (h*65)/100, fSmall, mLine3, Graphics.TEXT_JUSTIFY_CENTER);
        } else {
            // 2 lines format
            dc.drawText(w/2, (h*36)/100, fBig, mLine1, Graphics.TEXT_JUSTIFY_CENTER);
            dc.drawText(w/2, (h*56)/100, fSmall, mLine2, Graphics.TEXT_JUSTIFY_CENTER);
        }
    }
}

class AlertViewDelegate extends WatchUi.BehaviorDelegate {
    var mAlertView;
    
    function initialize(alertView) { 
        BehaviorDelegate.initialize();
        mAlertView = alertView;
    }
    
    function onTap(evt) {
        if (mAlertView != null) {
            mAlertView.dismiss();
        }
        return true;
    }
    
    function onBack() {
        if (mAlertView != null) {
            mAlertView.dismiss();
        }
        return true;
    }
}

// ╔════════════════════════════════════════════════════════════╗
// ║  MENUS: Language, Color, Max HR                           ║
// ╚════════════════════════════════════════════════════════════╝

class LanguageMenu extends WatchUi.Menu2 {
    function initialize() {
        Menu2.initialize({:title => "Language"});
        var names = ["English", "Hebrew", "Español", "Français", "Deutsch", "中文"];
        for (var i = 0; i < 6; i++) {
            addItem(new WatchUi.MenuItem(names[i], "", i, null));
        }
    }
}

class LanguageMenuDelegate extends WatchUi.Menu2InputDelegate {
    var mView;
    function initialize(view) { Menu2InputDelegate.initialize(); mView = view; }
    
    function onSelect(item) {
        Application.Storage.setValue("lang", item.getId());
        WatchUi.popView(WatchUi.SLIDE_RIGHT);
        WatchUi.requestUpdate();
    }
    
    function onBack() { WatchUi.popView(WatchUi.SLIDE_RIGHT); }
}

class NamePickerDelegate extends WatchUi.TextPickerDelegate {
    function initialize() { TextPickerDelegate.initialize(); }
    
    function onTextEntered(text, changed) {
        if (changed) { Application.Storage.setValue("userName", text); }
        WatchUi.popView(WatchUi.SLIDE_RIGHT);
        WatchUi.requestUpdate();
        return true;
    }
    
    function onCancel() {
        WatchUi.popView(WatchUi.SLIDE_RIGHT);
        return true;
    }
}

// ╔════════════════════════════════════════════════════════════════╗
// ║  COLOR MENU - Using CustomMenu for NATIVE smooth scrolling!    ║
// ║  CustomMenu inherits Menu2 scrolling + allows custom drawing   ║
// ╚════════════════════════════════════════════════════════════════╝

// Translations for "Color" title
var TR_COLOR_TITLE = ["Color", "צבע", "Color", "Couleur", "Farbe", "颜色"];

// Custom color menu item - draws color circle + colored text
class ColorMenuItem extends WatchUi.CustomMenuItem {
    var mColorIndex;
    var mColorHex;
    var mColorName;
    
    function initialize(colorIndex) {
        CustomMenuItem.initialize(colorIndex, {});
        mColorIndex = colorIndex;
        mColorHex = COLOR_HEX[colorIndex];
        mColorName = COLOR_NAMES[colorIndex][getLang()];
    }
    
    // Draw the menu item - called by CustomMenu
    function draw(dc) {
        var w = dc.getWidth();
        var h = dc.getHeight();
        var centerY = h / 2;
        var currentIdx = getColorIndex();
        
        // Background - highlight if selected
        if (mColorIndex == currentIdx) {
            dc.setColor(Graphics.COLOR_DK_GRAY, Graphics.COLOR_DK_GRAY);
            dc.fillRectangle(0, 0, w, h);
        }
        
        // Color circle on left
        var circleX = w / 5;
        var circleR = 14;
        dc.setColor(mColorHex, mColorHex);
        dc.fillCircle(circleX, centerY, circleR);
        
        // Color name in its own color - LARGE font
        dc.setColor(mColorHex, Graphics.COLOR_TRANSPARENT);
        dc.drawText(w / 3 + 10, centerY, Graphics.FONT_LARGE, mColorName, 
                    Graphics.TEXT_JUSTIFY_LEFT | Graphics.TEXT_JUSTIFY_VCENTER);
    }
}

// Title drawable for CustomMenu
class ColorMenuTitle extends WatchUi.Drawable {
    function initialize() {
        Drawable.initialize({});
    }
    
    function draw(dc) {
        var w = dc.getWidth();
        var h = dc.getHeight();
        var lang = getLang();
        var color = getMainColor();
        
        // Black background
        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        dc.fillRectangle(0, 0, w, h);
        
        // Title text in selected color
        dc.setColor(color, Graphics.COLOR_TRANSPARENT);
        dc.drawText(w / 2, h / 2, Graphics.FONT_LARGE, TR_COLOR_TITLE[lang], 
                    Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER);
    }
}

// The CustomMenu for colors - native smooth scrolling!
class ColorMenu extends WatchUi.CustomMenu {
    function initialize() {
        var titleDrawable = new ColorMenuTitle();
        CustomMenu.initialize(60, Graphics.COLOR_BLACK, {:title => titleDrawable, :titleItemHeight => 50});
        
        // Add all 10 color items
        for (var i = 0; i < 10; i++) {
            addItem(new ColorMenuItem(i));
        }
    }
}

// Delegate for ColorMenu
class ColorMenuDelegate extends WatchUi.Menu2InputDelegate {
    function initialize() { 
        Menu2InputDelegate.initialize(); 
    }
    
    function onSelect(item) {
        var colorIdx = item.getId();
        Application.Storage.setValue("color", colorIdx);
        WatchUi.popView(WatchUi.SLIDE_RIGHT);
        WatchUi.requestUpdate();
    }
    
    function onBack() {
        WatchUi.popView(WatchUi.SLIDE_RIGHT);
    }
}

// Translation for Max HR title
var TR_MAX_HR_TITLE = ["Max HR", "דופק מקס", "FC Máx", "FC Max", "Max HF", "最大心率"];

class MaxHRMenu extends WatchUi.Menu2 {
    function initialize() {
        Menu2.initialize({:title => TR_MAX_HR_TITLE[getLang()]});
        // Add Cancel option at the top for touchscreen users
        var lang = getLang();
        var cancelLabels = ["← Back", "← חזרה", "← Volver", "← Retour", "← Zurück", "← 返回"];
        addItem(new WatchUi.MenuItem(cancelLabels[lang], null, -1, null));
        addItem(new WatchUi.MenuItem(TR_AUTO[getLang()], null, 0, null));
        var pcts = [50, 55, 60, 65, 70, 75, 80, 85, 90];
        for (var i = 0; i < pcts.size(); i++) {
            addItem(new WatchUi.MenuItem(pcts[i].toString() + "%", null, i + 1, null));
        }
    }
}

class MaxHRMenuDelegate extends WatchUi.Menu2InputDelegate {
    var mView;
    function initialize(view) { Menu2InputDelegate.initialize(); mView = view; }
    
    function onSelect(item) {
        var hrMode = item.getId();
        
        // If Cancel/Back was selected, just go back
        if (hrMode == -1) {
            WatchUi.popView(WatchUi.SLIDE_DOWN);
            return;
        }
        
        Application.Storage.setValue("hrMode", hrMode);
        
        // FIRST close the menu, THEN show the alert!
        WatchUi.popView(WatchUi.SLIDE_DOWN);
        
        if (mView != null) {
            mView.setHrMode(hrMode);
            mView.confirmHrMode();  // This will show the alert AFTER menu is closed
        }
    }
    
    function onBack() { WatchUi.popView(WatchUi.SLIDE_DOWN); }
}

// ╔════════════════════════════════════════════════════════════╗
// ║  NAME ENTRY VIEW - KEYCAPS (SIMULATOR-LIKE)               ║
// ║  Row keyboard based on selected language                  ║
// ╚════════════════════════════════════════════════════════════╝

class NameEntryView extends WatchUi.View {
    var mName = "";
    var mRows = null;
    var mKeyZones = null;
    var mOkZone = null;
    var mSpaceZone = null;
    var mBackZone = null;
    var mCancelZone = null;
    var mW = 280;
    var mH = 280;

    function initialize(initialName) {
        View.initialize();
        mName = initialName;
        _buildKeyboardRows();
    }

    function _buildKeyboardRows() {
        var lang = getLang();
        mRows = [];

        if (lang == 0) { // English
            mRows = [
                ["P","O","I","U","Y","T","R","E","W","Q"],
                ["L","K","J","H","G","F","D","S","A"],
                ["M","N","B","V","C","X","Z"]
            ];
        } else if (lang == 1) { // Hebrew
            mRows = [
                ["ק","ר","א","ט","ו","ן","ם","פ"],
                ["ש","ד","ג","כ","ע","י","ח","ל","ך","ף"],
                ["ז","ס","ב","ה","נ","מ","צ","ת","ץ"]
            ];
        } else if (lang == 2) { // Spanish
            mRows = [
                ["P","O","I","U","Y","T","R","E","W","Q"],
                ["Ñ","L","K","J","H","G","F","D","S","A"],
                ["M","N","B","V","C","X","Z"]
            ];
        } else if (lang == 3) { // French
            mRows = [
                ["P","O","I","U","Y","T","R","E","W","Q"],
                ["À","L","K","J","H","G","F","D","S","A"],
                ["M","N","B","V","C","X","Z","É","È"]
            ];
        } else if (lang == 4) { // German
            mRows = [
                ["P","O","I","U","Y","T","R","E","W","Q"],
                ["Ü","L","K","J","H","G","F","D","S","A"],
                ["M","N","B","V","C","X","Z","Ä","Ö"]
            ];
        } else { // Chinese
            mRows = [
                ["李","王","张","刘","陈","杨"],
                ["赵","黄","周","吴","徐","孙"],
                ["朱","马","胡","郭","林","何"]
            ];
        }
    }

    function _appendChar(ch) {
        if (mName.length() >= 12) { return; }
        mName = mName + ch;
        WatchUi.requestUpdate();
    }

    function _backspace() {
        if (mName.length() <= 0) { return; }
        mName = mName.substring(0, mName.length() - 1);
        WatchUi.requestUpdate();
    }

    function _space() {
        if (mName.length() <= 0) { return; }
        if (mName.length() >= 12) { return; }
        mName = mName + " ";
        WatchUi.requestUpdate();
    }

    function getOkZone() { return mOkZone; }
    function getSpaceZone() { return mSpaceZone; }
    function getBackZone() { return mBackZone; }
    function getCancelZone() { return mCancelZone; }
    function getKeyZones() { return mKeyZones; }
    function getName() { return mName; }
    function getW() { return mW; }
    function getH() { return mH; }

    function onUpdate(dc) {
        var w = dc.getWidth();
        var h = dc.getHeight();
        mW = w;
        mH = h;

        var color = getMainColor();
        var lang = getLang();

        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        dc.clear();

        var fieldFont = Graphics.FONT_MEDIUM;
        var keyFont = Graphics.FONT_TINY;

        // Text field with ✓ inside
        var fieldY = h / 8;
        var fieldH = h / 9;
        var fieldW = w * 6 / 10;
        var fieldX = (w - fieldW) / 2;

        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        dc.fillRoundedRectangle(fieldX, fieldY, fieldW, fieldH, h / 60);
        
        dc.setColor(color, Graphics.COLOR_TRANSPARENT);
        dc.drawRectangle(fieldX, fieldY, fieldW, fieldH);

        // ✓ inside field (right side)
        var checkW = fieldH;
        var checkX = fieldX + fieldW - checkW;
        
        dc.setColor(color, color);
        dc.fillRectangle(checkX, fieldY, checkW, fieldH);
        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_TRANSPARENT);
        dc.drawText(checkX + checkW / 2, fieldY + fieldH / 6, keyFont, "V", Graphics.TEXT_JUSTIFY_CENTER);
        mOkZone = [fieldY, fieldY + fieldH, checkX, checkX + checkW];

        // Name text
        var shown = mName;
        if (shown == null || shown.equals("")) { shown = ""; }
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        dc.drawText(fieldX + (fieldW - checkW) / 2, fieldY + (fieldH - dc.getFontHeight(fieldFont)) / 2, fieldFont, shown, Graphics.TEXT_JUSTIFY_CENTER);

        // Keyboard
        var totalRows = mRows.size() + 1;
        var availableHeight = h - fieldY - fieldH - h / 12;
        var keyH = availableHeight / (totalRows + 1);
        var gap = keyH / 8;
        
        mKeyZones = [];
        var keyboardStartY = fieldY + fieldH + h / 20;
        var centerY = h / 2;
        var radius = w / 2;

        for (var r = 0; r < mRows.size(); r++) {
            var row = mRows[r];
            var cols = row.size();
            
            var rowY = keyboardStartY + r * (keyH + gap);
            
            var distFromCenter = rowY + keyH / 2 - centerY;
            if (distFromCenter < 0) { distFromCenter = -distFromCenter; }
            
            var ratio = distFromCenter * 100 / radius;
            var availableWidth;
            if (ratio < 15) {
                availableWidth = w * 98 / 100;
            } else if (ratio < 30) {
                availableWidth = w * 96 / 100;
            } else if (ratio < 45) {
                availableWidth = w * 92 / 100;
            } else if (ratio < 60) {
                availableWidth = w * 85 / 100;
            } else if (ratio < 75) {
                availableWidth = w * 75 / 100;
            } else if (ratio < 88) {
                availableWidth = w * 60 / 100;
            } else {
                availableWidth = w * 45 / 100;
            }
            
            var keyW = (availableWidth - (cols - 1) * gap) / cols;
            var rowX = (w - availableWidth) / 2;

            for (var c = 0; c < cols; c++) {
                var x;
                if (lang == 1) {
                    x = rowX + (cols - 1 - c) * (keyW + gap);
                } else {
                    x = rowX + c * (keyW + gap);
                }

                dc.setColor(Graphics.COLOR_DK_GRAY, Graphics.COLOR_DK_GRAY);
                dc.fillRoundedRectangle(x, rowY, keyW, keyH, h / 80);

                dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
                dc.drawText(x + keyW / 2, rowY + (keyH - dc.getFontHeight(keyFont)) / 2, keyFont, row[c], Graphics.TEXT_JUSTIFY_CENTER);

                mKeyZones.add([rowY, rowY + keyH, x, x + keyW, row[c]]);
            }
        }

        // Bottom row: space and backspace
        var ctrlY = keyboardStartY + mRows.size() * (keyH + gap);
        var ctrlH = keyH;
        
        var bottomDistFromCenter = ctrlY + ctrlH / 2 - centerY;
        if (bottomDistFromCenter < 0) { bottomDistFromCenter = -bottomDistFromCenter; }
        var bottomRatio = bottomDistFromCenter * 100 / radius;
        
        var bottomWidth;
        if (bottomRatio < 60) {
            bottomWidth = w * 70 / 100;
        } else if (bottomRatio < 80) {
            bottomWidth = w * 55 / 100;
        } else {
            bottomWidth = w * 40 / 100;
        }
        
        var spaceW = bottomWidth * 2 / 3;
        var backW = bottomWidth / 3 - gap;
        
        var spaceX = (w - bottomWidth) / 2;
        var backX = spaceX + spaceW + gap;

        // Space button
        dc.setColor(Graphics.COLOR_DK_GRAY, Graphics.COLOR_DK_GRAY);
        dc.fillRoundedRectangle(spaceX, ctrlY, spaceW, ctrlH, h / 80);
        mSpaceZone = [ctrlY, ctrlY + ctrlH, spaceX, spaceX + spaceW];

        // Backspace button
        dc.setColor(Graphics.COLOR_DK_GRAY, Graphics.COLOR_DK_GRAY);
        dc.fillRoundedRectangle(backX, ctrlY, backW, ctrlH, h / 80);
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        dc.drawText(backX + backW / 2, ctrlY + (ctrlH - dc.getFontHeight(keyFont)) / 2, keyFont, "<", Graphics.TEXT_JUSTIFY_CENTER);
        mBackZone = [ctrlY, ctrlY + ctrlH, backX, backX + backW];
        
        mCancelZone = null;
    }
}

class NameEntryDelegate extends WatchUi.BehaviorDelegate {
    function initialize() { BehaviorDelegate.initialize(); }

    function onTap(evt) {
        var coords = evt.getCoordinates();
        if (coords == null) { return false; }

        var tapX = coords[0];
        var tapY = coords[1];

        var v = WatchUi.getCurrentView()[0];
        if (v == null || !(v instanceof NameEntryView)) { return false; }

        // OK
        var ok = v.getOkZone();
        if (ok != null && tapY >= ok[0] && tapY <= ok[1] && tapX >= ok[2] && tapX <= ok[3]) {
            Application.Storage.setValue("userName", v.getName());
            WatchUi.popView(WatchUi.SLIDE_RIGHT);
            WatchUi.requestUpdate();
            return true;
        }

        // Space
        var sp = v.getSpaceZone();
        if (sp != null && tapY >= sp[0] && tapY <= sp[1] && tapX >= sp[2] && tapX <= sp[3]) {
            v._space();
            return true;
        }

        // Backspace
        var bk = v.getBackZone();
        if (bk != null && tapY >= bk[0] && tapY <= bk[1] && tapX >= bk[2] && tapX <= bk[3]) {
            v._backspace();
            return true;
        }

        // Cancel
        var cx = v.getCancelZone();
        if (cx != null && tapY >= cx[0] && tapY <= cx[1] && tapX >= cx[2] && tapX <= cx[3]) {
            Application.Storage.setValue("userName", v.getName());
            WatchUi.popView(WatchUi.SLIDE_RIGHT);
            WatchUi.requestUpdate();
            return true;
        }

        // Keycaps
        var zones = v.getKeyZones();
        if (zones != null) {
            for (var i = 0; i < zones.size(); i++) {
                var z = zones[i];
                if (tapY >= z[0] && tapY <= z[1] && tapX >= z[2] && tapX <= z[3]) {
                    v._appendChar(z[4]);
                    return true;
                }
            }
        }

        return false;
    }

    function onBack() {
        WatchUi.popView(WatchUi.SLIDE_RIGHT);
        return true;
    }
}
