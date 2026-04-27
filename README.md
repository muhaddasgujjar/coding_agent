# 🚀 Cursor MVP (Self-Healing Local Setup)

An immensely powerful, fully-local, dual-mode Auto-Agent IDE built to replicate the Cursor and Visual Studio Code experience utilizing **React, FastAPI, and LangGraph**. 

It provides an unparalleled standalone Desktop-like environment allowing you to bind natively into any of your local workspace folders. 

## ⚡ Features

### 1. 🧠 Dynamic Dual-Mode AI Engine 
The Agent intelligently maps routing out of the box dynamically via a Turing-Complete LangGraph Workflow:
*   **🗣️ Conversational (Generative) Mode:** Works flawlessly like ChatGPT. You can ask standard development and theory questions organically, and the system intelligently strips out background execution scripts returning purely textual insights.
*   **💻 Agentic (Execution) Mode:** Capable of spinning up automated sandbox instances dynamically! Ask the bot to structure, create, read, review, or debug entire Python frameworks natively. 

### 2. 🗂️ Native Workspace Injector (`os.chdir`)
Utilizing a hidden backend native Tkinter overlay, binding standard directories into memory is instantly possible! Upon launching the IDE, click **"Open Workspace Folder"** and link any directory dynamically from your file explorer. File tree crawling adapts and injects relative routing logic recursively on the fly!

### 3. 🛡️ Self-Healing Error Execution 
If the agent triggers a crash while autonomously developing a script (e.g. encountering `ModuleNotFound` exceptions), the ReAct LLM automatically analyzes its own output logic streams, uses pip dependencies autonomously, fixes the execution environment dynamically, and rebuilds the files iteratively. 

## 🔧 Technology Stack

- **Frontend:** React + Vite, Tailwind CSS v4, Monaco Web Editor (`@monaco-editor/react`), Lucide Icons.
- **Backend:** Python + FastAPI 
- **AI Core:** LangGraph (StateGraph Engine) + Groq Cloud Platform (`llama-3.3-70b-versatile`).
- **File Bridge:** `os`, Subprocess manipulation (`Python.exe`), Native `tkinter`.

## 🚀 Quickstart Guide

1. Ensure both **Node.js** and **Python** are globally installed.
2. Initialize dependencies for both frontend and backend:
   ```bash
   # Install React Client Dependencies
   cd client
   npm install

   # Setup Backend Python Agent Variables
   cd ../server
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Set your Groq LLM Key in a `.env` file within the `server/` directory:
   ```env
   GROQ_API_KEY=your_key_here
   ```
4. Double-Click `.\start_dev.bat` inside the root folder dynamically! 

*Note: The Dev server intelligently manages process-locking gracefully. Ghost Python ports are proactively killed inside the batch pipeline directly preventing `Errno 10048` lockups securely!*
