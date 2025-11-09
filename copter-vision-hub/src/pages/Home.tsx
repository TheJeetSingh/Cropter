import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { useEffect, useRef } from "react";
import { Activity, Sprout, Scan } from "lucide-react";
import heroImage from "@/assets/hero-farm.jpg";
import myFarmImage from "@/assets/my-farm.jpg";

const Home = () => {
  const heroRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleScroll = () => {
      if (heroRef.current) {
        const scrolled = window.scrollY;
        heroRef.current.style.transform = `translateY(${scrolled * 0.5}px)`;
      }
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative h-screen flex items-center justify-center overflow-hidden">
        {/* Background Image with Parallax */}
        <div 
          ref={heroRef}
          className="absolute inset-0 w-full h-[120%]"
          style={{ willChange: 'transform' }}
        >
          <img
            src={heroImage}
            alt="Aerial view of agricultural farm"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-background/60 via-background/40 to-background" />
        </div>

        {/* Content */}
        <div className="relative z-10 container mx-auto px-6 text-center">
          <div className="max-w-5xl mx-auto space-y-10 fade-in-up">
            <h1 className="text-8xl md:text-9xl font-light tracking-tight text-foreground text-balance">
              Agriculture.
              <br />
              <span className="font-semibold bg-gradient-hero bg-clip-text text-transparent">
                Elevated.
              </span>
            </h1>
            <p className="text-[1.75rem] md:text-[2.15rem] font-semibold text-foreground max-w-4xl mx-auto leading-snug tracking-tight">
              <span className="text-primary">Monitor crop health</span>, predict yields, and identify risks with precision drone technology.
            </p>
            <div className="flex gap-4 justify-center pt-6">
              <Link to="/features">
                <Button 
                  size="lg" 
                  className="rounded-full px-10 py-7 text-lg font-semibold shadow-medium hover:shadow-large transition-all"
                >
                  Explore Features
                </Button>
              </Link>
              <Link to="/my-farm">
                <Button 
                  size="lg" 
                  variant="outline" 
                  className="rounded-full px-10 py-7 text-lg font-semibold hover:bg-secondary/50 transition-all"
                >
                  View My Farm
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* Scroll Indicator */}
        <div className="absolute bottom-12 left-1/2 -translate-x-1/2 animate-bounce">
          <div className="w-6 h-10 border-2 border-muted-foreground/30 rounded-full p-1">
            <div className="w-1.5 h-3 bg-muted-foreground/30 rounded-full mx-auto" />
          </div>
        </div>
      </section>

      {/* Features Preview */}
      <section className="py-36 px-6">
        <div className="container mx-auto max-w-6xl">
          <div className="grid md:grid-cols-3 gap-14">
            <div className="space-y-5 fade-in-up" style={{ animationDelay: '0.1s' }}>
              <div className="text-6xl font-light text-primary">01</div>
              <h3 className="text-3xl font-semibold">Real-Time Monitoring</h3>
              <p className="text-lg text-muted-foreground leading-relaxed">
                Live aerial surveillance with instant data synchronization across all your devices.
              </p>
            </div>

            <div className="space-y-5 fade-in-up" style={{ animationDelay: '0.2s' }}>
              <div className="text-6xl font-light text-primary">02</div>
              <h3 className="text-3xl font-semibold">Predictive Analytics</h3>
              <p className="text-lg text-muted-foreground leading-relaxed">
                Machine learning insights for yield optimization and resource management.
              </p>
            </div>

            <div className="space-y-5 fade-in-up" style={{ animationDelay: '0.3s' }}>
              <div className="text-6xl font-light text-primary">03</div>
              <h3 className="text-3xl font-semibold">Risk Detection</h3>
              <p className="text-lg text-muted-foreground leading-relaxed">
                Early warning systems to protect your investment and maximize harvest quality.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* My Farm Preview */}
      <section className="py-36 px-6 bg-muted/20">
        <div className="container mx-auto max-w-6xl">
          <div className="grid gap-16 lg:grid-cols-[1.05fr_1fr] items-center">
            <div className="space-y-6">
              <h3 className="text-5xl font-light tracking-tight text-foreground">
                Meet the My Farm suite.
              </h3>
              <p className="text-lg text-muted-foreground leading-relaxed">
                Deploy drones for live scans, upload ground footage for on-demand analytics, and replay historical performance — all from a single control surface.
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
              <div className="flex flex-wrap gap-4 pt-6">
                <Button
                  asChild
                  size="lg"
                  className="rounded-full bg-gradient-to-r from-primary to-emerald-500 px-10 py-7 text-lg font-semibold text-primary-foreground shadow-[0_20px_45px_rgba(34,197,94,0.28)] transition-transform hover:-translate-y-0.5"
                >
                  <Link to="/my-farm">Launch My Farm</Link>
                </Button>
                <Button
                  asChild
                  size="lg"
                  variant="outline"
                  className="rounded-full px-10 py-7 text-lg font-semibold hover:bg-secondary/50 transition-all"
                >
                  <Link to="/my-drone">Schedule drone</Link>
                </Button>
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
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-36 px-6 bg-muted/30">
        <div className="container mx-auto max-w-4xl">
          <div className="grid grid-cols-3 gap-12 text-center">
            <div className="space-y-2">
              <div className="text-7xl font-light text-primary">99.9%</div>
              <div className="text-base text-muted-foreground uppercase tracking-wider">Uptime</div>
            </div>
            <div className="space-y-2">
              <div className="text-7xl font-light text-primary">50K+</div>
              <div className="text-base text-muted-foreground uppercase tracking-wider">Acres Monitored</div>
            </div>
            <div className="space-y-2">
              <div className="text-7xl font-light text-primary">24/7</div>
              <div className="text-base text-muted-foreground uppercase tracking-wider">Support</div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;
