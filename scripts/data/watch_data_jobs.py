"""Keep authorized downloads resumable overnight and refresh the artifact inventory.

Never submits an AppEEARS task: every AppEEARS restart includes its recorded task ID.
No credentials or bearer tokens are read or written by this supervisor.
"""

from __future__ import annotations

import json
import shlex
import shutil
import subprocess
import time
from pathlib import Path

from common import DEFAULT_CACHE, ROOT, now, write_json
from update_inventory import alive, build, read

PRIMARY_LOG = Path(
    "/tmp/claude-1000/-home-viet-projects-nasa/77cd2c5b-4676-4de5-9344-08fa2a4e1124/scratchpad/appeears.log"
)
PRIMARY_ID = "cda894d8-b108-48e9-bb21-4197c438c0ee"
SECOND_ID = "29e9d95a-58e2-4e37-a0ac-4309cd0428d4"


def finished(name):
    if name in ("imerg_monthly", "imerg_late", "gldas"):
        p = read(DEFAULT_CACHE / name / "progress.json", {})
        return p.get("completed", 0) == p.get("requested", -1)
    if name.startswith("nex_"):
        data = read(
            ROOT / "apps/api/src/fieldshift/resources/projections" / (name[4:] + ".json"), {}
        )
        return len(data.get("series", [])) == 8 and all(
            len(s["values"]) == 312 for s in data["series"]
        )
    primary = (DEFAULT_CACHE / "appeears/bundles" / PRIMARY_ID / "processed_summary.json").exists()
    second = (DEFAULT_CACHE / "appeears/bundles" / SECOND_ID / "processed_summary.json").exists()
    return {
        "appeears_primary": primary,
        "appeears_thermal_hls": second,
        "appeears_process": primary and second,
    }.get(name, False)


def main():
    time.sleep(1)  # Allow launcher to persist this supervisor PID before its first refresh.
    deadline = time.monotonic() + 86400
    last_status = None
    while time.monotonic() < deadline:
        jobs = read(DEFAULT_CACHE / "jobs.json", [])
        for job in jobs:
            name = job["name"]
            if name == "inventory_watch":
                continue
            done = finished(name)
            job["complete"] = done
            if not done and not alive(job["pid"]) and job.get("restart_count", 0) < 3:
                command = shlex.split(job["resume"].split(" && ", 1)[1])
                command[0] = str(ROOT / ".venv/bin/python")
                if (
                    name.startswith("appeears_")
                    and name != "appeears_process"
                    and "--task-id" not in command
                ):
                    raise RuntimeError("Refusing AppEEARS restart without task ID")
                with (ROOT / job["log"]).open("ab") as log:
                    p = subprocess.Popen(
                        ["nohup", *command],
                        cwd=ROOT,
                        stdin=subprocess.DEVNULL,
                        stdout=log,
                        stderr=log,
                        start_new_session=True,
                    )
                job["previous_pid"] = job["pid"]
                job["pid"] = p.pid
                job["restart_count"] = job.get("restart_count", 0) + 1
                print(now(), "resumed", name, "pid", p.pid, flush=True)
            job["running"] = alive(job["pid"])
        if PRIMARY_LOG.exists() and not next(
            (j.get("restart_count", 0) for j in jobs if j["name"] == "appeears_primary"), 0
        ):
            shutil.copyfile(PRIMARY_LOG, ROOT / ".fieldshift/logs/appeears_primary.log")
        write_json(DEFAULT_CACHE / "jobs.json", jobs)
        inventory = build()
        status = {s["source"]: s["status"] for s in inventory["sources"]}
        if status != last_status:
            print(now(), json.dumps(status), flush=True)
            last_status = status
        work = [j for j in jobs if j["name"] != "inventory_watch"]
        if work and all(j.get("complete") for j in work):
            print(now(), "All download and processing jobs complete.", flush=True)
            return
        time.sleep(30)
    print(
        now(), "Supervisor reached 24-hour limit; resume commands remain in inventory.", flush=True
    )


if __name__ == "__main__":
    main()
