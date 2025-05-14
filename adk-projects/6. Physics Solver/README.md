# 🧮 PhysicsSolver Agent

A lightweight Google ADK agent that evaluates numeric math and physics expressions using natural language input. Supports trigonometric functions (in degrees), logs, exponentials, and symbolic LaTeX formatting.

---

## ✅ Features

- Simple numeric math/physics expression evaluation
- Trigonometric functions auto-convert degrees to radians
- Clean step-by-step output with LaTeX formatting (via SymPy)
- Uses Gemini 2.0 Flash via Google ADK
- Designed for accurate function tool calling
- Minimal and fast – no external APIs required

---

## 🛠 Example

```bash
$ python3 agent.py
✅ Session 'session_state_demo_001' created for user 'user_state_demo'.

>>> User   Query: What is sin(30)?
<<< Agent Response: The value of sin(30) is approximately 0.5.
```

````

---

## ⚠️ Issue Faced

While integrating this agent, I kept encountering this error when running via `adk` CLI or `Runner`:

```
Failed to parse the parameter expression: 'str' of function numeric_solver for automatic function calling.
```

This happened **even though the function signature looked valid**:

```python
def numeric_solver(expression: str, precision: int = 3) -> dict:
```

---

## 🔍 Root Cause

The real issue was due to this line at the top of the file:

```python
from __future__ import annotations
```

This defers evaluation of type hints, turning `expression: str` into `'str'` (a string literal), which **breaks schema parsing** inside Google ADK’s function tool mechanism.

The ADK parser expects actual types (`str`, `int`, etc.), not deferred strings.

---

## ✅ Fix

I simply **removed** this line:

```diff
- from __future__ import annotations
```

Once removed, ADK was able to parse the function signature correctly, and the tool could be automatically invoked by Gemini during inference.

---

## 🧪 Supported Inputs

- `What is sin(45)?`
- `Evaluate sqrt(49) + log(100)`
- `What is (20**2 * sin(2*45)) / 9.8`

---

## 📦 Requirements

- Python 3.10+
- `google-adk`
- Optional: `sympy` and `pint` for LaTeX/units support

```bash
pip install google-adk sympy pint
```

---

## 📁 File Structure

```
.
├── agent.py               # Main entry point
├── numeric_solver_tool   # FunctionTool logic
└── README.md              # You're here
```

---

## 💡 Tip

Avoid asking:

> “What is sin(30 degrees)?”

Instead, say:

> “What is sin(30)?”

The tool already assumes degrees when evaluating trigonometric functions.

---

````
