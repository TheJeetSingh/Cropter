import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { 
  Activity, 
  Bug, 
  Sprout, 
  AlertTriangle, 
  CheckCircle2,
  Download
} from "lucide-react";
import type { AnalysisResponse } from "@/types/analysis";
import { getVideoUrl } from "@/lib/analysisApi";

interface AnalysisResultsProps {
  results: AnalysisResponse;
  videoName: string;
}

export function AnalysisResults({ results, videoName }: AnalysisResultsProps) {
  // Debug: Log the entire results object
  console.log('=== ANALYSIS RESULTS DEBUG ===');
  console.log('Full results:', JSON.stringify(results, null, 2));
  console.log('results.results:', results.results);
  console.log('analysis:', results.results?.analysis);
  console.log('class_counts:', results.results?.class_counts);
  
  const analysis = results.results?.analysis;
  const classCount = results.results?.class_counts;

  if (!analysis || !classCount) {
    console.error('Missing data!', { analysis, classCount });
    return (
      <Card className="shadow-medium border-border/50">
        <CardHeader>
          <CardTitle>Processing Complete</CardTitle>
          <CardDescription>Video analyzed successfully</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <p className="text-muted-foreground">
              Analysis data is incomplete. Debugging info:
            </p>
            <pre className="text-xs bg-muted p-4 rounded overflow-auto max-h-96">
              {JSON.stringify(results, null, 2)}
            </pre>
          </div>
        </CardContent>
      </Card>
    );
  }

  const healthScore = analysis.health_score;
  const healthColor = healthScore >= 75 ? 'text-green-500' : healthScore >= 50 ? 'text-yellow-500' : 'text-red-500';
  const healthBg = healthScore >= 75 ? 'bg-green-500' : healthScore >= 50 ? 'bg-yellow-500' : 'bg-red-500';

  return (
    <div className="space-y-6 fade-in-up">
      {/* Header */}
      <Card className="shadow-medium border-border/50">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-3xl font-light">Analysis Complete</CardTitle>
              <CardDescription className="text-base mt-2">{videoName}</CardDescription>
            </div>
            <Badge className="bg-green-500 text-white">
              Processed in {results.processing_time?.toFixed(1)}s
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-8 md:grid-cols-2">
            {/* Health Score */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Overall Health Score</h3>
                <span className={`text-3xl font-bold ${healthColor}`}>
                  {healthScore.toFixed(1)}%
                </span>
              </div>
              <Progress value={healthScore} className={`h-3 ${healthBg}`} />
              <p className="text-sm text-muted-foreground">
                Based on {analysis.total_detections} total detections across the field
              </p>
            </div>

            {/* Quick Stats - REAL YOLO OUTPUT */}
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-lg border border-border/60 bg-muted/30 p-4">
                <div className="flex items-center gap-2 text-green-500">
                  <CheckCircle2 className="h-5 w-5" />
                  <span className="text-sm font-medium">Healthy Crops</span>
                </div>
                <p className="mt-2 text-2xl font-semibold">{analysis.healthy_crops}</p>
              </div>
              <div className="rounded-lg border border-border/60 bg-muted/30 p-4">
                <div className="flex items-center gap-2 text-red-500">
                  <AlertTriangle className="h-5 w-5" />
                  <span className="text-sm font-medium">Unhealthy Crops</span>
                </div>
                <p className="mt-2 text-2xl font-semibold">{analysis.unhealthy_crops || 0}</p>
              </div>
            </div>
          </div>

          {/* Farm Health Status Badge */}
          {analysis.farm_health_status && (
            <div className="mt-6 flex items-center gap-3">
              <span className="text-sm font-medium text-muted-foreground">Farm Health:</span>
              <Badge 
                className={`text-base px-4 py-1.5 ${
                  analysis.farm_health_status === 'EXCELLENT' ? 'bg-green-600' :
                  analysis.farm_health_status === 'GOOD' ? 'bg-green-500' :
                  analysis.farm_health_status === 'FAIR' ? 'bg-yellow-500' :
                  analysis.farm_health_status === 'POOR' ? 'bg-orange-500' :
                  'bg-red-600'
                }`}
              >
                {analysis.farm_health_status}
              </Badge>
              {analysis.yield_estimation !== undefined && (
                <>
                  <span className="text-sm font-medium text-muted-foreground ml-4">Estimated Yield:</span>
                  <Badge variant="outline" className="text-base px-4 py-1.5">
                    {analysis.yield_estimation.toFixed(1)}%
                  </Badge>
                </>
              )}
            </div>
          )}

          {/* Video Links */}
          {results.results?.output_video_path && (
            <div className="mt-6 flex gap-3">
              <Button
                asChild
                size="lg"
                className="rounded-full px-8"
              >
                <a 
                  href={results.results.output_video_path.includes('youtube') || results.results.output_video_path.includes('youtu.be') 
                    ? results.results.output_video_path 
                    : getVideoUrl(results.results.output_video_path)} 
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Download className="mr-2 h-4 w-4" />
                  {results.results.output_video_path.includes('youtube') || results.results.output_video_path.includes('youtu.be')
                    ? 'Watch Annotated Video'
                    : 'Download Annotated Video'}
                </a>
              </Button>
              {results.results?.video_path && (results.results.video_path.includes('youtube') || results.results.video_path.includes('youtu.be')) && (
                <Button
                  asChild
                  size="lg"
                  variant="outline"
                  className="rounded-full px-8"
                >
                  <a 
                    href={results.results.video_path} 
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Watch Input Video
                  </a>
                </Button>
              )}
              {results.results?.json_path && (
                <Button
                  asChild
                  size="lg"
                  variant="outline"
                  className="rounded-full px-8"
                >
                  <a 
                    href={getVideoUrl(results.results.json_path)} 
                    download
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Download Report (JSON)
                  </a>
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Embedded YouTube Video (if output is YouTube link) */}
      {results.results?.output_video_path && 
       (results.results.output_video_path.includes('youtube.com') || results.results.output_video_path.includes('youtu.be')) && (
        <Card className="shadow-medium border-border/50">
          <CardHeader>
            <CardTitle className="text-2xl font-light">Annotated Video Output</CardTitle>
            <CardDescription>YOLO detection results visualization</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="aspect-video rounded-lg overflow-hidden bg-black">
              <iframe
                width="100%"
                height="100%"
                src={`https://www.youtube.com/embed/${
                  results.results.output_video_path.includes('watch?v=')
                    ? results.results.output_video_path.split('watch?v=')[1].split('&')[0]
                    : results.results.output_video_path.split('youtu.be/')[1]?.split('?')[0] || 
                      results.results.output_video_path.split('/').pop()
                }`}
                title="Annotated Video"
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                className="w-full h-full"
              />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Detection Summary Cards - REAL YOLO OUTPUT */}
      <div className="grid gap-6 md:grid-cols-4">
        {/* Weeds Detected */}
        <Card className="shadow-medium border-border/50">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-pink-500/10 p-2">
                <Sprout className="h-5 w-5 text-pink-500" />
              </div>
              <div>
                <CardTitle>Weeds Detected</CardTitle>
                <CardDescription>
                  Infestation: <Badge variant="secondary">{analysis.weed_growth.infestation_level}</Badge>
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-pink-500">{analysis.weeds_detected || analysis.weed_growth.weeds}</p>
            {analysis.area_coverage && (
              <p className="text-sm text-muted-foreground mt-2">Coverage: {analysis.area_coverage.weed_coverage.toFixed(1)}%</p>
            )}
          </CardContent>
        </Card>

        {/* Diseases Detected */}
        <Card className="shadow-medium border-border/50">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-red-500/10 p-2">
                <AlertTriangle className="h-5 w-5 text-red-500" />
              </div>
              <div>
                <CardTitle>Diseases Detected</CardTitle>
                <CardDescription>
                  Severity: <Badge variant={analysis.crop_health_issues.severity === 'high' ? 'destructive' : 'secondary'}>
                    {analysis.crop_health_issues.severity}
                  </Badge>
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-red-500">{analysis.diseases_detected || analysis.crop_health_issues.diseased_crops}</p>
            {analysis.area_coverage && (
              <p className="text-sm text-muted-foreground mt-2">Coverage: {analysis.area_coverage.disease_coverage.toFixed(1)}%</p>
            )}
          </CardContent>
        </Card>

        {/* Crop Health Issues */}
        <Card className="shadow-medium border-border/50">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-orange-500/10 p-2">
                <Activity className="h-5 w-5 text-orange-500" />
              </div>
              <div>
                <CardTitle>Unhealthy Crops</CardTitle>
                <CardDescription>Total Issues</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-orange-500">{analysis.unhealthy_crops || 0}</p>
            {analysis.area_coverage && (
              <p className="text-sm text-muted-foreground mt-2">Bad Area: {analysis.area_coverage.bad_crop_area.toFixed(1)}%</p>
            )}
          </CardContent>
        </Card>

        {/* Pest Infestations */}
        <Card className="shadow-medium border-border/50">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-purple-500/10 p-2">
                <Bug className="h-5 w-5 text-purple-500" />
              </div>
              <div>
                <CardTitle>Pest Infestations</CardTitle>
                <CardDescription>
                  Level: <Badge variant="secondary">{analysis.pest_infestations.infestation_level}</Badge>
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Pest Presence</span>
              <span className="font-semibold text-purple-500">{analysis.pest_infestations.pest_presence}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Pest Damage</span>
              <span className="font-semibold text-red-500">{analysis.pest_infestations.pest_damage}</span>
            </div>
            <div className="flex justify-between text-sm pt-2 border-t">
              <span className="font-medium">Total Pest Issues</span>
              <span className="font-bold">{analysis.pest_infestations.total_pest_issues}</span>
            </div>
          </CardContent>
        </Card>

        {/* Weed Growth */}
        <Card className="shadow-medium border-border/50">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-green-500/10 p-2">
                <AlertTriangle className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <CardTitle>Weed Growth</CardTitle>
                <CardDescription>
                  Level: <Badge variant="secondary">{analysis.weed_growth.infestation_level}</Badge>
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Individual Weeds</span>
              <span className="font-semibold text-green-600">{analysis.weed_growth.weeds}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Weed Infestations</span>
              <span className="font-semibold text-red-500">{analysis.weed_growth.weed_infestation}</span>
            </div>
            <div className="flex justify-between text-sm pt-2 border-t">
              <span className="font-medium">Total Weeds</span>
              <span className="font-bold">{analysis.weed_growth.total_weeds}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Area Coverage Breakdown - REAL YOLO OUTPUT */}
      {analysis.area_coverage && (
        <Card className="shadow-medium border-border/50">
          <CardHeader>
            <CardTitle className="text-2xl font-light">Area Coverage Analysis</CardTitle>
            <CardDescription>Percentage distribution across the field</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-6 md:grid-cols-2">
              {/* Good Crop Area */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-muted-foreground">Good Crop Area</span>
                  <span className="text-lg font-bold text-green-600">
                    {analysis.area_coverage.good_crop_area.toFixed(2)}%
                  </span>
                </div>
                <Progress value={analysis.area_coverage.good_crop_area} className="h-2 bg-green-600" />
              </div>

              {/* Bad Crop Area */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-muted-foreground">Bad Crop Area</span>
                  <span className="text-lg font-bold text-orange-600">
                    {analysis.area_coverage.bad_crop_area.toFixed(2)}%
                  </span>
                </div>
                <Progress value={analysis.area_coverage.bad_crop_area} className="h-2 bg-orange-600" />
              </div>

              {/* Weed Coverage */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-muted-foreground">Weed Coverage</span>
                  <span className="text-lg font-bold text-pink-600">
                    {analysis.area_coverage.weed_coverage.toFixed(2)}%
                  </span>
                </div>
                <Progress value={analysis.area_coverage.weed_coverage} className="h-2 bg-pink-600" />
              </div>

              {/* Disease Coverage */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-muted-foreground">Disease Coverage</span>
                  <span className="text-lg font-bold text-red-600">
                    {analysis.area_coverage.disease_coverage.toFixed(2)}%
                  </span>
                </div>
                <Progress value={analysis.area_coverage.disease_coverage} className="h-2 bg-red-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recommendations */}
      <Card className="shadow-medium border-border/50">
        <CardHeader>
          <CardTitle className="text-2xl font-light">Recommendations</CardTitle>
          <CardDescription>Actionable insights based on REAL YOLO detections</CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="space-y-3">
            {analysis.recommendations.map((rec, index) => (
              <li key={index} className="flex items-start gap-3">
                <CheckCircle2 className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                <span className="text-base">{rec}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {/* Detection Breakdown */}
      <Card className="shadow-medium border-border/50">
        <CardHeader>
          <CardTitle className="text-2xl font-light">Detection Breakdown</CardTitle>
          <CardDescription>All classes detected in the field</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
            {Object.entries(classCount).map(([className, count]) => (
              <div 
                key={className} 
                className="flex items-center justify-between rounded-lg border border-border/60 bg-muted/30 px-4 py-3"
              >
                <span className="text-sm font-medium capitalize">
                  {className.replace(/_/g, ' ')}
                </span>
                <span className="text-lg font-semibold text-primary">{count}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

