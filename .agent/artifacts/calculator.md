# .agent/artifacts/calculator.md

## CLI Calculator Summary

A secure, standalone Python CLI calculator supporting basic arithmetic operations.

### Features
- Supports: `add`, `sub`, `mul`, `div`
- Input validation:
  - Type coercion to float (prevents string injection)
  - Range checks for finite numbers (blocks `inf`/`nan`)
  - Division-by-zero protection
  - Overflow detection for large results
- Output formatting: integers shown without decimals; others with 2 decimal places

### Usage Examples