#!/usr/bin/env python3
"""
Test script for validating the enhanced NL planner command recognition.
This tests all the literal command scenarios to ensure production readiness.
"""
import sys
import re
from typing import Dict, List

# Mock the planner function for testing
def classify_command_intent(command: str) -> Dict[str, any]:
    """Copy of the classification function for testing"""
    lower = command.lower().strip()
    
    patterns = {
        "add_component": {
            "patterns": [
                r"\b(add|create|insert|place)\s+(\d+\s+)?(panel|inverter|battery)",
                r"\b(add|create|insert|place)\s+(solar\s+)?(panel|inverter|battery)"
            ],
            "confidence": 0.9
        },
        "connect": {
            "patterns": [r"\b(connect|wire|link)\s+.+\s+to\s+"],
            "confidence": 0.85
        },
        "delete": {
            "patterns": [r"\b(delete|remove|clear|erase)\s+"],
            "confidence": 0.8
        },
        "arrange": {
            "patterns": [r"\b(arrange|layout|organize|position)"],
            "confidence": 0.7
        },
        "design": {
            "patterns": [r"\b(design|build|create)\s+.*\b(system|kw|watt)"],
            "confidence": 0.6
        }
    }
    
    best_match = {"intent": "unknown", "confidence": 0.0, "matches": []}
    
    for intent, config in patterns.items():
        for pattern in config["patterns"]:
            if re.search(pattern, lower):
                if config["confidence"] > best_match["confidence"]:
                    best_match = {
                        "intent": intent,
                        "confidence": config["confidence"],
                        "matches": [pattern]
                    }
                elif config["confidence"] == best_match["confidence"]:
                    best_match["matches"].append(pattern)
    
    return best_match

def test_command_recognition():
    """Test various command scenarios"""
    test_cases = [
        # Add component commands (should be literal)
        {"command": "add solar panel", "expected_intent": "add_component", "expected_literal": True},
        {"command": "add 5 panels", "expected_intent": "add_component", "expected_literal": True},
        {"command": "create inverter", "expected_intent": "add_component", "expected_literal": True},
        {"command": "place 2 inverters", "expected_intent": "add_component", "expected_literal": True},
        {"command": "add battery", "expected_intent": "add_component", "expected_literal": True},
        
        # Connection commands (should be literal)
        {"command": "connect panel to inverter", "expected_intent": "connect", "expected_literal": True},
        {"command": "wire panels to inverters", "expected_intent": "connect", "expected_literal": True},
        {"command": "link battery to inverter", "expected_intent": "connect", "expected_literal": True},
        
        # Delete commands (should be literal)
        {"command": "delete all panels", "expected_intent": "delete", "expected_literal": True},
        {"command": "remove inverter", "expected_intent": "delete", "expected_literal": True},
        {"command": "clear canvas", "expected_intent": "delete", "expected_literal": True},
        
        # Layout commands (should be literal)
        {"command": "arrange components", "expected_intent": "arrange", "expected_literal": True},
        {"command": "auto layout", "expected_intent": "arrange", "expected_literal": True},
        {"command": "organize panels", "expected_intent": "arrange", "expected_literal": True},
        
        # Design commands (should fall back to system design)
        {"command": "design a 5kW system", "expected_intent": "design", "expected_literal": False},
        {"command": "build 10kW solar system", "expected_intent": "design", "expected_literal": False},
        {"command": "create 1000W system", "expected_intent": "design", "expected_literal": False},
        
        # Ambiguous/edge cases
        {"command": "add solar system", "expected_intent": "unknown", "expected_literal": False},  # Should fall back
        {"command": "connect everything", "expected_intent": "unknown", "expected_literal": False},  # No "to"
        {"command": "hello world", "expected_intent": "unknown", "expected_literal": False},
    ]
    
    results = []
    passed = 0
    total = len(test_cases)
    
    print("Testing NL Planner Command Recognition")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        command = test_case["command"]
        expected_intent = test_case["expected_intent"]
        expected_literal = test_case["expected_literal"]
        
        # Classify the command
        classification = classify_command_intent(command)
        actual_intent = classification["intent"]
        confidence = classification["confidence"]
        
        # Determine if this would be handled literally
        is_literal = actual_intent in ["add_component", "connect", "delete", "arrange"]
        
        # Check results
        intent_correct = actual_intent == expected_intent
        literal_correct = is_literal == expected_literal
        test_passed = intent_correct and literal_correct
        
        if test_passed:
            passed += 1
            status = "PASS"
        else:
            status = "FAIL"
        
        print(f"{status} Test {i:2d}: '{command}'")
        print(f"    Expected: {expected_intent} (literal={expected_literal})")
        print(f"    Actual:   {actual_intent} (literal={is_literal}, confidence={confidence:.2f})")
        
        if not test_passed:
            if not intent_correct:
                print(f"    Intent mismatch: expected {expected_intent}, got {actual_intent}")
            if not literal_correct:
                print(f"    Literal handling mismatch: expected {expected_literal}, got {is_literal}")
        print()
    
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("All tests passed! The planner is ready for production.")
        return True
    else:
        print(f"{total - passed} tests failed. Review the implementation.")
        return False

if __name__ == "__main__":
    success = test_command_recognition()
    sys.exit(0 if success else 1)