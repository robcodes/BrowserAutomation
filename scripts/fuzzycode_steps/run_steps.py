#!/usr/bin/env python3
"""
Runner script for FuzzyCode step-by-step automation
Can run all steps or individual steps
"""
import asyncio
import sys
from pathlib import Path

# Import all steps
from step01_navigate import step01_navigate
from step02_open_login import step02_open_login
from step03_fill_login import step03_fill_login
from step04_submit_login import step04_submit_login
from step05_close_modal import step05_close_modal
from step06_generate_code import step06_generate_code

STEPS = [
    ("Navigate to FuzzyCode", step01_navigate),
    ("Open Login Modal", step02_open_login),
    ("Fill Login Form", step03_fill_login),
    ("Submit Login", step04_submit_login),
    ("Close Modal", step05_close_modal),
    ("Generate Code", step06_generate_code)
]

async def run_all_steps(headless=True):
    """Run all steps in sequence"""
    print("="*60)
    print("Running ALL FuzzyCode Steps")
    print("="*60)
    
    results = []
    
    # Step 1 needs headless parameter
    print(f"\nRunning Step 1: {STEPS[0][0]}")
    result = await STEPS[0][1](headless=headless)
    results.append(result)
    
    if not result:
        print("\n❌ Step 1 failed, stopping execution")
        return results
    
    # Run remaining steps
    for i, (name, func) in enumerate(STEPS[1:], 2):
        print(f"\n{'='*60}")
        print(f"Running Step {i}: {name}")
        print("="*60)
        
        result = await func()
        results.append(result)
        
        if not result:
            print(f"\n❌ Step {i} failed, stopping execution")
            break
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for i, (name, _) in enumerate(STEPS, 1):
        status = "✅ PASSED" if i <= len(results) and results[i-1] else "❌ FAILED"
        print(f"Step {i}: {name} - {status}")
    
    return results

async def run_single_step(step_num, headless=True):
    """Run a single step"""
    if step_num < 1 or step_num > len(STEPS):
        print(f"❌ Invalid step number: {step_num}")
        print(f"   Valid steps are 1-{len(STEPS)}")
        return False
    
    name, func = STEPS[step_num - 1]
    print(f"Running Step {step_num}: {name}")
    
    if step_num == 1:
        return await func(headless=headless)
    else:
        return await func()

def print_usage():
    """Print usage information"""
    print("Usage: python run_steps.py [options]")
    print("\nOptions:")
    print("  all              Run all steps in sequence")
    print("  <step_number>    Run a specific step (1-6)")
    print("  --visible        Run in visible (non-headless) mode")
    print("\nExamples:")
    print("  python run_steps.py all           # Run all steps in headless mode")
    print("  python run_steps.py all --visible # Run all steps with visible browser")
    print("  python run_steps.py 1             # Run only step 1")
    print("  python run_steps.py 3             # Run only step 3")
    print("\nAvailable steps:")
    for i, (name, _) in enumerate(STEPS, 1):
        print(f"  {i}: {name}")

async def main():
    """Main entry point"""
    args = sys.argv[1:]
    
    if not args:
        print_usage()
        return
    
    # Check for visible mode
    headless = "--visible" not in args
    args = [arg for arg in args if arg != "--visible"]
    
    if not args:
        print_usage()
        return
    
    if args[0] == "all":
        results = await run_all_steps(headless=headless)
        success = all(results)
    elif args[0].isdigit():
        step_num = int(args[0])
        success = await run_single_step(step_num, headless=headless)
    else:
        print_usage()
        return
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())