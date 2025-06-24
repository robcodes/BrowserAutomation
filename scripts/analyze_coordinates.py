#!/usr/bin/env python3
"""Analyze the coordinate differences"""

print("Analyzing coordinate patterns:\n")

print("DIRECT X BUTTON SEARCH (successful):")
direct_coords = [
    [48, 951, 65, 968],
    [54, 951, 68, 966],
    [45, 947, 69, 969],
    [47, 958, 64, 974]
]

for coords in direct_coords:
    ymin, xmin, ymax, xmax = coords
    print(f"  {coords} - Center: x={int((xmin+xmax)/2)}, y={int((ymin+ymax)/2)}")

print("\nFIND ALL APPROACH (top-right elements):")
print("Attempt 3:")
find_all_1 = [
    [10, 936, 42, 989],
    [60, 907, 88, 935],
    [60, 936, 88, 963]
]
for coords in find_all_1:
    ymin, xmin, ymax, xmax = coords
    print(f"  {coords} - Center: x={int((xmin+xmax)/2)}, y={int((ymin+ymax)/2)}")

print("\nAttempt 4:")
find_all_2 = [
    [44, 915, 60, 936],
    [44, 940, 60, 956], 
    [37, 947, 60, 976]
]
for coords in find_all_2:
    ymin, xmin, ymax, xmax = coords
    print(f"  {coords} - Center: x={int((xmin+xmax)/2)}, y={int((ymin+ymax)/2)}")

print("\nOBSERVATIONS:")
print("1. Direct search consistently finds X at x≈960, y≈57")
print("2. Find all approach sees elements at different positions")
print("3. The 'expected' range of 940<xmin<980 might be too narrow")
print("4. Find all might be detecting different UI elements or splitting them differently")