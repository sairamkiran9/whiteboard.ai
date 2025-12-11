from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from hld_agent_canvas_integration import CanvasAwareHLDAgent

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = CanvasAwareHLDAgent()

@app.post("/api/analyze")
async def analyze_canvas(request: dict):
    """Analyze Excalidraw canvas and return suggestions"""
    canvas_data = request.get("canvas")
    context = request.get("context", "")

    # Save to temp file (or pass dict directly)
    import tempfile, json
    with tempfile.NamedTemporaryFile(mode='w', suffix='.excalidraw',
delete=False) as f:
        json.dump(canvas_data, f)
        temp_path = f.name

    # Analyze
    response = agent.analyze_canvas(temp_path, context)

    return response.model_dump()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time suggestions"""
    await websocket.accept()

    while True:
        data = await websocket.receive_json()

        # Analyze canvas
        # ... (similar to above)

        # Send back
        await websocket.send_json(response.model_dump())