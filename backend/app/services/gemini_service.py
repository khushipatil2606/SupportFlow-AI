import os
from dotenv import load_dotenv
from google import genai


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not set in the .env file"
    )


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ============================================================
# GEMINI AI RESPONSE
# ============================================================

def ask_gemini(prompt: str) -> str:
    """
    Send a prompt to Gemini and return the generated response.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        if response is not None and response.text:
            return response.text.strip()

        return "I could not generate a response."

    except Exception as e:
        print("Gemini error:", e)
        return "The AI service is temporarily unavailable."


# ============================================================
# GENERAL AI RESPONSE
# ============================================================

def generate_ai_response(prompt: str) -> str:
    """
    General wrapper used by the AI agent.
    """

    return ask_gemini(prompt)


# ============================================================
# ORDER STATUS TOOL
# ============================================================

def get_order_status_tool(order_id: int):
    """
    Wrapper around the existing order status tool.
    """

    from backend.app.services.order_tools import get_order_status

    return get_order_status(order_id)


# ============================================================
# PRODUCT DETAILS TOOL
# ============================================================

def get_product_details_tool(product_id: int):
    """
    Wrapper around the existing product details tool.
    """

    from backend.app.services.product_tools import get_product_details

    return get_product_details(product_id)


# ============================================================
# CREATE SUPPORT TICKET TOOL
# ============================================================

def create_support_ticket_tool(
    user_id: int,
    issue: str,
    priority: str = "Medium"
):
    """
    Wrapper around the existing support ticket tool.
    """

    from backend.app.services.ticket_tools import create_support_ticket

    return create_support_ticket(
        user_id=user_id,
        issue=issue,
        priority=priority
    )


# ============================================================
# CANCEL ORDER TOOL
# ============================================================

def cancel_order_tool(order_id: int):
    """
    Wrapper around the existing cancellation tool.
    """

    from backend.app.services.cancellation_tools import cancel_order

    return cancel_order(order_id)