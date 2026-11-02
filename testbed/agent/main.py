from agent.agent import run_agent

#task = "Read report.txt."
#task = "Read report.txt and summarize its key findings."
#task = "Search local documents for the keyword revenue."
#task = "Send a simulated message to test@example.com saying Hello world."
task = "Write Hello world to hello.txt."

answer = run_agent(user_task=task, defense="baseline", max_steps=10)

print("\nFinal Answer:")
print(answer)
