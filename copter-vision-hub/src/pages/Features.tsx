import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useEffect, useRef } from "react";
import cropsImage from "@/assets/crops-detail.jpg";

const Features = () => {
  const cardsRef = useRef<HTMLDivElement[]>([]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("feature-card-visible", "fade-in-up");
            entry.target.classList.remove("feature-card-hidden");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.2 }
    );

    cardsRef.current.forEach((card) => observer.observe(card));

    return () => observer.disconnect();
  }, []);

  return (
    <div className="min-h-screen pt-32 pb-20 px-6">
      <div className="container mx-auto max-w-5xl">
        <div className="text-center mb-20 space-y-4">
          <h1 className="text-6xl font-light tracking-tight text-foreground">
            Advanced <span className="font-semibold bg-gradient-hero bg-clip-text text-transparent">Features</span>
          </h1>
          <p className="text-xl font-light text-muted-foreground max-w-2xl mx-auto">
            Intelligent systems designed for modern agriculture
          </p>
        </div>

        <div className="space-y-12">
          {/* Plant Health Detection */}
          <Card
            ref={(el) => {
              if (el) cardsRef.current[0] = el;
            }}
            className="feature-card-hidden shadow-medium hover:shadow-large transition-all duration-300 border-border/50 overflow-hidden"
          >
            <div className="grid md:grid-cols-2 gap-0">
              <div className="relative h-64 md:h-auto overflow-hidden">
                <img
                  src={cropsImage}
                  alt="Close-up of healthy crops"
                  className="w-full h-full object-cover"
                />
              </div>
              <div>
                <CardHeader>
                  <CardTitle className="text-3xl font-light mb-2">Plant Health Detection</CardTitle>
                  <CardDescription className="text-base">
                    AI-powered multispectral analysis for crop optimization
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Overall Health Score</span>
                      <Badge className="bg-primary text-primary-foreground">Excellent</Badge>
                    </div>
                    <Progress value={87} className="h-1.5" />
                    <p className="text-sm text-muted-foreground">
                      87% optimal health indicators across monitored zones
                    </p>
                  </div>
                  
                  <div className="space-y-3 pt-4 border-t border-border">
                    <div className="flex items-center justify-between text-sm">
                      <span>Chlorophyll Levels</span>
                      <span className="font-medium text-primary">Optimal</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Water Stress</span>
                      <span className="font-medium text-primary">Low</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Pest Pressure</span>
                      <span className="font-medium text-destructive">Zone B Alert</span>
                    </div>
                  </div>

                  <div className="bg-muted/50 rounded-lg p-4 text-sm">
                    <div className="text-muted-foreground">
                      Last scan: 2 hours ago • 45 acres • 5cm/pixel resolution
                    </div>
                  </div>
                </CardContent>
              </div>
            </div>
          </Card>

          {/* Estimated Yield */}
          <Card
            ref={(el) => {
              if (el) cardsRef.current[1] = el;
            }}
            className="feature-card-hidden shadow-medium hover:shadow-large transition-all duration-300 border-border/50"
          >
            <CardHeader>
              <CardTitle className="text-3xl font-light mb-2">Estimated Yield</CardTitle>
              <CardDescription className="text-base">
                Predictive analytics for harvest planning
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-8">
              <div className="grid md:grid-cols-3 gap-6">
                <div className="space-y-2">
                  <div className="text-sm text-muted-foreground">Current Season</div>
                  <div className="text-5xl font-light text-primary">24.5</div>
                  <div className="text-xs text-muted-foreground uppercase tracking-wider">
                    tons per hectare
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="text-sm text-muted-foreground">Projected Increase</div>
                  <div className="text-5xl font-light text-primary">+12%</div>
                  <div className="text-xs text-muted-foreground uppercase tracking-wider">
                    vs. last season
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="text-sm text-muted-foreground">Harvest Window</div>
                  <div className="text-5xl font-light">Aug 15</div>
                  <div className="text-xs text-muted-foreground uppercase tracking-wider">
                    ±3 days
                  </div>
                </div>
              </div>

              <div className="space-y-4 pt-4 border-t border-border">
                <div className="text-sm font-medium">Yield Factors</div>
                <div className="space-y-3">
                  <div>
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span>Weather Conditions</span>
                      <span className="text-muted-foreground">95%</span>
                    </div>
                    <Progress value={95} className="h-1" />
                  </div>
                  <div>
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span>Soil Nutrients</span>
                      <span className="text-muted-foreground">82%</span>
                    </div>
                    <Progress value={82} className="h-1" />
                  </div>
                  <div>
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span>Detection Accuracy</span>
                      <span className="text-muted-foreground">94%</span>
                    </div>
                    <Progress value={94} className="h-1" />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Danger Areas */}
          <Card
            ref={(el) => {
              if (el) cardsRef.current[2] = el;
            }}
            className="feature-card-hidden shadow-medium hover:shadow-large transition-all duration-300 border-border/50"
          >
            <CardHeader>
              <CardTitle className="text-3xl font-light mb-2">Risk Detection</CardTitle>
              <CardDescription className="text-base">
                Early warning system for potential threats
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="p-6 bg-destructive/5 rounded-lg border-l-4 border-destructive">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="font-medium">Pest Infestation Risk</div>
                      <Badge variant="destructive">High Priority</Badge>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Elevated aphid activity detected in Zone B. Immediate intervention recommended within 48 hours.
                    </div>
                  </div>
                </div>

                <div className="p-6 bg-yellow-500/5 rounded-lg border-l-4 border-yellow-500">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="font-medium">Pest Alert</div>
                      <Badge variant="outline" className="border-yellow-500/50 text-yellow-700">
                        Medium Priority
                      </Badge>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Uneven water distribution in Sector 3. System diagnostics recommended.
                    </div>
                  </div>
                </div>

                <div className="p-6 bg-blue-500/5 rounded-lg border-l-4 border-blue-500">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="font-medium">Weather Advisory</div>
                      <Badge variant="outline" className="border-blue-500/50 text-blue-700">
                        Low Priority
                      </Badge>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Heavy precipitation forecasted. Consider harvest schedule adjustment.
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-muted/50 rounded-lg p-4 text-sm mt-6">
                <div className="text-muted-foreground">
                  All systems operational • Last threat scan: 15 minutes ago
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Features;
