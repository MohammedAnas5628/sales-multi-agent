import os
import threading
from pathlib import Path

from dotenv import load_dotenv
from apify_client import ApifyClient


# ============================================================
# ENVIRONMENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


# ============================================================
# CUSTOM EXCEPTION
# ============================================================

class ApifyAllTokensFailed(Exception):
    """
    Raised when all configured Apify tokens have failed
    because of authentication, quota, rate-limit, or
    availability problems.
    """

    pass


# ============================================================
# APIFY TOKEN MANAGER
# ============================================================

class ApifyTokenManager:

    def __init__(self):

        self.tokens = []

        # Load tokens in strict order:
        # 1 -> 2 -> 3

        for index in range(1, 4):

            token = os.getenv(
                f"APIFY_API_TOKEN_{index}"
            )

            if token:

                self.tokens.append(
                    {
                        "index": index,
                        "token": token.strip(),
                    }
                )

        if not self.tokens:

            # Backward compatibility for old .env
            legacy_token = os.getenv(
                "APIFY_API_TOKEN"
            )

            if legacy_token:

                self.tokens.append(
                    {
                        "index": 1,
                        "token": legacy_token.strip(),
                    }
                )

        if not self.tokens:

            raise ValueError(
                "No Apify API tokens found. "
                "Add APIFY_API_TOKEN_1, "
                "APIFY_API_TOKEN_2, and "
                "APIFY_API_TOKEN_3 to .env."
            )

        # Tokens that are known to be unavailable
        self.disabled_tokens = set()

        # Protect shared state because Maps/email
        # operations may run concurrently.
        self.lock = threading.Lock()

        print(
            f"[Apify] Loaded {len(self.tokens)} token(s)."
        )

    # ========================================================
    # GET AVAILABLE TOKENS
    # ========================================================

    def _get_available_tokens(self):

        with self.lock:

            return [
                item
                for item in self.tokens
                if item["index"]
                not in self.disabled_tokens
            ]

    # ========================================================
    # MARK TOKEN FAILED
    # ========================================================

    def _disable_token(
        self,
        token_index: int,
    ):

        with self.lock:

            self.disabled_tokens.add(
                token_index
            )

        print(
            f"[Apify] Token {token_index} "
            f"marked unavailable."
        )

    # ========================================================
    # DETECT TOKEN / SERVICE FAILURE
    # ========================================================

    @staticmethod
    def _should_failover(
        error: Exception,
    ) -> bool:

        # ----------------------------------------------------
        # HTTP status
        # ----------------------------------------------------

        status_code = getattr(
            error,
            "status_code",
            None,
        )

        if status_code is None:

            response = getattr(
                error,
                "response",
                None,
            )

            if response is not None:

                status_code = getattr(
                    response,
                    "status_code",
                    None,
                )

        if status_code in {
            401,  # Unauthorized
            403,  # Forbidden
            429,  # Rate limit
            500,
            502,
            503,
            504,
        }:

            return True

        # ----------------------------------------------------
        # Error message
        # ----------------------------------------------------

        message = str(
            error
        ).lower()

        failure_keywords = [

            "unauthorized",

            "forbidden",

            "invalid token",

            "invalid api token",

            "authentication",

            "auth",

            "quota",

            "usage limit",

            "usage-limit",

            "limit reached",

            "rate limit",

            "rate-limit",

            "too many requests",

            "credits",

            "credit limit",

            "exhausted",

            "temporarily unavailable",

            "service unavailable",

            "internal server error",

            "bad gateway",

            "gateway timeout",

            "timeout",
        ]

        return any(
            keyword in message
            for keyword in failure_keywords
        )

    # ========================================================
    # CREATE CLIENT
    # ========================================================

    @staticmethod
    def _create_client(
        token: str,
    ) -> ApifyClient:

        return ApifyClient(
            token
        )

    # ========================================================
    # RUN ACTOR WITH FAILOVER
    # ========================================================

    def run_actor(
        self,
        actor_id: str,
        run_input: dict,
    ):
        """
        Run an Apify actor.

        Order:

            Token 1
              ↓
            Token 2
              ↓
            Token 3
              ↓
            Fail

        Returns:

            client, run
        """

        available_tokens = (
            self._get_available_tokens()
        )

        if not available_tokens:

            raise ApifyAllTokensFailed(
                "All configured Apify tokens "
                "are currently unavailable."
            )

        last_error = None

        for item in available_tokens:

            token_index = item["index"]
            token = item["token"]

            print(
                f"\n[Apify] Trying token "
                f"{token_index}..."
            )

            try:

                client = (
                    self._create_client(
                        token
                    )
                )

                run = (
                    client
                    .actor(actor_id)
                    .call(
                        run_input=run_input
                    )
                )

                print(
                    f"[Apify] Token "
                    f"{token_index} "
                    f"succeeded."
                )

                return client, run

            except Exception as error:

                last_error = error

                print(
                    f"[Apify] Token "
                    f"{token_index} failed: "
                    f"{error}"
                )

                if not self._should_failover(
                    error
                ):

                    # This is probably an
                    # actor/input/programming
                    # error, not a token problem.
                    raise

                self._disable_token(
                    token_index
                )

                # Continue to next token

        raise ApifyAllTokensFailed(
            "All Apify tokens failed. "
            f"Last error: {last_error}"
        )

    # ========================================================
    # RESET DISABLED TOKENS
    # ========================================================

    def reset_tokens(self):

        with self.lock:

            self.disabled_tokens.clear()

        print(
            "[Apify] Token failover state reset."
        )

    # ========================================================
    # STATUS
    # ========================================================

    def status(self) -> dict:

        with self.lock:

            return {

                "total_tokens":
                    len(self.tokens),

                "available_tokens":
                    len(
                        self.tokens
                    )
                    - len(
                        self.disabled_tokens
                    ),

                "disabled_tokens":
                    sorted(
                        self.disabled_tokens
                    ),
            }


# ============================================================
# SHARED INSTANCE
# ============================================================

apify_manager = ApifyTokenManager()