#!/usr/bin/env python3
"""
Basic SMB Benchmarking Tool

Example Usage:

    Windows
    python smb_bench.py "Z:\SMBTarget" "C:\LocalSource" "SetupRun" --large-mb 1000 --small-count 2000
    python smb_bench.py "Z:\SMBTarget" "C:\LocalSource" "TestRun_01" --no-gen

    Mac
    python3 smb_bench.py /Volumes/Target /Users/Me/LocalSource "MacTest_01" --large-mb 1000 --small-count 1000
"""
import os
import time
import shutil
import argparse
import uuid
import json
import random
from pathlib import Path
from datetime import datetime

class SMBBenchmarker:
    """
    Basic SMB Benchmarking Tool
    """
    def __init__(self, target_path, source_path, test_name,
                 large_file_size_mb=1000,
                 small_file_count=1000,
                 small_min_kb=10,
                 small_max_kb=100,
                 no_generation=False):
        """
        Docstring for __init__

        :param self: Description
        :param target_path: Description
        :param source_path: Description
        :param test_name: Description
        :param large_file_size_mb: Description
        :param small_file_count: Description
        :param small_min_kb: Description
        :param small_max_kb: Description
        :param no_generation: Description
        """

        self.target = Path(target_path)
        self.source = Path(source_path)
        self.test_name = test_name
        self.no_generation = no_generation

        # Config
        self.large_size = large_file_size_mb * 1024 * 1024
        self.small_count = small_file_count
        self.small_min_size = small_min_kb * 1024
        self.small_max_size = small_max_kb * 1024

        self.results = {
            "test_name": test_name,
            "timestamp": datetime.now().isoformat(),
            "config": {
                "mode": "NO-GENERATION (Real Files)" if no_generation else "SYNTHETIC (Generated)",
                "large_file_mb": large_file_size_mb,
                "small_files_count": small_file_count,
                "small_min_kb": small_min_kb,
                "small_max_kb": small_max_kb,
                "total_small_files_mb": 0  # To be calculated
            },
            "large_file": {},
            "small_files": {}
        }

        # Directories
        self.local_staging = self.source / "smb_bench_staging"
        self.remote_staging = self.target / f"smb_bench_target_{test_name}"
        self.report_dir = self.source / "smb_bench_reports"

        # Prepare Local Dirs
        self.local_staging.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def _generate_file(self, path, size_bytes):
        """Generates a file with random data. Optimized for speed."""
        chunk_size = 1024 * 1024  # 1MB chunk
        with open(path, 'wb') as f:
            chunk = os.urandom(min(size_bytes, chunk_size))
            written = 0
            while written < size_bytes:
                bytes_to_write = min(size_bytes - written, len(chunk))
                f.write(chunk[:bytes_to_write])
                written += bytes_to_write

    def _calculate_metrics(self, bytes_transferred, time_seconds, file_count=1):
        """Calculates performance metrics for the given transfer."""
        if time_seconds == 0: return {}

        mb_per_sec = (bytes_transferred / 1_000_000) / time_seconds
        mib_per_sec = (bytes_transferred / 1_048_576) / time_seconds
        mbps = (bytes_transferred * 8) / 1_000_000 / time_seconds
        files_per_sec = file_count / time_seconds

        return {
            "seconds": round(time_seconds, 3),
            "mbps": round(mbps, 2),
            "MB_s": round(mb_per_sec, 2),
            "MiB_s": round(mib_per_sec, 2),
            "files_sec": round(files_per_sec, 1)
        }

    def setup_large_file(self):
        """Sets up the large test file."""
        fpath = self.local_staging / "large_test_file.bin"

        # CASE 1: No Generation Mode
        if self.no_generation:
            if fpath.exists():
                actual_size = fpath.stat().st_size
                print(f"[INFO] No-Gen Mode: Using existing large file ({actual_size/1024/1024:.2f} MB)")
                # Update Config to reflect reality
                self.large_size = actual_size
                self.results['config']['large_file_mb'] = round(actual_size / 1024 / 1024, 2)
                return fpath
            else:
                print(f"[ERROR] No-Gen Mode enabled but {fpath} not found.")
                return None

        # CASE 2: Normal Mode
        if fpath.exists() and fpath.stat().st_size == self.large_size:
            print(f"[INFO] Using existing large file: {fpath}")
        else:
            print(f"[SETUP] Generating {self.large_size/1024/1024:.2f} MB large file...")
            self._generate_file(fpath, self.large_size)
        return fpath

    def setup_small_files(self):
        """Sets up the small test files."""
        small_dir = self.local_staging / "small_files"
        small_dir.mkdir(exist_ok=True)

        existing = list(small_dir.glob("*.bin"))

        # CASE 1: No Generation Mode
        if self.no_generation:
            if len(existing) > 0:
                print(f"[INFO] No-Gen Mode: Using {len(existing)} existing small files.")

                # Calculate real stats
                sizes = [f.stat().st_size for f in existing]
                total_size = sum(sizes)
                min_size = min(sizes)
                max_size = max(sizes)

                # Update Config to reflect reality
                self.small_count = len(existing)
                self.results['config']['small_files_count'] = self.small_count
                self.results['config']['small_min_kb'] = round(min_size / 1024, 2)
                self.results['config']['small_max_kb'] = round(max_size / 1024, 2)
                self.results['config']['total_small_files_mb'] = round(total_size / 1024 / 1024, 2)

                print(f"       -> Total Size: {total_size/1024/1024:.2f} MB")
                return small_dir
            else:
                print(f"[ERROR] No-Gen Mode enabled but no .bin files found in {small_dir}")
                return None

        # CASE 2: Normal Mode
        # If count matches, reuse. If not, regenerate.
        if len(existing) == self.small_count:
            print(f"[INFO] Using {len(existing)} existing small files.")
            # Still update total size for report
            total_size = sum(f.stat().st_size for f in existing)
            self.results['config']['total_small_files_mb'] = round(total_size / 1024 / 1024, 2)
            return small_dir

        print(f"[SETUP] Generating {self.small_count} small files ({self.small_min_size/1024:.1f}KB - {self.small_max_size/1024:.1f}KB)...")
        shutil.rmtree(small_dir, ignore_errors=True)
        small_dir.mkdir()

        total_gen_size = 0
        for i in range(self.small_count):
            size = random.randint(self.small_min_size, self.small_max_size)
            self._generate_file(small_dir / f"small_{i}.bin", size)
            total_gen_size += size

        print(f"[SETUP] Total small files size: {total_gen_size/1024/1024:.2f} MB")
        self.results['config']['total_small_files_mb'] = round(total_gen_size / 1024 / 1024, 2)
        return small_dir

    def run_large_test(self, local_file):
        """Runs the large file test."""
        if not local_file: return

        print("\n--- Starting Large File Test (Throughput) ---")
        remote_file = self.remote_staging / local_file.name
        self.remote_staging.mkdir(parents=True, exist_ok=True)

        # UPLOAD
        print(f"Uploading {local_file.name} to {self.remote_staging}...")
        start = time.perf_counter()
        shutil.copy2(local_file, remote_file)
        duration = time.perf_counter() - start

        metrics = self._calculate_metrics(self.large_size, duration)
        print(f"-> Upload: {metrics['seconds']}s | {metrics['MB_s']} MB/s ({metrics['mbps']} Mbps)")
        self.results['large_file']['upload'] = metrics

        # DOWNLOAD
        # Note: We still use a temp filename for download to ensure we don't overwrite source
        local_temp = self.local_staging / f"download_temp_{uuid.uuid4()}.bin"
        print(f"Downloading back to local...")

        if hasattr(os, 'sync'): os.sync()

        start = time.perf_counter()
        shutil.copy2(remote_file, local_temp)
        duration = time.perf_counter() - start

        metrics = self._calculate_metrics(self.large_size, duration)
        print(f"-> Download: {metrics['seconds']}s | {metrics['MB_s']} MB/s ({metrics['mbps']} Mbps)")
        self.results['large_file']['download'] = metrics

        # Cleanup
        local_temp.unlink(missing_ok=True)
        remote_file.unlink(missing_ok=True)

    def run_small_test(self, local_dir):
        """Runs the small file test."""
        if not local_dir: return

        print("\n--- Starting Small File Test (Latency/Metadata) ---")
        remote_dir = self.remote_staging / "small_files_remote"
        remote_dir.mkdir(parents=True, exist_ok=True)

        files = list(local_dir.glob("*.bin"))
        total_size = sum(f.stat().st_size for f in files)
        file_count = len(files)

        # UPLOAD
        print(f"Uploading {file_count} files ({total_size/1024/1024:.2f} MB total)...")
        start = time.perf_counter()
        for f in files:
            shutil.copy2(f, remote_dir / f.name)
        duration = time.perf_counter() - start

        metrics = self._calculate_metrics(total_size, duration, file_count)
        print(f"-> Upload: {metrics['seconds']}s | {metrics['files_sec']} files/sec | {metrics['MB_s']} MB/s")
        self.results['small_files']['upload'] = metrics

        # DOWNLOAD
        local_temp_dir = self.local_staging / "small_files_temp_down"
        local_temp_dir.mkdir(exist_ok=True)

        print(f"Downloading batch back to local...")
        start = time.perf_counter()
        for f in files:
            shutil.copy2(remote_dir / f.name, local_temp_dir / f.name)
        duration = time.perf_counter() - start

        metrics = self._calculate_metrics(total_size, duration, file_count)
        print(f"-> Download: {metrics['seconds']}s | {metrics['files_sec']} files/sec | {metrics['MB_s']} MB/s")
        self.results['small_files']['download'] = metrics

        # Cleanup
        shutil.rmtree(local_temp_dir)
        shutil.rmtree(remote_dir)

    def cleanup_remote(self):
        """Cleans up the remote staging directory."""
        try:
            if self.remote_staging.exists():
                shutil.rmtree(self.remote_staging)
        except Exception as e:
            print(f"[WARN] Could not fully clean remote directory: {e}")

    def save_report(self):
        """Saves the benchmark report to a JSON file."""
        report_file = self.report_dir / f"SMB_Report_{self.test_name}_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=4)
        print(f"\n[DONE] Detailed report saved to: {report_file}")

        print("\n" + "="*75)
        print(f"SUMMARY: {self.test_name}")
        if self.no_generation: print("(NO-GENERATION MODE - REAL FILES USED)")
        print("="*75)
        print(f"{'Metric':<20} | {'Upload':<25} | {'Download':<25}")
        print("-" * 75)

        if 'upload' in self.results['large_file']:
            l_up = self.results['large_file']['upload']
            l_down = self.results['large_file']['download']
            l_up_str = f"{l_up['MB_s']} MB/s ({l_up['mbps']} Mbps)"
            l_down_str = f"{l_down['MB_s']} MB/s ({l_down['mbps']} Mbps)"
            print(f"{'Large File Seq':<20} | {l_up_str:<25} | {l_down_str:<25}")
        else:
            print(f"{'Large File Seq':<20} | {'SKIPPED':<25} | {'SKIPPED':<25}")

        print("-" * 75)

        if 'upload' in self.results['small_files']:
            s_up = self.results['small_files']['upload']
            s_down = self.results['small_files']['download']
            s_up_str = f"{s_up['files_sec']} files/s ({s_up['MB_s']} MB/s)"
            s_down_str = f"{s_down['files_sec']} files/s ({s_down['MB_s']} MB/s)"
            print(f"{'Small File Rand':<20} | {s_up_str:<25} | {s_down_str:<25}")
        else:
            print(f"{'Small File Rand':<20} | {'SKIPPED':<25} | {'SKIPPED':<25}")

        print("="*75)

def main():
    """Main function to parse arguments and run the SMB benchmark."""
    parser = argparse.ArgumentParser(description="Synthetic SMB Speed Test Tool")
    parser.add_argument("target", help="Target SMB Path")
    parser.add_argument("source", help="Local staging directory")
    parser.add_argument("name", help="Test Run Name")

    # Optional arguments
    parser.add_argument("--large-mb", type=int, default=1000, help="Large file size (MB)")
    parser.add_argument("--small-count", type=int, default=500, help="Small file count")
    parser.add_argument("--small-min-kb", type=int, default=10, help="Min small file size (KB)")
    parser.add_argument("--small-max-kb", type=int, default=100, help="Max small file size (KB)")

    # New flag
    parser.add_argument("--no-gen", action="store_true", help="Safe Mode: Do not generate or delete local source files. Use existing only.")

    args = parser.parse_args()

    print(f"Initializing SMB Bench: {args.name}")
    if args.no_gen: print("[MODE] NO-GENERATION (Using existing files only)")

    bench = SMBBenchmarker(
        args.target,
        args.source,
        args.name,
        large_file_size_mb=args.large_mb,
        small_file_count=args.small_count,
        small_min_kb=args.small_min_kb,
        small_max_kb=args.small_max_kb,
        no_generation=args.no_gen
    )

    try:
        large_file = bench.setup_large_file()
        small_dir = bench.setup_small_files()

        # Only run tests if setup (or finding files) was successful
        if large_file:
            bench.run_large_test(large_file)
        if small_dir:
            bench.run_small_test(small_dir)

        bench.save_report()
    except KeyboardInterrupt:
        print("\n[!] Test cancelled by user.")
    except Exception as e:
        print(f"\n[!] Error during execution: {e}")
    finally:
        print("Cleaning up remote artifacts...")
        bench.cleanup_remote()

if __name__ == "__main__":
    main()
