# 🧠 NeuroSymbolic Math Solver

A **Neuro-Symbolic AI system** that combines the power of Large Language Models with **exact symbolic computation** to solve mathematical problems with **100% accuracy and zero hallucination**.

---

## 🚀 Overview

Traditional LLMs (like Gemini/GPT) are great at understanding language but often fail at **precise mathematical reasoning**.  

This project solves that problem by separating:

- 🧠 **Understanding (Neural)** → handled by LLM  
- 🔢 **Computation (Symbolic)** → handled by math engines  

---

## ⚙️ Key Idea

> **LLM never performs calculations.**

Instead, it:
1. Parses the question → structured JSON  
2. Sends it to symbolic engines  
3. Explains the verified result  

---

## 🏗️ Architecture

User Query
↓
LLM (Parser - Gemini)
↓
Structured JSON
↓
Symbolic Router
↓
+-------------------------------+
| SymPy | Matplotlib | Z3 |
+-------------------------------+
↓
Result Verifier
↓
LLM (Explainer)
↓
Gradio UI

---

## ✨ Features

✔ Solve algebraic equations  
✔ Perform differentiation & integration  
✔ Evaluate limits  
✔ Taylor series expansion  
✔ Factorization & expansion  
✔ Function plotting  
✔ Identity verification (using Z3)  
✔ Step-by-step explanations  
✔ Graph visualization  
