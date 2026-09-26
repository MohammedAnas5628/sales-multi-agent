import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from langgraph.checkpoint.sqlite import SqliteSaver


# ============================================================
# ENVIRONMENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(
    BASE_DIR / ".env"
)

# Safer checkpoint deserialization
os.environ.setdefault(
    "LANGGRAPH_STRICT_MSGPACK",
    "true",
)


# ============================================================
# CHECKPOINT DATABASE
# ============================================================

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

CHECKPOINT_DB = DATA_DIR / "langgraph_checkpoints.sqlite"


# ============================================================
# SQLITE CONNECTION
# ============================================================

connection = sqlite3.connect(
    str(CHECKPOINT_DB),
    check_same_thread=False,
)


# ============================================================
# LANGGRAPH CHECKPOINTER
# ============================================================

checkpointer = SqliteSaver(
    connection
)

# Creates the required tables automatically.
checkpointer.setup()


print(
    f"LangGraph checkpoint database: {CHECKPOINT_DB}"
)