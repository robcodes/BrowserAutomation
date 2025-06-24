#!/usr/bin/env python3
"""
Runner script for FuzzyCode automation with Gemini Vision for modal closing
"""
import asyncio
import sys
from pathlib import Path

# Import all steps
from step01_navigate import step01_navigate
from step02_open_login import step02_open_login
from step03_fill_login import step03_fill_login
from step04_submit_login import step04_submit_login
from step05_close_modal_gemini import step05_close_modal  # Using Gemini version
from step06_generate_code import step06_generate_code

STEPS = [
    ("Navigate to FuzzyCode", step01_navigate),
    ("Open Login Modal", step02_open_login),
    ("Fill Login Form", step03_fill_login),
    ("Submit Login", step04_submit_login),
    ("Close Modal (Gemini)", step05_close_modal),  # Now using visual detection
    ("Generate Code", step06_generate_code)
]

async def run_all_steps(headless=True):
    """Run all steps in sequence"""
    print("="*60)
    print("Running ALL FuzzyCode Steps (with Gemini Vision)")
    print("="*60)
    
    results = []
    
    for i, (name, step_func) in enumerate(STEPS):
        print(f"\nRunning Step {i+1}: {name}")
        
        try:
            # All step functions now accept headless parameter
            if asyncio.iscoroutinefunction(step_func):
                if i == 0:  # Only first step needs headless param
                    result = await step_func(headless)
                else:
                    result = await step_func()
            else:
                result = step_func()
                
            results.append((name, result))
            
            if not result:
                print(f"\n❌ Step {i+1} failed, stopping execution")
                break
                
        except Exception as e:
            print(f"\n❌ Step {i+1} error: {str(e)}")
            results.append((name, False))
            break
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for i, (name, result) in enumerate(results):
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"Step {i+1}: {name} - {status}")
    
    # Fill in remaining steps as failed if we stopped early
    for i in range(len(results), len(STEPS)):
        print(f"Step {i+1}: {STEPS[i][0]} - ❌ FAILED")
    
    return all(result for _, result in results)

async def run_single_step(step_num: int, headless=True):
    """Run a single step"""
    if step_num < 1 or step_num > len(STEPS):
        print(f"Invalid step number: {step_num}. Must be between 1 and {len(STEPS)}")
        return False
    
    name, step_func = STEPS[step_num - 1]
    print(f"Running Step {step_num}: {name}")
    
    try:
        if asyncio.iscoroutinefunction(step_func):
            if step_num == 1:  # Only first step needs headless param
                result = await step_func(headless)
            else:
                result = await step_func()
        else:
            result = step_func()
        
        return result
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run FuzzyCode automation steps with Gemini Vision")
    parser.add_argument('step', nargs='?', default='all', 
                       help='Step number (1-6) or "all" to run all steps')
    parser.add_argument('--visible', action='store_true',
                       help='Run browser in visible mode (not headless)')
    
    args = parser.parse_args()
    headless = not args.visible
    
    if args.step == 'all':
        success = await run_all_steps(headless)
        sys.exit(0 if success else 1)
    else:
        try:
            step_num = int(args.step)
            success = await run_single_step(step_num, headless)
            sys.exit(0 if success else 1)
        except ValueError:
            print(f"Invalid step: {args.step}. Use a number 1-6 or 'all'")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())