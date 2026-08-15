import re

from sqlalchemy.orm import Session
from google.genai import types

from backend.app.services.gemini_service import (
    client,
    get_order_status_tool,
    get_product_details_tool,
    create_support_ticket_tool,
    cancel_order_tool,
)

from backend.app.services.order_tools import get_order_status
from backend.app.services.product_tools import get_product_details
from backend.app.services.ticket_tools import create_support_ticket
from backend.app.services.cancellation_tools import cancel_order

from backend.app.services.session_memory import (
    get_state,
    set_state,
    clear_state,
)


# ============================================================
# BASIC HELPERS
# ============================================================

def clean_text(value):
    if value is None:
        return ""

    return str(value).strip()


def normalize_text(value):
    value = clean_text(value).lower()

    value = re.sub(
        r"[^\w\s]",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


# ============================================================
# ORDER ID EXTRACTION
# ============================================================

def extract_order_id(message: str):

    match = re.search(
        r"(?:order|ord)\s*(?:#\s*|no\.?\s*|number\s*)?(\d+)",
        message.lower()
    )

    if match:
        return int(match.group(1))

    return None


# ============================================================
# PRODUCT ID EXTRACTION
# ============================================================

def extract_product_id(message: str):

    match = re.search(
        r"(?:product|prod)\s*(?:#\s*|no\.?\s*|number\s*)?(\d+)",
        message.lower()
    )

    if match:
        return int(match.group(1))

    return None


# ============================================================
# POSITIVE CONFIRMATION
# ============================================================

def is_positive_confirmation(text: str) -> bool:
    """
    Detects a clear YES confirmation.

    Examples:
    - Yes
    - Yes, cancel order #4.
    - Yes cancel order 4
    - Sure, go ahead
    - Okay, cancel it
    """

    text = normalize_text(text)

    if not text:
        return False

    # Explicit negative responses
    negative_phrases = {
        "no",
        "nope",
        "nah",
        "no cancel",
        "dont cancel",
        "do not cancel",
        "not cancel",
        "keep it",
        "keep my order",
        "keep the order",
        "cancel no",
    }

    if text in negative_phrases:
        return False

    if text.startswith("no "):
        return False

    if "dont cancel" in text:
        return False

    if "do not cancel" in text:
        return False

    if "keep my order" in text:
        return False

    if "keep the order" in text:
        return False

    # Simple YES responses
    exact_positive = {
        "yes",
        "yeah",
        "yep",
        "yup",
        "sure",
        "confirm",
        "confirmed",
        "okay",
        "ok",
        "proceed",
        "proceed please",
        "go ahead",
        "do it",
        "please do it",
    }

    if text in exact_positive:
        return True

    # IMPORTANT:
    # This handles:
    # "Yes, cancel order #4."
    # "Yes cancel order 4"
    # "Sure, cancel it"
    affirmative_words = (
        "yes",
        "yeah",
        "yep",
        "yup",
        "sure",
        "okay",
        "ok",
        "confirm",
        "confirmed",
        "proceed",
        "go ahead",
        "do it",
    )

    has_affirmative = any(
        text == word or text.startswith(word + " ")
        for word in affirmative_words
    )

    has_cancel = (
        "cancel" in text
        or "cancellation" in text
    )

    if has_affirmative and has_cancel:
        return True

    # Other affirmative forms
    positive_starts = (
        "yes ",
        "yeah ",
        "yep ",
        "yup ",
        "sure ",
        "confirm ",
        "confirmed ",
        "go ahead ",
        "do it ",
        "please cancel ",
        "please go ahead ",
        "okay cancel ",
        "ok cancel ",
        "yes cancel ",
    )

    return any(
        text.startswith(prefix)
        for prefix in positive_starts
    )


# ============================================================
# NEGATIVE CONFIRMATION
# ============================================================

def is_negative_confirmation(text: str) -> bool:

    text = normalize_text(text)

    if not text:
        return False

    negative_phrases = [
        "no",
        "nope",
        "no cancel",
        "dont cancel",
        "do not cancel",
        "not cancel",
        "keep it",
        "keep my order",
        "keep the order",
        "no please",
    ]

    if text in negative_phrases:
        return True

    if text.startswith("no "):
        return True

    if "dont cancel" in text:
        return True

    if "do not cancel" in text:
        return True

    if "keep my order" in text:
        return True

    return False


# ============================================================
# CRITICAL SAFETY DETECTOR
# ============================================================

def is_critical_safety_issue(text: str) -> bool:

    text = normalize_text(text)

    critical_safety_phrases = [

        # Electrical danger
        "electric shock",
        "electric shocks",
        "electrical shock",
        "electrical shocks",
        "got shocked",
        "received a shock",
        "shocked by the product",

        # Dangerous product
        "dangerous product",
        "product is dangerous",
        "product dangerous",
        "unsafe product",
        "product is unsafe",

        # Safety
        "safety hazard",
        "safety risk",
        "safety issue",
        "serious safety issue",
        "serious safety problem",

        # Fire
        "caught fire",
        "product caught fire",
        "started a fire",
        "electrical fire",
        "fire hazard",
        "smoke from product",
        "product is burning",
        "product burning",

        # Explosion
        "product exploded",
        "product explosion",
        "exploded",
        "explosion",

        # Injury
        "injury caused by product",
        "injured by product",
        "product caused injury",
        "hurt by product",
    ]

    return any(
        phrase in text
        for phrase in critical_safety_phrases
    )


# ============================================================
# RESPONSE FORMATTERS
# ============================================================

def format_order_status(result: dict) -> str:

    if not result:
        return "I couldn't find the order details."

    if result.get("success") is False:
        return result.get(
            "message",
            "I couldn't retrieve the order details."
        )

    order_id = result.get(
        "id",
        result.get("order_id", "")
    )

    status = result.get(
        "status",
        "Unknown"
    )

    total = result.get("total_amount")

    if total is not None:
        return (
            f"Your order #{order_id} is currently "
            f"{status}. "
            f"The total amount is ₹{total}."
        )

    return (
        f"Your order #{order_id} is currently "
        f"{status}."
    )


def format_product_details(result: dict) -> str:

    if not result:
        return "I couldn't find the product details."

    if result.get("success") is False:
        return result.get(
            "message",
            "I couldn't retrieve the product details."
        )

    product_id = result.get(
        "id",
        result.get("product_id", "")
    )

    name = result.get(
        "name",
        "Unknown"
    )

    description = result.get(
        "description",
        "No description available."
    )

    price = result.get("price")

    availability = result.get(
        "availability",
        result.get("stock", "Unknown")
    )

    response = (
        f"Here are the details for Product #{product_id}:\n\n"
        f"Name: {name}\n"
        f"Description: {description}\n"
    )

    if price is not None:
        response += f"Price: ₹{price}\n"

    response += f"Availability: {availability}"

    return response


def format_ticket_response(result: dict) -> str:

    if not result:
        return "I couldn't create the support ticket."

    if result.get("success") is False:
        return result.get(
            "message",
            "I couldn't create the support ticket."
        )

    ticket_id = result.get(
        "id",
        result.get("ticket_id")
    )

    priority = result.get("priority")

    if ticket_id:

        if priority:
            return (
                f"Your support ticket #{ticket_id} has been "
                f"created successfully with {priority} priority."
            )

        return (
            f"Your support ticket #{ticket_id} has been "
            f"created successfully."
        )

    return "Your support ticket has been created successfully."


# ============================================================
# ORDER STATUS REQUEST DETECTOR
# ============================================================

def is_order_status_request(text: str) -> bool:

    text = normalize_text(text)

    status_phrases = [
        "order status",
        "status of my order",
        "status of the order",
        "status for my order",
        "where is my order",
        "where is the order",
        "where my order",
        "track my order",
        "track the order",
        "tracking my order",
        "tracking the order",
        "order tracking",
        "order update",
        "delivery status",
        "where is my package",
        "where is my parcel",
        "when will my order arrive",
        "when will my order be delivered",
        "has my order arrived",
        "is my order delivered",
    ]

    status_words = [
        "status",
        "tracking",
        "track",
        "delivery",
        "delivered",
    ]

    if any(
        phrase in text
        for phrase in status_phrases
    ):
        return True

    if (
        "order" in text
        and any(
            word in text
            for word in status_words
        )
    ):
        return True

    return False


# ============================================================
# SUPPORT REQUEST DETECTOR
# ============================================================

def is_support_request(text: str) -> bool:

    text = normalize_text(text)

    support_phrases = [

        # Ticket
        "support ticket",
        "create ticket",
        "raise ticket",
        "open ticket",
        "report issue",
        "report this",
        "report a problem",
        "report problem",
        "file a complaint",
        "make a complaint",

        # Order problems
        "problem with my order",
        "problem with the order",
        "issue with my order",
        "issue with the order",

        # Product problems
        "problem with my product",
        "problem with the product",
        "issue with my product",
        "issue with the product",
        "i have a problem",
        "i have an issue",
        "damaged",
        "damage",
        "broken",
        "defective",
        "not working",
        "doesnt work",
        "does not work",

        # Critical safety
        "electric shock",
        "electrical shock",
        "got shocked",
        "dangerous product",
        "product is dangerous",
        "unsafe product",
        "product is unsafe",
        "safety hazard",
        "safety risk",
        "safety issue",
        "caught fire",
        "product caught fire",
        "electrical fire",
        "fire hazard",
        "product exploded",
        "explosion",
        "injury caused by product",
        "injured by product",

        # Priority
        "minor issue",
        "minor problem",
        "serious issue",
        "serious problem",
        "serious safety",
        "urgent issue",
        "urgent problem",
        "emergency",
    ]

    return any(
        phrase in text
        for phrase in support_phrases
    )


# ============================================================
# CANCEL REQUEST DETECTOR
# ============================================================

def is_cancel_request(text: str) -> bool:

    text = normalize_text(text)

    cancel_words = [
        "cancel",
        "cancellation",
        "cancel order",
        "want to cancel",
        "would like to cancel",
        "please cancel",
    ]

    return any(
        word in text
        for word in cancel_words
    )


# ============================================================
# PRIORITY DETECTOR
# ============================================================

def determine_priority(text: str) -> str:

    text = normalize_text(text)

    # --------------------------------------------------------
    # CRITICAL
    # --------------------------------------------------------

    critical_keywords = [
        "critical",
        "critical priority",
        "safety issue",
        "serious safety issue",
        "serious safety problem",
        "serious safety",
        "dangerous",
        "unsafe",
        "fire",
        "explosion",
        "electric shock",
        "electrical shock",
        "security breach",
        "hacked",
        "fraud",
        "injury",
    ]

    if any(
        keyword in text
        for keyword in critical_keywords
    ):
        return "Critical"

    # --------------------------------------------------------
    # HIGH
    # --------------------------------------------------------

    high_keywords = [
        "high priority",
        "urgent",
        "emergency",
        "damaged",
        "damage",
        "broken",
        "defective",
        "not working",
        "doesnt work",
        "does not work",
        "wrong product",
        "missing",
        "leaking",
        "serious problem",
        "serious issue",
    ]

    if any(
        keyword in text
        for keyword in high_keywords
    ):
        return "High"

    # --------------------------------------------------------
    # LOW
    # --------------------------------------------------------

    low_keywords = [
        "low priority",
        "not urgent",
        "minor issue",
        "minor problem",
        "small issue",
    ]

    if any(
        keyword in text
        for keyword in low_keywords
    ):
        return "Low"

    return "Medium"


# ============================================================
# CANCEL ORDER HANDLER
# ============================================================

def prepare_cancel_order(
    order_id: int,
    user_id: int,
    db: Session
):

    order_result = get_order_status(
        order_id=order_id,
        db=db
    )

    if not order_result:
        return f"I couldn't find order #{order_id}."

    if order_result.get("success") is False:
        return order_result.get(
            "message",
            f"I couldn't find order #{order_id}."
        )

    current_status = str(
        order_result.get("status", "")
    ).lower().strip()

    if current_status == "cancelled":
        return (
            f"Order #{order_id} has already been cancelled."
        )

    if current_status in [
        "delivered",
        "completed"
    ]:
        return (
            f"Order #{order_id} has already been "
            f"{current_status} and cannot be cancelled."
        )

    # Store pending cancellation
    set_state(
        user_id,
        {
            "awaiting_confirmation": True,
            "pending_action": "cancel_order",
            "order_id": order_id,
        }
    )

    return (
        f"I can help you cancel order #{order_id}.\n\n"
        f"I have NOT cancelled it yet.\n\n"
        f"Would you like me to cancel order #{order_id}?"
    )


# ============================================================
# SIMPLE REQUEST HANDLER
# ============================================================

def handle_simple_request(
    message: str,
    user_id: int,
    db: Session,
):

    text = normalize_text(message)

    order_id = extract_order_id(message)
    product_id = extract_product_id(message)

    # ========================================================
    # 1. CRITICAL SAFETY
    # ========================================================

    if is_critical_safety_issue(text):

        print(">>> CRITICAL SAFETY ISSUE DETECTED")

        priority = "Critical"

        result = create_support_ticket(
            user_id=user_id,
            issue=message,
            priority=priority,
            db=db,
        )

        ticket_response = format_ticket_response(result)

        return (
            "⚠️ Safety issue detected.\n\n"
            "Please stop using the product immediately and "
            "unplug it if it is safe to do so.\n\n"
            f"{ticket_response}\n\n"
            "Our support team should investigate this as a "
            "critical issue."
        )

    # ========================================================
    # 2. NORMAL SUPPORT TICKET
    # ========================================================

    if is_support_request(text):

        priority = determine_priority(text)

        print(">>> SUPPORT REQUEST DETECTED")
        print(">>> PRIORITY:", priority)

        result = create_support_ticket(
            user_id=user_id,
            issue=message,
            priority=priority,
            db=db,
        )

        return format_ticket_response(result)

    # ========================================================
    # 3. PRODUCT DETAILS
    # ========================================================

    product_keywords = [
        "product",
        "details",
        "information",
        "info",
        "about",
        "price",
        "availability",
        "available",
    ]

    if (
        product_id is not None
        and any(
            word in text
            for word in product_keywords
        )
    ):

        result = get_product_details(
            product_id=product_id,
            db=db,
        )

        return format_product_details(result)

    # ========================================================
    # 4. CANCEL ORDER
    # ========================================================

    if (
        order_id is not None
        and is_cancel_request(text)
    ):

        return prepare_cancel_order(
            order_id=order_id,
            user_id=user_id,
            db=db,
        )

    # ========================================================
    # 5. ORDER STATUS WITH ORDER NUMBER
    # ========================================================

    if (
        order_id is not None
        and is_order_status_request(text)
    ):

        result = get_order_status(
            order_id=order_id,
            db=db,
        )

        return format_order_status(result)

    # ========================================================
    # 6. ORDER STATUS WITHOUT ORDER NUMBER
    # ========================================================

    if (
        order_id is None
        and is_order_status_request(text)
    ):

        return (
            "Sure! I can check your order status. "
            "Please provide your order number, for example "
            "Order #4."
        )

    return None


# ============================================================
# MAIN AGENT
# ============================================================

def run_agent(
    message: str,
    user_id: int,
    db: Session,
) -> str:

    message = clean_text(message)

    if not message:
        return "Please tell me how I can help you."

    text = normalize_text(message)

    # ========================================================
    # STEP 1
    # CHECK PENDING CONFIRMATION
    # ========================================================

    # IMPORTANT:
    # Always load the saved state before checking it.
    state = get_state(user_id) or {}

    if state.get("awaiting_confirmation"):

        pending_action = state.get("pending_action")
        order_id = state.get("order_id")

        print(
            f">>> PENDING CONFIRMATION: "
            f"action={pending_action}, "
            f"order_id={order_id}, "
            f"message={message!r}"
        )

        # ----------------------------------------------------
        # CANCEL ORDER CONFIRMATION
        # ----------------------------------------------------

        if pending_action == "cancel_order":

            # =================================================
            # YES
            # =================================================

            if is_positive_confirmation(message):

                if not order_id:

                    clear_state(user_id)

                    return (
                        "I couldn't determine which order you "
                        "wanted to cancel. Please provide the "
                        "order ID."
                    )

                print(
                    f">>> CANCELLATION CONFIRMED "
                    f"FOR ORDER #{order_id}"
                )

                result = cancel_order(
                    order_id=int(order_id),
                    db=db,
                )

                clear_state(user_id)

                if result and result.get("success"):

                    return (
                        f"✅ Your order #{order_id} has been "
                        f"cancelled successfully."
                    )

                return (
                    result.get(
                        "message",
                        f"I was unable to cancel order #{order_id}.",
                    )
                    if result
                    else
                    f"I was unable to cancel order #{order_id}."
                )

            # =================================================
            # NO
            # =================================================

            if is_negative_confirmation(message):

                clear_state(user_id)

                return (
                    f"Okay, I won't cancel order #{order_id}."
                )

            # =================================================
            # NEW CRITICAL SAFETY REQUEST
            # =================================================

            if is_critical_safety_issue(text):

                clear_state(user_id)

                return handle_simple_request(
                    message=message,
                    user_id=user_id,
                    db=db,
                )

            # =================================================
            # NEW SUPPORT REQUEST
            # =================================================

            if is_support_request(text):

                clear_state(user_id)

                return handle_simple_request(
                    message=message,
                    user_id=user_id,
                    db=db,
                )

            # =================================================
            # NEW PRODUCT REQUEST
            # =================================================

            new_product_id = extract_product_id(message)

            if new_product_id is not None:

                clear_state(user_id)

                return handle_simple_request(
                    message=message,
                    user_id=user_id,
                    db=db,
                )

            # =================================================
            # NEW STATUS REQUEST
            # =================================================

            if is_order_status_request(text):

                clear_state(user_id)

                return handle_simple_request(
                    message=message,
                    user_id=user_id,
                    db=db,
                )

            # =================================================
            # USER PROVIDES DIFFERENT ORDER ID
            # =================================================

            new_order_id = extract_order_id(message)

            if (
                new_order_id is not None
                and new_order_id != order_id
            ):

                return prepare_cancel_order(
                    order_id=new_order_id,
                    user_id=user_id,
                    db=db,
                )

            # =================================================
            # UNCLEAR
            # =================================================

            return (
                f"I still need your confirmation. "
                f"Would you like me to cancel order #{order_id}?"
            )

    # ========================================================
    # STEP 2
    # SIMPLE REQUESTS
    # ========================================================

    simple_response = handle_simple_request(
        message=message,
        user_id=user_id,
        db=db,
    )

    if simple_response is not None:
        return simple_response

    # ========================================================
    # STEP 3
    # BASIC FALLBACKS
    # ========================================================

    # Greetings
    greeting_words = [
        "hi",
        "hello",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
    ]

    if text in greeting_words:

        return (
            "Hello! 👋 I'm SupportFlow AI. "
            "I can help you with order status, product details, "
            "order cancellations, and support tickets."
        )

    # Help
    if text in [
        "help",
        "what can you do",
        "what can you help with",
        "how can you help me",
    ]:

        return (
            "I can help you with:\n\n"
            "📦 Order status\n"
            "🛍️ Product details\n"
            "❌ Order cancellation\n"
            "🎫 Support tickets\n\n"
            "For example, you can ask: "
            "\"What is the status of order #4?\""
        )

    # ========================================================
    # STEP 4
    # GEMINI TOOLS
    # ========================================================

    tool = types.Tool(
    function_declarations=[
        {
            "name": "get_order_status",
            "description": "Get the current status and total amount of a customer's order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "integer",
                        "description": "The order ID to check."
                    }
                },
                "required": ["order_id"]
            }
        },
        {
            "name": "get_product_details",
            "description": "Get details about a product.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "The product ID to look up."
                    }
                },
                "required": ["product_id"]
            }
        },
        {
            "name": "create_support_ticket",
            "description": "Create a support ticket for a customer's issue.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "integer",
                        "description": "The customer user ID."
                    },
                    "issue": {
                        "type": "string",
                        "description": "Description of the customer's issue."
                    },
                    "priority": {
                        "type": "string",
                        "description": "Ticket priority.",
                        "enum": [
                            "Low",
                            "Medium",
                            "High",
                            "Critical"
                        ]
                    }
                },
                "required": [
                    "user_id",
                    "issue",
                    "priority"
                ]
            }
        },
        {
            "name": "cancel_order",
            "description": "Cancel a customer's order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "integer",
                        "description": "The order ID to cancel."
                    }
                },
                "required": ["order_id"]
            }
        }
    ]
)

    config = types.GenerateContentConfig(
        tools=[tool]
    )

    # ========================================================
    # STEP 5
    # ASK GEMINI
    # ========================================================

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=message,
            config=config,
        )

    except Exception as e:

        error_message = str(e)

        print(
            f"Gemini error: {error_message}"
        )

        # Do NOT expose Gemini/quota errors to the user.
        return (
            "I'm currently unable to answer that question. "
            "I can still help you with order status, product "
            "details, cancellations, and support tickets."
        )

    # ========================================================
    # STEP 6
    # GEMINI TOOL CALL
    # ========================================================

    if response.function_calls:

        function_call = response.function_calls[0]

        function_name = function_call.name

        args = function_call.args or {}

        # ====================================================
        # ORDER STATUS
        # ====================================================

        if function_name == "get_order_status":

            try:

                order_id = int(
                    args["order_id"]
                )

            except (
                KeyError,
                TypeError,
                ValueError,
            ):

                return (
                    "Please provide a valid order ID so I can "
                    "check your order status."
                )

            result = get_order_status(
                order_id=order_id,
                db=db,
            )

            return format_order_status(result)

        # ====================================================
        # PRODUCT DETAILS
        # ====================================================

        if function_name == "get_product_details":

            try:

                product_id = int(
                    args["product_id"]
                )

            except (
                KeyError,
                TypeError,
                ValueError,
            ):

                return (
                    "Please provide a valid product ID so I can "
                    "find the product details."
                )

            result = get_product_details(
                product_id=product_id,
                db=db,
            )

            return format_product_details(result)

        # ====================================================
        # CREATE SUPPORT TICKET
        # ====================================================

        if function_name == "create_support_ticket":

            issue = clean_text(
                args.get("issue")
            )

            if not issue:

                return (
                    "Please provide a short description of "
                    "the issue so I can create the support ticket."
                )

            # Safety issues ALWAYS become Critical.
            if is_critical_safety_issue(issue):

                priority = "Critical"

            else:

                priority = determine_priority(issue)

            result = create_support_ticket(
                user_id=user_id,
                issue=issue,
                priority=priority,
                db=db,
            )

            return format_ticket_response(result)

        # ====================================================
        # CANCEL ORDER
        # ====================================================

        if function_name == "cancel_order":

            try:

                order_id = int(
                    args["order_id"]
                )

            except (
                KeyError,
                TypeError,
                ValueError,
            ):

                return (
                    "Please provide a valid order ID so I can "
                    "check whether it can be cancelled."
                )

            return prepare_cancel_order(
                order_id=order_id,
                user_id=user_id,
                db=db,
            )

    # ========================================================
    # STEP 7
    # NORMAL GEMINI RESPONSE
    # ========================================================

    try:

        if response.text:

            return response.text.strip()

    except Exception:

        pass

    # ========================================================
    # FINAL FALLBACK
    # ========================================================

    return (
        "I'm sorry, I couldn't generate a response. "
        "Please try again."
    )