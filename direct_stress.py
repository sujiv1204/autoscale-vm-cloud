#!/usr/bin/env python3
"""Direct CPU stress test - runs in VM to generate high CPU load"""
import multiprocessing
import time
import sys


def cpu_burn():
    """Burn CPU cycles"""
    end_time = time.time() + 180  # 3 minutes
    while time.time() < end_time:
        _ = sum(i*i for i in range(10000))


if __name__ == '__main__':
    num_processes = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    print(f"Starting {num_processes} CPU-intensive processes...")

    processes = []
    for i in range(num_processes):
        p = multiprocessing.Process(target=cpu_burn)
        p.start()
        processes.append(p)
        print(f"Started process {i+1}/{num_processes}")

    print(
        f"\n🔥 All {num_processes} processes running. This will take 3 minutes...")

    for p in processes:
        p.join()

    print("✓ Stress test complete")
