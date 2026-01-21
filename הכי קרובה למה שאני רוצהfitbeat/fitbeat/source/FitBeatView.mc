using Toybox.WatchUi;
using Toybox.Graphics;
using Toybox.System;
using Toybox.Application;
using Toybox.Activity;
using Toybox.ActivityMonitor;
using Toybox.Timer;
using Toybox.Attention;

// ╔════════════════════════════════════════════════════════════╗
// ║  MAIN VIEW - FitBeat v4.3.0 - UPDATED                     ║
// ║  Displays: Time, Distance, Steps, Heart Rate              ║
// ║  ALL POSITIONS IN PERCENTAGES!                            ║
// ║  EXACT FONT SIZES PER GARMIN SPECS:                       ║
// ║  Time: FONT_NUMBER_MILD (62px)                          ║
// ║  Numbers: FONT_MEDIUM (39px)                              ║
// ║  Labels: FONT_XTINY (22px)                                ║
// ║  Heart Rate: FONT_NUMBER_MILD (62px)                      ║
// ╚════════════════════════════════════════════════════════════╝

class FitBeatView extends WatchUi.View {

    // Active goal mode (distance or time)
    const MODE_DISTANCE = 0;
    const MODE_TIME = 1;
    
    var mGoalDist = 5;
    var mGoalTimeMin = 30;
    var mActiveGoalMode = MODE_DISTANCE;
    var mHrMode = 0;
    var mHrTarget = 0;
    var mMaxHR = 190;
    
    var mActivityStarted = false;
    var mStartSteps = 0;
    var mStartDistCm = 0;

    // Walking time only advances when the user is actually moving
    var mElapsedWalkSec = 0;
    var mLastRawSteps = 0;
    var mLastRawDistCm = 0;
    
    var mHrAlertShown = false;
    var mHalfwayAlertShown = false;
    var mGoalAlertShown = false;
    var mHrMonitoringActive = false;
    
    var mTimer = null;
    
    // Tap zones (saved after drawing)
    var mTimeZoneTop = 0;
    var mTimeZoneBottom = 0;
    var mDistZoneTop = 0;
    var mDistZoneBottom = 0;
    var mTimeGoalZoneTop = 0;
    var mTimeGoalZoneBottom = 0;
    var mHrZoneTop = 0;
    var mHrZoneBottom = 0;
    
    var mAlertActive = false;
    var mAlertTimer = 0;

    function initialize() {
        View.initialize();
        _loadState();
    }

    function onShow() { _startTimer(); }
    function onHide() { _stopTimer(); }
    
    function _loadState() {
        try {
            var v = Application.Storage.getValue("goalDist");
            if (v != null) { mGoalDist = v; }
            v = Application.Storage.getValue("goalTimeMin");
            if (v != null) { mGoalTimeMin = v; }
            v = Application.Storage.getValue("activeGoalMode");
            if (v != null) { mActiveGoalMode = v; }
            v = Application.Storage.getValue("elapsedWalkSec");
            if (v != null) { mElapsedWalkSec = v; }
            v = Application.Storage.getValue("hrMode");
            if (v != null) { mHrMode = v; }
            v = Application.Storage.getValue("maxHr");
            if (v != null) { mMaxHR = v; }
            
            var started = Application.Storage.getValue("activityStarted");
            if (started != null && started == true) {
                mActivityStarted = true;
                var ss = Application.Storage.getValue("startSteps");
                if (ss != null) { mStartSteps = ss; }
                var sd = Application.Storage.getValue("startDist");
                if (sd != null) { mStartDistCm = sd; }
                var hs = Application.Storage.getValue("halfwayShown");
                if (hs != null) { mHalfwayAlertShown = hs; }
                var gs = Application.Storage.getValue("goalShown");
                if (gs != null) { mGoalAlertShown = gs; }

                // Optional persist
                var es = Application.Storage.getValue("elapsedWalkSec");
                if (es != null) { mElapsedWalkSec = es; }
            }
        } catch(e) {}
    }
    
    function _saveState() {
        try {
            Application.Storage.setValue("activityStarted", mActivityStarted);
            Application.Storage.setValue("startSteps", mStartSteps);
            Application.Storage.setValue("startDist", mStartDistCm);
            Application.Storage.setValue("halfwayShown", mHalfwayAlertShown);
            Application.Storage.setValue("goalShown", mGoalAlertShown);
            Application.Storage.setValue("activeGoalMode", mActiveGoalMode);
            Application.Storage.setValue("elapsedWalkSec", mElapsedWalkSec);
        } catch(e) {}
    }
    
    // ═══ PUBLIC API ═══
    function getTimeZone() { return [mTimeZoneTop, mTimeZoneBottom]; }
    function getDistZone() { return [mDistZoneTop, mDistZoneBottom]; }
    function getTimeGoalZone() { return [mTimeGoalZoneTop, mTimeGoalZoneBottom]; }
    function getHrZone() { return [mHrZoneTop, mHrZoneBottom]; }
    
    function setGoal(goal) { 
        var oldGoal = mGoalDist;
        mGoalDist = goal; 
        Application.Storage.setValue("goalDist", goal);
        
        // If activity is running and goal changed, recalculate alerts
        if (mActivityStarted && goal != oldGoal) {
            // Recalculate if we need to show halfway/goal alerts for new goal
            var m = _getMetrics();
            var distCm = m[1];
            var newGoalCm = _getGoalInCm();
            var newHalfway = newGoalCm / 2;
            
            // If we haven't reached new halfway yet, allow alert again
            if (distCm < newHalfway) {
                mHalfwayAlertShown = false;
            }
            // If we haven't reached new goal yet, allow alert again
            if (distCm < newGoalCm) {
                mGoalAlertShown = false;
            }
            _saveState();
        }
    }

    function setTimeGoal(goalMin) {
        var oldGoal = mGoalTimeMin;
        mGoalTimeMin = goalMin;
        Application.Storage.setValue("goalTimeMin", goalMin);

        // If time goal changed mid-activity, allow alerts again if we're below thresholds
        if (mActivityStarted && mActiveGoalMode == MODE_TIME && goalMin != oldGoal) {
            var goalSec = _getGoalTimeSec();
            var halfway = goalSec / 2;
            if (mElapsedWalkSec < halfway) { mHalfwayAlertShown = false; }
            if (mElapsedWalkSec < goalSec) { mGoalAlertShown = false; }
            _saveState();
        }
    }
    
    function setHrMode(mode) {
        mHrMode = mode;
        Application.Storage.setValue("hrMode", mode);
    }
    
    function startActivity(mode) {
        if (mode == null) { mode = MODE_DISTANCE; }
        mActiveGoalMode = mode;

        // START button ALWAYS starts a NEW activity and resets counters!
        // Reset the baseline to current values (effectively resetting to 0)
        try {
            var info = ActivityMonitor.getInfo();
            if (info != null) {
                if (info.steps != null) { mStartSteps = info.steps; }
                if (info.distance != null) { mStartDistCm = info.distance; }
                if (info.steps != null) { mLastRawSteps = info.steps; }
                if (info.distance != null) { mLastRawDistCm = info.distance; }
            }
        } catch(e) {}
        
        mActivityStarted = true;
        mElapsedWalkSec = 0;
        mHalfwayAlertShown = false;
        mGoalAlertShown = false;
        _calculateHrTarget();
        _saveState();
        WatchUi.requestUpdate();
    }
    
    function confirmHrMode() {
        _calculateHrTarget();
        mHrMonitoringActive = true;
        mHrAlertShown = false;
        _vibrate();
        WatchUi.requestUpdate();
    }
    
    function _calculateHrTarget() {
        if (mHrMode == 0) {
            var hr = _getHeartRate();
            if (hr != null && hr > 50) {
                mHrTarget = hr + 15;
                if (mHrTarget > mMaxHR) { mHrTarget = mMaxHR; }
            } else {
                mHrTarget = 100;
            }
        } else {
            var pct = 50 + (mHrMode - 1) * 5;
            mHrTarget = (mMaxHR * pct / 100);
        }
    }
    
    // ═══ SHOW FULL SCREEN ALERT (NOT OVERLAY!) ═══
    function _showFullScreenAlert(line1, line2) {
        var lang = getLang();
        var l1;
        var l2;
        if (line1 instanceof Array) {
            l1 = line1[lang];
        } else {
            l1 = line1;
        }
        if (line2 instanceof Array) {
            l2 = line2[lang];
        } else {
            l2 = line2;
        }
        
        _vibrate();
        
        // Push FULL SCREEN alert view
        WatchUi.pushView(new AlertView(l1, l2), new AlertViewDelegate(), WatchUi.SLIDE_UP);
        
        // Auto-dismiss after 5 seconds
        mAlertActive = true;
        mAlertTimer = 5;
    }

    function _getUserName() {
        try {
            var n = Application.Storage.getValue("userName");
            if (n != null && n != "") { return n; }
        } catch(e) {}
        return "";
    }
    
    function _vibrate() {
        try {
            if (Attention has :vibrate) {
                var vibeData = [new Attention.VibeProfile(100, 500)];
                Attention.vibrate(vibeData);
            }
        } catch(e) {}
    }
    
    // ═══ HELPERS ═══
    function _twoDigits(n) {
        if (n < 10) { return "0" + n.toString(); }
        return n.toString();
    }

    // Draw HH:MM left-to-right even inside RTL (avoids bidi control chars that can render as squares)
    function _drawTimeSplit(dc, x, y, f, hour, min) {
        var h = _twoDigits(hour);
        var m = _twoDigits(min);
        var c = ":";

        var wH = dc.getTextWidthInPixels(h, f);
        var wC = dc.getTextWidthInPixels(c, f);

        dc.drawText(x, y, f, h, Graphics.TEXT_JUSTIFY_LEFT);
        dc.drawText(x + wH, y, f, c, Graphics.TEXT_JUSTIFY_LEFT);
        dc.drawText(x + wH + wC, y, f, m, Graphics.TEXT_JUSTIFY_LEFT);
    }

    function _distStr(distCm) {
        if (distCm == null || distCm < 0) { return "0.00"; }
        var lang = getLang();
        
        var dist;
        if (lang == 0) { // English = miles
            dist = distCm / 160934.0;
        } else {
            dist = distCm / 100000.0;
        }
        
        var intPart = dist.toNumber();
        var frac = ((dist - intPart) * 100 + 0.5).toNumber();
        if (frac >= 100) { intPart += 1; frac = 0; }
        var fracStr = frac < 10 ? "0" + frac : frac.toString();
        return intPart.toString() + "." + fracStr;
    }
    
    function _getGoalInCm() {
        var lang = getLang();
        if (lang == 0) {
            return mGoalDist * 160934;
        } else {
            return mGoalDist * 100000;
        }
    }

    function _getGoalTimeSec() {
        if (mGoalTimeMin == null || mGoalTimeMin <= 0) { return 0; }
        return mGoalTimeMin * 60;
    }
    
    function _clamp01(x) {
        if (x < 0.0) { return 0.0; }
        if (x > 1.0) { return 1.0; }
        return x;
    }

    function _getHeartRate() {
        try {
            var actInfo = Activity.getActivityInfo();
            if (actInfo != null && actInfo.currentHeartRate != null) {
                return actInfo.currentHeartRate;
            }
        } catch(e) {}
        
        try {
            var it = ActivityMonitor.getHeartRateHistory(1, true);
            var s = it.next();
            if (s != null && s.heartRate != null && s.heartRate != ActivityMonitor.INVALID_HR_SAMPLE) {
                return s.heartRate;
            }
        } catch(e) {}
        
        return null;
    }

    function _getMetrics() {
        var steps = 0;
        var distCm = 0;
        var hr = null;

        try {
            var info = ActivityMonitor.getInfo();
            if (info != null) {
                if (info.steps != null) { steps = info.steps; }
                if (info.distance != null) { distCm = info.distance; }
            }
        } catch(e) {}

        if (mActivityStarted) {
            steps = steps - mStartSteps;
            distCm = distCm - mStartDistCm;
            if (steps < 0) { steps = 0; }
            if (distCm < 0) { distCm = 0; }
        }

        hr = _getHeartRate();
        return [steps, distCm, hr];
    }

    function _startTimer() as Void {
        if (mTimer != null) { return; }
        mTimer = new Timer.Timer();
        mTimer.start(method(:_onTick), 1000, true);
    }

    function _stopTimer() as Void {
        if (mTimer != null) { mTimer.stop(); }
        mTimer = null;
    }

    function _onTick() as Void {
        // Auto-dismiss alert
        if (mAlertActive && mAlertTimer > 0) {
            mAlertTimer -= 1;
            if (mAlertTimer <= 0) {
                mAlertActive = false;
                WatchUi.popView(WatchUi.SLIDE_DOWN);
            }
        }
        
        if (mActivityStarted && !mAlertActive) {
            _updateWalkingTime();
            if (mActiveGoalMode == MODE_DISTANCE) {
                _checkDistanceAlerts();
            } else {
                _checkTimeAlerts();
            }
        }
        
        if (mHrMonitoringActive && !mAlertActive) {
            _checkHrAlert();
        }
        
        WatchUi.requestUpdate();
    }

    function _updateWalkingTime() {
        // Only count seconds when the user is actually moving (steps or distance changes)
        try {
            var info = ActivityMonitor.getInfo();
            if (info == null) { return; }
            var rawSteps = info.steps != null ? info.steps : 0;
            var rawDist = info.distance != null ? info.distance : 0;

            // On first tick after start, seed last values
            if (mLastRawSteps == 0 && mLastRawDistCm == 0) {
                mLastRawSteps = rawSteps;
                mLastRawDistCm = rawDist;
                return;
            }

            var moved = false;
            if (rawSteps > mLastRawSteps) { moved = true; }
            if (rawDist > mLastRawDistCm) { moved = true; }

            if (moved) {
                mElapsedWalkSec += 1;
                // Persist lightly so we can resume if app is reopened
                Application.Storage.setValue("elapsedWalkSec", mElapsedWalkSec);
            }

            mLastRawSteps = rawSteps;
            mLastRawDistCm = rawDist;
        } catch(e) {}
    }
    
    function _checkHrAlert() {
        var hr = _getHeartRate();
        var lang = getLang();
        var name = _getUserName();
        var prefix = name != "" ? (name + ", ") : "";
        
        if (hr != null && mHrTarget > 0 && !mHrAlertShown) {
            if (hr > mHrTarget) {
                _showFullScreenAlert(prefix + TR_REST_NOW[lang], TR_HR_TOO_HIGH[lang]);
                mHrAlertShown = true;
            }
        }
        
        // Reset when HR drops
        if (hr != null && mHrTarget > 0 && mHrAlertShown) {
            var threshold = mHrTarget - (mHrTarget * 5 / 100);
            if (hr <= threshold) {
                _showFullScreenAlert(prefix + TR_GO_AHEAD[lang], TR_HR_OK[lang]);
                mHrAlertShown = false;
            }
        }
    }
    
    function _checkDistanceAlerts() {
        var m = _getMetrics();
        var distCm = m[1];
        var goalCm = _getGoalInCm();
        var lang = getLang();
        var name = _getUserName();
        
        // Halfway alert
        if (!mHalfwayAlertShown && goalCm > 0) {
            var halfway = goalCm / 2;
            if (distCm >= halfway && distCm < goalCm) {
                var l1 = (name != "" ? (TR_WELL_DONE[lang] + " " + name + "!") : (TR_WELL_DONE[lang] + "!"));
                _showFullScreenAlert(l1, TR_HALF_WAY[lang]);
                mHalfwayAlertShown = true;
                _saveState();
            }
        }
        
        // Goal alert
        if (!mGoalAlertShown && goalCm > 0) {
            if (distCm >= goalCm) {
                var l1g = (name != "" ? (TR_GOAL_DONE_LINE1[lang] + " " + name + "!") : (TR_GOAL_DONE_LINE1[lang] + "!"));
                _showFullScreenAlert(l1g, TR_GOAL_DONE_LINE2[lang]);
                mGoalAlertShown = true;
                _saveState();
            }
        }
    }
    function _checkTimeAlerts() {
        var goalSec = _getGoalTimeSec();
        if (goalSec <= 0) { return; }

        var lang = getLang();
        var name = _getUserName();

        // Halfway
        if (!mHalfwayAlertShown) {
            var halfway = goalSec / 2;
            if (mElapsedWalkSec >= halfway && mElapsedWalkSec < goalSec) {
                var l1 = (name != "" ? (TR_WELL_DONE[lang] + " " + name + "!") : (TR_WELL_DONE[lang] + "!"));
                _showFullScreenAlert(l1, TR_HALF_WAY[lang]);
                mHalfwayAlertShown = true;
                _saveState();
            }
        }

        // Goal
        if (!mGoalAlertShown) {
            if (mElapsedWalkSec >= goalSec) {
                var l1g = (name != "" ? (TR_GOAL_DONE_LINE1[lang] + " " + name + "!") : (TR_GOAL_DONE_LINE1[lang] + "!"));
                _showFullScreenAlert(l1g, TR_GOAL_DONE_LINE2[lang]);
                mGoalAlertShown = true;
                _saveState();
            }
        }
    }

    // ═══ DRAW STAIRCASE BAR (RTL - Right to Left, big to small) ═══
    function _drawSegmentBar(dc, x, y, barW, barH, frac) {
        var w = dc.getWidth();
        var segCount = 5;
        var gap = w / 100;
        var totalGap = (segCount - 1) * gap;
        var totalSegW = barW - totalGap;
        var baseSegW = totalSegW / segCount;
        
        var color = getMainColor();
        var filled = (frac * segCount + 0.001).toNumber();
        if (filled > segCount) { filled = segCount; }
        
        // Draw segments from RIGHT to LEFT, heights decrease (staircase effect)
        // Segment 0 is rightmost and tallest, segment 4 is leftmost and shortest
        var segHeights = [barH * 5 / 5, barH * 4 / 5, barH * 3 / 5, barH * 2 / 5, barH * 1 / 5];
        
        for (var i = 0; i < segCount; i++) {
            // Position: rightmost segment first
            var segX = x + barW - (i + 1) * baseSegW - i * gap;
            var segH = segHeights[i];
            var segY = y + barH - segH;  // Align to bottom
            
            // Fill based on progress (RTL: segment 0 fills first)
            if (i < filled) {
                dc.setColor(color, color);
            } else {
                dc.setColor(Graphics.COLOR_DK_GRAY, Graphics.COLOR_DK_GRAY);
            }
            dc.fillRectangle(segX, segY, baseSegW, segH);
        }
    }
    
    // ═══ DRAW RUNNING PERSON ICON ═══
    function _drawRunnerIcon(dc, cx, cy, size, color) {
        dc.setColor(color, color);
        // Head
        dc.fillCircle(cx, cy - size * 3 / 4, size / 4);
        // Body (diagonal line)
        dc.fillRectangle(cx - size / 10, cy - size / 2, size / 5, size / 2);
        // Legs (V shape)
        dc.fillRectangle(cx - size / 3, cy, size / 5, size / 3);
        dc.fillRectangle(cx + size / 8, cy - size / 6, size / 5, size / 2);
        // Arms
        dc.fillRectangle(cx - size / 4, cy - size / 3, size / 2, size / 6);
    }
    
    // ═══ DRAW HEART ICON ═══
    function _drawHeartIcon(dc, cx, cy, size, color) {
        dc.setColor(color, color);
        var r = size / 3;
        dc.fillCircle(cx - r, cy - r / 2, r);
        dc.fillCircle(cx + r, cy - r / 2, r);
        // Bottom triangle
        dc.fillPolygon([
            [cx - size * 2 / 3, cy],
            [cx + size * 2 / 3, cy],
            [cx, cy + size * 2 / 3]
        ]);
    }
    
    // ═══ DRAW FOOTPRINTS ICON ═══
    function _drawFootprintsIcon(dc, cx, cy, size, color) {
        dc.setColor(color, color);
        var footW = size / 4;
        var footH = size / 2;
        // Left foot
        dc.fillEllipse(cx - size / 3, cy - size / 6, footW, footH);
        dc.fillCircle(cx - size / 3, cy - size / 2, footW / 2);
        // Right foot (slightly lower)
        dc.fillEllipse(cx + size / 4, cy + size / 6, footW, footH);
        dc.fillCircle(cx + size / 4, cy - size / 4, footW / 2);
    }
    
    // ═══ DRAW CLOCK ICON ═══
    function _drawClockIcon(dc, cx, cy, size, color) {
        dc.setColor(color, color);
        var r = size / 2;
        // Circle outline
        dc.drawCircle(cx, cy, r);
        dc.drawCircle(cx, cy, r - 1);
        // Hour hand
        dc.fillRectangle(cx - 1, cy - r * 2 / 3, 2, r * 2 / 3);
        // Minute hand
        dc.fillRectangle(cx, cy - 1, r / 2, 2);
    }

    // ═══ MAIN SCREEN DRAWING ═══
    // ALL POSITIONS IN PERCENTAGES OF w AND h!
    function onUpdate(dc) {
        var w = dc.getWidth();
        var h = dc.getHeight();
        var lang = getLang();
        var color = getMainColor();

        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        dc.clear();

        var m = _getMetrics();
        var distCm = m[1];
        var hr = m[2];

        // ═══ EXACT FONTS PER SPEC ═══
        // System fonts - always use standard Garmin fonts (Hebrew not supported natively)
        var fTime = Graphics.FONT_NUMBER_MILD;
        var fNumbers = Graphics.FONT_MEDIUM;      // values
        var fLabels = Graphics.FONT_XTINY;        // units/labels
        var fHR = Graphics.FONT_NUMBER_MILD;      // heart rate digits
        
        var hTime = dc.getFontHeight(fTime);
        var hNumbers = dc.getFontHeight(fNumbers);
        var hLabels = dc.getFontHeight(fLabels);
        var hHR = dc.getFontHeight(fHR);
        
        // ═══ ALL POSITIONS IN PERCENTAGES! ═══
        var padSide = w / 14;             // Side padding = ~7%
        var iconSize = w / 11;            // Icon size = ~9%
        var barH = h / 28;                // Bar height = smaller
        var y = h / 40;                   // Start Y = 2.5%

        // ═══ TIME (CENTERED!) ═══
        mTimeZoneTop = 0;
        var ct = System.getClockTime();
        dc.setColor(color, Graphics.COLOR_BLACK);
        var timeStr = _twoDigits(ct.hour) + ":" + _twoDigits(ct.min);
        dc.drawText(w / 2, y, fTime, timeStr, Graphics.TEXT_JUSTIFY_CENTER);
        y += hTime + h / 50;
        mTimeZoneBottom = y;

        // ═══ DISTANCE - FONT_MEDIUM (39px) ═══
        mDistZoneTop = y;
        var distStr = _distStr(distCm);
        if (_isHebrew(lang)) { distStr = "" + distStr + ""; }
        dc.setColor(color, Graphics.COLOR_BLACK);
        dc.drawText(padSide, y, fNumbers, distStr, Graphics.TEXT_JUSTIFY_LEFT);
        var valW = dc.getTextWidthInPixels(distStr, fNumbers);
        dc.setColor(color, Graphics.COLOR_BLACK);
        var unitStr = LANG_UNITS[lang];
        if (_isHebrew(lang)) { unitStr = "" + unitStr + ""; }
        dc.drawText(padSide + valW + w / 56, y + (hNumbers - hLabels) / 2, fLabels, unitStr, Graphics.TEXT_JUSTIFY_LEFT);
        
        // Running person icon (right side)
        var iconX = w - padSide - iconSize / 2;
        var iconY = y + hNumbers / 2;
        _drawRunnerIcon(dc, iconX, iconY, iconSize, color);
        y += hNumbers + h / 100;

        // Distance progress bar (staircase RTL)
        var barW = w - padSide * 2;
        var goalCm = _getGoalInCm();
        var distFrac = goalCm > 0 ? _clamp01((distCm * 1.0) / goalCm) : 0.0;
        _drawSegmentBar(dc, padSide, y, barW, barH, distFrac);
        y += barH + h / 25;
        mDistZoneBottom = y;

        // ═══ TIME (minutes walked) ═══
        mTimeGoalZoneTop = y;
        var elapsedMin = (mElapsedWalkSec / 60).toNumber();
        var timeMinStr = elapsedMin.toString();
        if (_isHebrew(lang)) { timeMinStr = "" + timeMinStr + ""; }
        dc.setColor(color, Graphics.COLOR_BLACK);
        dc.drawText(padSide, y, fNumbers, timeMinStr, Graphics.TEXT_JUSTIFY_LEFT);
        valW = dc.getTextWidthInPixels(timeMinStr, fNumbers);
        dc.setColor(color, Graphics.COLOR_BLACK);
        dc.drawText(padSide + valW + w / 56, y + (hNumbers - hLabels) / 2, fLabels, TR_MINUTES[lang], Graphics.TEXT_JUSTIFY_LEFT);

        // Clock icon (right side)
        iconX = w - padSide - iconSize / 2;
        iconY = y + hNumbers / 2;
        _drawClockIcon(dc, iconX, iconY, iconSize, color);

        y += hNumbers + h / 100;

        // Time progress bar (staircase RTL)
        var goalSec = _getGoalTimeSec();
        var timeFrac = goalSec > 0 ? _clamp01((mElapsedWalkSec * 1.0) / goalSec) : 0.0;
        _drawSegmentBar(dc, padSide, y, barW, barH, timeFrac);
        y += barH + h / 25;
        mTimeGoalZoneBottom = y;

        // ═══ HEART RATE - FONT_NUMBER_MILD (62px) - raised up ═══
        mHrZoneTop = h - h / 3;
        var hrY = h - h / 6;
        var hrStr = "--";
        if (hr != null) { hrStr = hr.toString(); }
        if (_isHebrew(lang)) { hrStr = "" + hrStr + ""; }

        // Centered group at bottom: [heart icon] + gap + [HR number]
        var hr_size = iconSize / 3;
        var heartW  = 4 * hr_size;
        var gapW    = w / 60;
        var textW   = dc.getTextWidthInPixels(hrStr, fHR);
        var groupW  = heartW + gapW + textW;
        var groupX  = (w - groupW) / 2;

        // Heart icon
        var hx = groupX + heartW / 2;
        var hy = hrY + h / 60;
        dc.setColor(color, color);
        dc.fillCircle(hx - hr_size, hy - hr_size / 2, hr_size);
        dc.fillCircle(hx + hr_size, hy - hr_size / 2, hr_size);
        dc.fillPolygon([[hx - 2 * hr_size, hy], [hx + 2 * hr_size, hy], [hx, hy + 2 * hr_size]]);

        // HR number
        dc.setColor(color, Graphics.COLOR_BLACK);
        var textX = groupX + heartW + gapW;
        dc.drawText(textX, hrY - hHR / 3 + h / 80, fHR, hrStr, Graphics.TEXT_JUSTIFY_LEFT);
        mHrZoneBottom = h;
    }
}
