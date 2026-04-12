# .agent/artifacts/calculator.py
#!/usr/bin/env python3
"""
A simple CLI calculator supporting basic arithmetic operations.
Uses argparse for CLI interface and type hints throughout.
Python 3.11+ compatible.

Security note: This is a standalone utility with no network exposure.
Input validation includes:
- Type coercion to float (prevents injection via string parsing)
- Division-by-zero protection
- Range checks for floating-point overflow (via Python's native handling)
"""

import argparse
import sys


def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


def subtract(a: float, b: float) -> float:
    """Subtract second number from first."""
    return a - b


def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    # Prevent NaN/Inf injection via overflow checks
    result = a * b
    if not (-1e308 <= result <= 1e308):
        raise OverflowError("Result exceeds representable range.")
    return result


def divide(a: float, b: float) -> float:
    """Divide first number by second. Raises ValueError on division by zero."""
    if b == 0:
        raise ValueError("Division by zero is not allowed.")
    
    # Prevent NaN/Inf injection via overflow checks
    result = a / b
    if not (-1e308 <= result <= 1e308):
        raise OverflowError("Result exceeds representable range.")
    return result


OPERATIONS = {
    "add": add,
    "sub": subtract,
    "mul": multiply,
    "div": divide,
}


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="A simple CLI calculator supporting basic arithmetic operations.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python calculator.py add 2.5 3      # → 5.50
  python calculator.py div 10 0       # → Error: Division by zero is not allowed.
""",
    )
    parser.add_argument(
        "operation",
        choices=OPERATIONS.keys(),
        help="Operation to perform (add, sub, mul, div)",
    )
    parser.add_argument("a", type=float, help="First operand")
    parser.add_argument("b", type=float, help="Second operand")

    return parser.parse_args(args)


def main(argv: list[str] | None = None) -> int:
    """Main entry point for CLI calculator."""
    try:
        parsed = parse_args(argv)
        
        # Validate inputs are finite numbers (prevents 'inf', 'nan' injection)
        if not (-1e308 <= parsed.a <= 1e308 and -1e308 <= parsed.b <= 1e308):
            raise ValueError("Operands must be finite real numbers.")
        
        result = OPERATIONS[parsed.operation](parsed.a, parsed.b)
        
        # Format output: integer if whole number, otherwise 2 decimal places
        formatted_result = (
            f"{int(result)}"
            if isinstance(result, float) and result.is_integer()
            else f"{result:.2f}"
        )
        print(formatted_result)
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except OverflowError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())