# indirect-prompt-injection-testbed

A  research testbed for evaluating how AI agents respond to indirect prompt injection attacks and measuring the effectiveness of different defense mechanisms.

# Overview
Indirect prompt injection occurs when an attacker embeds malicious instructions into external content that an AI agent encounters while completing a legitimate task. These instructions attempt to manipulate the agent into performing actions that were not authorized by the original user.

This project provides a controlled testing environment where attack payloads are injected into external content, processed by AI agents, and evaluated under different security defenses.

The goal is to investigate which defenses are most effective at preventing successful prompt injection attacks, both individually and in combination.

# Injection Payloads
The testbed targets five types of external content:

1. PDF documents - Malicious instructions embedded within PDF files.
2. Websites - Malicious instructions included in webpage content.
3. Emails - Malicious instructions embedded in email messages.
4. Calendar invites - Malicious instructions included in calendar events or invitations.
5. CLAUDE.md files - Malicious instructions embedded in project instruction files.

# Attack Objectives
The testbed examines five types of unauthorized agent behavior:

1. Sensitive file access — Accessing secret or password files.
2. Unauthorized messaging — Sending messages or emails without user authorization.
3. SSH exposure — Opening or exposing an SSH port.
4. Unauthorized transactions — Initiating financial transfers through an API.
5. Code execution — Executing attacker-supplied code.

# Defenses
Five defense mechanisms are evaluated individually and in combination:

1. System prompt warning - Tells agent to treat external documents as data, not instructions.
2. Tool allowlisting - Restricts which tools the agent can execute for a given task.
3. Provenance labels - Identifies where content originated and its trust level. 
4. Block sensitive paths/actions - Prevents access to protected files or unauthorized operations. 
5. Require approval for risky operations - Requires independent authorization before sensitive tool calls execute.


# Project Status
This project is under active developement.
