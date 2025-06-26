#!/usr/bin/env python3
"""
Smart label placement version with thin crosshairs and labels completely outside boxes.
Includes improved prompts and detection analysis.
"""
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from PIL import Image, ImageDraw, ImageFont
import json
import time
import math
from typing import List, Tuple, Dict, Optional, Set
sys.path.append('/home/ubuntu/browser_automation')
from clients.gemini_detector import GeminiDetector

# Configuration
GEMINI_API_KEY = "AIzaSyDltBed5hYSZMfL2fsRcD2mXrwsiPaU7oA"
SOURCE_IMAGE = "/home/ubuntu/browser_automation/screenshots/element_search.png"
OUTPUT_DIR = Path("/home/ubuntu/browser_automation/screenshots")
CROSSHAIR_SIZE = 30  # Smaller than before
LABEL_DISTANCE = 60  # Distance from element to label
LABEL_RADIUS = 20   # Radius for circular labels

# Color palette - each element gets a unique color
COLORS = [
    '#FF0000',  # Red
    '#00FF00',  # Green
    '#0000FF',  # Blue
    '#FFFF00',  # Yellow
    '#FF00FF',  # Magenta
    '#00FFFF',  # Cyan
    '#FFA500',  # Orange
    '#800080',  # Purple
    '#FFC0CB',  # Pink
    '#A52A2A',  # Brown
    '#008080',  # Teal
    '#000080',  # Navy
    '#808000',  # Olive
    '#800000',  # Maroon
    '#C0C0C0',  # Silver
]

class SmartLabelPlacer:
    """Smart algorithm for placing labels outside bounding boxes without overlap"""
    
    def __init__(self, image_width: int, image_height: int):
        self.width = image_width
        self.height = image_height
        self.placed_labels = []  # Track placed label positions
        
    def find_label_position(self, bbox: Tuple[float, float, float, float], 
                          all_bboxes: List[Tuple[float, float, float, float]], 
                          label_idx: int) -> Tuple[float, float]:
        """Find optimal position for a label outside the bounding box"""
        x1, y1, x2, y2 = bbox
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        
        # Try positions in a circle around the element
        angles = [0, 45, 90, 135, 180, 225, 270, 315]  # 8 directions
        best_position = None
        best_score = float('-inf')
        
        for angle in angles:
            # Calculate candidate position
            rad = math.radians(angle)
            label_x = center_x + LABEL_DISTANCE * math.cos(rad)
            label_y = center_y + LABEL_DISTANCE * math.sin(rad)
            
            # Ensure label is within image bounds
            label_x = max(LABEL_RADIUS, min(self.width - LABEL_RADIUS, label_x))
            label_y = max(LABEL_RADIUS, min(self.height - LABEL_RADIUS, label_y))
            
            # Score this position
            score = self._score_position(label_x, label_y, bbox, all_bboxes)
            
            if score > best_score:
                best_score = score
                best_position = (label_x, label_y)
        
        # If no good position found, use force-directed approach
        if best_score < 0:
            best_position = self._force_directed_position(center_x, center_y, bbox, all_bboxes)
        
        self.placed_labels.append(best_position)
        return best_position
    
    def _score_position(self, x: float, y: float, current_bbox: Tuple, all_bboxes: List[Tuple]) -> float:
        """Score a label position based on overlap and distance from elements"""
        score = 0
        
        # Check overlap with all bounding boxes
        for bbox in all_bboxes:
            x1, y1, x2, y2 = bbox
            # Check if label circle overlaps with bbox
            if self._circle_rect_overlap(x, y, LABEL_RADIUS, x1, y1, x2, y2):
                score -= 100  # Heavy penalty for overlapping with boxes
        
        # Check overlap with already placed labels
        for lx, ly in self.placed_labels:
            dist = math.sqrt((x - lx)**2 + (y - ly)**2)
            if dist < LABEL_RADIUS * 2:
                score -= 50  # Penalty for overlapping with other labels
        
        # Prefer positions that maintain connection line visibility
        cx = (current_bbox[0] + current_bbox[2]) / 2
        cy = (current_bbox[1] + current_bbox[3]) / 2
        
        # Check if connection line would cross other boxes
        for bbox in all_bboxes:
            if bbox != current_bbox:
                if self._line_rect_intersect(cx, cy, x, y, bbox):
                    score -= 20
        
        # Slight preference for corners and edges
        edge_dist = min(x, y, self.width - x, self.height - y)
        score += edge_dist / 100
        
        return score
    
    def _circle_rect_overlap(self, cx: float, cy: float, r: float, 
                           x1: float, y1: float, x2: float, y2: float) -> bool:
        """Check if circle overlaps with rectangle"""
        # Find closest point on rectangle to circle center
        closest_x = max(x1, min(cx, x2))
        closest_y = max(y1, min(cy, y2))
        
        # Check distance
        dist = math.sqrt((cx - closest_x)**2 + (cy - closest_y)**2)
        return dist < r
    
    def _line_rect_intersect(self, x1: float, y1: float, x2: float, y2: float,
                           bbox: Tuple[float, float, float, float]) -> bool:
        """Check if line intersects with rectangle"""
        rx1, ry1, rx2, ry2 = bbox
        
        # Simple approximation: check if line endpoints are on opposite sides
        def sign(px, py, lx1, ly1, lx2, ly2):
            return (px - lx2) * (ly1 - ly2) - (lx1 - lx2) * (py - ly2)
        
        # Check each edge of the rectangle
        edges = [
            (rx1, ry1, rx2, ry1),  # Top
            (rx2, ry1, rx2, ry2),  # Right
            (rx2, ry2, rx1, ry2),  # Bottom
            (rx1, ry2, rx1, ry1),  # Left
        ]
        
        for ex1, ey1, ex2, ey2 in edges:
            # Check if lines intersect
            d1 = sign(ex1, ey1, x1, y1, x2, y2)
            d2 = sign(ex2, ey2, x1, y1, x2, y2)
            d3 = sign(x1, y1, ex1, ey1, ex2, ey2)
            d4 = sign(x2, y2, ex1, ey1, ex2, ey2)
            
            if d1 * d2 < 0 and d3 * d4 < 0:
                return True
        
        return False
    
    def _force_directed_position(self, cx: float, cy: float, current_bbox: Tuple,
                               all_bboxes: List[Tuple]) -> Tuple[float, float]:
        """Use force-directed approach to find non-overlapping position"""
        # Start from a grid position
        grid_size = 40
        grid_x = int(cx / grid_size) * grid_size
        grid_y = int(cy / grid_size) * grid_size
        
        # Try spiral pattern from grid position
        for radius in range(1, 10):
            for angle in range(0, 360, 30):
                rad = math.radians(angle)
                x = grid_x + radius * grid_size * math.cos(rad)
                y = grid_y + radius * grid_size * math.sin(rad)
                
                # Check bounds
                x = max(LABEL_RADIUS, min(self.width - LABEL_RADIUS, x))
                y = max(LABEL_RADIUS, min(self.height - LABEL_RADIUS, y))
                
                # Check if position is valid
                valid = True
                for bbox in all_bboxes:
                    if self._circle_rect_overlap(x, y, LABEL_RADIUS, *bbox):
                        valid = False
                        break
                
                if valid:
                    return (x, y)
        
        # Fallback: place at edge
        return (self.width - LABEL_RADIUS - 10, cy)

class ConsistencyAnalyzer:
    """Enhanced consistency analysis with X button detection"""
    
    def __init__(self):
        self.runs = []
        
    def add_run(self, run_num: int, coordinates: List[List[int]], prompt: str):
        """Add a run's results"""
        self.runs.append({
            'run': run_num,
            'count': len(coordinates),
            'coordinates': coordinates,
            'prompt': prompt
        })
    
    def find_consistent_elements(self, tolerance: int = 15) -> List[Dict]:
        """Find elements that appear consistently across all runs"""
        if len(self.runs) < 2:
            return []
        
        consistent_elements = []
        
        # For each element in the first run
        for idx, coords1 in enumerate(self.runs[0]['coordinates']):
            appears_in_all = True
            similar_coords = [coords1]
            
            # Check if it appears in all other runs
            for run in self.runs[1:]:
                found = False
                for coords2 in run['coordinates']:
                    if self._coords_similar(coords1, coords2, tolerance):
                        similar_coords.append(coords2)
                        found = True
                        break
                
                if not found:
                    appears_in_all = False
                    break
            
            if appears_in_all:
                # Calculate average position
                avg_coords = [
                    sum(c[i] for c in similar_coords) / len(similar_coords)
                    for i in range(4)
                ]
                consistent_elements.append({
                    'element_idx': idx + 1,
                    'avg_coords': avg_coords,
                    'variations': similar_coords
                })
        
        return consistent_elements
    
    def identify_x_button(self, consistent_elements: List[Dict]) -> Optional[Dict]:
        """Try to identify the X close button from consistent elements"""
        x_candidates = []
        
        for elem in consistent_elements:
            ymin, xmin, ymax, xmax = elem['avg_coords']
            
            # X button is typically:
            # 1. In the top-right area (x > 850, y < 150)
            # 2. Square-ish aspect ratio
            # 3. Small to medium size
            
            width = xmax - xmin
            height = ymax - ymin
            aspect_ratio = width / height if height > 0 else 0
            
            # Check if in top-right area
            if xmin > 850 and ymin < 150:
                # Check aspect ratio (should be roughly square)
                if 0.7 < aspect_ratio < 1.3:
                    # Check size (not too big, not too small)
                    if 20 < width < 100 and 20 < height < 100:
                        score = 0
                        # Higher score for more top-right position
                        score += (1000 - xmin) / 100  # Further right is better
                        score += (150 - ymin) / 10     # Higher up is better
                        
                        x_candidates.append({
                            'element': elem,
                            'score': score,
                            'position': f"({int(xmin)}, {int(ymin)})",
                            'size': f"{int(width)}x{int(height)}"
                        })
        
        # Return highest scoring candidate
        if x_candidates:
            x_candidates.sort(key=lambda x: x['score'], reverse=True)
            return x_candidates[0]
        
        return None
    
    def _coords_similar(self, coords1: List[int], coords2: List[int], tolerance: int) -> bool:
        """Check if two coordinate sets are similar within tolerance"""
        return all(abs(c1 - c2) <= tolerance for c1, c2 in zip(coords1, coords2))

def create_smart_bbox_annotation(image_path: str, coordinates: List[List[int]], 
                               run_num: int, output_path: str = None) -> str:
    """Create image with bounding boxes and smart label placement"""
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    
    # Font setup
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except:
        font = None
        small_font = None
    
    print(f"\nRun {run_num} - Drawing {len(coordinates)} bounding boxes with smart labels:")
    
    # Convert all coordinates to pixel space
    pixel_bboxes = []
    for coords in coordinates:
        ymin, xmin, ymax, xmax = coords
        x1 = xmin * img.width / 1000
        y1 = ymin * img.height / 1000
        x2 = xmax * img.width / 1000
        y2 = ymax * img.height / 1000
        pixel_bboxes.append((x1, y1, x2, y2))
    
    # Initialize smart label placer
    label_placer = SmartLabelPlacer(img.width, img.height)
    
    # Draw all bounding boxes and labels
    for idx, (coords, bbox) in enumerate(zip(coordinates, pixel_bboxes)):
        x1, y1, x2, y2 = bbox
        
        # Get color for this element
        color = COLORS[idx % len(COLORS)]
        
        print(f"  Element {idx + 1}: bbox={coords} -> pixels=[{int(x1)}, {int(y1)}, {int(x2)}, {int(y2)}]")
        
        # Draw bounding box
        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
        
        # Find smart label position
        label_x, label_y = label_placer.find_label_position(bbox, pixel_bboxes, idx)
        
        # Draw connection line
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        draw.line([(center_x, center_y), (label_x, label_y)], 
                 fill=color, width=1)
        
        # Draw label circle
        draw.ellipse(
            [label_x - LABEL_RADIUS, label_y - LABEL_RADIUS,
             label_x + LABEL_RADIUS, label_y + LABEL_RADIUS],
            fill=color,
            outline='white',
            width=2
        )
        
        # Draw label text
        label = str(idx + 1)
        if font:
            bbox = draw.textbbox((0, 0), label, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            draw.text((label_x - text_width/2, label_y - text_height/2), 
                     label, fill='white', font=font)
        else:
            draw.text((label_x - 5, label_y - 5), label, fill='white')
    
    # Add title
    title = f"Run {run_num}: Smart Label Placement ({len(coordinates)} elements)"
    if font:
        draw.text((10, 10), title, fill='white', font=font, 
                 stroke_width=2, stroke_fill='black')
    else:
        draw.text((10, 10), title, fill='white')
    
    if output_path:
        img.save(output_path)
        return output_path
    else:
        timestamp = int(time.time())
        path = OUTPUT_DIR / f"run{run_num}_smart_bboxes_{timestamp}.png"
        img.save(path)
        return str(path)

def create_smart_crosshair_annotation(image_path: str, coordinates: List[List[int]], 
                                    run_num: int, output_path: str = None) -> str:
    """Create image with thin crosshairs and smart label placement"""
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    
    # Font setup
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except:
        font = None
    
    print(f"\nRun {run_num} - Drawing {len(coordinates)} thin crosshairs with smart labels:")
    
    # Convert coordinates and calculate centers
    centers = []
    pixel_bboxes = []
    for coords in coordinates:
        ymin, xmin, ymax, xmax = coords
        
        # Calculate center
        center_x = ((xmin + xmax) / 2) * img.width / 1000
        center_y = ((ymin + ymax) / 2) * img.height / 1000
        centers.append((center_x, center_y))
        
        # Also store pixel bbox for label placement algorithm
        x1 = xmin * img.width / 1000
        y1 = ymin * img.height / 1000
        x2 = xmax * img.width / 1000
        y2 = ymax * img.height / 1000
        pixel_bboxes.append((x1, y1, x2, y2))
    
    # Initialize smart label placer
    label_placer = SmartLabelPlacer(img.width, img.height)
    
    # Draw all crosshairs and labels
    for idx, ((center_x, center_y), bbox) in enumerate(zip(centers, pixel_bboxes)):
        # Get color for this element
        color = COLORS[idx % len(COLORS)]
        
        print(f"  Element {idx + 1}: center=({int(center_x)}, {int(center_y)})")
        
        # Draw thin crosshair with subtle outline
        # White outline (very thin)
        draw.line(
            [(center_x - CROSSHAIR_SIZE/2, center_y), 
             (center_x + CROSSHAIR_SIZE/2, center_y)],
            fill='white', width=3
        )
        draw.line(
            [(center_x, center_y - CROSSHAIR_SIZE/2), 
             (center_x, center_y + CROSSHAIR_SIZE/2)],
            fill='white', width=3
        )
        
        # Colored crosshair (thin)
        draw.line(
            [(center_x - CROSSHAIR_SIZE/2, center_y), 
             (center_x + CROSSHAIR_SIZE/2, center_y)],
            fill=color, width=1
        )
        draw.line(
            [(center_x, center_y - CROSSHAIR_SIZE/2), 
             (center_x, center_y + CROSSHAIR_SIZE/2)],
            fill=color, width=1
        )
        
        # Center dot
        dot_size = 3
        draw.ellipse(
            [center_x - dot_size - 1, center_y - dot_size - 1, 
             center_x + dot_size + 1, center_y + dot_size + 1],
            fill='white', outline=None
        )
        draw.ellipse(
            [center_x - dot_size, center_y - dot_size, 
             center_x + dot_size, center_y + dot_size],
            fill=color, outline=None
        )
        
        # Find smart label position
        label_x, label_y = label_placer.find_label_position(bbox, pixel_bboxes, idx)
        
        # Draw connection line
        draw.line([(center_x, center_y), (label_x, label_y)], 
                 fill=color, width=1)
        
        # Draw label circle
        draw.ellipse(
            [label_x - LABEL_RADIUS, label_y - LABEL_RADIUS,
             label_x + LABEL_RADIUS, label_y + LABEL_RADIUS],
            fill=color,
            outline='white',
            width=2
        )
        
        # Draw label text
        label = str(idx + 1)
        if font:
            bbox_text = draw.textbbox((0, 0), label, font=font)
            text_width = bbox_text[2] - bbox_text[0]
            text_height = bbox_text[3] - bbox_text[1]
            draw.text((label_x - text_width/2, label_y - text_height/2), 
                     label, fill='white', font=font)
        else:
            draw.text((label_x - 5, label_y - 5), label, fill='white')
    
    # Add title
    title = f"Run {run_num}: Thin Crosshairs with Smart Labels ({len(coordinates)} elements)"
    if font:
        draw.text((10, 10), title, fill='white', font=font, 
                 stroke_width=2, stroke_fill='black')
    else:
        draw.text((10, 10), title, fill='white')
    
    if output_path:
        img.save(output_path)
        return output_path
    else:
        timestamp = int(time.time())
        path = OUTPUT_DIR / f"run{run_num}_smart_crosshairs_{timestamp}.png"
        img.save(path)
        return str(path)

async def run_detection_with_analysis(detector, run_num: int, analyzer: ConsistencyAnalyzer, 
                                    prompt: str) -> Dict:
    """Run a single detection with enhanced analysis"""
    print(f"\n{'='*60}")
    print(f"RUN {run_num}")
    print(f"{'='*60}")
    
    # Print the prompt being used
    print(f"\nPrompt: {prompt}")
    
    # Detect elements
    print(f"\nRun {run_num}: Detecting elements...")
    
    # Retry logic
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            result = await detector.detect_elements(
                SOURCE_IMAGE,
                prompt,
                save_annotated=False
            )
            break
        except Exception as e:
            if "overloaded" in str(e) and attempt < max_retries - 1:
                print(f"API overloaded, retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise
    
    coordinates = result['coordinates']
    print(f"\nRun {run_num}: Found {len(coordinates)} elements")
    
    # Save raw response
    raw_response_path = OUTPUT_DIR / f"run{run_num}_raw_response.json"
    with open(raw_response_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    # Detailed coordinate analysis
    print(f"\nRun {run_num} - Detailed coordinate analysis:")
    top_right_elements = []
    for idx, coords in enumerate(coordinates):
        ymin, xmin, ymax, xmax = coords
        width = xmax - xmin
        height = ymax - ymin
        center_x = (xmin + xmax) / 2
        center_y = (ymin + ymax) / 2
        
        print(f"  Element {idx + 1}:")
        print(f"    Coords: {coords}")
        print(f"    Size: {width}x{height}")
        print(f"    Center: ({int(center_x)}, {int(center_y)})")
        
        # Check if in top-right area
        if xmin > 850 and ymin < 150:
            top_right_elements.append({
                'idx': idx + 1,
                'coords': coords,
                'center': (center_x, center_y),
                'size': (width, height)
            })
            print(f"    *** TOP-RIGHT ELEMENT - Potential X button ***")
    
    if top_right_elements:
        print(f"\nFound {len(top_right_elements)} elements in top-right area:")
        for elem in top_right_elements:
            print(f"  Element {elem['idx']}: center={elem['center']}, size={elem['size']}")
    else:
        print("\n⚠️  NO ELEMENTS FOUND IN TOP-RIGHT AREA (x>850, y<150)")
    
    # Add to analyzer
    analyzer.add_run(run_num, coordinates, prompt)
    
    # Create visualizations
    bbox_path = create_smart_bbox_annotation(SOURCE_IMAGE, coordinates, run_num)
    crosshair_path = create_smart_crosshair_annotation(SOURCE_IMAGE, coordinates, run_num)
    
    print(f"\nRun {run_num} - Created visualizations:")
    print(f"  - Smart bounding boxes: {bbox_path}")
    print(f"  - Smart crosshairs: {crosshair_path}")
    
    return {
        'run': run_num,
        'count': len(coordinates),
        'coordinates': coordinates,
        'top_right_elements': top_right_elements,
        'bbox_path': bbox_path,
        'crosshair_path': crosshair_path,
        'raw_response_path': str(raw_response_path)
    }

async def main():
    print("=== Testing Smart Label Placement with Enhanced Detection ===\n")
    
    # Initialize detector
    detector = GeminiDetector(api_key=GEMINI_API_KEY)
    analyzer = ConsistencyAnalyzer()
    
    # Try different prompts to improve X button detection
    prompts = [
        "Return bounding boxes as JSON arrays [ymin, xmin, ymax, xmax] for ALL clickable elements including buttons, links, icons, form fields, close buttons (X), and any interactive UI elements. Pay special attention to the modal close button (X) typically found in the top-right corner. Be thorough and detect every possible clickable element.",
        
        "Return bounding boxes as JSON arrays [ymin, xmin, ymax, xmax] for EVERY clickable element in this modal dialog. This includes: the X close button in the top-right corner, all form fields, all buttons, all links, and any other interactive elements. Do not miss the modal close button.",
        
        "Return bounding boxes as JSON arrays [ymin, xmin, ymax, xmax] for ALL interactive UI elements. Start by looking for the modal's close button (usually an X or × symbol in the top-right), then find all other clickable elements like buttons, links, inputs, and icons. Be extremely thorough."
    ]
    
    # Run detection 3 times with different prompts
    all_runs = []
    for run_num in range(1, 4):
        prompt = prompts[run_num - 1]
        run_result = await run_detection_with_analysis(detector, run_num, analyzer, prompt)
        all_runs.append(run_result)
        
        # Small delay between runs
        if run_num < 3:
            await asyncio.sleep(2)
    
    # Analyze consistency
    print(f"\n{'='*60}")
    print("CONSISTENCY ANALYSIS")
    print(f"{'='*60}")
    
    consistent_elements = analyzer.find_consistent_elements()
    
    print(f"\nConsistent Elements (appearing in all runs):")
    if consistent_elements:
        for elem in consistent_elements:
            ymin, xmin, ymax, xmax = elem['avg_coords']
            print(f"  Element {elem['element_idx']}:")
            print(f"    Average position: [{int(ymin)}, {int(xmin)}, {int(ymax)}, {int(xmax)}]")
            print(f"    Center: ({int((xmin + xmax)/2)}, {int((ymin + ymax)/2)})")
    else:
        print("  No elements appeared consistently in all runs!")
    
    # Try to identify X button
    print(f"\n{'='*60}")
    print("X BUTTON DETECTION ANALYSIS")
    print(f"{'='*60}")
    
    x_button = analyzer.identify_x_button(consistent_elements)
    if x_button:
        print(f"\n✓ Most likely X button candidate:")
        print(f"  Element: {x_button['element']['element_idx']}")
        print(f"  Position: {x_button['position']}")
        print(f"  Size: {x_button['size']}")
        print(f"  Confidence score: {x_button['score']:.2f}")
    else:
        print("\n✗ Could not identify X button from consistent elements")
        
        # Check if any run found top-right elements
        any_top_right = False
        for run in all_runs:
            if run['top_right_elements']:
                any_top_right = True
                break
        
        if not any_top_right:
            print("\n⚠️  CRITICAL: No elements detected in top-right area across ANY run!")
            print("   This suggests the X button is not being detected at all.")
    
    # Summary
    print(f"\n{'='*60}")
    print("DETECTION SUMMARY")
    print(f"{'='*60}")
    
    # Element count analysis
    counts = [run['count'] for run in all_runs]
    print(f"\nElement counts per run: {counts}")
    if max(counts) - min(counts) > 2:
        print("⚠️  Large variation in counts - detection is inconsistent")
    else:
        print("✓ Element counts are relatively consistent")
    
    # Top-right detection summary
    print("\nTop-right area detection:")
    for run in all_runs:
        count = len(run['top_right_elements'])
        print(f"  Run {run['run']}: {count} elements in top-right")
    
    print("\nFiles created:")
    for run in all_runs:
        print(f"\nRun {run['run']}:")
        print(f"  - Smart bounding boxes: {run['bbox_path']}")
        print(f"  - Smart crosshairs: {run['crosshair_path']}")
        print(f"  - Raw response: {run['raw_response_path']}")
    
    print("\n=== Analysis Complete ===")
    print("\nKey improvements in this version:")
    print("- Smart label placement algorithm keeps ALL labels outside boxes")
    print("- Thin crosshairs (1px) with color coding maintained")
    print("- Enhanced prompts specifically mentioning X button")
    print("- Detailed analysis of top-right area for X button detection")
    print("- Consistency tracking across runs")

if __name__ == "__main__":
    asyncio.run(main())