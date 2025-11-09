# 🚁 Cropter - Agricultural Drone Analysis Platform

Complete system for drone-based farm monitoring with AI-powered crop analysis.

---

## 🚀 Quick Start (Mac)

### 1. Install Dependencies

```bash
# Backend
cd backend
pip3 install -r requirements.txt

# Frontend
cd ../copter-vision-hub
npm install
echo "VITE_BACKEND_URL=http://localhost:5000" > .env
```

### 2. Start All Services

Open **4 separate terminals**:

```bash
# Terminal 1: Backend API
cd backend
python3 app.py

# Terminal 2: AI Service (Mock YOLO)
cd backend
python3 ai_service.py

# Terminal 3: Drone WebSocket Server
cd backend
python3 phase_3_drone_server.py

# Terminal 4: Frontend
cd copter-vision-hub
npm run dev
```

**Or use the startup script:**
```bash
chmod +x start_mac.sh
./start_mac.sh
```

### 3. Access the App

Open browser: **http://localhost:5173**

---

## 📱 Features

### Phase 1: Farm Mapping
- Interactive map to draw field boundaries
- **Obstacle marking** (trees, buildings, etc.) - Orange zones
- **No-Fly Zone marking** (power lines, dangerous areas) - Amber/dashed zones
- Toggle between obstacle and no-fly zone modes
- Visual distinction:
  - 🟠 **Obstacles** - Solid orange, lower opacity
  - 🟡 **No-Fly Zones** - Dashed amber, higher opacity for emphasis
- Remove individual zones or restart mapping
- Save complete field configurations with all restrictions

### Phase 2 & 3: Mission Control
- Generate optimal flight paths with **beautiful visual diagrams**
- Interactive SVG visualization showing:
  - Complete flight path with waypoints
  - Start position (green marker)
  - Landing zone (red marker)
  - Flight waypoints (blue markers)
  - Gradient path lines with glow effects
  - Lawnmower pattern coverage
- Connect to Tello drone (WiFi: TELLO-XXXXXX)
- Live video stream from drone
- **Manual controls:** WASD (move), Arrow keys (altitude/rotate), Space (land)
- Autonomous mission execution
- Auto-record video on takeoff
- Stats cards with battery, distance, duration estimates

### Phase 4 & 5: Analysis Dashboard
- Upload drone footage
- AI-powered crop analysis (currently mock YOLO)
- Health score with issue breakdown
- Download annotated videos and reports

---

## 🎮 Using the Tello Drone

### Setup:
1. Power on Tello drone
2. Connect Mac to **Tello WiFi** (TELLO-XXXXXX)
3. Start drone server: `cd backend && python3 phase_3_drone_server.py`
4. Open Mission Control: http://localhost:5173/mission-control

### Flying:
1. Click **"Connect Drone"** → Battery shows
2. Click **"Start Stream"** → Live video appears
3. Click **"Takeoff"** → Drone rises + recording starts 🔴
4. Toggle **"Manual Mode ON"**
5. **Fly with keyboard:**
   - `W/A/S/D` - Forward/Left/Back/Right
   - `↑/↓` - Up/Down
   - `←/→` - Rotate
   - `SPACE` - Land (stops recording)
6. Video saved to: `~/Desktop/cropter_recordings/mission_YYYYMMDD_HHMMSS.avi`

### For Autonomous Flight:
1. Go to Farm Mapping → Draw field
2. Go to Mission Control → Load field → Generate path
3. Click **"START MISSION"** → Drone flies automatically

---

## 📁 Project Structure

```
Cropter/
├── backend/
│   ├── app.py                           # Main API server
│   ├── ai_service.py                    # AI analysis (mock YOLO)
│   ├── phase_2_flight_path_generator.py # Flight planning
│   ├── phase_3_drone_server.py          # Drone WebSocket server
│   └── requirements.txt                 # Python dependencies
│
├── copter-vision-hub/                   # React frontend
│   ├── src/
│   │   ├── pages/
│   │   │   ├── FarmMapping.tsx          # Phase 1
│   │   │   ├── MissionControl.tsx       # Phases 2 & 3
│   │   │   └── MyFarm.tsx               # Phases 4 & 5
│   │   ├── components/
│   │   │   └── AnalysisResults.tsx      # Results dashboard
│   │   ├── lib/analysisApi.ts           # API client
│   │   └── types/analysis.ts            # TypeScript types
│   └── package.json
│
├── README.md                            # This file
└── start_mac.sh                         # Startup script
```

---

## 🔌 Ports & Services

| Service | Port | URL |
|---------|------|-----|
| Backend API | 5000 | http://localhost:5000 |
| AI Service | 5001 | http://localhost:5001 |
| Drone Server | 8765 | ws://localhost:8765 |
| Frontend | 5173 | http://localhost:5173 |

---

## 🤖 AI Analysis (Currently Mock)

**Status:** Using mock YOLO data for testing integration

**Mock detections:**
- Healthy crops: 800
- Diseased crops: 120
- Weeds: 450
- Pests: 53
- Health Score: 72.5%

**To integrate real YOLO model:**
1. Get `best.pt` model file from AI teammate
2. Edit `backend/ai_service.py` → Set `MOCK_MODE = False`
3. Add model loading code
4. Restart AI service

---

## 🐛 Troubleshooting

### Port already in use:
```bash
lsof -i :5000
kill -9 [PID]
```

### Frontend can't reach backend:
```bash
cd copter-vision-hub
echo "VITE_BACKEND_URL=http://localhost:5000" > .env
# Restart frontend
```

### Drone won't connect:
- Ensure Mac is connected to **Tello WiFi** (not regular WiFi)
- Power cycle the drone
- Check battery > 10%
- Close any other drone apps

### Video recording not working:
```bash
# Install FFmpeg (required for video streaming)
brew install ffmpeg
```

---

## 📊 API Endpoints

### Backend (port 5000)
- `GET /api/health` - Health check
- `POST /api/upload` - Upload video for analysis
- `POST /api/generate-flight-path` - Generate mission waypoints
- `GET /outputs/<filename>` - Download results

### AI Service (port 5001)
- `GET /health` - Health check (shows mock/real mode)
- `POST /analyze` - Analyze video with YOLO

### Drone Server (WebSocket port 8765)
- Actions: `connect_drone`, `start_stream`, `takeoff`, `land`, `move_*`, `rotate_*`
- Streams: video frames, telemetry, mission status

---

## 🎯 Demo Workflow

1. **Farm Mapping** → Draw field boundaries on map
2. **Mission Control** → Generate flight path → Connect drone → Fly
3. **My Farm** → Upload recorded video → View analysis results

**OR** upload pre-recorded footage directly to skip drone steps.

---

## ✅ What's Complete

- ✅ All 5 phases integrated into single React app
- ✅ Real Tello drone control (manual + autonomous)
- ✅ Live video streaming + auto-recording
- ✅ Flight path generation
- ✅ Video upload + AI analysis (mock)
- ✅ Interactive farm mapping
- ✅ Results dashboard with downloads
- ✅ Cross-platform (Mac + Windows)

---

## 💡 Tips

- **Mac-specific:** Use `python3` and `pip3` commands
- **Tello WiFi:** Drone creates its own network (TELLO-XXXXXX)
- **Recording location:** Videos save to `~/Desktop/cropter_recordings/`
- **Mock AI:** Perfect for testing without real YOLO model
- **Demo tip:** Pre-record footage or use any video file for analysis

---

## 🚀 For Hackathon Demo

1. **Pre-demo:** Start all 4 services (use `start_mac.sh`)
2. **Option A - Live Flight:** Connect drone → Fly → Show recording
3. **Option B - Pre-recorded:** Upload video → Show instant analysis
4. **Highlight:** Real-time telemetry, auto-recording, AI insights dashboard

---

**Everything works out of the box. Just install, start, and fly!** 🚁
