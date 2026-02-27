---
applyTo: "**/*.py"
description: "Python coding conventions and guidelines for this repository."
---

# Python Coding Conventions

## Python-Specific Instructions

- Write clear, concise comments that explain the *why*, not just the *what*.
- Use descriptive names for variables, functions, and classes that convey intent.
- Add type hints to all function signatures (parameters and return types).
- Write PEP 257-compliant docstrings for all public modules, classes, and functions.

## General Instructions

- Prioritize readability over cleverness; code is read far more often than it is written.
- Include inline comments to explain non-obvious algorithms or business logic.
- Write maintainable code by keeping functions small and focused on a single responsibility.
- Account for edge cases explicitly and document any known limitations.
- Use exception handling to manage errors gracefully; avoid bare `except` clauses.

## Code Style and Formatting

- Follow [PEP 8](https://peps.python.org/pep-0008/) for all style decisions.
- Use 4 spaces for indentation; never use tabs.
- Limit all lines to a maximum of 88 characters (PEP 8 with Black's line-length extension).
- Place module-level docstrings at the top of each file, immediately after any `__future__` imports.
- Place class and function docstrings immediately after the `def` or `class` statement.

## Edge Cases and Testing

- Write unit tests for every public function, including happy-path and failure cases.
- Test edge cases explicitly: empty inputs, boundary values, `None`, and unexpected types.
- Use `pytest` and organise tests under a `tests/` directory that mirrors the source layout.
- Mock external dependencies (network calls, file I/O, system clock) in unit tests.

## Example of Proper Documentation

```python
from typing import Optional


def calculate_discount(price: float, discount_rate: float) -> Optional[float]:
    """Calculate the discounted price for a given item.

    Applies a percentage discount to the original price and returns the
    final price. Returns None if the inputs are invalid.

    Args:
        price: The original price of the item. Must be non-negative.
        discount_rate: The discount percentage as a decimal (e.g. 0.1 for 10%).
                       Must be between 0.0 and 1.0 inclusive.

    Returns:
        The discounted price, or None if either argument is out of range.

    Examples:
        >>> calculate_discount(100.0, 0.1)
        90.0
        >>> calculate_discount(-5.0, 0.1)  # invalid price
        None
    """
    if price < 0 or not (0.0 <= discount_rate <= 1.0):
        return None
    return price * (1 - discount_rate)
```
