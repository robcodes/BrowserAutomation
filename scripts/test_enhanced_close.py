#!/usr/bin/env python3
"""Test the enhanced Gemini click helper"""
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.gemini_click_helper_enhanced import close_fuzzycode_modal_smart

if __name__ == "__main__":
    asyncio.run(close_fuzzycode_modal_smart())