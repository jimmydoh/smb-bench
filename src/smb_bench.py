import os
import time
import shutil
import argparse
import sys
import uuid
import json
from pathlib import Path
from datetime import datetime

class SMBBenchmarker:
    def __init__(self, target_path, source_path, test_name, large_file_size_mb=1000, small_file_count=1000, small_file_size_kb=10):
        self.target = Path(target_path)
        self.source = Path(source_path)
        self.test_name = test_name
        
        # Config
        self.large_size = large_file_size_mb * 1024 * 1024
        self.small_count = small_file_count
        self.small_size = small_file_size_kb * 1024
        self.results = {
            "test_name": test_name,
            "timestamp": datetime.now().isoformat(),
            "large_file": {},
            "small_files": {}
        }

        # Directories
        self.local_staging = self.source / "smb_bench_staging"
        self.remote_staging = self.target / f"smb_bench_target_{test_name}"
        
        # Prepare
        self.local_staging.mkdir(parents=True, exist_ok=True)

    def _generate_file(self, path, size_bytes):
        """Generates a file with random data. Optimized for speed."""
        chunk_size = 1024 * 1024  # 1MB chunk
        with open(path, 'wb') as f:
            # Generate one random chunk and reuse it to save CPU time
            # preventing the CPU from becoming the bottleneck
            chunk = os.urandom(min(size_bytes, chunk_size)) 
            written = 0
            while written < size_bytes:
                bytes_to_write = min(size_bytes - written, len(chunk))
                f.write(chunk[:bytes_to_write])
                written += bytes_to_write

    def _calculate_mbps(self, bytes_transferred, time_seconds):
        if time_seconds == 0: return 0
        megabits = (bytes_transferred * 8) / (1000 * 1000)
        return megabits / time_seconds

    def setup_large_file(self):
        fpath = self.local_staging / "large_test_file.bin"
        if fpath.exists() and fpath.stat().st_size == self.large_size:
            print(f"[INFO] Using existing large file: {fpath}")
        else:
            print(f"[SETUP] Generating {self.large_size/1024/1024:.2f} MB large file...")
            self._generate_file(fpath, self.large_size)
        return fpath

    def setup_small_files(self):
        small_dir = self.local_staging / "small_files"
        small_dir.mkdir(exist_ok=True)
        
        existing = list(small_dir.glob("*.bin"))
        if len(existing) == self.small_count:
            print(f"[INFO] Using {len(existing)} existing small files.")
        else:
            print(f"[SETUP] Cleaning and generating {self.small_count} small files...")
            shutil.rmtree(small_dir, ignore_errors=True)
            small_dir.mkdir()
            for i in range(self.small_count):
                self._generate_file(small_dir / f"small_{i}.bin", self.small_size)
        return small_dir

    def run_large_test(self, local_file):
        print("\n--- Starting Large File Test (Throughput) ---")
        remote_file = self.remote_staging / local_file.name
        self.remote_staging.mkdir(parents=True, exist_ok=True)

        # UPLOAD
        print(f"Uploading {local_file.name} to {self.remote_staging}...")
        start = time.perf_counter()
        shutil.copy2(local_file, remote_file)
        duration = time.perf_counter() - start
        
        mbps = self._calculate_mbps(self.large_size, duration)
        print(f"-> Upload Complete: {duration:.2f}s | Speed: {mbps:.2f} Mbps")
        self.results['large_file']['upload'] = {'seconds': duration, 'mbps': mbps}

        # DOWNLOAD
        local_temp = self.local_staging / f"download_temp_{uuid.uuid4()}.bin"
        print(f"Downloading back to {local_temp}...")
        
        # Flush basic OS buffers implies a simple sync, though not perfect cache clearing
        if hasattr(os, 'sync'): os.sync()
        
        start = time.perf_counter()
        shutil.copy2(remote_file, local_temp)
        duration = time.perf_counter() - start
        
        mbps = self._calculate_mbps(self.large_size, duration)
        print(f"-> Download Complete: {duration:.2f}s | Speed: {mbps:.2f} Mbps")
        self.results['large_file']['download'] = {'seconds': duration, 'mbps': mbps}

        # Cleanup
        local_temp.unlink(missing_ok=True)
        remote_file.unlink(missing_ok=True)

    def run_small_test(self, local_dir):
        print("\n--- Starting Small File Test (Latency/Metadata) ---")
        remote_dir = self.remote_staging / "small_files_remote"
        remote_dir.mkdir(parents=True, exist_ok=True)
        
        files = list(local_dir.glob("*.bin"))
        total_size = self.small_count * self.small_size

        # UPLOAD
        print(f"Uploading {len(files)} files to SMB...")
        start = time.perf_counter()
        for f in files:
            shutil.copy2(f, remote_dir / f.name)
        duration = time.perf_counter() - start
        
        mbps = self._calculate_mbps(total_size, duration)
        print(f"-> Batch Upload Complete: {duration:.2f}s | Speed: {mbps:.2f} Mbps | Avg: {duration/self.small_count:.4f}s/file")
        self.results['small_files']['upload'] = {'seconds': duration, 'mbps': mbps, 'files_per_sec': self.small_count/duration}

        # DOWNLOAD
        local_temp_dir = self.local_staging / "small_files_temp_down"
        local_temp_dir.mkdir(exist_ok=True)
        
        print(f"Downloading batch back to local...")
        start = time.perf_counter()
        for f in files:
            shutil.copy2(remote_dir / f.name, local_temp_dir / f.name)
        duration = time.perf_counter() - start
        
        mbps = self._calculate_mbps(total_size, duration)
        print(f"-> Batch Download Complete: {duration:.2f}s | Speed: {mbps:.2f} Mbps")
        self.results['small_files']['download'] = {'seconds': duration, 'mbps': mbps, 'files_per_sec': self.small_count/duration}

        # Cleanup
        shutil.rmtree(local_temp_dir)
        shutil.rmtree(remote_dir)

    def cleanup_remote(self):
        try:
            if self.remote_staging.exists():
                shutil.rmtree(self.remote_staging)
        except Exception as e:
            print(f"[WARN] Could not fully clean remote directory: {e}")

    def save_report(self):
        report_file = f"SMB_Report_{self.test_name}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=4)
        print(f"\n[DONE] Detailed report saved to {report_file}")
        
        # Also print a summary table
        print("\n" + "="*50)
        print(f"SUMMARY: {self.test_name}")
        print("="*50)
        print(f"{'Metric':<20} | {'Upload':<12} | {'Download':<12}")
        print("-" * 50)
        
        l_up = f"{self.results['large_file']['upload']['mbps']:.0f} Mbps"
        l_down = f"{self.results['large_file']['download']['mbps']:.0f} Mbps"
        print(f"{'Large File Seq':<20} | {l_up:<12} | {l_down:<12}")
        
        s_up = f"{self.results['small_files']['upload']['mbps']:.0f} Mbps"
        s_down = f"{self.results['small_files']['download']['mbps']:.0f} Mbps"
        print(f"{'Small File Rand':<20} | {s_up:<12} | {s_down:<12}")
        print("="*50)

def main():
    parser = argparse.ArgumentParser(description="Synthetic SMB Speed Test Tool")
    parser.add_argument("target", help="Target SMB Path (e.g. Z:\\TestFolder or \\\\Server\\Share\\Test)")
    parser.add_argument("source", help="Local staging directory")
    parser.add_argument("name", help="Name of this test run (for reporting)")
    parser.add_argument("--large-mb", type=int, default=1000, help="Size of large file in MB (default 1000)")
    parser.add_argument("--small-count", type=int, default=500, help="Number of small files (default 500)")
    
    args = parser.parse_args()

    print(f"Initializing SMB Bench: {args.name}")
    print(f"Target: {args.target}")
    
    bench = SMBBenchmarker(args.target, args.source, args.name, large_file_size_mb=args.large_mb, small_file_count=args.small_count)
    
    try:
        large_file = bench.setup_large_file()
        small_dir = bench.setup_small_files()
        
        bench.run_large_test(large_file)
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
