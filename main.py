import asyncio
from dotenv import load_dotenv
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

from pydantic import BaseModel
from agents import (
    Agent,
    Runner,
    function_tool,
    InputGuardrail,
    GuardrailFunctionOutput,
    input_guardrail,
    WebSearchTool,
)

load_dotenv()

# --------------------------------------------------------------------------
# Part 1: Define Custom Tools
# --------------------------------------------------------------------------

# Simulated order database (Real system you will connect to database via MCP)
ORDERS_DB = {
    "ORD-001": {
        "item": "Wireless Headphones",
        "status": "Shipped",
        "eta": "October 5",
    },
    "ORD-002": {
        "item": "Python Programming Book",
        "status": "Delivered",
        "eta": "September 29",
    },
    "ORD-003": {
        "item": "USB-C Cable 3-pack",
        "status": "Processing",
        "eta": "October 12",
    },
}


@function_tool
def lookup_order(order_id: str) -> str:
    """Look up a customer's order status using the order ID."""

    order = ORDERS_DB.get(order_id.upper())

    if not order:
        return (
            f"Order {order_id} was not found. "
            "Please check the order ID and try again."
        )

    return (
        f"Order {order_id.upper()}:\n"
        f"Item: {order['item']}\n"
        f"Status: {order['status']}\n"
        f"Estimated Arrival: {order['eta']}"
    )


@function_tool
def process_refund(order_id: str, reason: str) -> str:
    """Process a refund request for a customer's order."""

    order = ORDERS_DB.get(order_id.upper())

    if not order:
        return f"Cannot process refund: Order {order_id} was not found."

    if order["status"] == "Processing":
        return (
            f"Refund for {order_id.upper()} cannot be processed because "
            "the order has not shipped yet. The order can be cancelled instead."
        )

    return (
        f"Refund initiated for order {order_id.upper()}:\n"
        f"Item: {order['item']}\n"
        f"Reason: {reason}\n"
        "The refund amount will be credited within 5-7 business days."
    )


# --------------------------------------------------------------------------
# Part 2: Define the Input Guardrails
# --------------------------------------------------------------------------

class SupposeCheck(BaseModel):
    is_support_question: bool
    reasoning: str

guardrail_checker = Agent(
    name="Support Topic Checker",
    instructions="""
    Determine whether the user's message is a customer support question.

    Valid topics:
    - Order status
    - Refunds
    - Returns
    - Product questions
    - Shipping
    - Customer support FAQs

    Invalid topics:
    - Personal advice
    - Jokes
    - Coding help
    - Creative writing
    - Unrelated conversations

    Return is_support_question=True only for customer support topics.
    """,
    output_type=SupportCheck,
)

@input_guardrail
async def support_only(ctx, agent, input):
    """Allow only customer support related requests."""

    result = await Runner.run(
        guardrail_checker,
        input,
        context=ctx.context,
    )

    final = result.final_output_as(SupportCheck)

    return GuardrailFunctionOutput(
        output_info={
            "reasoning": final.reasoning
        },
        tripwire_triggered=not final.is_support_question,
    )

# --------------------------------------------------------------------------
# Part 3: Define Specialist Agents
# --------------------------------------------------------------------------

order_agent = Agent(
    name="Order_Status_Agent",
    handoff_description=(
        "Handles questions about order status, shipping, and delivery."
    ),
    instructions="""
    You help customers check their order status.

    Use the lookup_order tool to find order information.

    If the customer does not provide an order ID,
    ask them to provide it.

    Be friendly, clear, and professional.
    """,
    tools=[lookup_order],
)


refund_agent = Agent(
    name="Refund_Agent",
    handoff_description=(
        "Handles refund requests, returns, and cancellations."
    ),
    instructions="""
    You help customers with refunds and returns.

    Always make sure you have:
    1. The order ID
    2. The reason for the refund

    Use the process_refund tool to process the request.

    Be empathetic, clear, and helpful.
    """,
    tools=[process_refund],
)


faq_agent = Agent(
    name="FAQ_Agent",
    handoff_description=(
        "Handles general product questions and frequently asked questions."
    ),
    instructions="""
    You answer general customer questions and FAQs.

    Use web search when current information is required.

    Common topics include:
    - Shipping policies
    - Return policies
    - Product information
    - General FAQs

    Be helpful and concise.
    """,
    tools=[WebSearchTool()],
)

# --------------------------------------------------------------------------
# Part 4: Define the triage Agent
# --------------------------------------------------------------------------

triage_agent = Agent(
    name="Customer_Support_Triage",
    instructions="""
    You are the front-line customer support agent.

    Understand the customer's request and route it to
    the appropriate specialist.

    Routing rules:

    - Order status, shipping, delivery
      -> Order Status Agent

    - Refunds, returns, cancellations
      -> Refund Agent

    - General questions, product information, FAQs
      -> FAQ Agent

    Be warm, professional, and route the customer quickly.
    """,
    handoffs=[
        order_agent,
        refund_agent,
        faq_agent,
    ],
    input_guardrails=[
        support_only
    ],
)

# --------------------------------------------------------------------------
# Part 5: Run the System
# --------------------------------------------------------------------------

async def handle_customer(message: str):
    """Process a customer message through the support system."""

    print(f"Customer: {message}")

    try:
        result = await Runner.run(
            triage_agent,
            message,
        )

        print(f"Agent: {result.last_agent_name}")
        print(f"Response: {result.final_output}")

    except Exception:
        print(
            "Blocked: This does not appear to be "
            "a customer support question."
        )

    print("-" * 70)
    print()


async def main():
    print("=" * 70)
    print("CUSTOMER SUPPORT AGENT SYSTEM")
    print("=" * 70)
    print()

    # Test 1: Order Status
    await handle_customer(
        "Where is my Order ORD-001?"
    )

    # Test 2: Refund
    await handle_customer(
        "I want a refund for my order ORD-002. "
        "The book arrived damaged."
    )

    # Test 3: FAQ / Web Search
    await handle_customer(
        "Where is the Amazon return policy?"
    )

    # Test 4: Off-topic request
    await handle_customer(
        "Can you help me write a poem about cats?"
    )


if __name__ == "__main__":
    asyncio.run(main())


    

# ----------------------------- OUTPUT -----------------------------
# Test 1: Order Status (Order Status Agent -> lookup_order tool)
    await handle_customer("Where is my Order ORD-001?")

# Test 2: Refund request (Refund Agent -> process_refund tool)
    await handle_customer("I want refund of my order ORD-002. The book arrived damaged.")
    
# Test 3: General FAQ (FAQ agent -> web search)
    await handle_customer("Where is Amazon return policy?")
    
# Test 4: Off topic (Blocked by guardrail)
    await handle_customer("Can you help me write a poem about cats?")
