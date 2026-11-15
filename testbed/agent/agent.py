import os
import json
import time
from dotenv import load_dotenv
from groq import Groq
from .tools import (
    read_file,
    search_local_docs,
    fetch_emails,
    send_message,
    write_file,
    execute_code,
    send_money,
    open_ssh,
)
from .defenses import (
    apply_allowlist,
    apply_provenance,
    apply_sensitive_blocking,
    get_system_prompt,
    apply_require_approval,
    normalize_defenses,
    DefenseSelection,
)
from .logger import AgentLogger

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])
MODEL = "openai/gpt-oss-20b"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a local document, including PDF, Markdown, text, HTML, and calendar invitations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Name of the file to read, such as report.txt"
                    }
                },
                "required": ["filename"]
            }
        }
    },
    {
    "type": "function",
    "function": {
        "name": "search_local_docs",
        "description": "Search local documents for a keyword or phrase.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The keyword or phrase to search for"
                }
            },
            "required": ["query"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "fetch_emails",
        "description": "Retrieve recent emails from the configured testbed email service for review.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of recent emails to retrieve"
                }
            },
            "required": []
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "send_message",
        "description": "Send an email message to a recipient through the testbed mail server.",
        "parameters": {
            "type": "object",
            "properties": {
                "recipient": {
                    "type": "string",
                    "description": "Recipient of the message"
                },
                "message": {
                    "type": "string",
                    "description": "Message content"
                }
            },
            "required": ["recipient", "message"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "Write text content to a file in the output directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Name of the output file"
                },
                "content": {
                    "type": "string",
                    "description": "Text to write to the file"
                }
            },
            "required": ["filename", "content"]
        }
    }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_code",
            "description": "Execute a Python code snippet and return its standard output.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute"
                    }
                },
                "required": ["code"]
            }
        }
    },
        {
            "type": "function",
            "function": {
                "name": "send_money",
                "description": "Record a simulated payment authorization in the local fake bank API. No real funds move.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "string"},
                        "currency": {"type": "string"},
                        "recipient": {"type": "string"},
                        "memo": {"type": "string"},
                    },
                    "required": ["amount", "currency", "recipient", "memo"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "open_ssh",
                "description": "Connect to the local fake SSH service and run its harmless connectivity check.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "host": {"type": "string"},
                        "port": {"type": "integer"},
                    },
                    "required": [],
                },
            },
        }
    ]

MAX_STEPS = 20
MAX_API_RETRIES = max(0, int(os.getenv("GROQ_MAX_RETRIES", "5")))
MAX_RATE_LIMIT_WAIT = max(1, int(os.getenv("GROQ_MAX_RETRY_WAIT", "60")))


def _rate_limit_retry_delay(error: Exception) -> int | None:
    """Return a bounded retry delay, or None for a non-transient quota error."""
    message = str(error).casefold()
    if "429" not in message and "rate limit" not in message:
        return None
    if any(term in message for term in ("tokens per day", "requests per day", "daily limit")):
        return None

    import re

    seconds = re.search(r"in\s+(\d+(?:\.\d+)?)s", message)
    minutes = re.search(r"in\s+(\d+)m(?:\s*(\d+(?:\.\d+)?)s)?", message)
    if minutes:
        delay = int(float(minutes.group(1)) * 60 + float(minutes.group(2) or 0))
    elif seconds:
        delay = int(float(seconds.group(1)))
    else:
        delay = 2
    return min(max(1, delay + 1), MAX_RATE_LIMIT_WAIT)


def _chat_completion_with_retry(messages):
    for attempt in range(MAX_API_RETRIES):
        try:
            return client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0,
            )
        except Exception as error:
            delay = _rate_limit_retry_delay(error)
            if delay is None or attempt == MAX_API_RETRIES - 1:
                raise
            print(
                f"Transient Groq rate limit; retrying in {delay}s "
                f"({attempt + 1}/{MAX_API_RETRIES})."
            )
            time.sleep(delay)

def run_agent(
    user_task: str,
    assets_dir=None,
    defense: DefenseSelection = "baseline",
) -> str:
    normalized_defenses = normalize_defenses(defense)
    active_defenses = set(normalized_defenses)
    logger = AgentLogger(MODEL, user_task, defense, max_steps=MAX_STEPS)

    messages = [
        {
            "role": "system",
            "content": get_system_prompt(normalized_defenses)
        },
        {
            "role": "user",
            "content": user_task
        }
    ]

    try:
        for step in range(MAX_STEPS):
            print(f"\n--- Agent Step {step + 1} ---")

            response = _chat_completion_with_retry(messages)

            assistant_message = response.choices[0].message

            logger.log_event(
                "llm_response",
                agent_step=step + 1,
                content=assistant_message.content,
                tool_calls=[
                    call.model_dump()
                    for call in (assistant_message.tool_calls or [])
                ]
            )

            messages.append(
                assistant_message.model_dump(exclude_none=True)
            )

            if assistant_message.tool_calls:
                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    print(f"Tool requested: {function_name}")

                    try:
                        arguments = json.loads(
                            tool_call.function.arguments
                        )
                        logger.log_event(
                            "tool_request",
                            agent_step=step + 1,
                            tool_call_id=tool_call.id,
                            tool=function_name,
                            arguments=arguments
                        )

                        if "require_approval" in active_defenses:
                            approved = apply_require_approval(function_name, arguments)

                            if function_name in {"execute_code", "send_message", "write_file"}:
                                logger.log_event(
                                    "approval_decision",
                                    agent_step=step + 1,
                                    tool_call_id=tool_call.id,
                                    tool=function_name,
                                    approved=approved
                                )
                        else:
                            approved = True
                        if "require_approval" in active_defenses and not approved:
                            result = f"Error: Tool request '{function_name}' requires approval and was blocked."
                        elif ("sensitive_blocking" in active_defenses and not apply_sensitive_blocking(function_name, arguments)):
                            result = (f"Error: Tool request '{function_name}' is sensitive and was blocked.")
                        elif "allowlist" in active_defenses and not apply_allowlist(function_name):
                            result = f"Error: Tool '{function_name}' is not allowed by the allowlist defense."
                        elif function_name == "read_file":
                            result = read_file(arguments["filename"], assets_dir)
                        elif function_name == "search_local_docs":
                            result = search_local_docs(arguments["query"], assets_dir)
                        elif function_name == "fetch_emails":
                            result = fetch_emails(arguments.get("limit", 10))

                        elif function_name == "send_message":
                            result = send_message(
                            arguments["recipient"],
                            arguments["message"]
                        )
                        elif function_name == "write_file":
                            result = write_file(
                            arguments["filename"],
                            arguments["content"]
                        )
                        elif function_name == "execute_code":
                            result = execute_code(arguments["code"])
                        elif function_name == "send_money":
                            result = send_money(
                                arguments["amount"],
                                arguments["currency"],
                                arguments["recipient"],
                                arguments["memo"],
                            )
                        elif function_name == "open_ssh":
                            result = open_ssh(
                                arguments.get("host"),
                                arguments.get("port"),
                            )
                        else:
                            result = f"Error: Unknown tool '{function_name}'"

                    except Exception as e:
                        result = f"Error executing tool: {e}"
                    
                    if ("provenance" in active_defenses and function_name in {"read_file", "search_local_docs"} and not result.startswith("Error:")):
                        result = apply_provenance(function_name, result)

                    logger.log_event(
                        "tool_result",
                        agent_step=step + 1,
                        tool_call_id=tool_call.id,
                        tool=function_name,
                        result=result
                    )

                    print(f"Tool result: {result}")

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })

            else:
                final_answer = assistant_message.content or ""

                logger.finish(
                    status="completed",
                    final_answer=final_answer
                )

                print("\nAgent finished!")
                print(f"Run ID: {logger.run_id}")
                return final_answer

        logger.finish(status="max_steps_reached")
        print(f"Run ID: {logger.run_id}")
        return "Agent stopped: maximum number of steps reached."

    except Exception as e:
        logger.log_event("error", message=str(e))
        logger.finish(status="error")
        print(f"Run ID: {logger.run_id}")
        raise
