import uuid
import logging
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.app.schemas.api import PipelineRequest, PipelineResponse, ErrorResponse
from backend.app.schemas.auth import User, UserCreate, LoginRequest
from backend.app.core.users import user_repo
from backend.app.agents.router import RouterAgent
from backend.app.agents.planner import PlannerAgent
from backend.app.agents.executor import ExecutorAgent
from backend.app.agents.validator import ValidatorAgent
from backend.app.core.history import HistoryRepository

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("antigravity")

app = FastAPI(title="Antigravity Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Agents
router_agent = RouterAgent()
planner_agent = PlannerAgent()
executor_agent = ExecutorAgent()
validator_agent = ValidatorAgent()
history_repo = HistoryRepository()

@app.get("/api/antigravity/history")
async def get_history():
    return history_repo.get_all()

@app.get("/api/antigravity/history")
async def get_history():
    return history_repo.get_all()

# --- AUTHENTICATION ---

@app.post("/api/register", response_model=User)
async def register(user_in: UserCreate):
    try:
        return user_repo.create_user(user_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/login")
async def login(creds: LoginRequest):
    user = user_repo.authenticate(creds.username, creds.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # In a real app, sign a JWT here. For now, return a session object.
    token = f"jwt-mock-{user['id']}"
    return {
        "access_token": token, 
        "token_type": "bearer", 
        "user": user
    }

@app.get("/api/me", response_model=User)
async def get_current_user(token: str):
    # Mock token validation: extract ID from "jwt-mock-{id}"
    try:
        if not token.startswith("jwt-mock-"):
            raise HTTPException(status_code=401, detail="Invalid token")
        user_id = token.replace("jwt-mock-", "")
        # In a real DB we'd fetch by ID. Here we scan (MVP)
        users = user_repo._load()
        for u in users:
            if u["id"] == user_id:
                return u
        raise HTTPException(status_code=404, detail="User not found")
    except Exception:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


@app.post("/api/upgrade")
async def upgrade_tier(request: dict):
    # Simulated Webhook from Stripe
    email = request.get("email")
    if not email:
         raise HTTPException(status_code=400, detail="Email required")
    
    updated_user = user_repo.upgrade_tier(email, "commander")
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "success", "user": updated_user}


@app.post("/api/antigravity/run", response_model=PipelineResponse)
async def run_pipeline(request: PipelineRequest):
    request_id = str(uuid.uuid4())
    logger.info(f"[{request_id}] Pipeline started.")
    
    response = PipelineResponse(request_id=request_id)
    
    try:
        # 1. Router
        logger.info(f"[{request_id}] Running Router...")
        router_out = router_agent.run(request.input)
        response.router = router_out
        
        # 2. Planner
        logger.info(f"[{request_id}] Running Planner...")
        planner_out = planner_agent.run(router_out)
        response.planner = planner_out
        
        # 3. Executor
        logger.info(f"[{request_id}] Running Executor...")
        executor_out = executor_agent.run(planner_out)
        response.executor = executor_out
        
        # 4. Validator
        logger.info(f"[{request_id}] Running Validator...")
        validator_out = validator_agent.run(executor_out)
        response.validator = validator_out
        
        # Save to History
        history_repo.save_entry(response.model_dump())

        return response

    except Exception as e:
        logger.error(f"[{request_id}] Error: {str(e)}")
        # Ideally capture stage, simplified here
        response.error = ErrorResponse(
            stage="request", 
            error_type="InternalServerError", 
            message=str(e)
        )
        return response

# Serve Static Files (UI)
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
