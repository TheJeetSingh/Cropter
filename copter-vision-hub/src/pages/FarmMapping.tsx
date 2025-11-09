import { useState, useRef, useEffect } from "react";
import { MapContainer, TileLayer, Rectangle, Polygon, useMapEvents, Marker, useMap } from "react-leaflet";
import { LatLng, LatLngBounds } from "leaflet";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Download, RotateCcw, Check, Plus } from "lucide-react";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// Fix Leaflet default marker icon issue with Vite
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface Obstacle {
  id: string;
  boundary: [number, number][];
  area: number;
}

interface NoFlyZone {
  id: string;
  boundary: [number, number][];
  area: number;
  reason?: string;
}

const FarmMapping = () => {
  const [pinA, setPinA] = useState<LatLng>(new LatLng(36.7367, -119.7851));
  const [pinB, setPinB] = useState<LatLng>(new LatLng(36.7386, -119.7823));
  const [mode, setMode] = useState<"base" | "obstacle" | "nofly">("base");
  const [nextPin, setNextPin] = useState<"a" | "b">("a");
  const [obstacles, setObstacles] = useState<Obstacle[]>([]);
  const [noFlyZones, setNoFlyZones] = useState<NoFlyZone[]>([]);
  const [obstacleStart, setObstacleStart] = useState<LatLng | null>(null);
  const [noFlyStart, setNoFlyStart] = useState<LatLng | null>(null);
  const [metrics, setMetrics] = useState({ width: 0, length: 0, baseArea: 0, netArea: 0 });

  const markerIconA = L.divIcon({
    className: "",
    html: `<span style="display:block;width:18px;height:18px;border-radius:50%;background:#22c55e;border:2px solid #0f172a;box-shadow:0 0 0 2px rgba(15,23,42,0.3);"></span>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  });

  const markerIconB = L.divIcon({
    className: "",
    html: `<span style="display:block;width:18px;height:18px;border-radius:50%;background:#ef4444;border:2px solid #0f172a;box-shadow:0 0 0 2px rgba(15,23,42,0.3);"></span>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  });

  const calculateMetrics = () => {
    const bounds = new LatLngBounds(pinA, pinB);
    const sw = bounds.getSouthWest();
    const ne = bounds.getNorthEast();
    const nw = new LatLng(ne.lat, sw.lng);
    const se = new LatLng(sw.lat, ne.lng);

    const width = sw.distanceTo(se);
    const length = sw.distanceTo(nw);
    const baseArea = width * length;
    const obstacleArea = obstacles.reduce((sum, obs) => sum + obs.area, 0);
    const noFlyArea = noFlyZones.reduce((sum, nfz) => sum + nfz.area, 0);
    const netArea = Math.max(baseArea - obstacleArea - noFlyArea, 0);

    setMetrics({ width, length, baseArea, netArea });
  };

  useEffect(() => {
    calculateMetrics();
  }, [pinA, pinB, obstacles, noFlyZones]);

  const latLngToMeters = (latLng: LatLng, origin: LatLng): [number, number] => {
    const R = 6371000;
    const lat1 = (origin.lat * Math.PI) / 180;
    const lat2 = (latLng.lat * Math.PI) / 180;
    const deltaLng = ((latLng.lng - origin.lng) * Math.PI) / 180;
    const deltaLat = ((latLng.lat - origin.lat) * Math.PI) / 180;

    const x = R * deltaLng * Math.cos((lat1 + lat2) / 2);
    const y = R * deltaLat;

    return [parseFloat(x.toFixed(2)), parseFloat(y.toFixed(2))];
  };

  const exportJSON = () => {
    const bounds = new LatLngBounds(pinA, pinB);
    const sw = bounds.getSouthWest();
    const ne = bounds.getNorthEast();
    const nw = new LatLng(ne.lat, sw.lng);
    const se = new LatLng(sw.lat, ne.lng);
    const origin = sw;

    const boundary = [
      [0, 0],
      latLngToMeters(se, origin),
      latLngToMeters(ne, origin),
      latLngToMeters(nw, origin),
      [0, 0],
    ];

    const obstaclesData = obstacles.map((obs) => ({
      type: "obstacle",
      boundary: obs.boundary.map((latLng) => latLngToMeters(new LatLng(latLng[0], latLng[1]), origin)),
    }));

    const noFlyZonesData = noFlyZones.map((nfz) => ({
      type: "no_fly_zone",
      boundary: nfz.boundary.map((latLng) => latLngToMeters(new LatLng(latLng[0], latLng[1]), origin)),
      reason: nfz.reason || "Safety restriction",
    }));

    const timestamp = new Date().toISOString().replace(/[-:]/g, "").split(".")[0];
    const fieldId = `farm_${timestamp}`;

    const json = {
      field_id: fieldId,
      name: "Farm Field from Phase 1 Mapping",
      boundary,
      obstacles: obstaclesData,
      no_fly_zones: noFlyZonesData,
      reference_point: {
        lat: parseFloat(origin.lat.toFixed(6)),
        lon: parseFloat(origin.lng.toFixed(6)),
      },
    };

    const jsonString = JSON.stringify(json, null, 2);
    const blob = new Blob([jsonString], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${fieldId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const MapClickHandler = () => {
    useMapEvents({
      click: (e) => {
        if (mode === "base") {
          if (nextPin === "a") {
            setPinA(e.latlng);
            setNextPin("b");
          } else {
            setPinB(e.latlng);
            setNextPin("a");
          }
        } else if (mode === "obstacle") {
          const bounds = new LatLngBounds(pinA, pinB);
          if (!bounds.contains(e.latlng)) {
            alert("Please click inside the main rectangle.");
            return;
          }

          if (!obstacleStart) {
            setObstacleStart(e.latlng);
          } else {
            const obsBounds = new LatLngBounds(obstacleStart, e.latlng);
            const sw = obsBounds.getSouthWest();
            const ne = obsBounds.getNorthEast();
            const nw = new LatLng(ne.lat, sw.lng);
            const se = new LatLng(sw.lat, ne.lng);

            const width = sw.distanceTo(se);
            const length = sw.distanceTo(nw);
            const area = width * length;

            if (area > 1) {
              const newObstacle: Obstacle = {
                id: crypto.randomUUID(),
                boundary: [
                  [sw.lat, sw.lng],
                  [se.lat, se.lng],
                  [ne.lat, ne.lng],
                  [nw.lat, nw.lng],
                  [sw.lat, sw.lng],
                ],
                area,
              };
              setObstacles([...obstacles, newObstacle]);
            }

            setObstacleStart(null);
          }
        } else if (mode === "nofly") {
          const bounds = new LatLngBounds(pinA, pinB);
          if (!bounds.contains(e.latlng)) {
            alert("Please click inside the main rectangle.");
            return;
          }

          if (!noFlyStart) {
            setNoFlyStart(e.latlng);
          } else {
            const nfzBounds = new LatLngBounds(noFlyStart, e.latlng);
            const sw = nfzBounds.getSouthWest();
            const ne = nfzBounds.getNorthEast();
            const nw = new LatLng(ne.lat, sw.lng);
            const se = new LatLng(sw.lat, ne.lng);

            const width = sw.distanceTo(se);
            const length = sw.distanceTo(nw);
            const area = width * length;

            if (area > 1) {
              const newNoFlyZone: NoFlyZone = {
                id: crypto.randomUUID(),
                boundary: [
                  [sw.lat, sw.lng],
                  [se.lat, se.lng],
                  [ne.lat, ne.lng],
                  [nw.lat, nw.lng],
                  [sw.lat, sw.lng],
                ],
                area,
                reason: "Safety restriction",
              };
              setNoFlyZones([...noFlyZones, newNoFlyZone]);
            }

            setNoFlyStart(null);
          }
        }
      },
    });
    return null;
  };

  const DraggableMarkers = () => {
    const map = useMap();

    return (
      <>
        <Marker
          position={pinA}
          draggable={mode === "base"}
          icon={markerIconA}
          eventHandlers={{
            dragend: (e) => {
              setPinA(e.target.getLatLng());
            },
          }}
        />
        <Marker
          position={pinB}
          draggable={mode === "base"}
          icon={markerIconB}
          eventHandlers={{
            dragend: (e) => {
              setPinB(e.target.getLatLng());
            },
          }}
        />
      </>
    );
  };

  const formatMeters = (value: number) => {
    if (value >= 1000) return `${(value / 1000).toFixed(2)} km`;
    return `${value.toFixed(1)} m`;
  };

  const formatArea = (sqm: number) => {
    if (sqm >= 1000000) return `${(sqm / 1000000).toFixed(2)} km²`;
    if (sqm >= 10000) return `${(sqm / 10000).toFixed(2)} ha`;
    return `${sqm.toFixed(1)} m²`;
  };

  return (
    <div className="min-h-screen pt-32 pb-20 px-6">
      <div className="container mx-auto max-w-7xl">
        <div className="text-center mb-12 space-y-4">
          <h1 className="text-6xl font-light tracking-tight text-foreground">
            Farm <span className="font-semibold bg-gradient-hero bg-clip-text text-transparent">Mapping</span>
          </h1>
          <p className="text-xl font-light text-muted-foreground">Phase 1: Define field boundaries and obstacles</p>
        </div>

        <div className="grid lg:grid-cols-4 gap-6">
          <aside className="lg:col-span-1 space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Controls</CardTitle>
                <CardDescription>
                  {mode === "base" 
                    ? "Click or drag pins on map" 
                    : mode === "obstacle"
                    ? "Click inside rectangle for obstacles"
                    : "Click inside rectangle for no-fly zones"}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-2">
                  <span className="w-4 h-4 rounded-full bg-green-500 border-2 border-background" />
                  <span className="text-sm">Pin A (SW corner)</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-4 h-4 rounded-full bg-red-500 border-2 border-background" />
                  <span className="text-sm">Pin B (NE corner)</span>
                </div>
                {mode === "base" && (
                  <div className="text-sm text-muted-foreground">
                    Next click sets: <span className="font-semibold text-foreground">Pin {nextPin.toUpperCase()}</span>
                  </div>
                )}
                {mode === "obstacle" && obstacleStart && (
                  <div className="text-sm text-muted-foreground">Click opposite corner to complete obstacle</div>
                )}
                {mode === "nofly" && noFlyStart && (
                  <div className="text-sm text-muted-foreground">Click opposite corner to complete no-fly zone</div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Metrics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Width:</span>
                  <span className="font-medium">{formatMeters(metrics.width)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Length:</span>
                  <span className="font-medium">{formatMeters(metrics.length)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Base Area:</span>
                  <span className="font-medium">{formatArea(metrics.baseArea)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Net Area:</span>
                  <span className="font-medium text-primary">{formatArea(metrics.netArea)}</span>
                </div>
              </CardContent>
            </Card>

            <div className="space-y-2">
              {mode === "base" ? (
                <>
                  <Button onClick={() => setMode("obstacle")} className="w-full gap-2">
                    <Check className="w-4 h-4" />
                    Lock Boundary
                  </Button>
                  <Button
                    onClick={() => {
                      setPinA(new LatLng(36.7367, -119.7851));
                      setPinB(new LatLng(36.7386, -119.7823));
                      setNextPin("a");
                    }}
                    variant="outline"
                    className="w-full gap-2"
                  >
                    <RotateCcw className="w-4 h-4" />
                    Reset
                  </Button>
                </>
              ) : (
                <>
                  <div className="flex gap-2">
                    <Button
                      onClick={() => setMode("obstacle")}
                      variant={mode === "obstacle" ? "default" : "outline"}
                      className="flex-1 gap-2"
                      size="sm"
                    >
                      <Plus className="w-4 h-4" />
                      Obstacles
                    </Button>
                    <Button
                      onClick={() => setMode("nofly")}
                      variant={mode === "nofly" ? "default" : "outline"}
                      className="flex-1 gap-2"
                      size="sm"
                    >
                      <Plus className="w-4 h-4" />
                      No-Fly
                    </Button>
                  </div>
                  <Button onClick={exportJSON} className="w-full gap-2 bg-primary">
                    <Download className="w-4 h-4" />
                    Export Field Map
                  </Button>
                  <Button
                    onClick={() => {
                      setMode("base");
                      setObstacles([]);
                      setNoFlyZones([]);
                      setObstacleStart(null);
                      setNoFlyStart(null);
                    }}
                    variant="outline"
                    className="w-full gap-2"
                  >
                    <RotateCcw className="w-4 h-4" />
                    Restart Mapping
                  </Button>
                </>
              )}
            </div>

            {obstacles.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <span className="w-3 h-3 rounded bg-orange-500" />
                    Obstacles
                  </CardTitle>
                  <CardDescription>{obstacles.length} defined</CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  {obstacles.map((obs, idx) => (
                    <div key={obs.id} className="flex justify-between items-center text-sm">
                      <span>Obstacle {idx + 1}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground">{formatArea(obs.area)}</span>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setObstacles(obstacles.filter((o) => o.id !== obs.id))}
                        >
                          Remove
                        </Button>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}

            {noFlyZones.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <span className="w-3 h-3 rounded bg-amber-500" />
                    No-Fly Zones
                  </CardTitle>
                  <CardDescription>{noFlyZones.length} defined</CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  {noFlyZones.map((nfz, idx) => (
                    <div key={nfz.id} className="flex justify-between items-center text-sm">
                      <span>Zone {idx + 1}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground">{formatArea(nfz.area)}</span>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setNoFlyZones(noFlyZones.filter((z) => z.id !== nfz.id))}
                        >
                          Remove
                        </Button>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
          </aside>

          <div className="lg:col-span-3">
            <Card>
              <CardContent className="p-4">
                <div className="rounded-lg overflow-hidden border border-border h-[600px]">
                  <MapContainer
                    center={[36.7378, -119.7838]}
                    zoom={17}
                    style={{ height: "100%", width: "100%" }}
                    zoomControl={true}
                  >
                    <TileLayer
                      url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                    />
                    <MapClickHandler />
                    <DraggableMarkers />
                    <Rectangle
                      bounds={new LatLngBounds(pinA, pinB)}
                      pathOptions={{ color: "#38bdf8", weight: 2, fillOpacity: 0.12, dashArray: "6 4" }}
                    />
                    {obstacles.map((obs) => (
                      <Polygon
                        key={obs.id}
                        positions={obs.boundary.map((coord) => [coord[0], coord[1]])}
                        pathOptions={{ color: "#f97316", weight: 2, fillOpacity: 0.25 }}
                      />
                    ))}
                    {noFlyZones.map((nfz) => (
                      <Polygon
                        key={nfz.id}
                        positions={nfz.boundary.map((coord) => [coord[0], coord[1]])}
                        pathOptions={{ 
                          color: "#f59e0b", 
                          weight: 3, 
                          fillOpacity: 0.35, 
                          dashArray: "10 5",
                          fillPattern: "diagonal-stripe-1"
                        }}
                      />
                    ))}
                  </MapContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FarmMapping;

