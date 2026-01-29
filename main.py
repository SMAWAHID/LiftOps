import uuid
import logging
import os
import stripe
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.app.schemas.api import PipelineRequest, PipelineResponse, ErrorResponse
from backend.app.schemas.auth import User, UserCreate, LoginRequest, SocialLoginRequest
from backend.app.core.users import user_repo
from backend.app.agents.router import RouterAgent
from backend.app.agents.planner import PlannerAgent
from backend.app.agents.executor import ExecutorAgent
from backend.app.agents.validator import ValidatorAgent
from backend.app.core.history import HistoryRepository

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("antigravity")

# Load environment variables
load_dotenv()

# Stripe Setup
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "sk_test_PLACEHOLDER")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "pk_test_PLACEHOLDER")
stripe.api_key = STRIPE_SECRET_KEY

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


@app.post("/api/social-login")
async def social_login(req: SocialLoginRequest):
    # 1. Check if user exists
    user = user_repo.get_by_email(req.email)
    
    if not user:
        # 2. Register if new. Generate random password for social users.
        try:
            random_pw = str(uuid.uuid4())
            new_user_in = UserCreate(
                email=req.email, 
                full_name=req.full_name or "Social User", 
                password=random_pw
            )
            user = user_repo.create_user(new_user_in)
        except ValueError as e:
            # Race condition or other error
            raise HTTPException(status_code=400, detail=str(e))
            
    # 3. Create Session Token
    token = f"jwt-mock-{user['id']}"
    return {
        "access_token": token, 
        "token_type": "bearer", 
        "user": user
    }


@app.get("/api/config/stripe-key")
async def get_stripe_key():
    return {"publishableKey": STRIPE_PUBLISHABLE_KEY}


class PaymentIntentRequest(BaseModel):
    items: list = []
    email: str


@app.post("/api/create-payment-intent")
async def create_payment_intent(request: PaymentIntentRequest):
    try:
        # Calculate order amount (Commander Plan - $99.00)
        # In a real app, look up price by item ID
        amount = 9900  # cents

        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="usd",
            automatic_payment_methods={"enabled": True},
            metadata={"email": request.email, "target_tier": "commander"},
        )
        return {"clientSecret": intent.client_secret}
    except Exception as e:
        logger.error(f"Stripe Error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/verify-payment")
async def verify_payment(data: dict = Body(...)):
    payment_intent_id = data.get("paymentIntentId")
    email = data.get("email") # fallback if not in metadata

    if not payment_intent_id:
        raise HTTPException(status_code=400, detail="Missing paymentIntentId")

    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        if intent.status == "succeeded":
            # Payment success, upgrade user
            user_email = intent.metadata.get("email") or email
            if not user_email:
                 raise HTTPException(status_code=400, detail="Could not identify user email from payment")
            
            updated_user = user_repo.upgrade_tier(user_email, "commander")
            if not updated_user:
                # If user not found, maybe create or log error? For now 404.
                raise HTTPException(status_code=404, detail="User found for upgrade")
                
            return {"status": "success", "user": updated_user}
        else:
            return {"status": "pending", "details": f"Payment status is {intent.status}"}
            
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
