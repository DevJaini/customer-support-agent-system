# Customer Support Agent System

A multi-agent customer support system built with the OpenAI Agents SDK. The system uses a triage agent to route customer requests to specialized agents for order status, refunds, and FAQs.

## Features

- Multi-agent architecture with agent handoffs
- Custom function tools for order lookup and refunds
- Input guardrails to block unrelated requests
- Web search for FAQ and current information
- Structured output using Pydantic
- Async agent execution

## Architecture

```text
Customer
   ↓
Input Guardrail
   ↓
Triage Agent
   ├── Order Status Agent → lookup_order()
   ├── Refund Agent → process_refund()
   └── FAQ Agent → WebSearchTool
```

## Tech Stack

- Python
- OpenAI Agents SDK
- Pydantic
- Web Search
- asyncio
- python-dotenv

## Example Requests
```text
"Where is my Order ORD-001?"
→ Order Status Agent

"I want a refund for order ORD-002."
→ Refund Agent

"What is the return policy?"
→ FAQ Agent

"Write me a poem about cats."
→ Blocked by the input guardrail
```
