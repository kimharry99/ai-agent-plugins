---
globs: "*.py"
description: "Strict OOP conventions — all methods and variables must live inside classes"
---

# Strict OOP

This project enforces strict object-oriented design in Python code.

Rules:
- All functions must be defined as methods inside a class. No module-level functions.
- All variables (except constants) must be defined inside a class (as instance or class attributes). No module-level variables.
- Module-level constants (`UPPER_SNAKE_CASE`) are allowed.
- Module-level imports are allowed (they are not variables).

Rationale: Module-level functions add callable names directly to the module's global namespace. Defining behavior as methods keeps it under the class that owns that behavior, making ownership, discovery, and naming boundaries explicit.
