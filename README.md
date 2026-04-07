---
title: Llm Debug Gym
emoji: 🚀
colorFrom: yellow
colorTo: indigo
sdk: docker
app_port: 8000
pinned: false
license: mit
short_description: An OpenEnv-compliant RL gym for automated LLM debugging
---
# 🤖 LLM Debug Gym

**LLM Debug Gym** is a professional-grade Reinforcement Learning (RL) environment designed for training and evaluating Large Language Models (LLMs) on code debugging tasks. Built on the **OpenEnv** framework, it provides a stateful interface where an AI agent interacts with a buggy codebase, performs edits, and runs tests to verify its fixes in real-time.

---

## 🏗️ Architecture & Working

The project utilizes a **Client-Server architecture** to isolate the evaluation environment from the agent logic, ensuring a robust and reproducible testing ground.

1. **The Environment (Server)**: A FastAPI server running inside a Docker container. It manages the "Ground Truth"—buggy code, hidden unit tests, and the reward calculation logic.
2. **The Agent (Client)**: A Python script (`inference.py`) that communicates with the server via REST API. It uses the **Qwen-2.5-72B-Instruct** model to analyze feedback and generate logical fixes.

### The Interaction Sequence:
- **RESET**: The server initializes a specific task (e.g., a buggy Binary Search) and sends the initial code state and task description to the agent.
- **WRITE**: The agent processes the bug and returns a corrected Python code block.
- **TEST**: The server receives the code, executes it against a hidden test suite, and checks for regressions.
- **REWARD**: The server returns a reward of **0.0** for failure or **1.0** for a successful fix.

---

## 📋 Prerequisites

To run this project, ensure you have the following installed:
- **Python 3.10+**
- **[uv](https://github.com/astral-sh/uv)**: A high-performance Python package manager and resolver.
- **Docker Desktop**: Required for building and running the containerized environment.
- **Hugging Face API Token**: Required to access the LLM inference endpoints.

---

## 🚀 Step-by-Step Setup

### 1. Project Initialization
Clone the repository and install the synchronized virtual environment using `uv`:
```bash
git clone <your-repo-url>
cd LLM_debug_gym
# Install all dependencies and lock the environment
uv sync
```

### 2. Environment Configuration
Create a file named `.env` in the root directory. This allows the agent to authenticate with Hugging Face and locate your server:
```env
# Your Hugging Face Access Token
HF_TOKEN="your_hf_token_here"
# The LLM model used for debugging
MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
# Server URL:
# Use http://localhost:8000 for local development
# Use your https://<name>.hf.space for cloud/Space deployment
ENV_URL="http://localhost:8000"
```

---

## 💻 Execution Guide
**Run the requirements.txt file to install required dependencies:**
```bash
    uv install -r requirements.txt
```

### Mode A: Local Development
To run the system on your local machine without Docker:

1. **Start the Server**:
```bash
    uv run server
```
2. **Run the Agent** (in a separate terminal):
```bash
    uv run python inference.py
```

### Mode B: Docker Deployment (Production)
To mirror the cloud environment exactly as it runs on Hugging Face:

1. **Build the Image**:
```bash
    docker build -t debug-gym .
```
2. **Run the Container**:
```bash
    # Maps internal port 8000 to your local port 8000
    docker run -p 8000:8000 debug-gym
```

---

## 🛠️ Project Structure

We follow a modular Python package structure to ensure strictly compliant imports and "ready for multi-mode deployment" status:

- **`server/`**: The core environment package.
  - `__init__.py`: Marks the directory as a Python package.
  - `app.py`: The FastAPI entry point (contains the `main()` startup function).
  - `environment.py`: Defines the RL logic and reward system.
- **`tasks.py`**: A library of buggy Python functions and corresponding hidden test cases.
- **`inference.py`**: The agent logic that handles LLM prompting and API communication.
- **`Dockerfile`**: Configuration for the Python 3.12-slim production container.
- **`pyproject.toml`**: Metadata and dependency management, including the `server` entry point.

---

## 📝 License
This project is licensed under the MIT License.

---

## 📬 Contact & Collaboration

Created by **Hithesh Reddy**. I am a CSE student passionate about AI Safety and NLP.

* **Email:** [hitheshreddys2005@gmail.com]
* **LinkedIn:** [https://www.linkedin.com/in/hitheshreddys/]

*Currently open to research internships and AI/ML collaborations!*
