using Toybox.WatchUi;
using Toybox.Graphics;
using Toybox.System;
using Toybox.Application;
using Toybox.Activity;
using Toybox.ActivityMonitor;
using Toybox.Timer;
using Toybox.Attention;
using Toybox.Time;
using Toybox.Time.Gregorian;

// ╔════════════════════════════════════════════════════════════╗
// ║  MAIN VIEW - FitBeat v4.3.2 - SEPARATE GOALS FIX          ║
// ║  Displays: Time, Distance, Time Goal, Heart Rate          ║
// ║  ALL POSITIONS IN PERCENTAGES!                            ║
// ║  SEPARATE GOALS: Distance & Time work INDEPENDENTLY!      ║
// ║  EXACT FONT SIZES PER GARMIN SPECS                        ║
// ╚════════════════════════════════════════════════════════════╝

class FitBeatView extends WatchUi.View {

    // Active goal modes (SEPARATE!)
    const MODE_DISTANCE = 0;
    const MODE_TIME = 1;
    
    var mGoalDist = 5;
    var mGoalTimeMin = 30;
    var mHrMode = 0;
    var mHrTarget = 0;
    var mMaxHR = 190;
    
    // ═══ SEPARATE GOAL TRACKING! ═══
    var mDistGoalActive = false;    // Is distance goal active?
    var mTimeGoalActive = false;    // Is time goal active?
    
    var mStartSteps = 0;
    var mStartDistCm = 0;
    var mDistanceCm = 0;            // Current distance in cm

    // Walking time - counts every second when time goal is active
    var mElapsedWalkSec = 0;
    var mLastRawSteps = 0;
    var mLastRawDistCm = 0;
    
    // ═══ SMART TIMER - Track movement for 5-minute stop detection ═══
    var mLastMovementTime = 0;      // Time of last detected movement
    var mLastStepsForMovement = 0;  // Steps count at last check
    
    // ═══ SEPARATE ALERTS FOR EACH GOAL! ═══
    var mDistHalfwayShown = false;
    var mDistGoalShown = false;
    var mTimeHalfwayShown = false;
    var mTimeGoalShown = false;
    
    var mHrAlertShown = false;
    var mHrMonitoringActive = false;
    
    var mTimer = null;
    var mIsVisible = false;
    
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

    function initialize() {
        View.initialize();
        _loadState();
    }

    function onShow() { 
        mIsVisible = true;
        _loadState();  // Reload state when returning from picker
        _startTimer(); 
    }
    
    function onHide() { 
        mIsVisible = false;
        _saveState();  // Save state before switching to another screen
        _stopTimer(); 
    }
    
    function _loadState() {
        try {
            var v = Application.Storage.getValue("goalDist");
            if (v != null) { mGoalDist = v; }
            v = Application.Storage.getValue("goalTimeMin");
            if (v != null) { mGoalTimeMin = v; }
            v = Application.Storage.getValue("elapsedWalkSec");
            if (v != null) { mElapsedWalkSec = v; }
            v = Application.Storage.getValue("hrMode");
            if (v != null) { mHrMode = v; }
            v = Application.Storage.getValue("maxHr");
            if (v != null) { mMaxHR = v; }
            
            // Load separate goal states
            var distActive = Application.Storage.getValue("distGoalActive");
            if (distActive != null) { mDistGoalActive = distActive; }
            
            var timeActive = Application.Storage.getValue("timeGoalActive");
            if (timeActive != null) { mTimeGoalActive = timeActive; }
            
            // Load distance baseline
            var ss = Application.Storage.getValue("startSteps");
            if (ss != null) { mStartSteps = ss; }
            var sd = Application.Storage.getValue("startDist");
            if (sd != null) { mStartDistCm = sd; }
            var dc = Application.Storage.getValue("distanceCm");
            if (dc != null) { mDistanceCm = dc; }
            
            // Load separate alert states
            var dhs = Application.Storage.getValue("distHalfwayShown");
            if (dhs != null) { mDistHalfwayShown = dhs; }
            var dgs = Application.Storage.getValue("distGoalShown");
            if (dgs != null) { mDistGoalShown = dgs; }
            var ths = Application.Storage.getValue("timeHalfwayShown");
            if (ths != null) { mTimeHalfwayShown = ths; }
            var tgs = Application.Storage.getValue("timeGoalShown");
            if (tgs != null) { mTimeGoalShown = tgs; }
            
        } catch(e) {}
    }
    
    function _saveState() {
        try {
            // Save separate goal states
            Application.Storage.setValue("distGoalActive", mDistGoalActive);
            Application.Storage.setValue("timeGoalActive", mTimeGoalActive);
            Application.Storage.setValue("startSteps", mStartSteps);
            Application.Storage.setValue("startDist", mStartDistCm);
            Application.Storage.setValue("distanceCm", mDistanceCm);
            Application.Storage.setValue("elapsedWalkSec", mElapsedWalkSec);
            
            // Save separate alert states
            Application.Storage.setValue("distHalfwayShown", mDistHalfwayShown);
            Application.Storage.setValue("distGoalShown", mDistGoalShown);
            Application.Storage.setValue("timeHalfwayShown", mTimeHalfwayShown);
            Application.Storage.setValue("timeGoalShown", mTimeGoalShown);
        } catch(e) {}
    }
    
    // ═══ PUBLIC API ═══
    function getTimeZone() { return [mTimeZoneTop, mTimeZoneBottom]; }
    function getDistZone() { return [mDistZoneTop, mDistZoneBottom]; }
    function getTimeGoalZone() { return [mTimeGoalZoneTop, mTimeGoalZoneBottom]; }
    function getHrZone() { return [mHrZoneTop, mHrZoneBottom]; }
    function isDistGoalActive() { return mDistGoalActive; }
    function isTimeGoalActive() { return mTimeGoalActive; }
    
    function setGoal(goal) { 
        var oldGoal = mGoalDist;
        mGoalDist = goal; 
        Application.Storage.setValue("goalDist", goal);
        
        // If distance goal is active and changed, recalculate alerts
        if (mDistGoalActive && goal != oldGoal) {
            var newGoalCm = _getGoalInCm();
            var newHalfway = newGoalCm / 2;
            
            // If we haven't reached new halfway yet, allow alert again
            if (mDistanceCm < newHalfway) {
                mDistHalfwayShown = false;
            }
            // If we haven't reached new goal yet, allow alert again
            if (mDistanceCm < newGoalCm) {
                mDistGoalShown = false;
            }
            _saveState();
        }
    }

    function setTimeGoal(goalMin) {
        var oldGoal = mGoalTimeMin;
        mGoalTimeMin = goalMin;
        Application.Storage.setValue("goalTimeMin", goalMin);

        // If time goal active and changed, allow alerts again if below thresholds
        if (mTimeGoalActive && goalMin != oldGoal) {
            var goalSec = _getGoalTimeSec();
            var halfway = goalSec / 2;
            if (mElapsedWalkSec < halfway) { mTimeHalfwayShown = false; }
            if (mElapsedWalkSec < goalSec) { mTimeGoalShown = false; }
            _saveState();
        }
    }
    
    function setHrMode(mode) {
        mHrMode = mode;
        Application.Storage.setValue("hrMode", mode);
    }
    
    // ═══ START DISTANCE GOAL - Does NOT reset time! ═══
    function startDistanceGoal() {
        // Reset distance baseline to current values
        try {
            var info = ActivityMonitor.getInfo();
            if (info != null) {
                if (info.steps != null) { mStartSteps = info.steps; }
                if (info.distance != null) { mStartDistCm = info.distance; }
            }
        } catch(e) {}
        
        mDistGoalActive = true;
        mDistanceCm = 0;
        mDistHalfwayShown = false;
        mDistGoalShown = false;
        _calculateHrTarget();
        
        // ═══ SMART TIMER: If no time goal, start timer and track movement ═══
        if (!mTimeGoalActive) {
            mElapsedWalkSec = 0;
            mLastMovementTime = System.getTimer();
            try {
                var info = ActivityMonitor.getInfo();
                if (info != null && info.steps != null) {
                    mLastStepsForMovement = info.steps;
                }
            } catch(e) {}
        }
        
        _saveState();
        WatchUi.requestUpdate();
    }
    
    // ═══ RESET DISTANCE GOAL - Reset distance to 0 and deactivate ═══
    function resetDistanceGoal() {
        mDistGoalActive = false;
        mDistanceCm = 0;
        mStartSteps = 0;
        mStartDistCm = 0;
        mDistHalfwayShown = false;
        mDistGoalShown = false;
        
        // ALWAYS reset timer (smart timer) when resetting distance
        mElapsedWalkSec = 0;
        
        // Save ALL values to Storage
        Application.Storage.setValue("distGoalActive", false);
        Application.Storage.setValue("distanceCm", 0);
        Application.Storage.setValue("startSteps", 0);
        Application.Storage.setValue("startDist", 0);
        Application.Storage.setValue("distHalfwayShown", false);
        Application.Storage.setValue("distGoalShown", false);
        Application.Storage.setValue("elapsedWalkSec", 0);
        
        WatchUi.requestUpdate();
    }
    
    // ═══ CONTINUE DISTANCE GOAL - Keep current progress, just update goal ═══
    function continueDistanceGoal() {
        // Don't reset distance - just reactivate with new goal
        mDistGoalActive = true;
        
        // Recalculate alerts based on new goal
        var newGoalCm = _getGoalInCm();
        var newHalfway = newGoalCm / 2;
        
        if (mDistanceCm < newHalfway) {
            mDistHalfwayShown = false;
        }
        if (mDistanceCm < newGoalCm) {
            mDistGoalShown = false;
        }
        
        _calculateHrTarget();
        _saveState();
        WatchUi.requestUpdate();
    }
    
    // ═══ START TIME GOAL - Does NOT reset distance! ═══
    function startTimeGoal() {
        mTimeGoalActive = true;
        mElapsedWalkSec = 0;  // Reset time counter
        mTimeHalfwayShown = false;
        mTimeGoalShown = false;
        _calculateHrTarget();
        _saveState();
        WatchUi.requestUpdate();
    }
    
    // ═══ RESET TIME GOAL - Reset time to 0 and deactivate ═══
    function resetTimeGoal() {
        mTimeGoalActive = false;
        mElapsedWalkSec = 0;
        mTimeHalfwayShown = false;
        mTimeGoalShown = false;
        
        // Save ALL values to Storage
        Application.Storage.setValue("timeGoalActive", false);
        Application.Storage.setValue("elapsedWalkSec", 0);
        Application.Storage.setValue("timeHalfwayShown", false);
        Application.Storage.setValue("timeGoalShown", false);
        
        WatchUi.requestUpdate();
    }
    
    // Legacy function for compatibility
    function startActivity(mode) {
        if (mode == null || mode == MODE_DISTANCE) {
            startDistanceGoal();
        } else {
            startTimeGoal();
        }
    }
    
    function confirmHrMode() {
        _calculateHrTarget();
        mHrMonitoringActive = true;
        mHrAlertShown = false;
        _vibrate();
        
        // Show confirmation message with the calculated HR target
        var lang = getLang();
        var line1 = TR_HR_TARGET_SET[lang];
        var line2 = TR_STAY_BELOW[lang];
        var line3 = mHrTarget.toString() + " " + TR_BPM[lang];
        
        _showFullScreenAlert(line1, line2, line3, "hr");
        
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
    
    // ═══ SHOW FULL SCREEN ALERT (NOT OVERLAY!) - 3 LINES FORMAT ═══
    function _showFullScreenAlert(line1, line2, line3, alertType) {
        var lang = getLang();
        var l1;
        var l2;
        var l3;
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
        if (line3 != null && line3 instanceof Array) {
            l3 = line3[lang];
        } else {
            l3 = line3;
        }
        
        _vibrate();
        
        // Create AlertView with auto-dismiss timer (3 seconds) and animation type
        var aType = alertType != null ? alertType : "halfway";
        var alertView = new AlertView(l1, l2, l3, aType);
        var alertDelegate = new AlertViewDelegate(alertView);
        
        // Push FULL SCREEN alert view with 3 lines and selected color!
        WatchUi.pushView(alertView, alertDelegate, WatchUi.SLIDE_UP);
        
        // Mark alert as active (prevents goal checks during alert)
        mAlertActive = true;
        // Timer is now managed by AlertView itself!
    }
    
    // Called when alert is dismissed (by timer or user)
    function onAlertDismissed() {
        mAlertActive = false;
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

        // Calculate distance from baseline if distance goal is active
        if (mDistGoalActive) {
            distCm = distCm - mStartDistCm;
            steps = steps - mStartSteps;
            if (steps < 0) { steps = 0; }
            if (distCm < 0) { distCm = 0; }
            mDistanceCm = distCm;
        }
        // When not in distance goal, keep mDistanceCm as is (could be 0 after reset)
        // Don't overwrite with ActivityMonitor value!

        hr = _getHeartRate();
        return [steps, mDistanceCm, hr];
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
        // ═══ CHECK FOR MIDNIGHT RESET ═══
        _checkMidnightReset();
        
        // Check if alert was dismissed (AlertView manages its own timer now)
        if (mAlertActive) {
            // Check if current view is still AlertView
            try {
                var currentView = WatchUi.getCurrentView();
                if (currentView != null) {
                    var view = currentView[0];
                    if (view == null || !(view instanceof AlertView)) {
                        // Alert was dismissed, reset flag
                        mAlertActive = false;
                    }
                }
            } catch(e) {
                mAlertActive = false;
            }
        }
        
        // Update time goal if active (count every second!)
        if (mTimeGoalActive && !mAlertActive) {
            mElapsedWalkSec += 1;  // Count every second!
            Application.Storage.setValue("elapsedWalkSec", mElapsedWalkSec);
            _checkTimeAlerts();
        }
        
        // ═══ SMART TIMER: Count time when distance goal active but NO time goal ═══
        if (mDistGoalActive && !mTimeGoalActive && !mAlertActive) {
            mElapsedWalkSec += 1;  // Count seconds!
            Application.Storage.setValue("elapsedWalkSec", mElapsedWalkSec);
            
            // Check for movement - reset timer if stopped for 5 minutes
            _checkMovementAndReset();
        }
        
        // Check distance alerts if distance goal is active
        if (mDistGoalActive && !mAlertActive) {
            _checkDistanceAlerts();
        }
        
        // Check HR alerts
        if (mHrMonitoringActive && !mAlertActive) {
            _checkHrAlert();
        }
        
        WatchUi.requestUpdate();
    }
    
    // ═══ CHECK FOR MIDNIGHT AND RESET DISTANCE ═══
    function _checkMidnightReset() {
        try {
            var now = Time.now();
            var info = Gregorian.info(now, Time.FORMAT_SHORT);
            var lastResetDay = Application.Storage.getValue("lastResetDay");
            var today = info.day;
            
            // If it's a new day, reset distance
            if (lastResetDay != null && lastResetDay != today) {
                mDistGoalActive = false;
                mDistanceCm = 0;
                mStartSteps = 0;
                mStartDistCm = 0;
                mDistHalfwayShown = false;
                mDistGoalShown = false;
                Application.Storage.setValue("lastResetDay", today);
                _saveState();
            } else if (lastResetDay == null) {
                // First run - just save today
                Application.Storage.setValue("lastResetDay", today);
            }
        } catch(e) {}
    }
    
    // ═══ CHECK MOVEMENT AND RESET TIMER IF STOPPED FOR 5 MINUTES ═══
    function _checkMovementAndReset() {
        try {
            var info = ActivityMonitor.getInfo();
            if (info != null && info.steps != null) {
                var currentSteps = info.steps;
                
                // Check if there's movement (new steps)
                if (currentSteps > mLastStepsForMovement) {
                    // Movement detected - update last movement time
                    mLastMovementTime = System.getTimer();
                    mLastStepsForMovement = currentSteps;
                } else {
                    // No movement - check if 5 minutes (300000 ms) have passed
                    var currentTime = System.getTimer();
                    var timeSinceMovement = currentTime - mLastMovementTime;
                    
                    // 5 minutes = 300 seconds = 300000 milliseconds
                    if (timeSinceMovement >= 300000) {
                        // Reset only the timer, NOT the distance!
                        mElapsedWalkSec = 0;
                        mLastMovementTime = currentTime;
                        Application.Storage.setValue("elapsedWalkSec", mElapsedWalkSec);
                    }
                }
            }
        } catch(e) {}
    }
    
    function _checkHrAlert() {
        var hr = _getHeartRate();
        var lang = getLang();
        var name = _getUserName();
        var nameLine = name != "" ? (name + ",") : "";
        
        if (hr != null && mHrTarget > 0 && !mHrAlertShown) {
            if (hr > mHrTarget) {
                // 3 lines: Name, Rest message, HR exceeded message (no animation)
                _showFullScreenAlert(nameLine, TR_REST_NOW[lang], TR_HR_TOO_HIGH[lang], "hr");
                mHrAlertShown = true;
            }
        }
        
        // Reset when HR drops
        if (hr != null && mHrTarget > 0 && mHrAlertShown) {
            var threshold = mHrTarget - (mHrTarget * 5 / 100);
            if (hr <= threshold) {
                // 3 lines: Name, Continue message, HR OK message (no animation)
                _showFullScreenAlert(nameLine, TR_GO_AHEAD[lang], TR_HR_OK[lang], "hr");
                mHrAlertShown = false;
            }
        }
    }
    
    // ═══ CHECK DISTANCE ALERTS (SEPARATE!) ═══
    function _checkDistanceAlerts() {
        var m = _getMetrics();
        var distCm = m[1];
        var goalCm = _getGoalInCm();
        var lang = getLang();
        var name = _getUserName();
        var nameLine = name != "" ? (name + ",") : "";
        
        // 50% alert (🎈 balloons) - 3 lines: Name, Keep going, Halfway message
        if (!mDistHalfwayShown && goalCm > 0) {
            var halfway = goalCm / 2;
            if (distCm >= halfway && distCm < goalCm) {
                _showFullScreenAlert(nameLine, TR_KEEP_GOING[lang], TR_HALF_WAY[lang], "halfway");
                mDistHalfwayShown = true;
                _saveState();
            }
        }
        
        // Goal alert (★ stars) - 3 lines: Name, Great job, Goal completed
        if (!mDistGoalShown && goalCm > 0) {
            if (distCm >= goalCm) {
                _showFullScreenAlert(nameLine, TR_GOAL_DONE_LINE1[lang], TR_GOAL_DONE_LINE2[lang], "goal");
                mDistGoalShown = true;
                _saveState();
                // Distance continues tracking! No reset!
            }
        }
    }
    
    // ═══ CHECK TIME ALERTS (SEPARATE!) ═══
    function _checkTimeAlerts() {
        var goalSec = _getGoalTimeSec();
        if (goalSec <= 0) { return; }

        var lang = getLang();
        var name = _getUserName();
        var nameLine = name != "" ? (name + ",") : "";

        // 50% alert (🎈 balloons) - 3 lines: Name, Keep going, Halfway message
        if (!mTimeHalfwayShown) {
            var halfway = goalSec / 2;
            if (mElapsedWalkSec >= halfway && mElapsedWalkSec < goalSec) {
                _showFullScreenAlert(nameLine, TR_KEEP_GOING[lang], TR_HALF_WAY[lang], "halfway");
                mTimeHalfwayShown = true;
                _saveState();
            }
        }

        // Goal alert (★ stars) - 3 lines: Name, Great job, Goal completed - RESETS time after goal!
        if (!mTimeGoalShown) {
            if (mElapsedWalkSec >= goalSec) {
                _showFullScreenAlert(nameLine, TR_GOAL_DONE_LINE1[lang], TR_GOAL_DONE_LINE2[lang], "goal");
                mTimeGoalShown = true;
                
                // Time goal RESETS after completion!
                mTimeGoalActive = false;
                mElapsedWalkSec = 0;
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
        var fTime = Graphics.FONT_NUMBER_MILD;
        var fNumbers = Graphics.FONT_MEDIUM;
        var fLabels = Graphics.FONT_XTINY;
        var fHR = Graphics.FONT_NUMBER_MILD;
        
        var hTime = dc.getFontHeight(fTime);
        var hNumbers = dc.getFontHeight(fNumbers);
        var hLabels = dc.getFontHeight(fLabels);
        var hHR = dc.getFontHeight(fHR);
        
        // ═══ ALL POSITIONS IN PERCENTAGES! ═══
        var padSide = w / 14;
        var iconSize = w / 11;
        var barH = h / 28;
        var y = h / 40;

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
        
        // Running person icon (right side) - USES MAIN COLOR!
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

        // ═══ TIME (minutes:seconds walked) ═══
        mTimeGoalZoneTop = y;
        var elapsedMin = (mElapsedWalkSec / 60).toNumber();
        var elapsedSec = mElapsedWalkSec - (elapsedMin * 60);
        var timeMinStr = elapsedMin.toString() + ":" + _twoDigits(elapsedSec);
        if (_isHebrew(lang)) { timeMinStr = "" + timeMinStr + ""; }
        dc.setColor(color, Graphics.COLOR_BLACK);
        dc.drawText(padSide, y, fNumbers, timeMinStr, Graphics.TEXT_JUSTIFY_LEFT);
        valW = dc.getTextWidthInPixels(timeMinStr, fNumbers);
        dc.setColor(color, Graphics.COLOR_BLACK);
        dc.drawText(padSide + valW + w / 56, y + (hNumbers - hLabels) / 2, fLabels, TR_MINUTES[lang], Graphics.TEXT_JUSTIFY_LEFT);

        // Clock icon (right side) - USES MAIN COLOR!
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

        // ═══ HEART RATE - FONT_NUMBER_MILD (62px) ═══
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

        // Heart icon - USES MAIN COLOR!
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
