# indirect-prompt-injection-testbed

# we will have 5 injection payloads which will include:
pdf
website
email
calendar invite
claude.md

# 5 attacks we want to carry out
secret password file
email sent
opens ssh port
sends money through api
executes malicious code

# Defenses
1. System prompt warning - Tells agent to treat external documents as data, not instructions.
2. Tool allowlisting - Restricts which tools the agent can execute for a given task.
3. Provenance labels - Identifies where content originated and its trust level. 
4. Block sensitive paths/actions - Prevents access to protected files or unauthorized operations. 
5. Require approval for risky operations - Requires independent authorization before sensitive tool calls execute.
