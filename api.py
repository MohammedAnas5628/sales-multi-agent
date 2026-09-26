import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware

from langgraph.types import Command

from main import app as sales_workflow
from auth.routes import router as auth_router


# ============================================================
# ENVIRONMENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Sales Multi-Agent API",
    version="1.0.0",
)


# ============================================================
# SESSION MIDDLEWARE
# ============================================================

SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")

if not SESSION_SECRET_KEY:
    raise ValueError(
        "SESSION_SECRET_KEY not found in .env"
    )

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    https_only=False,  # Local development
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# AUTH ROUTES
# ============================================================

app.include_router(
    auth_router,
)


# ============================================================
# REQUEST MODEL
# ============================================================

class SalesRequest(BaseModel):

    user_request: str = Field(
        min_length=1,
        description="Lead search request.",
    )

    lead_limit: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum number of leads to process.",
    )


# ============================================================
# APPROVAL MODEL
# ============================================================

class ApprovalRequest(BaseModel):

    action: str

    email_index: int | None = None

    subject: str | None = None

    body: str | None = None


# ============================================================
# HELPER
# ============================================================

def get_logged_in_user_email(
    request: Request,
) -> str:

    user_email = request.session.get(
        "user_email"
    )

    if not user_email:

        raise HTTPException(
            status_code=401,
            detail="Google login required.",
        )

    return user_email


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "message": "Sales Multi-Agent API is running."
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "ok"
    }


# ============================================================
# CURRENT USER
# ============================================================

@app.get("/auth/me")
def get_current_user(
    request: Request,
):

    user_email = request.session.get(
        "user_email"
    )

    if not user_email:

        return {
            "authenticated": False,
            "user_email": None,
        }

    return {
        "authenticated": True,
        "user_email": user_email,
    }


# ============================================================
# START SALES WORKFLOW
# ============================================================

@app.post("/run-sales")
def run_sales(
    payload: SalesRequest,
    request: Request,
):

    user_email = get_logged_in_user_email(
        request
    )

    # --------------------------------------------------------
    # Generate unique LangGraph thread
    # --------------------------------------------------------

    thread_id = str(
        uuid.uuid4()
    )

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    # --------------------------------------------------------
    # Initial state
    # --------------------------------------------------------

    initial_state = {

        "user_request":
            payload.user_request.strip(),

        "user_email":
            user_email,

        "lead_limit":
            payload.lead_limit,

        "status":
            "started",
    }

    # --------------------------------------------------------
    # Start workflow
    # --------------------------------------------------------

    try:

        result = sales_workflow.invoke(
            initial_state,
            config=config,
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Workflow failed: {str(e)}",
        )

    # --------------------------------------------------------
    # Check for Human-in-the-Loop interrupt
    # --------------------------------------------------------

    interrupts = result.get(
        "__interrupt__"
    )

    if interrupts:

        interrupt_value = (
            interrupts[0].value
            if interrupts
            else None
        )

        return {

            "thread_id":
                thread_id,

            "status":
                "pending_approval",

            "lead_limit":
                payload.lead_limit,

            "approval":
                interrupt_value,
        }

    # --------------------------------------------------------
    # Completed without interrupt
    # --------------------------------------------------------

    final_state = (
        sales_workflow.get_state(config)
    )

    values = (
        final_state.values or {}
    )

    response = {

        "thread_id":
            thread_id,

        "status":
            values.get(
                "status",
                "completed",
            ),

        "lead_limit":
            values.get(
                "lead_limit",
                payload.lead_limit,
            ),

        "lead_count":
            len(
                values.get(
                    "leads",
                    [],
                )
            ),

        "qualified_count":
            len(
                values.get(
                    "qualified_leads",
                    [],
                )
            ),

        "email_count":
            len(
                values.get(
                    "emails",
                    [],
                )
            ),
    }

    excel_file = values.get(
        "excel_file"
    )

    if excel_file:

        response["excel_file"] = (
            excel_file
        )

        response["excel_download_url"] = (
            f"/exports/{Path(excel_file).name}"
        )

    return response


# ============================================================
# APPROVAL / RESUME WORKFLOW
# ============================================================

@app.post(
    "/run-sales/{thread_id}/approval"
)
def handle_approval(
    thread_id: str,
    payload: ApprovalRequest,
    request: Request,
):

    user_email = get_logged_in_user_email(
        request
    )

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    # --------------------------------------------------------
    # Verify workflow ownership
    # --------------------------------------------------------

    try:

        saved_state = (
            sales_workflow.get_state(
                config
            )
        )

    except Exception as e:

        raise HTTPException(
            status_code=404,
            detail=f"Workflow not found: {str(e)}",
        )

    saved_values = (
        saved_state.values or {}
    )

    stored_user_email = (
        saved_values.get(
            "user_email"
        )
    )

    if stored_user_email != user_email:

        raise HTTPException(
            status_code=403,
            detail=(
                "This workflow does not belong "
                "to the logged-in user."
            ),
        )

    # --------------------------------------------------------
    # Validate action
    # --------------------------------------------------------

    action = (
        payload.action
        .strip()
        .lower()
    )

    allowed_actions = {
        "approve",
        "edit",
        "reject",
    }

    if action not in allowed_actions:

        raise HTTPException(
            status_code=400,
            detail=(
                "Action must be approve, "
                "edit, or reject."
            ),
        )

    # --------------------------------------------------------
    # Build resume payload
    # --------------------------------------------------------

    resume_data = {

        "action":
            action,

        "email_index":
            payload.email_index,

        "subject":
            payload.subject,

        "body":
            payload.body,
    }

    # --------------------------------------------------------
    # Resume LangGraph
    # --------------------------------------------------------

    try:

        result = sales_workflow.invoke(
            Command(
                resume=resume_data
            ),
            config=config,
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Approval failed: {str(e)}",
        )

    # --------------------------------------------------------
    # Check if another interrupt exists
    # --------------------------------------------------------

    interrupts = result.get(
        "__interrupt__"
    )

    if interrupts:

        interrupt_value = (
            interrupts[0].value
            if interrupts
            else None
        )

        return {

            "thread_id":
                thread_id,

            "status":
                "pending_approval",

            "approval":
                interrupt_value,
        }

    # --------------------------------------------------------
    # Final state
    # --------------------------------------------------------

    final_state = (
        sales_workflow.get_state(
            config
        )
    )

    values = (
        final_state.values or {}
    )

    response = {

        "thread_id":
            thread_id,

        "status":
            values.get(
                "status",
                "completed",
            ),

        "approval_status":
            values.get(
                "approval_status"
            ),

        "lead_limit":
            values.get(
                "lead_limit"
            ),

        "lead_count":
            len(
                values.get(
                    "leads",
                    [],
                )
            ),

        "qualified_count":
            len(
                values.get(
                    "qualified_leads",
                    [],
                )
            ),

        "email_count":
            len(
                values.get(
                    "emails",
                    [],
                )
            ),
    }

    excel_file = values.get(
        "excel_file"
    )

    if excel_file:

        response["excel_file"] = (
            excel_file
        )

        response["excel_download_url"] = (
            f"/exports/{Path(excel_file).name}"
        )

    return response


# ============================================================
# GET WORKFLOW STATUS
# ============================================================

@app.get(
    "/run-sales/{thread_id}"
)
def get_sales_status(
    thread_id: str,
    request: Request,
):

    user_email = get_logged_in_user_email(
        request
    )

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    try:

        saved_state = (
            sales_workflow.get_state(
                config
            )
        )

    except Exception as e:

        raise HTTPException(
            status_code=404,
            detail=f"Workflow not found: {str(e)}",
        )

    values = (
        saved_state.values or {}
    )

    # --------------------------------------------------------
    # Verify ownership
    # --------------------------------------------------------

    stored_user_email = (
        values.get(
            "user_email"
        )
    )

    if stored_user_email != user_email:

        raise HTTPException(
            status_code=403,
            detail=(
                "This workflow does not belong "
                "to the logged-in user."
            ),
        )

    # --------------------------------------------------------
    # Return status
    # --------------------------------------------------------

    return {

        "thread_id":
            thread_id,

        "status":
            values.get(
                "status"
            ),

        "approval_status":
            values.get(
                "approval_status"
            ),

        "lead_limit":
            values.get(
                "lead_limit"
            ),

        "lead_count":
            len(
                values.get(
                    "leads",
                    [],
                )
            ),

        "qualified_count":
            len(
                values.get(
                    "qualified_leads",
                    [],
                )
            ),

        "researched_count":
            len(
                values.get(
                    "researched_leads",
                    [],
                )
            ),

        "email_count":
            len(
                values.get(
                    "emails",
                    [],
                )
            ),

        "excel_file":
            values.get(
                "excel_file"
            ),
    }


# ============================================================
# EXCEL DOWNLOAD
# ============================================================

@app.get(
    "/exports/{filename}"
)
def download_export(
    filename: str,
):

    export_dir = (
        BASE_DIR
        / "data"
        / "exports"
    )

    file_path = (
        export_dir
        / filename
    )

    # Prevent path traversal
    if file_path.resolve().parent != export_dir.resolve():

        raise HTTPException(
            status_code=400,
            detail="Invalid filename.",
        )

    if not file_path.exists():

        raise HTTPException(
            status_code=404,
            detail="Export file not found.",
        )

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type=(
            "application/"
            "vnd.openxmlformats-officedocument"
            ".spreadsheetml.sheet"
        ),
    )