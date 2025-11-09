"""
Cropter Drone WebSocket Server
Handles drone control via WebSocket for Mission Control frontend
"""

import asyncio
import websockets
import json
import cv2
import base64
import os
from datetime import datetime
import time
from pathlib import Path
import numpy as np

# Try to use REAL drone by default
MOCK_MODE = False

try:
    from djitellopy import Tello
    DJITELLOPY_AVAILABLE = True
except ImportError:
    DJITELLOPY_AVAILABLE = False
    print("⚠️  djitellopy not installed - running in MOCK mode")
    MOCK_MODE = True

class MockTello:
    """Mock Tello for testing without hardware"""
    def __init__(self):
        self.battery = 85
        self.height = 0
        self.flight_time = 0
        self.temperature_high = 25
        self.temperature_low = 23
        self.is_flying = False
        
    def connect(self):
        print("✓ Mock drone connected")
        return True
    
    def get_battery(self):
        return self.battery
    
    def get_height(self):
        return self.height
    
    def get_flight_time(self):
        return self.flight_time
    
    def get_highest_temperature(self):
        return self.temperature_high
    
    def get_lowest_temperature(self):
        return self.temperature_low
    
    def takeoff(self):
        print("🚁 Mock takeoff")
        self.is_flying = True
        self.height = 100
        
    def land(self):
        print("🛬 Mock land")
        self.is_flying = False
        self.height = 0
        
    def move_forward(self, distance):
        print(f"→ Mock move forward {distance}cm")
        
    def move_back(self, distance):
        print(f"← Mock move back {distance}cm")
        
    def move_left(self, distance):
        print(f"← Mock move left {distance}cm")
        
    def move_right(self, distance):
        print(f"→ Mock move right {distance}cm")
        
    def move_up(self, distance):
        print(f"↑ Mock move up {distance}cm")
        self.height += distance
        
    def move_down(self, distance):
        print(f"↓ Mock move down {distance}cm")
        self.height = max(0, self.height - distance)
        
    def rotate_clockwise(self, degrees):
        print(f"↻ Mock rotate CW {degrees}°")
        
    def rotate_counter_clockwise(self, degrees):
        print(f"↺ Mock rotate CCW {degrees}°")


class DroneServer:
    def __init__(self):
        self.tello = None
        self.connected_clients = set()
        self.mock_mode = MOCK_MODE
        self.streaming = False
        self.recording = False
        self.video_writer = None
        self.current_recording_file = None
        self.frame_read = None
        
        # Setup recordings directory
        desktop = Path.home() / "Desktop"
        self.recordings_dir = desktop / "cropter_recordings"
        self.recordings_dir.mkdir(exist_ok=True)
        print(f"📁 Recordings: {self.recordings_dir}")
    
    def connect_drone(self):
        """Connect to Tello drone"""
        try:
            if self.mock_mode or not DJITELLOPY_AVAILABLE:
                self.tello = MockTello()
                self.tello.connect()
                return {
                    "success": True,
                    "battery": self.tello.get_battery(),
                    "mode": "MOCK"
                }
            else:
                print("🔌 Connecting to REAL Tello drone...")
                print("   Make sure you're connected to Tello WiFi (TELLO-XXXXXX)")
                self.tello = Tello()
                self.tello.connect()
                battery = self.tello.get_battery()
                print(f"✓ Connected! Battery: {battery}%")
                return {
                    "success": True,
                    "battery": battery,
                    "mode": "REAL",
                    "sdk_version": self.tello.query_sdk_version()
                }
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            print("💡 Make sure:")
            print("   1. Tello drone is powered on")
            print("   2. Your computer is connected to Tello WiFi")
            print("   3. No other app is using the drone")
            return {"success": False, "error": str(e)}
    
    def start_stream(self):
        """Start video stream from drone"""
        try:
            if self.mock_mode or not self.tello:
                return {"success": False, "error": "Not available in mock mode or drone not connected"}
            
            print("📹 Starting video stream...")
            self.tello.streamon()
            time.sleep(2)  # Give stream time to initialize
            
            self.frame_read = self.tello.get_frame_read()
            self.streaming = True
            
            # Start video streaming task
            asyncio.create_task(self.stream_video_task())
            
            print("✓ Video stream started")
            print("💡 Recording will start automatically on takeoff")
            return {"success": True}
        except Exception as e:
            print(f"✗ Stream start failed: {e}")
            print("💡 Drone can still fly, but video/recording won't work")
            print("💡 To fix: Install FFmpeg for Windows")
            print("   -> Run: choco install ffmpeg")
            print("   -> Or download from: https://www.gyan.dev/ffmpeg/builds/")
            return {"success": False, "error": str(e)}
    
    def start_recording(self):
        """Start recording video to file"""
        try:
            if not self.streaming:
                return {"success": False, "error": "Stream not active"}
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.current_recording_file = self.recordings_dir / f"mission_{timestamp}.avi"
            
            frame = self.frame_read.frame
            height, width, _ = frame.shape
            
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            self.video_writer = cv2.VideoWriter(
                str(self.current_recording_file),
                fourcc,
                30.0,
                (width, height)
            )
            
            self.recording = True
            print(f"🔴 Recording: {self.current_recording_file.name}")
            return {"success": True, "filename": self.current_recording_file.name}
        except Exception as e:
            print(f"✗ Recording start failed: {e}")
            return {"success": False, "error": str(e)}
    
    def stop_recording(self):
        """Stop recording and save file"""
        try:
            self.recording = False
            
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None
            
            file_path = self.current_recording_file
            filename = file_path.name if file_path else "unknown"
            
            print(f"⬛ Recording saved: {filename}")
            
            file_size_mb = 0
            if file_path and file_path.exists():
                file_size_mb = file_path.stat().st_size / (1024 * 1024)
                print(f"  Size: {file_size_mb:.1f} MB")
            
            return {
                "success": True,
                "filename": filename,
                "file_path": str(file_path),
                "file_size_mb": round(file_size_mb, 2)
            }
        except Exception as e:
            print(f"✗ Stop recording failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def stream_video_task(self):
        """Stream video frames to all connected clients"""
        print("🎥 Video streaming task started")
        
        while self.streaming and self.frame_read:
            try:
                frame = self.frame_read.frame
                if frame is None:
                    await asyncio.sleep(0.033)
                    continue
                
                # Write to recording if active
                if self.recording and self.video_writer:
                    self.video_writer.write(frame)
                
                # Resize for web streaming
                frame_resized = cv2.resize(frame, (960, 720))
                
                # Add telemetry overlay
                telemetry = self.get_telemetry()
                frame_with_overlay = self.add_telemetry_overlay(frame_resized, telemetry)
                
                # Encode as JPEG
                _, buffer = cv2.imencode('.jpg', frame_with_overlay, [cv2.IMWRITE_JPEG_QUALITY, 80])
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
                
                # Broadcast to all clients
                if self.connected_clients:
                    message = json.dumps({
                        "type": "video_frame",
                        "data": frame_base64,
                        "recording": self.recording,
                        "telemetry": telemetry
                    })
                    websockets.broadcast(self.connected_clients, message)
                
                await asyncio.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                print(f"Stream error: {e}")
                await asyncio.sleep(0.1)
    
    def add_telemetry_overlay(self, frame, telemetry):
        """Add telemetry data overlay to video frame"""
        try:
            overlay = frame.copy()
            
            # Semi-transparent background
            cv2.rectangle(overlay, (0, 0), (300, 120), (0, 0, 0), -1)
            frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
            
            y_offset = 25
            
            # Battery
            battery = telemetry.get('battery', 0)
            color = (0, 255, 0) if battery > 30 else (0, 165, 255) if battery > 20 else (0, 0, 255)
            cv2.putText(frame, f"Battery: {battery}%", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            y_offset += 25
            
            # Height
            height = telemetry.get('height', 0)
            cv2.putText(frame, f"Height: {height}cm", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            y_offset += 25
            
            # Flight time
            flight_time = telemetry.get('flight_time', 0)
            cv2.putText(frame, f"Time: {flight_time}s", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            y_offset += 25
            
            # Recording indicator
            if self.recording:
                if int(time.time() * 2) % 2 == 0:
                    cv2.circle(frame, (270, 15), 10, (0, 0, 255), -1)
                cv2.putText(frame, "REC", (230, 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            return frame
        except:
            return frame
    
    def get_telemetry(self):
        """Get current drone telemetry"""
        try:
            if not self.tello:
                return {}
            
            return {
                "battery": self.tello.get_battery(),
                "height": self.tello.get_height(),
                "flight_time": self.tello.get_flight_time(),
                "temperature": {
                    "high": self.tello.get_highest_temperature(),
                    "low": self.tello.get_lowest_temperature()
                }
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def handle_client(self, websocket):
        """Handle WebSocket client connection"""
        self.connected_clients.add(websocket)
        client_addr = websocket.remote_address
        print(f"✓ Client connected from {client_addr}")
        
        try:
            async for message in websocket:
                data = json.loads(message)
                action = data.get("action")
                
                response = {"success": False, "error": "Unknown action"}
                
                if action == "connect":
                    response = self.connect_drone()
                
                elif action == "start_stream":
                    response = self.start_stream()
                
                elif action == "start_recording":
                    response = self.start_recording()
                
                elif action == "stop_recording":
                    response = self.stop_recording()
                
                elif action == "get_status":
                    telemetry = self.get_telemetry() if self.tello else {}
                    response = {
                        "success": True,
                        "telemetry": telemetry,
                        "mode": "MOCK" if self.mock_mode else "REAL"
                    }
                
                elif action == "takeoff":
                    if self.tello:
                        self.tello.takeoff()
                        await asyncio.sleep(3)
                        
                        # Auto-start recording after takeoff (only if streaming works)
                        if self.streaming and not self.recording:
                            recording_result = self.start_recording()
                            if recording_result.get("success"):
                                print(f"🔴 Recording started: {recording_result.get('filename')}")
                            else:
                                print(f"⚠️  Recording not available: {recording_result.get('error')}")
                        else:
                            print("⚠️  Flying without video recording (stream not active)")
                        
                        response = {"success": True, "message": "Takeoff complete"}
                    else:
                        response = {"success": False, "error": "Drone not connected"}
                
                elif action == "land":
                    if self.tello:
                        self.tello.land()
                        await asyncio.sleep(3)
                        
                        # Auto-stop recording after landing
                        if self.recording:
                            recording_result = self.stop_recording()
                            response = {
                                "success": True,
                                "message": "Landed",
                                "recording": recording_result
                            }
                        else:
                            response = {"success": True, "message": "Landed"}
                    else:
                        response = {"success": False, "error": "Drone not connected"}
                
                elif action == "move_forward":
                    if self.tello:
                        distance = data.get("distance", 20)
                        self.tello.move_forward(min(distance, 500))
                        response = {"success": True}
                    else:
                        response = {"success": False, "error": "Drone not connected"}
                
                elif action == "move_back":
                    if self.tello:
                        distance = data.get("distance", 20)
                        self.tello.move_back(min(distance, 500))
                        response = {"success": True}
                    else:
                        response = {"success": False, "error": "Drone not connected"}
                
                elif action == "move_left":
                    if self.tello:
                        distance = data.get("distance", 20)
                        self.tello.move_left(min(distance, 500))
                        response = {"success": True}
                    else:
                        response = {"success": False, "error": "Drone not connected"}
                
                elif action == "move_right":
                    if self.tello:
                        distance = data.get("distance", 20)
                        self.tello.move_right(min(distance, 500))
                        response = {"success": True}
                    else:
                        response = {"success": False, "error": "Drone not connected"}
                
                elif action == "move_up":
                    if self.tello:
                        distance = data.get("distance", 20)
                        self.tello.move_up(min(distance, 500))
                        response = {"success": True}
                    else:
                        response = {"success": False, "error": "Drone not connected"}
                
                elif action == "move_down":
                    if self.tello:
                        distance = data.get("distance", 20)
                        self.tello.move_down(min(distance, 500))
                        response = {"success": True}
                    else:
                        response = {"success": False, "error": "Drone not connected"}
                
                elif action == "rotate_cw":
                    if self.tello:
                        degrees = data.get("degrees", 15)
                        self.tello.rotate_clockwise(degrees)
                        response = {"success": True}
                    else:
                        response = {"success": False, "error": "Drone not connected"}
                
                elif action == "rotate_ccw":
                    if self.tello:
                        degrees = data.get("degrees", 15)
                        self.tello.rotate_counter_clockwise(degrees)
                        response = {"success": True}
                    else:
                        response = {"success": False, "error": "Drone not connected"}
                
                elif action == "emergency_stop":
                    if self.tello:
                        print("⚠️  EMERGENCY STOP")
                        self.tello.land()
                        response = {"success": True, "message": "Emergency stop executed"}
                    else:
                        response = {"success": False, "error": "Drone not connected"}
                
                elif action == "execute_mission":
                    mission_data = data.get("mission_data")
                    if not mission_data:
                        response = {"success": False, "error": "No mission data"}
                    else:
                        print(f"🚁 Starting mission: {mission_data.get('mission_id')}")
                        print(f"   Waypoints: {len(mission_data.get('waypoints', []))}")
                        # In mock mode, just simulate success
                        response = {
                            "success": True,
                            "message": "Mission started (MOCK mode - no actual flight)"
                        }
                
                await websocket.send(json.dumps(response))
                
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"✗ Client handler error: {e}")
        finally:
            self.connected_clients.remove(websocket)
            print(f"✗ Client disconnected from {client_addr}")


async def main():
    server = DroneServer()
    
    print("\n" + "="*60)
    print("      CROPTER DRONE WEBSOCKET SERVER")
    print("="*60)
    print("\n📡 WebSocket: ws://localhost:8765")
    print(f"📁 Recordings: {server.recordings_dir}")
    print(f"🎮 Mode: {'MOCK (no drone needed)' if server.mock_mode else 'REAL TELLO DRONE'}")
    
    if not server.mock_mode:
        print("\n⚠️  REAL DRONE MODE:")
        print("   1. Power on your Tello drone")
        print("   2. Connect your computer to Tello WiFi (TELLO-XXXXXX)")
        print("   3. Click 'Connect Drone' in Mission Control")
        print("   4. You'll see REAL video feed and telemetry")
        print("   5. Video will be recorded to Desktop/cropter_recordings/")
        print("\n💡 AI Analysis will still use MOCK data (Phase 4)")
    else:
        print("\n⚠️  MOCK MODE:")
        print("   - No actual drone needed for testing")
        print("   - All commands are simulated")
        print("   - Safe to test keyboard controls")
    
    print("\n🔌 Waiting for connections...")
    print("="*60 + "\n")
    
    async with websockets.serve(server.handle_client, "0.0.0.0", 8765):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")

