from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import pytz
from trial_document_search.routes import routes
app = FastAPI()

# Set Mumbai timezone (IST)
mumbai_tz = pytz.timezone("Asia/Kolkata")

# Store the server start time in IST
server_start_time = datetime.now(mumbai_tz).strftime("%Y-%m-%d %H:%M:%S %Z")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

app.include_router(routes.router, prefix="/api/v1/ml", tags=["api"])

@app.get("/")
async def root():
    print(f"Server started at: {server_start_time}")
    return {
        "message": "Slices Clinical Trial Service Running",
        "server_started_at": server_start_time
    }
