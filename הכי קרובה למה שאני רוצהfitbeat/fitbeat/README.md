# 📱 FitBeat v4.3.1

**Multi-language fitness tracker for Garmin Fenix 8 Solar 51mm**

---

## ✨ Features

- 🌐 **6 Languages**: English, עברית, Español, Français, Deutsch, 中文
- 🎨 **10 Colors**: Green, Cyan, Blue, Purple, Red, Orange, Yellow, Pink, Lime, White
- ⌨️ **Dynamic Keyboard**: Changes based on selected language
- 📊 **Real-time Tracking**: Distance, Steps, Heart Rate
- 🎯 **Goal Setting**: Custom distance goals (1-20 km/mi)
- 💓 **HR Zones**: Auto + Manual modes (50%-90%)

---

## 🔨 Build

```cmd
cd fitbeat
monkeyc -o FitBeat.prg -f monkey.jungle -y developer_key.der -d fenix8solar51mm
```

---

## 📏 Font Sizes (Garmin Fenix 8)

- Time: 69px (FONT_NUMBER_MEDIUM)
- Distance/Steps: 39px (FONT_MEDIUM)
- Labels: 22px (FONT_XTINY)
- Heart Rate: 62px (FONT_NUMBER_MILD)
- Goal: 107px (FONT_NUMBER_HOT)

---

## 🌐 Simulator

```
https://fenix-preview.preview.emergentagent.com/fitbeat-interactive.html
```

---

**Built for Garmin Fenix 8 Solar 51mm** ⌚✨