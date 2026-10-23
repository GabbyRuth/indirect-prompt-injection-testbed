from agent import run_agent

task = "Read report.txt and summarize its key findings."

answer = run_agent(user_task=task, defense="baseline", max_steps=10)

print("\nFinal Answer:")
print(answer)
