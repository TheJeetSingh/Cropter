import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useEffect, useState } from "react";
import droneImage from "@/assets/drone-flight.jpg";

const MyDrone = () => {
  const [battery, setBattery] = useState(78);
  const [altitude, setAltitude] = useState(125.4);

  useEffect(() => {
    // Simulate live telemetry updates
    const interval = setInterval(() => {
      setBattery((prev) => Math.max(70, prev - 0.1));
      setAltitude((prev) => prev + (Math.random() - 0.5) * 2);
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen pt-32 pb-20 px-6">
      <div className="container mx-auto max-w-6xl">
        <div className="text-center mb-16 space-y-4">
          <h1 className="text-6xl font-light tracking-tight text-foreground">
            My <span className="font-semibold bg-gradient-hero bg-clip-text text-transparent">Drone</span>
          </h1>
          <p className="text-xl font-light text-muted-foreground">
            Real-time telemetry and monitoring
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Camera Feed */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="shadow-medium border-border/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-2xl font-light">Live Feed</CardTitle>
                    <CardDescription>4K • 60 FPS • HDR</CardDescription>
                  </div>
                  <Badge className="bg-red-500 animate-pulse">LIVE</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="relative aspect-video rounded-lg overflow-hidden bg-gradient-to-br from-slate-900 to-slate-800">
                  <img
                    src={droneImage}
                    alt="Drone camera feed"
                    className="w-full h-full object-cover opacity-40"
                  />
                  
                  {/* HUD Overlay */}
                  <div className="absolute top-6 left-6 right-6 flex justify-between text-xs text-white font-mono">
                    <div className="bg-black/60 backdrop-blur-sm px-4 py-2 rounded">
                      ALT: {altitude.toFixed(1)}m
                    </div>
                    <div className="bg-black/60 backdrop-blur-sm px-4 py-2 rounded">
                      SPD: 8.5 m/s
                    </div>
                    <div className="bg-black/60 backdrop-blur-sm px-4 py-2 rounded">
                      GPS: 12 SAT
                    </div>
                  </div>

                  {/* Center Crosshair */}
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div className="relative">
                      <div className="w-12 h-12 border border-white/40 rounded-full" />
                      <div className="absolute top-1/2 left-1/2 w-6 h-px bg-white/40 -translate-x-1/2" />
                      <div className="absolute top-1/2 left-1/2 h-6 w-px bg-white/40 -translate-y-1/2" />
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-center gap-3 mt-6">
                  <Button size="sm" variant="outline" className="rounded-full">
                    Record
                  </Button>
                  <Button size="sm" variant="outline" className="rounded-full">
                    Snapshot
                  </Button>
                  <Button size="sm" variant="outline" className="rounded-full">
                    Reset View
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Flight Path */}
            <Card className="shadow-medium border-border/50">
              <CardHeader>
                <CardTitle className="text-2xl font-light">Flight Path</CardTitle>
                <CardDescription>Today's coverage area</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="aspect-video rounded-lg bg-muted/50 flex items-center justify-center">
                  <div className="text-center space-y-2">
                    <div className="text-4xl font-light text-primary">45.2</div>
                    <div className="text-sm text-muted-foreground uppercase tracking-wider">
                      Acres Covered
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Telemetry Sidebar */}
          <div className="space-y-6">
            {/* Status */}
            <Card className="shadow-medium border-border/50">
              <CardHeader>
                <CardTitle className="text-xl font-light">Status</CardTitle>
                <CardDescription>DJI Agras T40</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Flight Mode</span>
                  <Badge className="bg-primary text-primary-foreground">Active</Badge>
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Battery</span>
                    <span className="font-medium">{battery.toFixed(1)}%</span>
                  </div>
                  <Progress value={battery} className="h-1.5" />
                  <div className="text-xs text-muted-foreground">
                    ~{Math.floor(battery * 0.36)} minutes remaining
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Signal Strength</span>
                    <span className="font-medium">95%</span>
                  </div>
                  <Progress value={95} className="h-1.5" />
                </div>
              </CardContent>
            </Card>

            {/* Telemetry */}
            <Card className="shadow-medium border-border/50">
              <CardHeader>
                <CardTitle className="text-xl font-light">Telemetry</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Altitude</span>
                  <span className="font-medium">{altitude.toFixed(1)} m</span>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Speed</span>
                  <span className="font-medium">8.5 m/s</span>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Temperature</span>
                  <span className="font-medium">24°C</span>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">GPS Satellites</span>
                  <span className="font-medium">12</span>
                </div>

                <div className="pt-4 border-t border-border space-y-1">
                  <div className="text-sm text-muted-foreground">Coordinates</div>
                  <div className="font-mono text-xs">40.7128° N, 74.0060° W</div>
                </div>
              </CardContent>
            </Card>

            {/* Statistics */}
            <Card className="shadow-medium border-border/50">
              <CardHeader>
                <CardTitle className="text-xl font-light">Statistics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Total Flights</span>
                  <span className="font-medium">127</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Today's Flight Time</span>
                  <span className="font-medium">2h 34m</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Last Service</span>
                  <span className="font-medium">3 days ago</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MyDrone;
