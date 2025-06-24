# Bounding Box Detector - Original Proof of Concept

This directory contains the original proof of concept for the Gemini Vision integration:

- `bb_detector.html` - Interactive web-based tool for testing Gemini Vision API
- `bb_detector.html.backup` - Backup of the original version

## Purpose

This HTML file was used to prove that Gemini Vision API could:
1. Detect UI elements in screenshots
2. Return accurate bounding box coordinates
3. Handle various types of UI elements (buttons, modals, forms)

## Current Status

The proof of concept has been successfully converted into production-ready Python code:
- Core implementation: `/clients/gemini_detector.py`
- Browser integration: `/scripts/gemini_click_helper.py`
- Working examples: `/examples/gemini_vision/`

This HTML file is kept for reference and historical purposes only. For actual usage, please use the Python implementation.