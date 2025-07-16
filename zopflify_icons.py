#!/usr/bin/env python

import concurrent.futures
import datetime
import os
import pathlib
import re
import subprocess
import time

from concurrent.futures import ProcessPoolExecutor


MAX_WORKERS = round(os.cpu_count() * 0.75)


def compress(path):
    start_time = time.monotonic()

    proc = subprocess.run(
        [
            "zopflipng",
            "--iterations=100",
            "--filters=01234mepb",
            "--lossy_8bit",
            "--lossy_transparent",
            "-y",
            str(path),
            str(path),
        ],
        stdout=subprocess.PIPE,
        encoding="utf8",
    )

    input_size = None
    result_size = None
    for line in proc.stdout.splitlines():
        if (m := re.match(r"Input size: ([0-9]*)", line)) is not None:
            input_size = int(m.group(1))
        if (m := re.match(r"Result size: ([0-9]*)", line)) is not None:
            result_size = int(m.group(1))

    elapsed_time = time.monotonic() - start_time
    return path, input_size, result_size, elapsed_time


def main():
    start_time = time.monotonic()

    tree_root = pathlib.Path(".")
    paths = []
    for dirpath, dirnames, filenames in tree_root.walk():
        for filename in filenames:
            if filename.endswith(".png"):
                path = dirpath / filename
                paths.append(path)

    total_initial_size = 0
    total_result_size = 0
    total_final_size = 0
    num_files = len(paths)

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(compress, path) for path in paths]

        num_completed = 0
        for fut in concurrent.futures.as_completed(futures):
            path, initial_size, result_size, path_time = fut.result()

            num_completed += 1
            total_initial_size += initial_size
            total_result_size += result_size
            total_final_size += min(initial_size, result_size)
            percent_original = 100 * total_final_size / total_initial_size
            elapsed_time = time.monotonic() - start_time

            print(
                f"({num_completed:4}/{num_files:4})"
                f"  {initial_size:6}"
                f"  {result_size:6}"
                f"  {total_initial_size:9}"
                f"  {total_result_size:9}"
                f"  {total_final_size:9}"
                f"  {percent_original:6.5}"
                f"  {path_time:6.5}"
                f"  {elapsed_time:7.6}"
                f"  {elapsed_time*(num_files/num_completed-1):7.6}"
                f"  {path}",
                flush=True,
            )

    elapsed_time = time.monotonic() - start_time
    print(
        f"Total time: {datetime.timedelta(seconds=elapsed_time)}"
        f" ({elapsed_time} seconds)"
    )


if __name__ == '__main__':
    main()
