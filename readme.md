# Apnar Mentor AI 🧠

### Your Personal AI Mentor for Daily Progress, Discipline & Accountability

Apnar Mentor AI is a locally powered personal mentoring chatbot designed to help students stay productive, track daily responsibilities, reflect on unfinished tasks, and build better habits through meaningful conversations.

Instead of simply answering questions, Apnar Mentor AI aims to act like a supportive mentor who checks in on your day, asks what you accomplished, understands why certain tasks remain incomplete, and helps you plan your next steps.

---

## ✨ Key Features

### 💬 1. Natural AI Conversations
- Chat with an AI mentor through a web-based interface.
- Designed to support Bangla, Banglish, and English conversations.
- Provides practical, friendly, and encouraging responses.

### 📅 2. Daily Check-ins
- Review what you accomplished during the day.
- Reflect on completed and incomplete responsibilities.
- Build a consistent daily review habit.

### ✅ 3. To-Do Accountability
- Organize daily tasks and priorities.
- Identify unfinished tasks.
- Discuss obstacles that prevented task completion.
- Develop realistic plans for completing pending work.

### 🎯 4. Personalized Mentoring
- Ask follow-up questions about productivity challenges.
- Encourage honest self-reflection instead of empty motivation.
- Suggest actionable improvements based on available user context.

### 🖥️ 5. Local AI Inference
- Integrates with Ollama to run language models locally.
- Supports configurable models, such as Qwen 3.5 and Gemma 2, when installed and compatible.
- Reduces dependence on external hosted AI APIs.

### 🌐 6. Web-Based Interface
- Communicate with the mentor through a browser.
- Connect the frontend to a Python FastAPI backend.
- Keep the AI interaction layer separate from the user interface.

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend application logic |
| FastAPI | REST API and backend services |
| Ollama | Local language model runtime |
| Qwen 3.5 / Gemma 2 | Configurable local AI models |
| HTML, CSS, JavaScript or React | Frontend, depending on the implementation |
| Requests | Communication with the Ollama API |
| python-dotenv | Environment variable configuration |

*The exact frontend framework and additional dependencies depend on the project's current implementation.*

---

## 🏗️ How It Works

1. The user opens the web application.
2. The user sends a message or discusses daily tasks.
3. The frontend sends the message to the FastAPI backend.
4. The backend prepares the prompt and relevant conversation context.
5. Ollama processes the request using the configured local language model.
6. The backend returns the generated response to the frontend.
7. The user continues the conversation and receives mentoring guidance.

### Architecture

```text
                ┌─────────────────────┐
                │       User          │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │    Web Frontend      │
                └──────────┬──────────┘
                           │ HTTP Request
                           ▼
                ┌─────────────────────┐
                │   FastAPI Backend   │
                │                     │
                │ Prompt & Context    │
                │ Management          │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │   Ollama Runtime    │
                │                     │
                │ Local Language      │
                │ Model               │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ Generated Response  │
                └─────────────────────┘
```

---

## 🚀 Getting Started

### Prerequisites

Install the following software before running the application:

- Python 3.10 or newer, compatible with the project's dependencies.
- Ollama.
- A supported local language model.
- Node.js and npm if the frontend uses React or another Node-based toolchain.

### 1. Clone or Download the Project

If the project is hosted on GitHub:

```bash
git clone YOUR_REPOSITORY_URL
cd 3d_mentor_app_gemini
```

Alternatively, download the project ZIP and extract it.

### 2. Install Python Dependencies

Open a terminal in the project directory:

```bash
python -m venv .venv
```

Activate the environment on Windows:

```cmd
.venv\Scripts\activate
```

Install the project's dependencies:

```bash
pip install -r requirements.txt
```

If a `requirements.txt` file is not present, install the dependencies listed in the project configuration.

### 3. Install and Start Ollama

Download Ollama from:

https://ollama.com/download

Verify that it is installed:

```bash
ollama --version
```

Pull a supported model:

```bash
ollama pull qwen3.5:2b
```

Alternatively, use Gemma 2 if that is the model selected for your application:

```bash
ollama pull gemma2:2b
```

Test the model directly:

```bash
ollama run qwen3.5:2b
```

Type a message and verify that the model generates a response before proceeding.

### 4. Configure Environment Variables

Create a `.env` file in the backend project directory:

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen3.5:2b
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_TIMEOUT=180
```

If using Gemma 2, change the model setting:

```env
OLLAMA_MODEL=gemma2:2b
```

Ensure the configured model is installed in Ollama.

**Important:** Never commit secrets or private credentials to a public repository.

### 5. Start the FastAPI Backend

Run:

```bash
python -m uvicorn main:app --reload
```

The backend should become available at:

- API base: http://127.0.0.1:8000
- Interactive API documentation: http://127.0.0.1:8000/docs

Keep the backend terminal open while testing the application.

### 6. Start the Frontend

If the frontend has its own directory containing `package.json`, open a separate terminal and navigate to that directory.

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Open the local URL printed in the terminal.

*The exact command and URL depend on the frontend framework and its configuration.*

---

## 🧪 Testing and Troubleshooting

### Test Ollama Independently

Before debugging the website, confirm that the model responds directly:

```bash
ollama run qwen3.5:2b
```

If this works, test the FastAPI backend separately through its API documentation.

### Common Problems

| Problem | What to Check |
|---|---|
| Ollama connection refused | Confirm that Ollama is running and the configured URL is correct. |
| Model not found | Run `ollama list` and verify the model name. |
| Empty AI response | Inspect the Ollama API response, including `content`, `thinking`, and completion status. |
| Website receives no response | Check browser developer tools, API URL, request payload, and backend logs. |
| CORS error | Configure FastAPI CORS middleware for the actual frontend origin. |
| Backend repeatedly restarts | Check file changes, startup errors, and development reload behavior. |
| Slow responses | Check model size, available RAM, prompt length, and generation settings. |

### Useful Diagnostic Commands

```bash
ollama list
ollama ps
```

Check the API documentation:

http://127.0.0.1:8000/docs

---

## 🔒 Privacy and Security

Apnar Mentor AI is designed around local model inference through Ollama. When the application is configured to use a local model, prompts can be processed on the user's machine rather than sent to a hosted LLM provider.

However, local inference alone does not guarantee complete privacy. Frontend telemetry, logs, external integrations, or other application components may still transmit or store information. Review the application's actual data flows before using sensitive personal information.

---

## 🗺️ Future Improvements

- [ ] Persistent daily task management.
- [ ] Automatic daily check-in reminders.
- [ ] Task completion tracking and progress summaries.
- [ ] Long-term conversation memory.
- [ ] Personalized mentoring based on previous progress.
- [ ] Better Bangla and Banglish response consistency.
- [ ] Improved handling of model thinking and empty responses.
- [ ] Daily, weekly, and monthly productivity reports.
- [ ] Configurable mentoring styles and goals.
- [ ] Automated tests for backend and frontend integration.

---

## 🎯 Project Goal

The goal of Apnar Mentor AI is to make personal accountability more accessible by combining local AI with practical daily planning and reflection.

It is designed to encourage users to ask themselves:

- What did I accomplish today?
- Which tasks remain incomplete?
- Why did I struggle to finish them?
- What can I change tomorrow?
- What is the next small action I can take?

The objective is not just to get more tasks done, but to build consistency, self-awareness, and better decision-making over time.

---

## 🤝 Contributing

Contributions, suggestions, and bug reports are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Make your changes.
4. Test the application.
5. Submit a pull request describing your improvements.

---

## 📄 License

Choose and add an appropriate open-source license before distributing the project publicly.

---

**Apnar Mentor AI — Reflect on today. Improve tomorrow.**
