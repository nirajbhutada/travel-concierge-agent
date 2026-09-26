# ✈️ Travel Concierge Agent

An intelligent, multi-turn AI travel assistant built with the **Google Agent Development Kit (ADK)** and powered by **Gemini 2.5 Flash**. The agent helps travelers discover destinations, generate custom travel postcards & video clips, convert currencies, search nearby attractions, store travel facts in Firestore, and remember user preferences across sessions.

![Travel Concierge Agent Demo](./demo.gif)

---

## 🌟 Capabilities & Features

Based strictly on the code implemented in `app/`:

- **🧠 Cross-Session Memory Bank**: Automatically preloads and remembers user preferences, facts, and dietary restrictions across conversations using ADK Memory Service.
- **🖼️ Multimodal Postcard Image Generation**: Generates high-quality travel postcard photos using `gemini-3.1-flash-lite-image`, uploading the binary directly to Google Cloud Storage.
- **🎥 Destination Video Generation**: Generates short travel video clips using `gemini-omni-flash-preview` (in the `global` region), storing artifacts in the ADK session and uploading to Cloud Storage.
- **🗄️ Firestore Destination Database**: Queries travel destinations by country or budget (`search_destinations`) and saves new destination records (`add_destination`) in Google Cloud Firestore.
- **🗺️ Maps & Geolocation Integration**: Converts location addresses into geographic coordinates (`geocode_address`) and finds nearby attractions (`find_nearby_places`) using Google Maps APIs.
- **💱 Live Currency Conversion**: Converts travel budget figures between foreign currencies and USD using real-time exchange rates (`convert_currency`).
- **🧮 Python Code Execution Sandbox**: Safely executes Python calculations for complex travel budgets and split costs via `AgentEngineSandboxCodeExecutor`.
- **📱 A2UI Rich UI Components**: Emits flat, structured A2UI JSON components (`Card`, `Column`, `Row`, `Text`, `Image`) rendered directly in the chat interface.

---

## 🏗️ Architecture & Technology Stack

| Component | Technology / Service |
| :--- | :--- |
| **Agent Framework** | Google Agent Development Kit (`google-adk`) |
| **Reasoning Model** | `gemini-2.5-flash` |
| **Image Generation** | `gemini-3.1-flash-lite-image` |
| **Video Generation** | `gemini-omni-flash-preview` |
| **Database** | Google Cloud Firestore |
| **Media Storage** | Google Cloud Storage |
| **UI Protocol** | A2UI (`a2ui_callback`, `A2uiSchemaManager`) |
| **Frontend UI** | FastAPI Proxy + Plain HTML5/CSS3 Chat Interface |

---

## 🛠️ Local Development & Quick Start

### Prerequisites
- Python 3.11+
- `uv` package manager installed

### 1. Install Dependencies
```bash
uv sync
```

### 2. Set Up Environment Variables
Create a `.env` file in the project root:
```bash
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_MAPS_API_KEY=your-maps-api-key
```

### 3. Run the ADK Agent Playground
To run the local ADK developer playground:
```bash
uv run adk web . --port 8080 --reload_agents
```

### 4. Run the Web Frontend Locally
Navigate to the `frontend/` directory and launch the FastAPI server:
```bash
cd frontend
pip install -r requirements.txt
export AGENT_ENGINE_RESOURCE_NAME="projects/your-project-id/locations/us-east1/reasoningEngines/your-engine-id"
export AGENT_DIRECTORY="app"
python main.py
```

---

## 🧪 Testing

Run unit and integration test suites using `pytest`:
```bash
uv run pytest tests/unit tests/integration
```
