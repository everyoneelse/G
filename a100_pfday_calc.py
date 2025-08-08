#!/usr/bin/env python3
import math
from typing import Dict

TARGET_PF_DAYS = 1.0  # compute budget

# 1 PF-day = 1000 TFLOP/s * day
TFLOPS_PER_PFLOPS = 1000.0

def required_gpus(tflops_per_gpu: float, target_pf_days: float = TARGET_PF_DAYS) -> float:
    """Return the fractional number of GPUs needed to reach target PF-days in one day at theoretical peak."""
    if tflops_per_gpu <= 0:
        raise ValueError("TFLOPS per GPU must be positive")
    total_required_tflops = TFLOPS_PER_PFLOPS * target_pf_days
    return total_required_tflops / tflops_per_gpu


def main() -> None:
    scenarios: Dict[str, float] = {
        "A100 80GB SXM FP16/BF16 (dense) 312 TFLOPS": 312.0,
        "A100 80GB SXM FP16/BF16 (2:1 sparse) 624 TFLOPS": 624.0,
        "A100 80GB SXM TF32 156 TFLOPS": 156.0,
    }

    print(f"Target: {TARGET_PF_DAYS} PF-day\n")
    header = f"{'Scenario':60}  {'TFLOPS/GPU':>12}  {'GPUs (float)':>13}  {'GPUs (ceil)':>12}"
    print(header)
    print("-" * len(header))

    for name, tflops in scenarios.items():
        n = required_gpus(tflops)
        n_ceil = math.ceil(n - 1e-12)
        print(f"{name:60}  {tflops:12.1f}  {n:13.3f}  {n_ceil:12d}")

    print("\nNote: This uses theoretical peak throughput; real training usually achieves 30–60% of peak.")


if __name__ == "__main__":
    main()