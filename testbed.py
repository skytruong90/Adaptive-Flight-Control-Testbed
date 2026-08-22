from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Plant:
    pitch_deg: float = 0.0
    rate_dps: float = 0.0
    effectiveness: float = 1.0

    def step(self, command: float, dt: float) -> None:
        accel = self.effectiveness * 6.0 * command - 1.8 * self.rate_dps - 0.7 * self.pitch_deg
        self.rate_dps += accel * dt
        self.pitch_deg += self.rate_dps * dt


class Controller:
    def __init__(self, adaptive: bool):
        self.adaptive = adaptive
        self.kp = 1.2
        self.kd = 0.35

    def update(self, target: float, pitch: float, rate: float, dt: float) -> float:
        error = target - pitch
        if self.adaptive:
            self.kp = min(2.8, max(0.7, self.kp + 0.015 * abs(error) * dt - 0.003 * dt))
        return max(-1.0, min(1.0, self.kp * error / 10.0 - self.kd * rate / 10.0))


def command_profile(t: float) -> float:
    if t < 4:
        return 0.0
    if t < 16:
        return 8.0
    return -3.0


def simulate(duration: float, dt: float, adaptive: bool) -> list[dict[str, float]]:
    plant = Plant()
    controller = Controller(adaptive)
    rows: list[dict[str, float]] = []
    steps = int(duration / dt)
    for i in range(steps + 1):
        t = i * dt
        if t >= 12.0:
            plant.effectiveness = 0.55
        target = command_profile(t)
        u = controller.update(target, plant.pitch_deg, plant.rate_dps, dt)
        plant.step(u, dt)
        rows.append({"t_s": t, "target_deg": target, "pitch_deg": plant.pitch_deg,
                     "rate_dps": plant.rate_dps, "control": u, "kp": controller.kp,
                     "effectiveness": plant.effectiveness})
    return rows


def metrics(rows: list[dict[str, float]]) -> dict[str, float | int]:
    errors = [r["target_deg"] - r["pitch_deg"] for r in rows]
    rms = math.sqrt(sum(e * e for e in errors) / len(errors))
    effort = sum(abs(r["control"]) for r in rows) / len(rows)
    return {"samples": len(rows), "rms_tracking_error_deg": round(rms, 3),
            "mean_control_effort": round(effort, 3), "final_kp": round(rows[-1]["kp"], 3)}


def write(rows: list[dict[str, float]], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    with (output / "response.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    (output / "report.json").write_text(json.dumps(metrics(rows), indent=2), encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["fixed", "adaptive"], default="adaptive")
    p.add_argument("--duration", type=float, default=25.0)
    p.add_argument("--dt", type=float, default=0.02)
    p.add_argument("--output", type=Path, default=Path("artifacts"))
    a = p.parse_args()
    rows = simulate(a.duration, a.dt, a.mode == "adaptive")
    write(rows, a.output)
    print(json.dumps(metrics(rows), indent=2))


if __name__ == "__main__":
    main()
