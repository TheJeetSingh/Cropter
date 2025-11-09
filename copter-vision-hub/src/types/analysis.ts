/**
 * TypeScript Types for Agricultural YOLO Analysis
 * Based on AI Model Schema
 */

// Detection types
export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface Detection {
  bbox: [number, number, number, number]; // [x1, y1, x2, y2]
  confidence: number; // 0.0-1.0
  class_id: number; // 0-10
  class_name: string;
}

export interface FrameDetection {
  frame_number: number;
  timestamp: number; // seconds
  detections: Detection[];
}

// Location types for specific issues
export interface IssueLocation {
  type: string;
  bbox: [number, number, number, number];
  confidence: number;
}

// Analysis sub-types
export interface CropHealthIssues {
  diseased_crops: number;
  nutrient_deficiency: number;
  total_health_issues: number;
  healthy_crops: number;
  health_issue_locations: IssueLocation[];
  severity: 'low' | 'medium' | 'high';
}

export interface PestInfestations {
  pest_damage: number;
  pest_presence: number;
  total_pest_issues: number;
  pest_locations: IssueLocation[];
  infestation_level: 'none' | 'low' | 'medium' | 'high';
}

export interface WeedGrowth {
  weeds: number;
  weed_infestation: number;
  total_weeds: number;
  weed_locations: IssueLocation[];
  infestation_level: 'none' | 'low' | 'medium' | 'high';
}

// Area coverage analysis (REAL YOLO OUTPUT)
export interface AreaCoverage {
  good_crop_area: number; // percentage
  bad_crop_area: number; // percentage
  weed_coverage: number; // percentage
  disease_coverage: number; // percentage
}

// Complete analysis structure (REAL YOLO OUTPUT)
export interface Analysis {
  total_detections: number;
  healthy_crops: number;
  unhealthy_crops?: number;
  weeds_detected?: number;
  diseases_detected?: number;
  optimal_growth_areas?: number;
  health_score: number; // 0-100
  yield_estimation?: number; // percentage
  farm_health_status?: 'EXCELLENT' | 'GOOD' | 'FAIR' | 'POOR' | 'CRITICAL';
  detection_coverage?: number; // percentage of frames with detections
  area_coverage?: AreaCoverage;
  recommendations: string[];
  crop_health_issues: CropHealthIssues;
  pest_infestations: PestInfestations;
  weed_growth: WeedGrowth;
}

// Heatmap paths
export interface Heatmaps {
  all: string;
  weeds: string;
  diseases: string;
}

// Video info
export interface VideoInfo {
  fps: number;
  width: number;
  height: number;
  total_frames: number;
  processed_frames: number;
}

// Complete video analysis result
export interface VideoAnalysisResult {
  video_path: string;
  output_video_path: string;
  json_path: string;
  total_detections: number;
  class_counts: Record<string, number>;
  frame_detections: FrameDetection[];
  video_info?: VideoInfo;
}

// Complete image analysis result
export interface ImageAnalysisResult {
  detections: Detection[];
  annotated_image_path: string;
  heatmaps: Heatmaps;
  dry_soil_path: string;
  analysis: Analysis;
  report_path: string;
}

// Backend request types
export interface AnalysisOptions {
  conf_threshold?: number; // 0.0-1.0, default: 0.25
  frame_skip?: number; // Process every Nth frame, default: 1
  save_video?: boolean; // default: true
  save_json?: boolean; // default: true
  output_dir?: string; // default: "outputs"
  generate_heatmaps?: boolean; // default: false
  generate_report?: boolean; // default: true
}

export interface AnalysisMetadata {
  upload_timestamp?: string;
  user_id?: string;
  session_id?: string;
  video_name?: string;
  description?: string;
  location?: string;
  crop_type?: string;
}

export interface AnalysisRequest {
  request_type: 'video_analysis' | 'image_analysis';
  video_path?: string;
  image_path?: string;
  options?: AnalysisOptions;
  metadata?: AnalysisMetadata;
}

// Backend response types
export interface AnalysisResponse {
  status: 'success' | 'processing' | 'error';
  request_id?: string;
  processing_time?: number; // seconds
  results?: VideoAnalysisResult & { analysis?: Analysis };
  error_code?: string;
  error_message?: string;
  timestamp?: string;
}

// Frontend upload state
export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

export interface AnalysisState {
  isUploading: boolean;
  isAnalyzing: boolean;
  uploadProgress: UploadProgress | null;
  results: AnalysisResponse | null;
  error: string | null;
}

// Class names constants
export const CLASS_NAMES = [
  'healthy_crop',
  'diseased_crop',
  'nutrient_deficiency',
  'pest_damage',
  'pest_presence',
  'weed',
  'weed_infestation',
  'dry_crop',
  'dry_soil',
  'overwatered',
  'optimal_growth',
] as const;

export type ClassName = typeof CLASS_NAMES[number];

