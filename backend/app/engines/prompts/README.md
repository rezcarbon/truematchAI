# Prompt registry (server-side only)

The templates in this directory are **proprietary** and form part of the
assessment system's intellectual property.

Rules:

- Prompts are **never** exposed through any API endpoint, response body, log
  line, or error message. They are imported only by engine modules executing
  server-side.
- The current templates are **placeholder scaffolds**. They are intended to be
  reviewed and hardened (instruction tightening, output-schema enforcement,
  jailbreak resistance, evaluation) before production use.
- The stable system blocks are designed to be sent with prompt caching enabled
  (see `app/engines/client.py`) so the large instruction blocks are cached
  across the pipeline's calls.

Do not copy prompt text into documentation, tickets, or client-facing material.
