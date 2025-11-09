import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import {
  Upload,
  Wifi,
  WifiOff,
  Play,
  Square,
  AlertCircle,
  Video,
  Navigation,
  Gauge,
  Battery,
  Radio,
  MapPin,
  Zap,
} from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface Telemetry {
  battery: number;
  height: number;
  flight_time: number;
  temperature?: { high: number; low: number };
  position?: { x: number; y: number; z: number };
  distance_traveled?: number;
}

interface MissionStatus {
  status: string;
  message: string;
  waypoint?: number;
  total_waypoints?: number;
  progress?: number;
  battery?: number;
  distance_traveled?: number;
}

const MissionControl = () => {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [droneConnected, setDroneConnected] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [videoFrame, setVideoFrame] = useState<string>("");
  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
  const [missionStatus, setMissionStatus] = useState<MissionStatus | null>(null);
  const [fieldMap, setFieldMap] = useState<any>(null);
  const [flightPlan, setFlightPlan] = useState<any>(null);
  const [altitude, setAltitude] = useState([200]); // cm
  const [overlap, setOverlap] = useState([30]); // percentage
  const [manualMode, setManualMode] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Keyboard controls state
  const keysPressed = useRef<Set<string>>(new Set());
  const controlInterval = useRef<NodeJS.Timeout | null>(null);

  // WebSocket connection
  useEffect(() => {
    const websocket = new WebSocket("ws://localhost:8765");

    websocket.onopen = () => {
      console.log("WebSocket connected");
      setConnected(true);
      setWs(websocket);
    };

    websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === "video_frame") {
          setVideoFrame(data.data);
          if (data.telemetry) setTelemetry(data.telemetry);
          if (data.mission_active) {
            setMissionStatus({
              status: "executing",
              message: `Waypoint ${data.waypoint}/${data.total_waypoints}`,
              waypoint: data.waypoint,
              total_waypoints: data.total_waypoints,
            });
          }
        } else if (data.type === "mission_status") {
          setMissionStatus(data);
        }
      } catch (error) {
        console.error("WebSocket message error:", error);
      }
    };

    websocket.onclose = () => {
      console.log("WebSocket disconnected");
      setConnected(false);
      setWs(null);
    };

    websocket.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    return () => {
      websocket.close();
    };
  }, []);

  // Keyboard controls
  useEffect(() => {
    if (!manualMode || !droneConnected) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      keysPressed.current.add(e.key.toLowerCase());
      if (!controlInterval.current) {
        controlInterval.current = setInterval(sendManualCommands, 200);
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      keysPressed.current.delete(e.key.toLowerCase());
      if (keysPressed.current.size === 0 && controlInterval.current) {
        clearInterval(controlInterval.current);
        controlInterval.current = null;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
      if (controlInterval.current) {
        clearInterval(controlInterval.current);
      }
    };
  }, [manualMode, droneConnected]);

  const sendManualCommands = () => {
    if (!ws || !droneConnected) return;

    const keys = keysPressed.current;

    // Movement commands (WASD)
    if (keys.has("w")) sendCommand("move_forward", { distance: 20 });
    if (keys.has("s")) sendCommand("move_back", { distance: 20 });
    if (keys.has("a")) sendCommand("move_left", { distance: 20 });
    if (keys.has("d")) sendCommand("move_right", { distance: 20 });

    // Altitude (Arrow Up/Down)
    if (keys.has("arrowup")) sendCommand("move_up", { distance: 20 });
    if (keys.has("arrowdown")) sendCommand("move_down", { distance: 20 });

    // Rotation (Arrow Left/Right)
    if (keys.has("arrowleft")) sendCommand("rotate_ccw", { degrees: 15 });
    if (keys.has("arrowright")) sendCommand("rotate_cw", { degrees: 15 });

    // Land (Space)
    if (keys.has(" ")) {
      sendCommand("land");
      setManualMode(false);
    }
  };

  const sendCommand = (action: string, params?: any) => {
    if (!ws) return;
    ws.send(JSON.stringify({ action, ...params }));
  };

  const connectDrone = () => {
    if (!ws) return;
    ws.send(JSON.stringify({ action: "connect" }));
    setTimeout(() => {
      setDroneConnected(true);
    }, 2000);
  };

  const startStream = () => {
    if (!ws) return;
    ws.send(JSON.stringify({ action: "start_stream" }));
    setStreaming(true);
  };

  const loadFieldMap = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const json = JSON.parse(e.target?.result as string);
        setFieldMap(json);
        console.log("Field map loaded:", json);
      } catch (error) {
        console.error("Invalid JSON file:", error);
      }
    };
    reader.readAsText(file);
  };

  const generateFlightPath = async () => {
    if (!fieldMap) return;

    try {
      const response = await fetch("http://localhost:5000/api/generate-flight-path", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          field_config: fieldMap,
          altitude_m: altitude[0] / 100,
          overlap_pct: overlap[0] / 100,
        }),
      });

      const data = await response.json();
      setFlightPlan(data);
      console.log("Flight plan generated:", data);
    } catch (error) {
      console.error("Flight path generation failed:", error);
    }
  };

  const executeMission = () => {
    if (!ws || !flightPlan) return;

    ws.send(
      JSON.stringify({
        action: "execute_mission",
        mission_data: {
          mission_id: `mission_${Date.now()}`,
          field_id: fieldMap?.field_id,
          waypoints: flightPlan.waypoints,
          altitude: altitude[0],
        },
      })
    );
  };

  const emergencyStop = () => {
    if (!ws) return;
    ws.send(JSON.stringify({ action: "emergency_stop" }));
    setManualMode(false);
  };

  const takeoff = () => {
    if (!ws) return;
    sendCommand("takeoff");
  };

  return (
    <div className="min-h-screen pt-32 pb-20 px-6">
      <div className="container mx-auto max-w-7xl">
        <div className="text-center mb-12 space-y-4">
          <h1 className="text-6xl font-light tracking-tight text-foreground">
            Mission <span className="font-semibold bg-gradient-hero bg-clip-text text-transparent">Control</span>
          </h1>
          <p className="text-xl font-light text-muted-foreground">Phases 2 & 3: Flight planning and autonomous execution</p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Control Panel */}
          <div className="lg:col-span-2 space-y-6">
            {/* Status Bar */}
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <Badge variant={connected ? "default" : "secondary"} className="gap-2">
                      {connected ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
                      {connected ? "Server Connected" : "Server Offline"}
                    </Badge>
                    <Badge variant={droneConnected ? "default" : "secondary"} className="gap-2">
                      <Radio className="w-4 h-4" />
                      {droneConnected ? "Drone Connected" : "Drone Offline"}
                    </Badge>
                    {streaming && (
                      <Badge variant="default" className="gap-2 bg-red-500">
                        <Video className="w-4 h-4" />
                        Streaming
                      </Badge>
                    )}
                  </div>
                  <Button variant="destructive" onClick={emergencyStop} className="gap-2">
                    <AlertCircle className="w-4 h-4" />
                    EMERGENCY STOP
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Video Feed */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-2xl font-light">Live Feed</CardTitle>
                    <CardDescription>Tello drone camera</CardDescription>
                  </div>
                  {streaming && <Badge className="bg-red-500 animate-pulse">LIVE</Badge>}
                </div>
              </CardHeader>
              <CardContent>
                <div className="relative aspect-video rounded-lg overflow-hidden bg-slate-900">
                  {videoFrame ? (
                    <img src={`data:image/jpeg;base64,${videoFrame}`} alt="Drone feed" className="w-full h-full object-cover" />
                  ) : (
                    <div className="absolute inset-0 flex items-center justify-center text-muted-foreground">
                      <div className="text-center space-y-2">
                        <Video className="w-12 h-12 mx-auto opacity-50" />
                        <p>No video stream</p>
                        <p className="text-sm">Connect drone and start stream</p>
                      </div>
                    </div>
                  )}

                  {/* Telemetry Overlay */}
                  {telemetry && (
                    <div className="absolute top-4 left-4 right-4 flex justify-between text-xs text-white font-mono">
                      <div className="bg-black/60 backdrop-blur-sm px-3 py-2 rounded">
                        <Battery className="w-3 h-3 inline mr-1" />
                        {telemetry.battery}%
                      </div>
                      <div className="bg-black/60 backdrop-blur-sm px-3 py-2 rounded">
                        <Gauge className="w-3 h-3 inline mr-1" />
                        {telemetry.height}cm
                      </div>
                      <div className="bg-black/60 backdrop-blur-sm px-3 py-2 rounded">
                        <Zap className="w-3 h-3 inline mr-1" />
                        {telemetry.flight_time}s
                      </div>
                    </div>
                  )}

                  {/* Mission Progress */}
                  {missionStatus && missionStatus.waypoint && (
                    <div className="absolute bottom-4 left-4 right-4 bg-black/60 backdrop-blur-sm px-4 py-3 rounded">
                      <div className="flex justify-between text-white text-sm mb-2">
                        <span>Mission Progress</span>
                        <span>
                          {missionStatus.waypoint}/{missionStatus.total_waypoints}
                        </span>
                      </div>
                      <Progress
                        value={((missionStatus.waypoint || 0) / (missionStatus.total_waypoints || 1)) * 100}
                        className="h-2"
                      />
                    </div>
                  )}
                </div>

                {/* Manual Controls */}
                <div className="mt-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold">Manual Controls</h3>
                    <Button
                      size="sm"
                      variant={manualMode ? "default" : "outline"}
                      onClick={() => setManualMode(!manualMode)}
                      disabled={!droneConnected}
                    >
                      {manualMode ? "Manual Mode ON" : "Manual Mode OFF"}
                    </Button>
                  </div>
                  {manualMode && (
                    <Alert>
                      <Navigation className="w-4 h-4" />
                      <AlertDescription>
                        <div className="space-y-1 text-sm">
                          <div>
                            <strong>WASD:</strong> Forward, Left, Back, Right
                          </div>
                          <div>
                            <strong>↑↓:</strong> Up, Down
                          </div>
                          <div>
                            <strong>←→:</strong> Rotate Left, Right
                          </div>
                          <div>
                            <strong>SPACE:</strong> Land
                          </div>
                        </div>
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Control Sidebar */}
          <div className="space-y-6">
            {/* Connection */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Connection</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button onClick={connectDrone} disabled={!connected || droneConnected} className="w-full">
                  Connect Drone
                </Button>
                <Button onClick={startStream} disabled={!droneConnected || streaming} className="w-full" variant="secondary">
                  Start Stream
                </Button>
                <Button onClick={takeoff} disabled={!droneConnected} className="w-full" variant="outline">
                  Takeoff
                </Button>
              </CardContent>
            </Card>

            {/* Phase 1: Load Field Map */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Phase 1: Field Map</CardTitle>
                <CardDescription>Load exported JSON from farm mapping</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <input ref={fileInputRef} type="file" accept=".json" onChange={loadFieldMap} className="hidden" />
                <Button
                  onClick={() => fileInputRef.current?.click()}
                  variant="outline"
                  className="w-full gap-2"
                >
                  <Upload className="w-4 h-4" />
                  Load Field Map
                </Button>
                {fieldMap && (
                  <div className="text-sm space-y-1 p-3 bg-muted rounded-md">
                    <div className="font-medium">{fieldMap.name}</div>
                    <div className="text-muted-foreground text-xs">ID: {fieldMap.field_id}</div>
                    <div className="text-muted-foreground text-xs">
                      Boundary: {fieldMap.boundary?.length || 0} points
                    </div>
                    <div className="text-muted-foreground text-xs">
                      Obstacles: {fieldMap.obstacles?.length || 0}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Phase 2: Flight Path */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Phase 2: Flight Path</CardTitle>
                <CardDescription>Generate optimal waypoints</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Altitude: {altitude[0]}cm</Label>
                  <Slider value={altitude} onValueChange={setAltitude} min={50} max={300} step={10} />
                </div>
                <div className="space-y-2">
                  <Label>Overlap: {overlap[0]}%</Label>
                  <Slider value={overlap} onValueChange={setOverlap} min={10} max={50} step={5} />
                </div>
                <Button onClick={generateFlightPath} disabled={!fieldMap} className="w-full">
                  Generate Flight Path
                </Button>
                {flightPlan && (
                  <div className="space-y-4">
                    {/* Flight Path Visualization */}
                    <div className="relative overflow-hidden rounded-xl border border-border bg-gradient-to-br from-background via-secondary/5 to-primary/5 p-6">
                      <div className="absolute inset-0 bg-grid-pattern opacity-[0.02]"></div>
                      
                      {/* SVG Canvas */}
                      <svg
                        viewBox="0 0 400 400"
                        className="w-full h-auto max-h-[400px] drop-shadow-lg"
                        style={{ filter: "drop-shadow(0 4px 20px rgba(34, 197, 94, 0.15))" }}
                      >
                        {/* Gradient Definitions */}
                        <defs>
                          <linearGradient id="pathGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="rgb(34, 197, 94)" stopOpacity="0.8" />
                            <stop offset="100%" stopColor="rgb(16, 185, 129)" stopOpacity="0.9" />
                          </linearGradient>
                          <filter id="glow">
                            <feGaussianBlur stdDeviation="2" result="coloredBlur" />
                            <feMerge>
                              <feMergeNode in="coloredBlur" />
                              <feMergeNode in="SourceGraphic" />
                            </feMerge>
                          </filter>
                          <marker
                            id="arrowhead"
                            markerWidth="10"
                            markerHeight="10"
                            refX="8"
                            refY="3"
                            orient="auto"
                          >
                            <polygon points="0 0, 10 3, 0 6" fill="rgb(34, 197, 94)" />
                          </marker>
                        </defs>

                        {/* Field Boundary */}
                        {fieldMap?.boundary && flightPlan?.waypoints && (() => {
                          // Waypoints use x,y (cm) coordinates, field uses lat/lng
                          // Find bounds from waypoints instead
                          const wpBounds = flightPlan.waypoints.reduce(
                            (acc: any, wp: any) => ({
                              minX: Math.min(acc.minX, wp.x || 0),
                              maxX: Math.max(acc.maxX, wp.x || 0),
                              minY: Math.min(acc.minY, wp.y || 0),
                              maxY: Math.max(acc.maxY, wp.y || 0),
                            }),
                            { minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity }
                          );

                          // Add padding
                          const padding = 50;
                          const scaleX = (x: number) => 
                            padding + ((x - wpBounds.minX) / (wpBounds.maxX - wpBounds.minX)) * (400 - 2 * padding);
                          const scaleY = (y: number) => 
                            (400 - padding) - ((y - wpBounds.minY) / (wpBounds.maxY - wpBounds.minY)) * (400 - 2 * padding);

                          return (
                            <g>
                              {/* Clean Background */}
                              <rect
                                x="0"
                                y="0"
                                width="400"
                                height="400"
                                fill="#f9fafb"
                                stroke="rgba(0, 0, 0, 0.08)"
                                strokeWidth="1"
                              />

                              {/* Flight Path - Draw FIRST (background, very faded) */}
                              {flightPlan.waypoints && flightPlan.waypoints.length > 0 && (
                                <g opacity="0.3">
                                  {/* Individual Path Segments */}
                                  {flightPlan.waypoints
                                    .filter((wp: any) => wp && typeof wp.x === 'number' && typeof wp.y === 'number')
                                    .map((wp: any, i: number, arr: any[]) => {
                                      if (i === arr.length - 1) return null;
                                      const nextWp = arr[i + 1];
                                      
                                      return (
                                        <line
                                          key={`segment-${i}`}
                                          x1={scaleX(wp.x)}
                                          y1={scaleY(wp.y)}
                                          x2={scaleX(nextWp.x)}
                                          y2={scaleY(nextWp.y)}
                                          stroke="rgb(59, 130, 246)"
                                          strokeWidth="1.5"
                                          strokeLinecap="round"
                                        />
                                      );
                                    })}
                                </g>
                              )}

                              {/* Obstacles (Orange) - Draw ON TOP with white blocker underneath */}
                              {fieldMap?.obstacles?.map((obs: any, idx: number) => {
                                const obsBoundary = obs.boundary || [];
                                if (obsBoundary.length < 3) return null;
                                
                                const obsPath = obsBoundary
                                  .map((coord: number[], i: number) => 
                                    `${i === 0 ? 'M' : 'L'} ${scaleX(coord[0] * 100)} ${scaleY(coord[1] * 100)}`
                                  )
                                  .join(' ') + ' Z';
                                
                                return (
                                  <g key={`obstacle-${idx}`}>
                                    {/* White blocker layer to ensure path is covered */}
                                    <path
                                      d={obsPath}
                                      fill="white"
                                      stroke="none"
                                    />
                                    {/* Orange obstacle layer */}
                                    <path
                                      d={obsPath}
                                      fill="rgb(249, 115, 22)"
                                      stroke="rgb(234, 88, 12)"
                                      strokeWidth="4"
                                    />
                                    <text
                                      x={scaleX(obsBoundary[0][0] * 100 + 10)}
                                      y={scaleY(obsBoundary[0][1] * 100 + 10)}
                                      fontSize="16"
                                      fill="rgb(124, 45, 18)"
                                      fontWeight="700"
                                    >
                                      🚧
                                    </text>
                                  </g>
                                );
                              })}

                              {/* No-Fly Zones (Amber) - Draw ON TOP with white blocker underneath */}
                              {fieldMap?.no_fly_zones?.map((nfz: any, idx: number) => {
                                const nfzBoundary = nfz.boundary || [];
                                if (nfzBoundary.length < 3) return null;
                                
                                const nfzPath = nfzBoundary
                                  .map((coord: number[], i: number) => 
                                    `${i === 0 ? 'M' : 'L'} ${scaleX(coord[0] * 100)} ${scaleY(coord[1] * 100)}`
                                  )
                                  .join(' ') + ' Z';
                                
                                return (
                                  <g key={`nofly-${idx}`}>
                                    {/* White blocker layer to ensure path is COMPLETELY covered */}
                                    <path
                                      d={nfzPath}
                                      fill="white"
                                      stroke="none"
                                    />
                                    {/* Amber no-fly zone layer */}
                                    <path
                                      d={nfzPath}
                                      fill="rgb(245, 158, 11)"
                                      stroke="rgb(217, 119, 6)"
                                      strokeWidth="5"
                                      strokeDasharray="10 5"
                                    />
                                    <text
                                      x={scaleX(nfzBoundary[0][0] * 100 + 15)}
                                      y={scaleY(nfzBoundary[0][1] * 100 + 20)}
                                      fontSize="22"
                                      fill="rgb(120, 53, 15)"
                                      fontWeight="700"
                                    >
                                      ⚠️ NO-FLY
                                    </text>
                                  </g>
                                );
                              })}

                              {/* Waypoint markers - Draw LAST so they're always visible */}
                              {flightPlan.waypoints && flightPlan.waypoints.length > 0 && (
                                <g>
                                  {flightPlan.waypoints
                                    .filter((wp: any) => wp && typeof wp.x === 'number' && typeof wp.y === 'number')
                                    .map((wp: any, i: number) => {
                                      const isStart = i === 0;
                                      const isEnd = i === flightPlan.waypoints.length - 1;
                                      
                                      return (
                                        <g key={`waypoint-${i}`}>
                                          {isStart && (
                                            <>
                                              <circle
                                                cx={scaleX(wp.x)}
                                                cy={scaleY(wp.y)}
                                                r="10"
                                                fill="rgb(34, 197, 94)"
                                                stroke="white"
                                                strokeWidth="3"
                                              />
                                              <text
                                                x={scaleX(wp.x)}
                                                y={scaleY(wp.y) - 18}
                                                textAnchor="middle"
                                                fontSize="13"
                                                fontWeight="700"
                                                fill="rgb(34, 197, 94)"
                                                className="pointer-events-none select-none"
                                              >
                                                START
                                              </text>
                                            </>
                                          )}
                                          
                                          {isEnd && (
                                            <>
                                              <circle
                                                cx={scaleX(wp.x)}
                                                cy={scaleY(wp.y)}
                                                r="10"
                                                fill="rgb(239, 68, 68)"
                                                stroke="white"
                                                strokeWidth="3"
                                              />
                                              <text
                                                x={scaleX(wp.x)}
                                                y={scaleY(wp.y) - 18}
                                                textAnchor="middle"
                                                fontSize="13"
                                                fontWeight="700"
                                                fill="rgb(239, 68, 68)"
                                                className="pointer-events-none select-none"
                                              >
                                                END
                                              </text>
                                            </>
                                          )}
                                          
                                          {!isStart && !isEnd && (
                                            <circle
                                              cx={scaleX(wp.x)}
                                              cy={scaleY(wp.y)}
                                              r="2.5"
                                              fill="rgb(59, 130, 246)"
                                              stroke="white"
                                              strokeWidth="1"
                                            />
                                          )}
                                        </g>
                                      );
                                    })}
                                </g>
                              )}
                            </g>
                          );
                        })()}
                      </svg>

                      {/* Legend */}
                      <div className="mt-4 flex flex-wrap items-center justify-center gap-4 text-xs">
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full bg-green-500 shadow-sm"></div>
                          <span className="text-muted-foreground font-medium">Start</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full bg-blue-500 shadow-sm"></div>
                          <span className="text-muted-foreground font-medium">Path</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full bg-red-500 shadow-sm"></div>
                          <span className="text-muted-foreground font-medium">End</span>
                        </div>
                        {fieldMap?.obstacles && fieldMap.obstacles.length > 0 && (
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded bg-orange-500 shadow-sm"></div>
                            <span className="text-muted-foreground font-medium">Obstacles</span>
                          </div>
                        )}
                        {fieldMap?.no_fly_zones && fieldMap.no_fly_zones.length > 0 && (
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded bg-amber-500 shadow-sm border-2 border-amber-600 border-dashed"></div>
                            <span className="text-muted-foreground font-medium">No-Fly Zones</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Warning for impossible missions */}
                    {flightPlan.estimated_battery_pct > 100 ? (
                      <Alert className="border-red-500 bg-red-50 mb-4">
                        <AlertCircle className="h-4 w-4 text-red-600" />
                        <AlertDescription className="text-red-800">
                          <strong>Mission Impossible!</strong> This route requires {flightPlan.batteries_needed} batteries 
                          ({Math.floor(flightPlan.estimated_duration_sec / 60)} minutes). 
                          Tello max: ~30 min/battery. <strong>Reduce obstacles or field size!</strong>
                        </AlertDescription>
                      </Alert>
                    ) : flightPlan.estimated_battery_pct > 80 && (
                      <Alert className="border-amber-500 bg-amber-50 mb-4">
                        <AlertCircle className="h-4 w-4 text-amber-600" />
                        <AlertDescription className="text-amber-800">
                          <strong>High Battery Usage:</strong> This mission will use {flightPlan.estimated_battery_pct}% battery 
                          (~{Math.floor(flightPlan.estimated_duration_sec / 60)} minutes). Consider simplifying the route.
                        </AlertDescription>
                      </Alert>
                    )}

                    {/* Stats Grid */}
                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-4 rounded-lg bg-gradient-to-br from-primary/10 to-primary/5 border border-primary/20">
                        <div className="text-2xl font-bold text-primary">{flightPlan.total_waypoints}</div>
                        <div className="text-xs text-muted-foreground mt-1">Waypoints</div>
                      </div>
                      <div className="p-4 rounded-lg bg-gradient-to-br from-blue-500/10 to-blue-500/5 border border-blue-500/20">
                        <div className="text-2xl font-bold text-blue-600">{flightPlan.total_distance_m}m</div>
                        <div className="text-xs text-muted-foreground mt-1">Total Distance</div>
                      </div>
                      <div className={`p-4 rounded-lg ${
                        flightPlan.estimated_battery_pct > 100 
                          ? 'bg-gradient-to-br from-red-500/20 to-red-500/10 border border-red-500/40' 
                          : flightPlan.estimated_battery_pct > 80
                          ? 'bg-gradient-to-br from-amber-500/15 to-amber-500/8 border border-amber-500/30'
                          : 'bg-gradient-to-br from-amber-500/10 to-amber-500/5 border border-amber-500/20'
                      }`}>
                        <div className={`text-2xl font-bold ${
                          flightPlan.estimated_battery_pct > 100 ? 'text-red-600' : 'text-amber-600'
                        }`}>
                          {flightPlan.estimated_battery_pct}%
                          {flightPlan.batteries_needed && flightPlan.batteries_needed > 1 && (
                            <span className="text-sm ml-1">({flightPlan.batteries_needed}x)</span>
                          )}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          Est. Battery
                          {flightPlan.estimated_battery_pct > 100 && (
                            <span className="block text-red-500 font-semibold mt-1">⚠️ IMPOSSIBLE</span>
                          )}
                        </div>
                      </div>
                      <div className="p-4 rounded-lg bg-gradient-to-br from-emerald-500/10 to-emerald-500/5 border border-emerald-500/20">
                        <div className="text-2xl font-bold text-emerald-600">
                          {Math.floor(flightPlan.estimated_duration_sec / 60)}:{String(flightPlan.estimated_duration_sec % 60).padStart(2, '0')}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">Est. Duration</div>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Phase 3: Execute Mission */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Phase 3: Execute</CardTitle>
                <CardDescription>Autonomous flight</CardDescription>
              </CardHeader>
              <CardContent>
                <Button
                  onClick={executeMission}
                  disabled={!droneConnected || !flightPlan}
                  className="w-full gap-2 bg-primary"
                  size="lg"
                >
                  <Play className="w-5 h-5" />
                  START MISSION
                </Button>
              </CardContent>
            </Card>

            {/* Telemetry */}
            {telemetry && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Telemetry</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Battery:</span>
                    <span className="font-medium">{telemetry.battery}%</span>
                  </div>
                  <Progress value={telemetry.battery} className="h-2" />
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Height:</span>
                    <span className="font-medium">{telemetry.height}cm</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Flight Time:</span>
                    <span className="font-medium">{telemetry.flight_time}s</span>
                  </div>
                  {telemetry.distance_traveled && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Distance:</span>
                      <span className="font-medium">{telemetry.distance_traveled.toFixed(1)}m</span>
                    </div>
                  )}
                  {telemetry.temperature && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Temperature:</span>
                      <span className="font-medium">
                        {((telemetry.temperature.high + telemetry.temperature.low) / 2).toFixed(0)}°C
                      </span>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MissionControl;

