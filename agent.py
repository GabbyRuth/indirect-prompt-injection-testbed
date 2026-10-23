import os
import json
from dotenv import load_dotenv
from groq import Groq
from tools import read_file
from defenses import get_system_prompt
from logger import AgentLogger

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])
MODEL = "qwen/qwen3.8-27b"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a text file in the documents directory.",
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
    }
]


def run_agent(user_task: str, defense: str = "baseline", max_steps: int = 10) -> str:
    logger = AgentLogger(MODEL, user_task, defense, max_steps)

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
        for step in range(max_steps):
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
                            result = read_file(arguments["filename"])
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

