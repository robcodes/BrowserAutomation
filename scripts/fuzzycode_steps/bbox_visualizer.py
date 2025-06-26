#!/usr/bin/env python3
"""
Reusable module for visualizing bounding boxes and crosshairs with smart label placement.
Supports both bbox and crosshair visualization modes.
"""

import json
import math
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from pathlib import Path


# Colors for bounding boxes (bright, distinct colors)
COLORS = [
    '#FF0000',  # Red
    '#00FF00',  # Green
    '#FFFF00',  # Yellow
    '#0000FF',  # Blue
    '#FF00FF',  # Magenta
    '#00FFFF',  # Cyan
    '#FF8000',  # Orange
    '#8000FF',  # Purple
]


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def calculate_label_bounds(x, y, label_text, font):
    """Calculate the bounding rectangle for a label"""
    if font:
        bbox = font.getbbox(label_text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    else:
        text_width = len(label_text) * 8
        text_height = 12
    
    # Add padding for the circle background
    radius = max(15, max(text_width, text_height) // 2 + 3)
    return {
        'x1': x - radius,
        'y1': y - radius,
        'x2': x + radius,
        'y2': y + radius,
        'radius': radius
    }


def rectangles_overlap(rect1, rect2):
    """Check if two rectangles overlap"""
    return not (rect1['x2'] < rect2['x1'] or rect2['x2'] < rect1['x1'] or 
                rect1['y2'] < rect2['y1'] or rect2['y2'] < rect1['y1'])


def point_in_rectangle(x, y, rect):
    """Check if a point is inside a rectangle"""
    return rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]


def line_intersects_rectangle(x1, y1, x2, y2, rect_x1, rect_y1, rect_x2, rect_y2):
    """Check if a line segment intersects with a rectangle"""
    # Check if line endpoints are inside rectangle
    if (rect_x1 <= x1 <= rect_x2 and rect_y1 <= y1 <= rect_y2) or \
       (rect_x1 <= x2 <= rect_x2 and rect_y1 <= y2 <= rect_y2):
        return True
    
    # Check intersection with each edge of rectangle
    def line_intersect(p1, p2, p3, p4):
        """Check if two line segments intersect"""
        def ccw(A, B, C):
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
        return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)
    
    # Rectangle edges
    edges = [
        ((rect_x1, rect_y1), (rect_x2, rect_y1)),  # top
        ((rect_x2, rect_y1), (rect_x2, rect_y2)),  # right
        ((rect_x2, rect_y2), (rect_x1, rect_y2)),  # bottom
        ((rect_x1, rect_y2), (rect_x1, rect_y1))   # left
    ]
    
    line_seg = ((x1, y1), (x2, y2))
    for edge in edges:
        if line_intersect(line_seg[0], line_seg[1], edge[0], edge[1]):
            return True
    return False


def detect_clusters(box_positions, cluster_distance=80):
    """Detect clusters of nearby bounding boxes"""
    clusters = []
    assigned = [False] * len(box_positions)
    
    for i, box1 in enumerate(box_positions):
        if assigned[i]:
            continue
            
        # Start new cluster
        cluster = [i]
        assigned[i] = True
        
        # Find all boxes within cluster distance
        cx1 = (box1[0] + box1[2]) / 2
        cy1 = (box1[1] + box1[3]) / 2
        
        for j, box2 in enumerate(box_positions):
            if assigned[j] or i == j:
                continue
                
            cx2 = (box2[0] + box2[2]) / 2
            cy2 = (box2[1] + box2[3]) / 2
            
            distance = math.sqrt((cx1 - cx2)**2 + (cy1 - cy2)**2)
            if distance < cluster_distance:
                cluster.append(j)
                assigned[j] = True
        
        if len(cluster) > 1:  # Only keep clusters with multiple boxes
            clusters.append(cluster)
    
    return clusters


def get_cluster_boundary(cluster_indices, box_positions):
    """Get the bounding rectangle of a cluster"""
    min_x = min(box_positions[i][0] for i in cluster_indices)
    min_y = min(box_positions[i][1] for i in cluster_indices)
    max_x = max(box_positions[i][2] for i in cluster_indices)
    max_y = max(box_positions[i][3] for i in cluster_indices)
    return (min_x, min_y, max_x, max_y)


def find_smart_label_position(box_center, current_box, current_box_idx, all_boxes, all_labels, img_width, img_height, label_text, font, clusters):
    """Find optimal position for label to avoid overlaps with cluster-aware algorithm"""
    cx, cy = box_center
    
    # Check if this box is in a cluster
    in_cluster = False
    cluster_boundary = None
    for cluster in clusters:
        if current_box_idx in cluster:
            in_cluster = True
            cluster_boundary = get_cluster_boundary(cluster, all_boxes)
            break
    
    # Determine distances to try based on clustering
    if in_cluster:
        # For clustered boxes, start with larger distances
        distances = [80, 120, 160, 200, 250, 300]
    else:
        # For isolated boxes, can use smaller distances
        distances = [40, 60, 80, 120, 160]
    
    # More angles for better coverage
    angles = [i * 15 for i in range(24)]  # 24 directions
    
    best_pos = None
    min_penalty = float('inf')
    
    for distance in distances:
        for angle in angles:
            # Calculate potential label position
            rad = math.radians(angle)
            lx = cx + distance * math.cos(rad)
            ly = cy + distance * math.sin(rad)
            
            # Keep label within image bounds with margin
            margin = 30
            lx = max(margin, min(lx, img_width - margin))
            ly = max(margin, min(ly, img_height - margin))
            
            # Calculate label bounds at this position
            label_bounds = calculate_label_bounds(lx, ly, label_text, font)
            
            # Calculate penalty for this position
            penalty = 0
            
            # 1. CRITICAL: Penalty for connecting line intersecting other boxes
            for i, box in enumerate(all_boxes):
                if i == current_box_idx:  # Skip the current box
                    continue
                    
                bx1, by1, bx2, by2 = box
                
                # Check if connecting line intersects this box
                if line_intersects_rectangle(cx, cy, lx, ly, bx1, by1, bx2, by2):
                    penalty += 2000  # VERY HIGH penalty for line intersection
                
                # Check if label center is inside box
                if point_in_rectangle(lx, ly, box):
                    penalty += 1500  # Very high penalty for center inside box
                
                # Check if label circle overlaps with box
                label_rect = [label_bounds['x1'], label_bounds['y1'], 
                             label_bounds['x2'], label_bounds['y2']]
                box_rect = {'x1': bx1, 'y1': by1, 'x2': bx2, 'y2': by2}
                
                if rectangles_overlap({'x1': label_rect[0], 'y1': label_rect[1], 
                                     'x2': label_rect[2], 'y2': label_rect[3]}, box_rect):
                    box_area = (bx2 - bx1) * (by2 - by1)
                    penalty += min(800, box_area / 50)
            
            # 2. Penalty for being too close to other labels
            for other_label_pos in all_labels:
                if other_label_pos:
                    ox, oy = other_label_pos
                    other_label_bounds = calculate_label_bounds(ox, oy, "1", font)
                    
                    distance_between = math.sqrt((lx - ox)**2 + (ly - oy)**2)
                    min_distance = label_bounds['radius'] + other_label_bounds['radius'] + 15
                    
                    if distance_between < min_distance:
                        penalty += (min_distance - distance_between) * 15
            
            # 3. For clustered boxes, prefer positions away from cluster center
            if in_cluster and cluster_boundary:
                cluster_cx = (cluster_boundary[0] + cluster_boundary[2]) / 2
                cluster_cy = (cluster_boundary[1] + cluster_boundary[3]) / 2
                
                # Prefer directions that move away from cluster center
                to_cluster_center = math.sqrt((cluster_cx - cx)**2 + (cluster_cy - cy)**2)
                to_label_from_cluster = math.sqrt((cluster_cx - lx)**2 + (cluster_cy - ly)**2)
                
                if to_label_from_cluster < to_cluster_center:
                    penalty += 300  # Penalty for moving toward cluster center
                else:
                    penalty -= 50  # Bonus for moving away from cluster
            
            # 4. Distance penalty (but much lower weight for clustered boxes)
            actual_distance = math.sqrt((lx - cx)**2 + (ly - cy)**2)
            if in_cluster:
                penalty += actual_distance * 0.02  # Very low weight for clustered boxes
            else:
                penalty += actual_distance * 0.1  # Normal weight for isolated boxes
            
            # 5. Edge penalties
            edge_margin = 40
            if lx < edge_margin:
                penalty += (edge_margin - lx) * 3
            if lx > img_width - edge_margin:
                penalty += (lx - (img_width - edge_margin)) * 3
            if ly < edge_margin:
                penalty += (edge_margin - ly) * 3
            if ly > img_height - edge_margin:
                penalty += (ly - (img_height - edge_margin)) * 3
            
            # 6. Directional preferences for clusters
            if in_cluster and cluster_boundary:
                # Prefer outward directions from cluster edges
                cluster_left = cluster_boundary[0]
                cluster_right = cluster_boundary[2]
                cluster_top = cluster_boundary[1]
                cluster_bottom = cluster_boundary[3]
                
                # If box is on left edge of cluster, prefer left placement
                if cx - cluster_left < 20 and lx < cx:
                    penalty -= 100
                # If box is on right edge of cluster, prefer right placement  
                elif cluster_right - cx < 20 and lx > cx:
                    penalty -= 100
                # If box is on top edge of cluster, prefer top placement
                elif cy - cluster_top < 20 and ly < cy:
                    penalty -= 100
                # If box is on bottom edge of cluster, prefer bottom placement
                elif cluster_bottom - cy < 20 and ly > cy:
                    penalty -= 100
            
            if penalty < min_penalty:
                min_penalty = penalty
                best_pos = (lx, ly)
    
    # Enhanced fallback strategy for difficult cases
    if best_pos is None or min_penalty > 1000:
        # Try image corners with very large distances
        fallback_positions = [
            (60, 60),  # Top-left
            (img_width - 60, 60),  # Top-right
            (60, img_height - 60),  # Bottom-left
            (img_width - 60, img_height - 60),  # Bottom-right
            (img_width // 2, 60),  # Top-center
            (img_width // 2, img_height - 60),  # Bottom-center
            (60, img_height // 2),  # Left-center
            (img_width - 60, img_height // 2),  # Right-center
        ]
        
        for fallback_pos in fallback_positions:
            lx, ly = fallback_pos
            
            # Check if this position has line intersections
            has_intersection = False
            for i, box in enumerate(all_boxes):
                if i == current_box_idx:
                    continue
                if line_intersects_rectangle(cx, cy, lx, ly, box[0], box[1], box[2], box[3]):
                    has_intersection = True
                    break
            
            if not has_intersection:
                # Check conflicts with existing labels
                conflicts = False
                for other_label_pos in all_labels:
                    if other_label_pos:
                        ox, oy = other_label_pos
                        if math.sqrt((lx - ox)**2 + (ly - oy)**2) < 60:
                            conflicts = True
                            break
                
                if not conflicts:
                    best_pos = fallback_pos
                    break
    
    return best_pos if best_pos else (cx + 100, cy - 100)  # Final fallback


def optimize_all_label_positions(box_positions, img_width, img_height, font):
    """Optimize label positions for all boxes using a cluster-aware multi-pass approach"""
    num_boxes = len(box_positions)
    label_positions = [None] * num_boxes
    
    # Detect clusters of nearby boxes
    clusters = detect_clusters(box_positions)
    
    # Sort boxes by constraint priority:
    # 1. Boxes in clusters (most constrained)
    # 2. Smaller boxes (more constrained)
    def box_priority(idx):
        x1, y1, x2, y2 = box_positions[idx]
        area = (x2 - x1) * (y2 - y1)
        
        # Check if box is in a cluster
        in_cluster = any(idx in cluster for cluster in clusters)
        
        # Prioritize clustered boxes, then by area
        if in_cluster:
            return (0, area)  # Clustered boxes first, then by area
        else:
            return (1, area)  # Non-clustered boxes second, then by area
    
    box_indices_by_priority = sorted(range(num_boxes), key=box_priority)
    
    # Place labels in order of constraint (most constrained first)
    for idx in box_indices_by_priority:
        x1, y1, x2, y2 = box_positions[idx]
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        
        label_text = str(idx + 1)
        
        # Find position considering all already placed labels and clusters
        label_pos = find_smart_label_position(
            (cx, cy), box_positions[idx], idx, box_positions, label_positions, 
            img_width, img_height, label_text, font, clusters
        )
        label_positions[idx] = label_pos
    
    return label_positions


def visualize(screenshot_path, json_data=None, json_path=None, mode='bbox', output_path=None):
    """
    Create a visualization with either bounding boxes or crosshairs.
    
    Args:
        screenshot_path: Path to the screenshot image
        json_data: JSON data containing coordinates (use this OR json_path)
        json_path: Path to JSON file containing coordinates (use this OR json_data)
        mode: 'bbox' for bounding boxes, 'crosshair' for crosshairs
        output_path: Where to save the output (auto-generated if not provided)
    
    Returns:
        Path to the created image
    """
    # Load JSON data
    if json_data is None and json_path is None:
        raise ValueError("Either json_data or json_path must be provided")
    
    if json_path:
        with open(json_path, 'r') as f:
            json_data = json.load(f)
    
    # Extract coordinates - handle both direct array and nested response
    if isinstance(json_data, list):
        coordinates = json_data
    elif 'coordinates' in json_data:
        coordinates = json_data['coordinates']
    else:
        # Try to extract from Gemini API response format
        try:
            text = json_data['candidates'][0]['content']['parts'][0]['text']
            # Extract coordinates from text using regex
            import re
            regex = r'\[\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\]'
            matches = re.findall(regex, text)
            coordinates = [json.loads(match) for match in matches]
        except (KeyError, IndexError):
            raise ValueError("Could not extract coordinates from JSON data")
    
    if not coordinates:
        raise ValueError("No coordinates found in data")
    
    # Load the image
    img = Image.open(screenshot_path)
    width, height = img.size
    
    # Create drawing context
    draw = ImageDraw.Draw(img)
    
    # Try to load font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    except:
        try:
            # Try alternative font paths
            font = ImageFont.truetype("arial.ttf", 14)
        except:
            font = None
    
    # Process all boxes first
    box_positions = []
    
    for idx, box in enumerate(coordinates):
        # Normalize coordinates (divide by 1000 as bb_detector.html does)
        ymin, xmin, ymax, xmax = [coord / 1000 for coord in box]
        
        # Calculate pixel positions
        x1 = int(xmin * width)
        y1 = int(ymin * height)
        x2 = int(xmax * width)
        y2 = int(ymax * height)
        
        # Store box position
        box_positions.append((x1, y1, x2, y2))
    
    # Optimize label positions for all boxes
    label_positions = optimize_all_label_positions(box_positions, width, height, font)
    
    # Now draw everything based on mode
    for idx, (box_pos, label_pos) in enumerate(zip(box_positions, label_positions)):
        color = COLORS[idx % len(COLORS)]
        rgb_color = hex_to_rgb(color)
        
        x1, y1, x2, y2 = box_pos
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        
        if mode == 'bbox':
            # Draw bounding box
            draw.rectangle([x1, y1, x2, y2], outline=rgb_color, width=3)
        else:  # crosshair mode
            # Draw thin crosshair (1 pixel width)
            crosshair_size = 20
            # Horizontal line
            draw.line([(cx - crosshair_size, cy), (cx + crosshair_size, cy)], 
                     fill=rgb_color, width=1)
            # Vertical line
            draw.line([(cx, cy - crosshair_size), (cx, cy + crosshair_size)], 
                     fill=rgb_color, width=1)
        
        # Draw label with connecting line
        label = str(idx + 1)
        lx, ly = label_pos
        
        # Draw thin connecting line from label to center
        draw.line([(lx, ly), (cx, cy)], fill=rgb_color, width=1)
        
        # Calculate appropriate radius for label circle
        label_bounds = calculate_label_bounds(lx, ly, label, font)
        radius = label_bounds['radius']
        
        # Draw label background circle
        draw.ellipse([lx-radius, ly-radius, lx+radius, ly+radius], 
                    fill=rgb_color, outline='white', width=2)
        
        # Draw label text
        if font:
            bbox = font.getbbox(label)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width = len(label) * 8
            text_height = 12
            
        draw.text((lx - text_width//2, ly - text_height//2), 
                 label, fill='white', font=font)
    
    # Save the result
    if output_path is None:
        timestamp = int(datetime.now().timestamp())
        mode_name = 'bboxes' if mode == 'bbox' else 'crosshairs'
        output_dir = Path(screenshot_path).parent
        output_path = output_dir / f"visualized_{mode_name}_{timestamp}.png"
    
    img.save(output_path)
    return str(output_path)


# Convenience functions
def visualize_bboxes(screenshot_path, json_data=None, json_path=None, output_path=None):
    """Create a bounding box visualization"""
    return visualize(screenshot_path, json_data, json_path, mode='bbox', output_path=output_path)


def visualize_crosshairs(screenshot_path, json_data=None, json_path=None, output_path=None):
    """Create a crosshair visualization"""
    return visualize(screenshot_path, json_data, json_path, mode='crosshair', output_path=output_path)