"""
Cropter Flight Path Generator - IMPROVED
Generates optimal coverage paths for Tello drone with realistic constraints
"""

import math
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

try:
    from shapely.geometry import Polygon, Point, LineString, MultiLineString
    from shapely.ops import unary_union
    SHAPELY_AVAILABLE = True
except ImportError:
    print("⚠️  Shapely not installed. Install with: pip install shapely")
    SHAPELY_AVAILABLE = False


@dataclass
class TelloSpecs:
    """Tello drone specifications and constraints"""
    # Camera specs
    CAMERA_FOV_H = 82.6  # degrees (horizontal)
    CAMERA_FOV_V = 51.0  # degrees (vertical)
    
    # Flight limits (REALISTIC for Tello)
    MAX_ALTITUDE_M = 3.0  # Safe max over crops (10m absolute max)
    MIN_ALTITUDE_M = 0.5  # Minimum safe altitude
    MAX_SPEED_MS = 2.0  # Conservative speed (8 m/s max)
    MAX_RANGE_M = 80  # WiFi range limit (100m theoretical)
    
    # Battery constraints
    BATTERY_LIFE_MIN = 30  # minutes max flight time
    BATTERY_BUFFER_PCT = 0.20  # 20% reserve for landing
    USABLE_FLIGHT_TIME_SEC = int(BATTERY_LIFE_MIN * 60 * (1 - BATTERY_BUFFER_PCT))  # ~1440s
    
    # Movement limits
    MAX_MOVE_CM = 500  # Max single movement command
    MIN_MOVE_CM = 20  # Minimum reliable movement
    
    # Positioning accuracy (Tello uses vision, not GPS!)
    POSITION_DRIFT_CM = 50  # Expected cumulative drift


class FlightPathGenerator:
    """Generate realistic flight paths for Tello drone"""
    
    def __init__(self):
        self.specs = TelloSpecs()
    
    def calculate_camera_footprint(self, altitude_m: float) -> Tuple[float, float]:
        """
        Calculate camera ground coverage at given altitude
        
        Returns:
            (width_m, height_m) - footprint dimensions in meters
        """
        fov_h_rad = math.radians(self.specs.CAMERA_FOV_H)
        fov_v_rad = math.radians(self.specs.CAMERA_FOV_V)
        
        width_m = 2 * altitude_m * math.tan(fov_h_rad / 2)
        height_m = 2 * altitude_m * math.tan(fov_v_rad / 2)
        
        return width_m, height_m
    
    def _route_around_obstacle(self, 
                               start_x: float, start_y: float,
                               end_x: float, end_y: float,
                               obstacles, altitude_m: float) -> List[Dict]:
        """
        Generate waypoints to route around obstacles from start to end point
        
        Returns list of intermediate waypoints (does not include start/end)
        """
        if obstacles is None:
            return []
        
        routing_waypoints = []
        
        try:
            # Get obstacle bounds
            obs_minx, obs_miny, obs_maxx, obs_maxy = obstacles.bounds
            
            # Calculate routing points (corners of obstacle bounding box + buffer)
            buffer = 0.5  # 0.5m buffer
            
            # Four possible routing points around the obstacle
            top_left = (obs_minx - buffer, obs_maxy + buffer)
            top_right = (obs_maxx + buffer, obs_maxy + buffer)
            bottom_left = (obs_minx - buffer, obs_miny - buffer)
            bottom_right = (obs_maxx + buffer, obs_miny - buffer)
            
            # Test 4 possible routes and pick the shortest safe one
            routes = [
                [top_left, top_right],      # Route over the top
                [bottom_left, bottom_right], # Route under the bottom
                [top_left, bottom_left],     # Route around left side
                [top_right, bottom_right],   # Route around right side
            ]
            
            best_route = None
            min_distance = float('inf')
            
            for route in routes:
                # Build complete path with this route
                path_coords = [(start_x, start_y)] + route + [(end_x, end_y)]
                test_line = LineString(path_coords)
                
                # Check if this route is safe (doesn't intersect obstacle)
                if not obstacles.intersects(test_line):
                    # Calculate total distance
                    total_dist = 0
                    for i in range(len(path_coords) - 1):
                        dx = path_coords[i+1][0] - path_coords[i][0]
                        dy = path_coords[i+1][1] - path_coords[i][1]
                        total_dist += math.sqrt(dx*dx + dy*dy)
                    
                    if total_dist < min_distance:
                        min_distance = total_dist
                        best_route = route
            
            # Use the best route found
            if best_route:
                for x, y in best_route:
                    routing_waypoints.append({
                        'x': int(x * 100),
                        'y': int(y * 100),
                        'z': int(altitude_m * 100)
                    })
            else:
                # Fallback: use boundary points if no simple route works
                print(f"⚠️  Complex obstacle - using boundary routing")
                
                if obstacles.geom_type == 'Polygon':
                    boundary_coords = list(obstacles.exterior.coords)
                elif obstacles.geom_type == 'MultiPolygon':
                    boundary_coords = list(list(obstacles.geoms)[0].exterior.coords)
                else:
                    return []
                
                # Find closest boundary points
                closest_to_start = min(boundary_coords, 
                                      key=lambda p: (p[0]-start_x)**2 + (p[1]-start_y)**2)
                closest_to_end = min(boundary_coords,
                                    key=lambda p: (p[0]-end_x)**2 + (p[1]-end_y)**2)
                
                routing_waypoints.append({
                    'x': int(closest_to_start[0] * 100),
                    'y': int(closest_to_start[1] * 100),
                    'z': int(altitude_m * 100)
                })
                
                if closest_to_start != closest_to_end:
                    routing_waypoints.append({
                        'x': int(closest_to_end[0] * 100),
                        'y': int(closest_to_end[1] * 100),
                        'z': int(altitude_m * 100)
                    })
                    
        except Exception as e:
            print(f"⚠️  Routing error: {e}")
            return []
        
        return routing_waypoints
    
    def estimate_coverage_area(self, altitude_m: float, overlap_pct: float = 0.3) -> float:
        """
        Estimate how much area can be covered in one battery cycle
        
        Returns:
            area_sqm - maximum coverage area in square meters
        """
        footprint_w, footprint_h = self.calculate_camera_footprint(altitude_m)
        effective_width = footprint_w * (1 - overlap_pct)
        
        # Account for: takeoff (3s), landing (3s), hover time (1s per waypoint)
        # Average speed 2 m/s
        overhead_sec = 6  # takeoff + landing
        usable_time = self.specs.USABLE_FLIGHT_TIME_SEC - overhead_sec
        
        # Assume 1s hover per waypoint, estimate ~40 waypoints per mission
        hover_time = 40
        flight_time = usable_time - hover_time
        
        # Distance covered
        total_distance = flight_time * self.specs.MAX_SPEED_MS
        
        # Coverage area (distance * effective width)
        coverage_area = total_distance * effective_width
        
        return coverage_area
    
    def load_field_config(self, config_path: str) -> Dict:
        """
        Load field configuration from text file
        
        Expected format:
        {
            "field_id": "uuid",
            "name": "North Field",
            "boundary": [[x1, y1], [x2, y2], ...],  # in meters
            "obstacles": [
                {"type": "tree", "boundary": [[x, y], ...]},
                {"type": "building", "boundary": [[x, y], ...]}
            ],
            "no_fly_zones": [[[x, y], ...], ...],
            "reference_point": {"lat": 0, "lon": 0}  # for satellite sync
        }
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            print(f"✓ Loaded field config: {config.get('name', 'Unknown')}")
            return config
        except Exception as e:
            print(f"✗ Failed to load field config: {e}")
            return None
    
    def validate_field_size(self, boundary: List[Tuple[float, float]], 
                           altitude_m: float, overlap_pct: float) -> Dict:
        """
        Check if field is too large for Tello to cover
        
        Returns dict with validation results and warnings
        """
        if not SHAPELY_AVAILABLE:
            return {"valid": False, "error": "Shapely library required"}
        
        polygon = Polygon(boundary)
        field_area_sqm = polygon.area
        
        # Check if within WiFi range
        centroid = polygon.centroid
        max_distance_from_center = 0
        for x, y in boundary:
            dist = math.sqrt((x - centroid.x)**2 + (y - centroid.y)**2)
            max_distance_from_center = max(max_distance_from_center, dist)
        
        warnings = []
        
        if max_distance_from_center > self.specs.MAX_RANGE_M:
            warnings.append(f"Field extends {max_distance_from_center:.1f}m from center (WiFi limit: {self.specs.MAX_RANGE_M}m)")
        
        # Check if coverageable in one flight
        max_coverage = self.estimate_coverage_area(altitude_m, overlap_pct)
        
        if field_area_sqm > max_coverage:
            flights_needed = math.ceil(field_area_sqm / max_coverage)
            warnings.append(f"Field requires ~{flights_needed} battery cycles (area: {field_area_sqm:.0f}m², max per flight: {max_coverage:.0f}m²)")
        
        return {
            "valid": len(warnings) == 0,
            "field_area_sqm": field_area_sqm,
            "max_coverage_per_flight": max_coverage,
            "max_distance_from_center": max_distance_from_center,
            "warnings": warnings
        }
    
    def generate_grid_pattern(self, 
                             field_config: Dict,
                             altitude_m: float = 2.0,
                             overlap_pct: float = 0.3,
                             optimize_for_battery: bool = True) -> Dict:
        """
        Generate lawnmower grid pattern with Tello constraints
        
        Args:
            field_config: Field configuration dict
            altitude_m: Flight altitude (default 2m for crop detail)
            overlap_pct: Image overlap 0-1 (0.3 = 30%)
            optimize_for_battery: Limit waypoints to fit in one battery cycle
        
        Returns:
            Mission dict with waypoints and metadata
        """
        
        if not SHAPELY_AVAILABLE:
            return {"success": False, "error": "Shapely library required"}
        
        boundary = field_config.get('boundary', [])
        if not boundary:
            return {"success": False, "error": "No field boundary defined"}
        
        # Validate field
        validation = self.validate_field_size(boundary, altitude_m, overlap_pct)
        if validation['warnings']:
            print("\n⚠️  WARNINGS:")
            for warning in validation['warnings']:
                print(f"   • {warning}")
        
        # Create polygons
        farm_polygon = Polygon(boundary)
        
        # Process obstacles and no-fly zones
        obstacle_polygons = []
        obstacles = field_config.get('obstacles', [])
        no_fly_zones = field_config.get('no_fly_zones', [])
        
        for obs in obstacles:
            obs_boundary = obs.get('boundary', [])
            if obs_boundary:
                obstacle_polygons.append(Polygon(obs_boundary))
        
        for nfz in no_fly_zones:
            nfz_boundary = nfz.get('boundary', [])
            if nfz_boundary:
                obstacle_polygons.append(Polygon(nfz_boundary))
        
        # Calculate safe flight zone
        safe_zone = farm_polygon
        if obstacle_polygons:
            obstacles_union = unary_union(obstacle_polygons)
            # Add 2m buffer around obstacles for safety
            obstacles_buffered = obstacles_union.buffer(2.0)
            safe_zone = farm_polygon.difference(obstacles_buffered)
        
        # Calculate grid spacing
        footprint_w, footprint_h = self.calculate_camera_footprint(altitude_m)
        grid_spacing = footprint_w * (1 - overlap_pct)
        
        print(f"\n📐 Grid Parameters:")
        print(f"   Altitude: {altitude_m}m")
        print(f"   Camera footprint: {footprint_w:.2f}m x {footprint_h:.2f}m")
        print(f"   Grid spacing: {grid_spacing:.2f}m (overlap: {overlap_pct*100:.0f}%)")
        
        # Generate waypoints - simple grid first, then route around obstacles
        minx, miny, maxx, maxy = safe_zone.bounds
        raw_waypoints = []
        
        num_rows = int((maxy - miny) / grid_spacing) + 1
        
        for i in range(num_rows):
            y = miny + (i * grid_spacing)
            
            # Lawnmower pattern (alternate direction)
            if i % 2 == 0:
                start_x, end_x = minx, maxx
            else:
                start_x, end_x = maxx, minx
            
            line = LineString([(start_x, y), (end_x, y)])
            
            if safe_zone.intersects(line):
                clipped = safe_zone.intersection(line)
                
                # Handle line segments
                segments = []
                if clipped.geom_type == 'LineString':
                    segments = [clipped]
                elif clipped.geom_type == 'MultiLineString':
                    segments = list(clipped.geoms)
                
                # Sort segments based on direction
                if i % 2 == 0:
                    segments.sort(key=lambda seg: seg.coords[0][0])
                else:
                    segments.sort(key=lambda seg: -seg.coords[0][0])
                
                for segment in segments:
                    coords = list(segment.coords)
                    for x, y_coord in coords:
                        raw_waypoints.append({
                            'x': x,
                            'y': y_coord,
                            'z': altitude_m
                        })
        
        # Now route around obstacles between ALL consecutive waypoints
        waypoints = []
        buffered_obstacles_list = [poly.buffer(2.0) for poly in obstacle_polygons] if obstacle_polygons else []
        
        for i, wp in enumerate(raw_waypoints):
            # Add current waypoint
            waypoints.append({
                'x': int(wp['x'] * 100),
                'y': int(wp['y'] * 100),
                'z': int(wp['z'] * 100)
            })
            
            # Check if line to NEXT waypoint intersects obstacle
            if i < len(raw_waypoints) - 1:
                next_wp = raw_waypoints[i + 1]
                
                if buffered_obstacles_list:
                    line_to_next = LineString([(wp['x'], wp['y']), (next_wp['x'], next_wp['y'])])
                    
                    # Collect only the obstacles that block this line
                    blocking = [obs for obs in buffered_obstacles_list if obs.intersects(line_to_next)]
                    if blocking:
                        local_blockers = unary_union(blocking)
                        # Need to route around just these blockers
                        routing_wps = self._route_around_obstacle(
                            wp['x'], wp['y'],
                            next_wp['x'], next_wp['y'],
                            local_blockers,
                            altitude_m
                        )
                        waypoints.extend(routing_wps)
        
        # Optimize waypoint order (remove near-duplicates)
        waypoints = self.remove_duplicate_waypoints(waypoints, threshold_cm=30)
        
        # Limit waypoints if needed for battery
        if optimize_for_battery:
            max_waypoints = self.calculate_max_waypoints()
            if len(waypoints) > max_waypoints:
                print(f"\n⚠️  Limiting waypoints to {max_waypoints} (battery constraint)")
                print(f"   Original: {len(waypoints)} waypoints")
                waypoints = self.subsample_waypoints(waypoints, max_waypoints)
                print(f"   Reduced: {len(waypoints)} waypoints")
        
        # Calculate mission metadata
        metadata = self.calculate_mission_metadata(waypoints, altitude_m)
        
        # Check if mission is safe
        if metadata['battery_pct'] > 100:
            print(f"\n❌ MISSION IMPOSSIBLE: Requires {metadata['battery_pct']}% battery ({metadata['batteries_needed']} batteries)")
            print(f"   Duration: {metadata['duration_sec']//60}min {metadata['duration_sec']%60}s")
            print(f"   Tello max: ~30 minutes per battery")
            print(f"   REDUCE obstacles or field size!")
        elif metadata['battery_pct'] > 80:
            print(f"\n⚠️  WARNING: Estimated battery usage is {metadata['battery_pct']}%")
            print(f"   Consider reducing complexity")
        
        return {
            'success': True,
            'mission_id': None,  # Set by backend
            'field_id': field_config.get('field_id'),
            'field_name': field_config.get('name'),
            'waypoints': waypoints,
            'pattern': 'grid',
            'altitude': int(altitude_m * 100),  # cm
            'overlap_pct': overlap_pct,
            'total_waypoints': len(waypoints),
            'estimated_duration_sec': metadata['duration_sec'],
            'estimated_battery_pct': metadata['battery_pct'],
            'batteries_needed': metadata['batteries_needed'],
            'total_distance_m': metadata['distance_m'],
            'coverage_area_sqm': safe_zone.area,
            'validation': validation,
            'is_feasible': metadata['battery_pct'] <= 100
        }
    
    def generate_adaptive_pattern(self,
                                 field_config: Dict,
                                 altitude_m: float = 2.0,
                                 overlap_pct: float = 0.3) -> Dict:
        """
        Generate adaptive pattern that splits large fields into battery-sized chunks
        """
        
        if not SHAPELY_AVAILABLE:
            return {"success": False, "error": "Shapely library required"}
        
        boundary = field_config.get('boundary', [])
        farm_polygon = Polygon(boundary)
        
        # Calculate max coverage per flight
        max_coverage = self.estimate_coverage_area(altitude_m, overlap_pct)
        field_area = farm_polygon.area
        
        if field_area <= max_coverage:
            # Single flight is enough
            return self.generate_grid_pattern(field_config, altitude_m, overlap_pct)
        
        # Need multiple flights - split field into sections
        num_sections = math.ceil(field_area / max_coverage)
        
        print(f"\n📊 Field requires {num_sections} flights")
        print(f"   Field area: {field_area:.0f}m²")
        print(f"   Max per flight: {max_coverage:.0f}m²")
        
        # Split field into vertical strips
        minx, miny, maxx, maxy = farm_polygon.bounds
        strip_width = (maxx - minx) / num_sections
        
        missions = []
        
        for i in range(num_sections):
            strip_minx = minx + (i * strip_width)
            strip_maxx = minx + ((i + 1) * strip_width)
            
            # Create strip polygon
            strip = Polygon([
                (strip_minx, miny),
                (strip_maxx, miny),
                (strip_maxx, maxy),
                (strip_minx, maxy)
            ])
            
            # Intersect with farm
            strip_area = farm_polygon.intersection(strip)
            
            if strip_area.area < 1:  # Skip tiny sections
                continue
            
            # Create sub-config for this strip
            strip_boundary = list(strip_area.exterior.coords)
            
            strip_config = {
                **field_config,
                'boundary': strip_boundary,
                'name': f"{field_config.get('name', 'Field')} - Section {i+1}"
            }
            
            # Generate mission for this strip
            mission = self.generate_grid_pattern(strip_config, altitude_m, overlap_pct)
            if mission['success']:
                missions.append(mission)
        
        return {
            'success': True,
            'type': 'multi_flight',
            'num_flights': len(missions),
            'missions': missions,
            'field_id': field_config.get('field_id'),
            'field_name': field_config.get('name'),
            'total_area_sqm': field_area
        }
    
    def remove_duplicate_waypoints(self, waypoints: List[Dict], 
                                   threshold_cm: int = 30) -> List[Dict]:
        """Remove waypoints that are too close together"""
        if not waypoints:
            return []
        
        filtered = [waypoints[0]]
        
        for wp in waypoints[1:]:
            last_wp = filtered[-1]
            dist = math.sqrt(
                (wp['x'] - last_wp['x'])**2 +
                (wp['y'] - last_wp['y'])**2
            )
            
            if dist >= threshold_cm:
                filtered.append(wp)
        
        return filtered
    
    def subsample_waypoints(self, waypoints: List[Dict], 
                           max_waypoints: int) -> List[Dict]:
        """Reduce waypoints while maintaining coverage"""
        if len(waypoints) <= max_waypoints:
            return waypoints
        
        # Keep first and last, subsample middle
        step = len(waypoints) / max_waypoints
        indices = [0] + [int(i * step) for i in range(1, max_waypoints-1)] + [len(waypoints)-1]
        
        return [waypoints[i] for i in indices]
    
    def calculate_max_waypoints(self) -> int:
        """Calculate maximum waypoints that fit in one battery cycle"""
        # Conservative estimate: 2 seconds per waypoint (movement + hover)
        time_per_waypoint = 2
        overhead = 10  # takeoff + landing + buffer
        
        max_waypoints = (self.specs.USABLE_FLIGHT_TIME_SEC - overhead) // time_per_waypoint
        
        return int(max_waypoints * 0.9)  # 10% safety margin
    
    def calculate_mission_metadata(self, waypoints: List[Dict], 
                                   altitude_m: float) -> Dict:
        """Calculate mission duration, battery, distance"""
        
        if len(waypoints) < 2:
            return {
                'duration_sec': 0,
                'battery_pct': 0,
                'distance_m': 0
            }
        
        # Calculate 3D distance
        total_distance_cm = 0
        for i in range(len(waypoints) - 1):
            wp1, wp2 = waypoints[i], waypoints[i+1]
            dist = math.sqrt(
                (wp2['x'] - wp1['x'])**2 +
                (wp2['y'] - wp1['y'])**2 +
                (wp2['z'] - wp1['z'])**2
            )
            total_distance_cm += dist
        
        total_distance_m = total_distance_cm / 100
        
        # Estimate time (conservative 2 m/s average)
        flight_time_sec = total_distance_m / 2.0
        hover_time_sec = len(waypoints) * 1  # 1s hover per waypoint
        takeoff_landing_sec = 6
        
        total_time_sec = flight_time_sec + hover_time_sec + takeoff_landing_sec
        
        # Battery estimate: what % of usable flight time does this use?
        # USABLE_FLIGHT_TIME_SEC = 624s (80% of total after 20% reserve)
        battery_pct = (total_time_sec / self.specs.USABLE_FLIGHT_TIME_SEC) * 100
        
        # Calculate how many batteries needed
        batteries_needed = math.ceil(battery_pct / 100)
        
        return {
            'duration_sec': int(total_time_sec),
            'battery_pct': int(battery_pct),
            'batteries_needed': batteries_needed,
            'distance_m': round(total_distance_m, 2)
        }
    
    def save_flight_plan(self, flight_plan: Dict, filename: str):
        """Save flight plan to JSON file"""
        output_path = Path(filename)
        with open(output_path, 'w') as f:
            json.dump(flight_plan, f, indent=2)
        print(f"✓ Flight plan saved: {output_path}")
        return str(output_path)


# CLI tool for testing
if __name__ == "__main__":
    import sys
    
    generator = FlightPathGenerator()
    
    print("\n" + "="*60)
    print("           CROPTER FLIGHT PATH GENERATOR v2.0")
    print("="*60)
    
    # Example: Small backyard field (realistic for Tello)
    example_field = {
        "field_id": "test_001",
        "name": "Backyard Garden",
        "boundary": [
            (0, 0), (20, 0), (20, 15), (0, 15), (0, 0)
        ],  # 20m x 15m = 300 sqm
        "obstacles": [
            {
                "type": "tree",
                "boundary": [(5, 5), (7, 5), (7, 7), (5, 7), (5, 5)]
            }
        ],
        "no_fly_zones": []
    }
    
    print(f"\n📍 Field: {example_field['name']}")
    print(f"   Dimensions: ~20m x 15m")
    print(f"   Obstacles: 1 tree")
    
    # Generate flight plan
    print("\n🔷 Generating grid pattern...")
    mission = generator.generate_grid_pattern(
        field_config=example_field,
        altitude_m=2.0,
        overlap_pct=0.3
    )
    
    if mission['success']:
        print(f"\n✅ Flight plan generated:")
        print(f"   Waypoints: {mission['total_waypoints']}")
        print(f"   Distance: {mission['total_distance_m']}m")
        print(f"   Est. duration: {mission['estimated_duration_sec']}s ({mission['estimated_duration_sec']//60}min {mission['estimated_duration_sec']%60}s)")
        print(f"   Est. battery: ~{mission['estimated_battery_pct']}%")
        print(f"   Coverage: {mission['coverage_area_sqm']:.0f}m²")
        
        # Save to file
        output_file = Path.home() / "Desktop" / "test_flight_plan.json"
        generator.save_flight_plan(mission, str(output_file))
        
        print(f"\n💡 To execute: Load this JSON and send via WebSocket")
    else:
        print(f"\n✗ Failed: {mission.get('error')}")