import os
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

LOG_DIR = Path(os.getenv("AGENT_LOG_DIR", str(Path(__file__).resolve().parents[2] / "logs")))


class AgentLogger:
    def __init__(self, model, user_task, defense, max_steps):
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        self.run_id = uuid4().hex

        self.data = {
            "run_id": self.run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": model,
            "user_task": user_task,
            "defense": defense,
            "max_steps": max_steps,
            "events": [],
            "final_answer": None,
            "status": "running"
        }

        # Save immediately so the run exists even if it crashes
        self.save()

    def log_event(self, event_type, **details):
        self.data["events"].append({
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **details
        })

        # Save after every event
        self.save()

    def finish(self, status, final_answer=None):
        self.data["status"] = status
        self.data["final_answer"] = final_answer
        self.data["finished_at"] = datetime.now(timezone.utc).isoformat()
        self.save()

    def save(self):
        log_path = LOG_DIR / f"{self.run_id}.json"

        with log_path.open("w", encoding="utf-8") as file:
            json.dump(self.data, file, indent=2, ensure_ascii=False)
