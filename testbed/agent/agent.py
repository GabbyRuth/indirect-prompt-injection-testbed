import os
import json
from dotenv import load_dotenv
from groq import Groq
from .tools import read_file, summarize_document, search_local_docs, send_message, write_file
from .defenses import get_system_prompt
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
            "name": "summarize_document",
            "description": "Read a local document and return a concise summary of its contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Name of the document to summarize, such as report.txt"
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
        "name": "send_message",
        "description": "Send a simulated message to a recipient.",
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
}
]

MAX_STEPS = 20

def run_agent(user_task: str, assets_dir = None, defense: str = "baseline") -> str:
    logger = AgentLogger(MODEL, user_task, defense, max_steps=10)

    messages = [
        {
            "role": "system",
            "content": get_system_prompt(defense)
        },
        {
            "role": "user",
            "content": user_task
        }
    ]

    try:
        for step in range(MAX_STEPS):
            print(f"\n--- Agent Step {step + 1} ---")

            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0
            )

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

                        if function_name == "read_file":
                            result = read_file(arguments["filename"], assets_dir)
                        elif function_name == "summarize_document":
                            result = summarize_document(arguments["filename"], assets_dir)
                        elif function_name == "search_local_docs":
                            result = search_local_docs(arguments["query"], assets_dir)

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
                        else:
                            result = f"Error: Unknown tool '{function_name}'"

                    except Exception as e:
                        result = f"Error executing tool: {e}"

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

