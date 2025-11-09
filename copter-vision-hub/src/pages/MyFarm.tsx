import { Link } from "react-router-dom";
import { useRef, useState } from "react";
import { Activity, PlaneTakeoff, UploadCloud, Scan, Clock, Loader2, Sprout } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";
import myFarmImage from "@/assets/my-farm.jpg";
import { analyzeVideo } from "@/lib/analysisApi";
import { AnalysisResults } from "@/components/AnalysisResults";
import type { AnalysisResponse, UploadProgress } from "@/types/analysis";

const MyFarm = () => {
  const { toast } = useToast();
  const uploadInputRef = useRef<HTMLInputElement>(null);
  const [uploadName, setUploadName] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null);
  const [analysisResults, setAnalysisResults] = useState<AnalysisResponse | null>(null);

  const handleUploadSelect = async (files: FileList | null) => {
    if (!files || files.length === 0) {
      return;
    }

    const file = files[0];
    
    // Validate file type
    const validTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska'];
    if (!validTypes.includes(file.type)) {
      toast({
        title: "Invalid file type",
        description: "Please upload a video file (MP4, AVI, MOV, or MKV)",
        variant: "destructive",
      });
      return;
    }

    // Validate file size (max 500MB)
    const maxSize = 500 * 1024 * 1024; // 500MB
    if (file.size > maxSize) {
      toast({
        title: "File too large",
        description: "Please upload a video smaller than 500MB",
        variant: "destructive",
      });
      return;
    }

    setUploadName(file.name);
    setIsUploading(true);
    setIsAnalyzing(false);
    setAnalysisResults(null);
    setUploadProgress(null);

    try {
      // Upload and analyze
      const result = await analyzeVideo(
        file,
        {
          conf_threshold: 0.25,
          frame_skip: 2, // Process every 2nd frame for faster demo
          save_video: true,
          save_json: true,
        },
        {
          upload_timestamp: new Date().toISOString(),
          video_name: file.name,
        },
        (progress) => {
          setUploadProgress(progress);
          if (progress.percentage === 100) {
            setIsUploading(false);
            setIsAnalyzing(true);
          }
        }
      );

      setIsAnalyzing(false);
      setAnalysisResults(result);

      toast({
        title: "Analysis Complete!",
        description: `Processed ${result.results?.total_detections || 0} detections`,
      });
    } catch (error) {
      setIsUploading(false);
      setIsAnalyzing(false);
      console.error('Upload error:', error);
      
      toast({
        title: "Analysis Failed",
        description: error instanceof Error ? error.message : "Failed to analyze video. Please try again.",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="min-h-screen pt-36 pb-24 px-6 bg-muted/10">
      <div className="container mx-auto max-w-6xl space-y-24">
        {/* Analysis Results */}
        {analysisResults && uploadName && (
          <section className="animate-in fade-in slide-in-from-bottom-4 duration-700">
            <AnalysisResults results={analysisResults} videoName={uploadName} />
          </section>
        )}

        {/* Upload Progress */}
        {(isUploading || isAnalyzing) && (
          <section className="text-center space-y-6 animate-in fade-in slide-in-from-bottom-4">
            <div className="rounded-3xl border border-border/60 bg-background/95 p-10 shadow-xl">
              <div className="space-y-6">
                <div className="flex items-center justify-center gap-3">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                  <h2 className="text-3xl font-semibold">
                    {isUploading ? "Uploading Video..." : "Analyzing Field..."}
                  </h2>
                </div>
                
                {uploadProgress && isUploading && (
                  <div className="space-y-2">
                    <Progress value={uploadProgress.percentage} className="h-2" />
                    <p className="text-sm text-muted-foreground">
                      {uploadProgress.percentage}% - {(uploadProgress.loaded / 1024 / 1024).toFixed(1)} MB of {(uploadProgress.total / 1024 / 1024).toFixed(1)} MB
                    </p>
                  </div>
                )}

                {isAnalyzing && (
                  <div className="space-y-3">
                    <p className="text-lg text-muted-foreground">
                      Running YOLO model on video frames...
                    </p>
                    <p className="text-sm text-muted-foreground">
                      This may take 2-5 minutes depending on video length
                    </p>
                  </div>
                )}
              </div>
            </div>
          </section>
        )}

        <section className="text-center space-y-8">
          <span className="inline-flex items-center gap-2 rounded-full border border-border/60 bg-background/95 px-6 py-3 text-xs uppercase tracking-[0.5em] text-primary">
            My Farm Suite
          </span>
          <h1 className="text-6xl md:text-7xl font-light tracking-tight text-foreground">
            Command and understand every acre.
          </h1>
          <p className="mx-auto max-w-3xl text-xl text-muted-foreground">
            Deploy your fleet, upload on-the-ground footage, and review historical insights from a single hub built for precision agriculture.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
            <Button
              asChild
              size="lg"
              className="rounded-full px-10 py-6 text-lg font-semibold shadow-medium hover:shadow-large transition-all"
            >
              <Link to="/my-drone">Deploy drone</Link>
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="rounded-full px-10 py-6 text-lg font-semibold hover:bg-secondary/50 transition-all"
              onClick={() => uploadInputRef.current?.click()}
              disabled={isUploading || isAnalyzing}
            >
              {isUploading || isAnalyzing ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Processing...
                </>
              ) : (
                "Upload footage"
              )}
            </Button>
            <input
              ref={uploadInputRef}
              type="file"
              accept="video/*"
              className="hidden"
              onChange={(event) => handleUploadSelect(event.target.files)}
            />
          </div>
        </section>

        <section className="grid gap-8 lg:grid-cols-2">
          <div className="group relative overflow-hidden rounded-[2rem] border border-border/60 bg-background/95 p-10 shadow-[0_24px_60px_rgba(18,38,28,0.18)] transition-transform hover:-translate-y-1">
            <div className="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-primary/10 blur-3xl transition-opacity group-hover:opacity-80" />
            <div className="relative flex flex-col gap-5">
              <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/15 text-primary">
                <PlaneTakeoff className="h-6 w-6" />
              </div>
              <h2 className="text-3xl font-semibold text-foreground">Deploy Copter for live scans</h2>
              <p className="text-lg text-muted-foreground">
                Schedule flights, automate mission planning, and collect multispectral, thermal, and RGB imagery with centimeter accuracy.
              </p>
              <Button
                asChild
                size="lg"
                className="mt-2 w-fit rounded-full px-8 py-4 text-base font-semibold shadow-medium transition-transform hover:-translate-y-0.5"
              >
                <Link to="/my-drone">Schedule a mission</Link>
              </Button>
              <div className="mt-6 grid gap-4 sm:grid-cols-2 text-sm text-muted-foreground">
                <div className="rounded-2xl border border-border/60 bg-muted/30 p-4">
                  <p className="font-semibold text-foreground">Live telemetry</p>
                  <p>Altitude, speed, and camera payload streamed in real time.</p>
                </div>
                <div className="rounded-2xl border border-border/60 bg-muted/30 p-4">
                  <p className="font-semibold text-foreground">Automated stitching</p>
                  <p>Generate orthomosaics and NDVI maps minutes after landing.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="group relative overflow-hidden rounded-[2rem] border border-border/60 bg-background/95 p-10 shadow-[0_24px_60px_rgba(18,38,28,0.18)] transition-transform hover:-translate-y-1">
            <div className="absolute -left-28 -bottom-28 h-80 w-80 rounded-full bg-emerald-500/10 blur-3xl transition-opacity group-hover:opacity-80" />
            <div className="relative flex flex-col gap-5">
              <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/15 text-emerald-500">
                <UploadCloud className="h-6 w-6" />
              </div>
              <h2 className="text-3xl font-semibold text-foreground">Upload footage for analytics</h2>
              <p className="text-lg text-muted-foreground">
                Bring in drone, tractor, or ground-cam video to unlock AI-assisted scouting, disease detection, and pest monitoring.
              </p>
              <label className={`mt-2 inline-flex w-full flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-border/70 bg-muted/30 px-8 py-10 text-center text-base font-medium text-muted-foreground transition-colors hover:border-primary/60 hover:text-foreground ${isUploading || isAnalyzing ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}>
                <UploadCloud className="h-10 w-10 text-primary" />
                <span>{uploadName ?? "Upload MP4 / MOV / MKV"}</span>
                {!isUploading && !isAnalyzing && (
                <input
                  type="file"
                  accept="video/*"
                  className="hidden"
                  onChange={(event) => handleUploadSelect(event.target.files)}
                />
                )}
              </label>
              {(isUploading || isAnalyzing) && uploadName && (
                <p className="text-sm text-primary">
                  {isUploading ? "Uploading..." : "Analyzing..."} {uploadName}
                </p>
              )}
              <div className="mt-6 grid gap-4 sm:grid-cols-2 text-sm text-muted-foreground">
                <div className="rounded-2xl border border-border/60 bg-muted/30 p-4">
                  <p className="font-semibold text-foreground">Spatial tagging</p>
                  <p>Frame-by-frame geolocation to compare with historical datasets.</p>
                </div>
                <div className="rounded-2xl border border-border/60 bg-muted/30 p-4">
                  <p className="font-semibold text-foreground">Instant insights</p>
                  <p>Auto-detect anomalies, water stress, and pest signatures.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-16 lg:grid-cols-[1.05fr_1fr] items-center">
          <div className="space-y-6">
            <h2 className="text-5xl font-light tracking-tight text-foreground">
              Visual intelligence without leaving the barn.
            </h2>
            <p className="text-lg text-muted-foreground leading-relaxed">
              Composite dashboards merge video overlays, drone telemetry, and agronomic layers to keep your team aligned on crop health, pest management, and operational risks.
            </p>
            <div className="flex flex-wrap gap-3 pt-2">
              <div className="rounded-full border border-border/60 bg-background px-4 py-2 text-sm text-muted-foreground">
                Precision overlays
              </div>
              <div className="rounded-full border border-border/60 bg-background px-4 py-2 text-sm text-muted-foreground">
                Drone telemetry
              </div>
              <div className="rounded-full border border-border/60 bg-background px-4 py-2 text-sm text-muted-foreground">
                Agronomic insights
              </div>
            </div>
          </div>

          <div className="relative">
            <div className="relative overflow-hidden rounded-[2.5rem] border border-border/40 shadow-[0_30px_60px_rgba(15,35,25,0.18)]">
              <img
                src={myFarmImage}
                alt="Aerial view of a modern farm landscape"
                className="h-full w-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-tr from-background/45 via-background/10 to-transparent" />

              <div className="absolute top-8 left-8 flex items-center gap-3 rounded-2xl border border-white/40 bg-white/80 px-4 py-3 text-sm font-medium text-primary shadow-[0_10px_30px_rgba(34,197,94,0.22)] backdrop-blur">
                <Scan className="h-5 w-5" />
                Live drone pass • 76m altitude
              </div>

              <div className="absolute bottom-8 right-8 w-60 space-y-3 rounded-2xl border border-white/30 bg-background/90 p-4 shadow-[0_20px_45px_rgba(20,30,25,0.25)] backdrop-blur">
                <div className="flex items-center justify-between text-xs uppercase tracking-widest text-muted-foreground">
                  <span>AR Metrics</span>
                  <span>Sync 01:24</span>
                </div>
                <div className="rounded-xl border border-border/60 bg-background/90 p-3">
                  <div className="flex items-center gap-3">
                    <Activity className="h-4 w-4 text-primary" />
                    <div className="text-sm font-medium text-foreground">
                      Health Index
                    </div>
                    <span className="ml-auto text-sm font-semibold text-primary">92%</span>
                  </div>
                  <div className="mt-3 h-1.5 rounded-full bg-muted">
                    <div className="h-full w-[92%] rounded-full bg-primary" />
                  </div>
                </div>
                <div className="rounded-xl border border-border/60 bg-background/90 p-3">
                  <div className="flex items-center gap-3">
                    <Sprout className="h-4 w-4 text-emerald-500" />
                    <div className="text-sm font-medium text-foreground">
                      Growth Status
                    </div>
                    <span className="ml-auto text-sm font-semibold text-emerald-500">Optimal</span>
                  </div>
                  <p className="mt-2 text-xs text-muted-foreground">
                    Healthy growth detected across north fields.
                  </p>
                </div>
              </div>
            </div>

            <div className="absolute -bottom-10 -left-10 hidden rotate-3 rounded-3xl border border-primary/20 bg-primary/5 px-5 py-6 text-xs font-medium uppercase tracking-[0.5em] text-primary shadow-inner sm:block">
              AR Overlay Active
            </div>
          </div>
        </section>

        <section className="grid gap-12 lg:grid-cols-[1fr_0.85fr]">
          <div className="rounded-[2rem] border border-border/60 bg-background/95 p-10 shadow-[0_24px_60px_rgba(18,38,28,0.18)]">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/15 text-primary">
                <Clock className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-3xl font-semibold text-foreground">Farm timeline</h3>
                <p className="text-sm uppercase tracking-[0.4em] text-muted-foreground">Recent activity</p>
              </div>
            </div>
              <div className="mt-8 space-y-6">
                <div className="relative pl-6 before:absolute before:left-1.5 before:top-1 before:h-full before:w-px before:bg-border">
                  <div className="absolute left-0 top-1.5 h-3 w-3 rounded-full border border-primary bg-background" />
                  <p className="text-sm uppercase tracking-wide text-muted-foreground">Oct 23 • Soil Cluster A</p>
                  <p className="text-lg text-foreground">Nutrient imbalance detected • Recommendation issued</p>
                </div>
                <div className="relative pl-6 before:absolute before:left-1.5 before:top-1 before:h-full before:w-px before:bg-border">
                  <div className="absolute left-0 top-1.5 h-3 w-3 rounded-full border border-emerald-500 bg-background" />
                  <p className="text-sm uppercase tracking-wide text-muted-foreground">Sep 12 • Orchard Belt</p>
                <p className="text-lg text-foreground">Canopy vigor improved after targeted fertilization treatment</p>
                </div>
                <div className="relative pl-6">
                  <div className="absolute left-0 top-1.5 h-3 w-3 rounded-full border border-border bg-background" />
                  <p className="text-sm uppercase tracking-wide text-muted-foreground">Aug 02 • Field 3</p>
                  <p className="text-lg text-foreground">Historical imagery archived</p>
                </div>
              </div>
          </div>

          <div className="flex flex-col justify-between gap-6 rounded-[2rem] border border-border/60 bg-background/95 p-10 shadow-[0_24px_60px_rgba(18,38,28,0.18)]">
                <div className="space-y-4">
              <h3 className="text-3xl font-semibold text-foreground">Quick Actions</h3>
                  <p className="text-lg text-muted-foreground">
                Deploy a new mission or upload footage to analyze your farm with AI-powered insights.
                  </p>
                </div>
            <div className="flex flex-col gap-3">
                <Button
                asChild
                  size="lg"
                className="rounded-full bg-gradient-to-r from-primary to-emerald-500 px-10 py-6 text-lg font-semibold text-primary-foreground shadow-[0_20px_45px_rgba(34,197,94,0.28)] transition-transform hover:-translate-y-0.5"
                >
                <Link to="/mission-control">Launch Mission</Link>
                </Button>
                <Button
                  asChild
                  size="lg"
                variant="outline"
                className="rounded-full border-primary/50 px-10 py-6 text-lg font-semibold text-primary hover:bg-primary/10"
                >
                <Link to="/farm-mapping">Map New Field</Link>
                </Button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default MyFarm;

