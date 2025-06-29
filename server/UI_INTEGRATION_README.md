# Browser Automation UI Integration

## Overview

The browser server has been enhanced with a web-based UI that provides an intuitive interface for browser automation tasks. The UI integrates the modular tools for screenshot capture, element detection using Gemini Vision API, and visualization of bounding boxes.

## What's New

### 1. Reorganized Tools
The following tools have been moved to the server directory and integrated as modules:
- `screenshot_to_gemini_bb_json.py` - Detects elements using Gemini Vision API
- `bbox_visualizer.py` - Visualizes bounding boxes and crosshairs on screenshots

These tools maintain their standalone CLI functionality while also being importable by the server.

### 2. New API Routes

#### GET `/get_screenshot/{session_id}/{page_id}`
- Captures a screenshot from an active browser session
- Returns base64 encoded image data

#### POST `/navigate_to`
- Navigates a browser page to a specified URL
- Request body:
  ```json
  {
    "session_id": "string",
    "page_id": "string", 
    "url": "string"
  }
  ```

#### POST `/screenshot_to_bounding_boxes`
- Sends screenshot to Gemini Vision API for element detection
- Request body:
  ```json
  {
    "screenshot": "base64_string",
    "api_key": "string",
    "prompt": "optional_string"
  }
  ```
- Returns detected bounding boxes as [ymin, xmin, ymax, xmax] arrays

#### POST `/visualize_bounding_boxes`
- Creates visualization of bounding boxes on screenshot
- Request body:
  ```json
  {
    "screenshot": "base64_string",
    "bounding_boxes": [[ymin, xmin, ymax, xmax], ...],
    "mode": "bbox" | "crosshair"
  }
  ```
- Returns base64 encoded visualization image

### 3. Web UI

Access the UI at: **http://localhost:8000/ui**

#### Features:
- **Session Management**: Start and manage browser sessions
- **Navigation**: Navigate to any URL
- **Screenshot Capture**: Take screenshots or upload existing ones
- **Element Detection**: Use Gemini Vision to detect clickable elements
- **Visualization**: View results as bounding boxes or crosshairs
- **Workflow Progress**: Visual progress indicator for each step

#### UI Workflow:
1. **Start Session** → Creates new browser instance
2. **Navigate** → Go to target website
3. **Screenshot** → Capture current page
4. **Detect Elements** → Use Gemini Vision API
5. **Visualize** → Show boxes or crosshairs

#### Additional Features:
- Collapsible JSON output for detected elements
- File upload support for existing screenshots
- Loading states and error handling
- Responsive design with clean Apple-inspired UI

## Usage

### Starting the Server
```bash
cd .
python server/browser_server_enhanced.py
```

### Accessing the UI
Open your browser and navigate to: **http://localhost:8000/ui**

### API Documentation
Interactive API docs available at: **http://localhost:8000/docs**

## Configuration

### CORS
The server is configured with permissive CORS settings for development:
```python
allow_origins=["*"]
allow_credentials=True
allow_methods=["*"]
allow_headers=["*"]
```

### Static Files
Static files are served from `/server/static/` directory.

## Important Notes

1. **Coordinate Normalization**: The system maintains the /1000 normalization from the original tools
2. **Temporary Files**: Screenshots are temporarily saved to `/tmp/` during processing
3. **Session Persistence**: Browser sessions persist until explicitly closed
4. **API Key**: The default Gemini API key in the UI should be replaced with your own

## Standalone Tool Usage

The moved tools still work as CLI utilities:

```bash
# Detect bounding boxes
python screenshot_to_gemini_bb_json.py screenshot.png --api-key YOUR_KEY

# Visualize bounding boxes
python bbox_visualizer.py screenshot.png boxes.json --mode bbox
```

## Architecture

```
/browser_automation/server/
├── browser_server_enhanced.py    # Main server with new routes
├── screenshot_to_gemini_bb_json.py  # Element detection module
├── bbox_visualizer.py            # Visualization module
└── static/
    └── index.html               # Web UI
```

The server imports the detection and visualization modules directly, maintaining clean separation of concerns while enabling seamless integration.