# FitBeat v4.3.1 - Build Instructions

## 🛠️ Prerequisites

1. **Garmin Connect IQ SDK 8.4.0+**
2. **Developer Key** (included: `developer_key.der`)
3. **Target Device**: Garmin Fenix 8 Solar 51mm

---

## 🔨 Build Command

### Windows:
```cmd
cd "C:\Users\gabbyc\Desktop\fitbeat"
"%APPDATA%\Garmin\ConnectIQ\Sdks\connectiq-sdk-win-8.4.0-2025-12-03-5122605dc\bin\monkeyc.bat" -o FitBeat.prg -f monkey.jungle -y developer_key.der -d fenix8solar51mm
```

### If nested folder (fitbeat\fitbeat):
```cmd
cd "C:\Users\gabbyc\Desktop\fitbeat\fitbeat"
[same command]
```

### macOS:
```bash
cd ~/Desktop/fitbeat
~/Library/Application\ Support/Garmin/ConnectIQ/Sdks/connectiq-sdk-mac-8.4.0/bin/monkeyc -o FitBeat.prg -f monkey.jungle -y developer_key.der -d fenix8solar51mm
```

---

## ⚠️ Important

- Run from **inside** the `fitbeat/` directory
- All files must be in same directory
- Check `dir` or `ls` to verify you see `monkey.jungle`

---

## 🐛 Troubleshooting

### "jungle file doesn't exist"
```cmd
dir  # Check you see monkey.jungle
cd fitbeat  # If you see a fitbeat folder
```

### "developer_key.der not found"
```cmd
dir  # Verify developer_key.der exists
```

---

## ✅ Checklist

- [ ] I'm in `fitbeat/` directory
- [ ] I see `monkey.jungle`
- [ ] I see `developer_key.der`
- [ ] SDK path is correct
- [ ] Device is `fenix8solar51mm`

---

**Ready to build!** 🚀