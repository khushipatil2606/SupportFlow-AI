// ============================================================
// SupportFlow AI - Frontend Application
// ============================================================


// ============================================================
// API CONFIGURATION
// ============================================================

const API_URL = "http://127.0.0.1:8000/agent/chat";

const TICKET_HISTORY_URL = "http://127.0.0.1:8000/agent/tickets";

const USER_ID = 2;


// ============================================================
// DOM ELEMENTS
// ============================================================

const messageInput = document.getElementById("messageInput");

const chatMessages = document.getElementById("chatMessages");

const sendButton = document.getElementById("sendButton");


// ============================================================
// STATE
// ============================================================

let isSending = false;


// ============================================================
// SEND MESSAGE
// ============================================================

async function sendMessage() {

    if (isSending) {
        return;
    }

    if (!messageInput || !chatMessages) {
        console.error("Required chat elements were not found.");
        return;
    }

    const message = messageInput.value.trim();

    if (!message) {
        return;
    }


    // Remove welcome screen

    const welcome =
        document.querySelector(".welcome-message");

    if (welcome) {
        welcome.remove();
    }


    // Show user message

    addMessage(message, "user");


    // Clear input

    messageInput.value = "";

    resetTextarea();


    // Disable sending

    isSending = true;

    if (sendButton) {
        sendButton.disabled = true;
    }


    // Show typing indicator

    const typingId = showTyping();


    try {

        // ====================================================
        // SEND REQUEST TO FASTAPI
        // ====================================================

        const response = await fetch(API_URL, {

            method: "POST",

            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },

            body: JSON.stringify({
                user_id: USER_ID,
                message: message
            })

        });


        // Remove typing indicator

        removeTyping(typingId);


        // ====================================================
        // HANDLE SERVER ERROR
        // ====================================================

        if (!response.ok) {

            let errorMessage =
                `Server returned error ${response.status}.`;

            try {

                const errorData =
                    await response.json();

                if (errorData.detail) {

                    errorMessage =
                        errorData.detail;

                }

                else if (errorData.message) {

                    errorMessage =
                        errorData.message;

                }

            }

            catch (error) {

                console.warn(
                    "Could not read server error response."
                );

            }

            throw new Error(errorMessage);
        }


        // ====================================================
        // READ RESPONSE
        // ====================================================

        const data =
            await response.json();


        // ====================================================
        // DISPLAY AI RESPONSE
        // ====================================================

        if (data && data.response) {

            addMessage(
                data.response,
                "ai"
            );

        }

        else {

            addMessage(
                "I received an empty response from the AI service.",
                "ai"
            );

        }

    }


    catch (error) {

        console.error(
            "SupportFlow AI API Error:",
            error
        );


        removeTyping(typingId);


        let userMessage =
            "⚠️ Something went wrong while contacting SupportFlow AI.";


        // Connection error

        if (
            error instanceof TypeError &&
            error.message.includes("fetch")
        ) {

            userMessage =
                "⚠️ I couldn't connect to the SupportFlow AI server. " +
                "Please make sure the FastAPI server is running on port 8000.";

        }


        // Server error

        else {

            userMessage =
                "⚠️ " +
                (error.message || "Something went wrong.");

        }


        addMessage(
            userMessage,
            "ai"
        );

    }


    finally {

        isSending = false;

        if (sendButton) {
            sendButton.disabled = false;
        }

        messageInput.focus();

    }

}


// ============================================================
// ADD MESSAGE
// ============================================================

function addMessage(text, sender) {

    if (!chatMessages) {
        return;
    }

    const row = document.createElement("div");
    row.className = `message-row ${sender}`;

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";

    // AI RESPONSE
    if (sender === "ai") {
        bubble.innerHTML = formatAIResponse(String(text));
    }

    // USER MESSAGE
    else {
        bubble.textContent = String(text);
    }

    row.appendChild(bubble);
    chatMessages.appendChild(row);

    scrollToBottom();
}


// ============================================================
// FORMAT AI RESPONSE
// ============================================================

function formatAIResponse(text) {

    // Escape HTML for safety
    let formatted = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

    // Bold: **text**
    formatted = formatted.replace(
        /\*\*(.*?)\*\*/g,
        "<strong>$1</strong>"
    );

    // Italic: *text*
    formatted = formatted.replace(
        /(^|[^\*])\*([^*\n]+)\*(?!\*)/g,
        "$1<em>$2</em>"
    );

    // Bullet points
    formatted = formatted.replace(
        /^[ \t]*[*\-•][ \t]+(.+)$/gm,
        "<span class=\"ai-bullet\">• $1</span>"
    );

    // Numbered lists
    formatted = formatted.replace(
        /^([ \t]*\d+\.)[ \t]+(.+)$/gm,
        "<span class=\"ai-numbered\">$1 $2</span>"
    );

    // Preserve new lines
    formatted = formatted.replace(/\n/g, "<br>");

    return formatted;
}

// ============================================================
// SCROLL TO BOTTOM
// ============================================================

function scrollToBottom() {

    if (!chatMessages) {
        return;
    }

    chatMessages.scrollTop =
        chatMessages.scrollHeight;

}


// ============================================================
// QUICK MESSAGE
// ============================================================

function sendQuickMessage(message) {

    if (!message) {
        return;
    }

    if (isSending) {
        return;
    }

    messageInput.value =
        message;

    sendMessage();

}


// ============================================================
// QUICK ACTIONS
// ============================================================

function askOrderStatus() {

    sendQuickMessage(
        "What is the status of my order #3?"
    );

}


function askProductDetails() {

    sendQuickMessage(
        "Tell me the details of product #1."
    );

}


function askCancelOrder() {

    sendQuickMessage(
        "I want to cancel my order #3."
    );

}


function askCreateTicket() {

    sendQuickMessage(
        "I received a damaged product and want to report this issue."
    );

}


// ============================================================
// TICKET HISTORY
// ============================================================

async function showTicketHistory() {

    if (isSending) {
        return;
    }

    if (!chatMessages) {
        console.error(
            "Chat messages container was not found."
        );
        return;
    }


    // Remove welcome screen

    const welcome =
        document.querySelector(".welcome-message");

    if (welcome) {
        welcome.remove();
    }


    // Lock UI while loading

    isSending = true;

    if (sendButton) {
        sendButton.disabled = true;
    }


    // Show typing

    const typingId =
        showTyping();


    try {

        // ====================================================
        // GET TICKET HISTORY
        // ====================================================

        const response =
            await fetch(
                `${TICKET_HISTORY_URL}/${USER_ID}`,
                {
                    method: "GET",

                    headers: {
                        "Accept": "application/json"
                    }
                }
            );


        removeTyping(typingId);


        // ====================================================
        // HANDLE ERROR
        // ====================================================

        if (!response.ok) {

            let errorMessage =
                `Unable to load ticket history. ` +
                `Server returned ${response.status}.`;

            try {

                const errorData =
                    await response.json();

                if (errorData.detail) {

                    errorMessage =
                        errorData.detail;

                }

                else if (errorData.message) {

                    errorMessage =
                        errorData.message;

                }

            }

            catch (error) {

                console.warn(
                    "Could not read ticket history error."
                );

            }

            throw new Error(errorMessage);
        }


        // ====================================================
        // READ DATA
        // ====================================================

        const data =
            await response.json();


        // ====================================================
        // NO TICKETS
        // ====================================================

        if (
            !data ||
            !Array.isArray(data.tickets) ||
            data.tickets.length === 0
        ) {

            addMessage(
                "📋 You don't have any support tickets yet.",
                "ai"
            );

            return;
        }


        // ====================================================
        // CREATE HISTORY MESSAGE
        // ====================================================

        const row =
            document.createElement("div");

        row.className =
            "message-row ai";


        const bubble =
            document.createElement("div");

        bubble.className =
            "message-bubble";


        const history =
            document.createElement("div");

        history.className =
            "ticket-history";


        // ====================================================
        // TITLE
        // ====================================================

        const title =
            document.createElement("h3");

        title.textContent =
            "📋 Support Ticket History";

        history.appendChild(title);


        // ====================================================
        // TOTAL TICKETS
        // ====================================================

        const total =
            document.createElement("p");

        total.textContent =
            `Total Tickets: ${
                data.total_tickets ??
                data.tickets.length
            }`;

        history.appendChild(total);


        // ====================================================
        // TICKET CARDS
        // ====================================================

        data.tickets.forEach(
            function(ticket) {

                const card =
                    document.createElement("div");

                card.className =
                    "ticket-card";


                // ------------------------------------------
                // HEADER
                // ------------------------------------------

                const header =
                    document.createElement("div");

                header.className =
                    "ticket-header";


                const ticketNumber =
                    document.createElement("strong");

                ticketNumber.textContent =
                    `🎫 Ticket #${ticket.ticket_id}`;


                const status =
                    document.createElement("span");

                status.className =
                    "ticket-status";

                status.textContent =
                    ticket.status ||
                    "Unknown";


                header.appendChild(
                    ticketNumber
                );

                header.appendChild(
                    status
                );


                // ------------------------------------------
                // ISSUE
                // ------------------------------------------

                const issue =
                    document.createElement("div");

                issue.className =
                    "ticket-issue";

                issue.textContent =
                    ticket.issue ||
                    "No issue description provided.";


                // ------------------------------------------
                // FOOTER
                // ------------------------------------------

                const footer =
                    document.createElement("div");

                footer.className =
                    "ticket-footer";


                const priority =
                    document.createElement("span");

                priority.textContent =
                    `Priority: ${
                        ticket.priority ||
                        "Medium"
                    }`;


                const ticketStatus =
                    document.createElement("span");

                ticketStatus.textContent =
                    `Status: ${
                        ticket.status ||
                        "Unknown"
                    }`;


                footer.appendChild(
                    priority
                );

                footer.appendChild(
                    ticketStatus
                );


                // ------------------------------------------
                // BUILD CARD
                // ------------------------------------------

                card.appendChild(
                    header
                );

                card.appendChild(
                    issue
                );

                card.appendChild(
                    footer
                );


                history.appendChild(
                    card
                );

            }
        );


        // ====================================================
        // ADD HISTORY TO CHAT
        // ====================================================

        bubble.appendChild(
            history
        );

        row.appendChild(
            bubble
        );

        chatMessages.appendChild(
            row
        );


        scrollToBottom();

    }


    catch (error) {

        console.error(
            "Ticket History Error:",
            error
        );


        removeTyping(
            typingId
        );


        addMessage(
            `⚠️ ${
                error.message ||
                "I couldn't load your ticket history."
            }`,
            "ai"
        );

    }


    finally {

        isSending = false;

        if (sendButton) {
            sendButton.disabled = false;
        }

        if (messageInput) {
            messageInput.focus();
        }

    }

}


// ============================================================
// TYPING INDICATOR
// ============================================================

function showTyping() {

    if (!chatMessages) {
        return null;
    }


    const id =
        "typing-" +
        Date.now();


    const row =
        document.createElement("div");

    row.className =
        "message-row ai";

    row.id =
        id;


    const typing =
        document.createElement("div");

    typing.className =
        "typing";


    const dot1 =
        document.createElement("span");

    const dot2 =
        document.createElement("span");

    const dot3 =
        document.createElement("span");


    typing.appendChild(dot1);

    typing.appendChild(dot2);

    typing.appendChild(dot3);


    row.appendChild(
        typing
    );

    chatMessages.appendChild(
        row
    );


    scrollToBottom();


    return id;

}


// ============================================================
// REMOVE TYPING INDICATOR
// ============================================================

function removeTyping(id) {

    if (!id) {
        return;
    }


    const element =
        document.getElementById(id);


    if (element) {
        element.remove();
    }

}


// ============================================================
// CLEAR CHAT
// ============================================================

function clearChat() {

    if (!chatMessages) {
        return;
    }

    if (isSending) {
        return;
    }


    chatMessages.innerHTML = `

        <div class="welcome-message">

            <div class="welcome-icon">
                🤖
            </div>

            <h2>
                How can I help you?
            </h2>

            <p>
                I can help with orders, products,
                cancellations and support tickets.
            </p>

            <div class="suggestions">

                <button
                    onclick="sendQuickMessage(
                        'What is the status of my order #3?'
                    )"
                >
                    📦 Check my order
                </button>


                <button
                    onclick="sendQuickMessage(
                        'Tell me the details of product #1.'
                    )"
                >
                    🛍️ Product information
                </button>


                <button
                    onclick="sendQuickMessage(
                        'I received a damaged product and want to report this issue.'
                    )"
                >
                    🎫 Report an issue
                </button>

            </div>

        </div>

    `;


    // Reset input

    messageInput.value = "";

    resetTextarea();

    messageInput.focus();

}


// ============================================================
// ENTER KEY
// ============================================================

function handleKeyDown(event) {

    if (
        event.key === "Enter" &&
        !event.shiftKey
    ) {

        event.preventDefault();

        sendMessage();

    }

}


// ============================================================
// AUTO RESIZE TEXTAREA
// ============================================================

if (messageInput) {

    messageInput.addEventListener(
        "input",
        function() {

            this.style.height =
                "auto";

            this.style.height =
                Math.min(
                    this.scrollHeight,
                    120
                ) + "px";

        }
    );

}


// ============================================================
// RESET TEXTAREA
// ============================================================

function resetTextarea() {

    if (!messageInput) {
        return;
    }

    messageInput.style.height =
        "auto";

}


// ============================================================
// INITIALIZATION
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function() {

        console.log(
            "SupportFlow AI frontend initialized."
        );

        console.log(
            "Chat API:",
            API_URL
        );

        console.log(
            "Ticket History API:",
            TICKET_HISTORY_URL
        );

        console.log(
            "User ID:",
            USER_ID
        );


        if (messageInput) {
            messageInput.focus();
        }

    }
);
// ==========================================
// ORDER HISTORY WITH PRODUCT DETAILS
// ==========================================

// ==========================================
// ORDER HISTORY WITH PRODUCT DETAILS
// ==========================================

async function getOrderHistory() {

    const welcome = document.querySelector(".welcome-message");

    if (welcome) {
        welcome.remove();
    }

    // Show user's message
    addMessage("Show me my order history.", "user");

    const typingId = showTyping();

    try {

        // ==========================================
        // GET USER ORDERS
        // ==========================================

        const orderResponse = await fetch(
            `http://127.0.0.1:8000/orders/user/${USER_ID}`
        );

        if (!orderResponse.ok) {
            throw new Error(
                `Order API returned ${orderResponse.status}`
            );
        }

        const orders = await orderResponse.json();


        // ==========================================
        // REMOVE TYPING INDICATOR
        // ==========================================

        removeTyping(typingId);


        // ==========================================
        // NO ORDERS
        // ==========================================

        if (!orders || orders.length === 0) {

            addMessage(
                "📦 You currently have no orders.",
                "ai"
            );

            return;
        }


        // ==========================================
        // GET ALL PRODUCTS
        // ==========================================

        let products = [];

        try {

            const productResponse = await fetch(
                "http://127.0.0.1:8000/products/"
            );

            if (productResponse.ok) {

                products = await productResponse.json();

            } else {

                console.warn(
                    "Could not load products."
                );

            }

        } catch (productError) {

            console.error(
                "Product API Error:",
                productError
            );

        }


        // ==========================================
        // CREATE HISTORY CONTAINER
        // ==========================================

        const historyRow =
            document.createElement("div");

        historyRow.className =
            "message-row ai";


        const historyBubble =
            document.createElement("div");

        historyBubble.className =
            "message-bubble order-history";


        // ==========================================
        // HEADING
        // ==========================================

        const heading =
            document.createElement("h3");

        heading.textContent =
            "📋 Order History";

        historyBubble.appendChild(heading);


        // ==========================================
        // TOTAL ORDERS
        // ==========================================

        const total =
            document.createElement("p");

        total.className =
            "order-total";

        total.textContent =
            `Total Orders: ${orders.length}`;

        historyBubble.appendChild(total);


        // ==========================================
        // CREATE ORDER CARDS
        // ==========================================

        orders.forEach(order => {

            // Find matching product
            const product =
                products.find(
                    p => p.id === order.product_id
                );


            // Product information
            const productName =
                product?.name ||
                `Product #${order.product_id}`;


            const productDescription =
                product?.description ||
                "";


            const productPrice =
                product?.price;


            // ==========================================
            // ORDER CARD
            // ==========================================

            const card =
                document.createElement("div");

            card.className =
                "order-card";


            // ==========================================
            // CARD HEADER
            // ==========================================

            const header =
                document.createElement("div");

            header.className =
                "order-card-header";


            const orderTitle =
                document.createElement("strong");

            orderTitle.textContent =
                `📦 Order #${order.id}`;


            const status =
                document.createElement("span");

            status.className =
                `order-status ${order.status
                    .toLowerCase()
                    .replace(/\s+/g, "-")}`;

            status.textContent =
                order.status;


            header.appendChild(orderTitle);

            header.appendChild(status);

            card.appendChild(header);


            // ==========================================
            // PRODUCT NAME
            // ==========================================

            const productTitle =
                document.createElement("h4");

            productTitle.className =
                "order-product-name";

            productTitle.textContent =
                productName;

            card.appendChild(productTitle);


            // ==========================================
            // DESCRIPTION
            // ==========================================

            if (productDescription) {

                const description =
                    document.createElement("p");

                description.className =
                    "order-product-description";

                description.textContent =
                    productDescription;

                card.appendChild(description);
            }


            // ==========================================
            // PRODUCT ID
            // ==========================================

            const productId =
                document.createElement("p");

            productId.innerHTML =
                `<strong>Product ID:</strong> ${order.product_id}`;

            card.appendChild(productId);


            // ==========================================
            // ORDER AMOUNT
            // ==========================================

            const amount =
                document.createElement("p");

            amount.innerHTML =
                `<strong>Order Amount:</strong> ₹${Number(
                    order.total_amount
                ).toLocaleString("en-IN")}`;

            card.appendChild(amount);


            // ==========================================
            // PRODUCT PRICE
            // ==========================================

            if (productPrice !== undefined) {

                const price =
                    document.createElement("p");

                price.innerHTML =
                    `<strong>Product Price:</strong> ₹${Number(
                        productPrice
                    ).toLocaleString("en-IN")}`;

                card.appendChild(price);
            }


            // ==========================================
            // STATUS
            // ==========================================

            const statusText =
                document.createElement("p");

            statusText.innerHTML =
                `<strong>Status:</strong> ${order.status}`;

            card.appendChild(statusText);


            // Add card to history
            historyBubble.appendChild(card);

        });


        // ==========================================
        // ADD HISTORY TO CHAT
        // ==========================================

        historyRow.appendChild(historyBubble);

        chatMessages.appendChild(historyRow);


        // ==========================================
        // SCROLL TO LATEST
        // ==========================================

        chatMessages.scrollTop =
            chatMessages.scrollHeight;


    } catch (error) {

        console.error(
            "Order History Error:",
            error
        );

        removeTyping(typingId);

        addMessage(
            "⚠️ I couldn't load your order history. Please make sure the FastAPI server is running.",
            "ai"
        );

    }
}