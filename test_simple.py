"""
Simple test of the DC switch regex patterns
"""
import re

def test_patterns():
    # Test protective device patterns
    switch_pattern = r"\b(dc\s+switch|disconnect|breaker|fuse|protection|safety\s+switch)\b"
    between_pattern = r"\bbetween\b"
    
    # The problematic command from the user
    problematic_command = "add dc switch off between panel and inverter"
    
    print(f"Testing: '{problematic_command}'")
    print(f"  Matches switch pattern: {bool(re.search(switch_pattern, problematic_command.lower()))}")
    print(f"  Matches between pattern: {bool(re.search(between_pattern, problematic_command.lower()))}")
    
    # This should now be classified as add_protective_device instead of design
    add_pattern = r"\b(add|create|insert|place)\b"
    design_pattern = r"\b(design|build|create)\s+.*\b(system|kw|watt)"
    
    print(f"  Matches add pattern: {bool(re.search(add_pattern, problematic_command.lower()))}")
    print(f"  Matches design pattern: {bool(re.search(design_pattern, problematic_command.lower()))}")
    
    print("\nExpected behavior:")
    print("- Should match switch pattern: YES")
    print("- Should match between pattern: YES") 
    print("- Should match add pattern: YES")
    print("- Should match design pattern: NO")
    print("- Should be classified as: add_protective_device (confidence >0.9)")
    print("- Should NOT create 13 panels and inverter!")

if __name__ == "__main__":
    test_patterns()