# SMB Bench - SMB/Network Share Performance Testing Tool

A comprehensive Python-based benchmarking tool for testing SMB (Server Message Block) and network share performance. This tool measures both throughput (large file transfers) and latency/metadata operations (small file operations) to provide a complete picture of your network share performance.

## Features

- **Large File Throughput Testing**: Measures sequential read/write speeds with large files
- **Small File Latency Testing**: Measures metadata operation speeds with many small files
- **TCP Latency Measurement**: Measures network latency to the SMB server using TCP SYN/SYN-ACK timing (no ICMP required)
- **Bidirectional Testing**: Tests both upload and download speeds
- **Flexible Configuration**: Customizable file sizes, counts, and test parameters
- **No-Generation Mode**: Run tests using existing files without regeneration
- **Detailed JSON Reports**: Save comprehensive test results for later analysis
- **Human-Readable Summaries**: Console output with formatted metrics

## Prerequisites

- Python 3.6 or higher
- Write access to both local staging directory and target SMB share
- Sufficient disk space for test files (default: ~1GB for large file test)

## Installation

No installation required! Simply clone the repository and run the script:

```bash
git clone https://github.com/jimmydoh/smb-bench.git
cd smb-bench
```

Or download the `smb_bench.py` script directly and run it.

## Usage

### Basic Syntax

```bash
python src/smb_bench.py <target> <source> <name> [options]
```

### Required Arguments

- `target`: Path to the target SMB share or network location to test
- `source`: Local directory for staging test files and storing reports
- `name`: Descriptive name for this test run (used in reports)

### Optional Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--large-mb` | 1000 | Size of the large test file in megabytes |
| `--small-count` | 500 | Number of small files to generate |
| `--small-min-kb` | 10 | Minimum size of small files in kilobytes |
| `--small-max-kb` | 100 | Maximum size of small files in kilobytes |
| `--no-gen` | False | Safe mode: Use existing files only, don't generate new ones |
| `--batch` | 1 | Number of times to run the test (generates aggregate statistics) |
| `--server` | None | Server hostname or IP for TCP latency measurement (port 445). Auto-detected from UNC paths (`\\server\share`) when not provided. |

## Example Usage Scenarios

### Example 1: Basic Default Test (Windows)

Test a mapped network drive with default parameters (1GB large file, 500 small files):

```bash
python src/smb_bench.py S:\SMBTarget C:\Temp\smb_tests baseline_test
```

This creates a baseline performance measurement with standard settings.

### Example 2: Quick Small Test (Windows)

Run a faster test with smaller file sizes for quick validation:

```bash
python src/smb_bench.py S:\SMBTarget C:\Temp\smb_tests quick_test --large-mb 100 --small-count 100
```

Useful for quick checks or when testing in resource-constrained environments.

### Example 3: Large File Throughput Focus (Windows)

Focus on large file throughput with a 5GB test file:

```bash
python src/smb_bench.py S:\SMBTarget C:\Temp\smb_tests large_throughput --large-mb 5000 --small-count 0
```

Ideal for measuring maximum sequential transfer speeds (note: small file test will be skipped with 0 count).

### Example 4: Small File Latency Focus (Windows)

Focus on metadata and small file operations with many tiny files:

```bash
python src/smb_bench.py S:\SMBTarget C:\Temp\smb_tests metadata_test --large-mb 100 --small-count 5000 --small-min-kb 1 --small-max-kb 10
```

Excellent for testing scenarios with many small files like code repositories or configuration directories.

### Example 5: UNC Path Testing (Windows)

Test a Windows network share using UNC path notation:

```bash
python src/smb_bench.py \\servername\SMBTarget C:\Temp\smb_tests unc_test --large-mb 2000 --small-count 1000
```

Useful when testing shares that aren't mapped to drive letters.

### Example 6: No-Generation Mode (Windows)

Run tests using previously generated files without regenerating them:

```bash
python src/smb_bench.py S:\SMBTarget C:\Temp\smb_tests repeat_test --no-gen
```

Useful for:
- Consistent test conditions across multiple runs
- Avoiding time spent generating files
- Testing with specific pre-created file content

### Example 7: Comparative Testing (Windows)

Run multiple tests with different parameters to compare performance:

```bash
# Test 1: Baseline
python src/smb_bench.py S:\SMBTarget C:\Temp\smb_tests baseline --large-mb 1000 --small-count 500

# Test 2: Many small files
python src/smb_bench.py S:\SMBTarget C:\Temp\smb_tests many_small --large-mb 1000 --small-count 2000 --small-min-kb 5 --small-max-kb 20

# Test 3: Large throughput
python src/smb_bench.py S:\SMBTarget C:\Temp\smb_tests large_files --large-mb 3000 --small-count 200
```

Then compare the JSON reports to identify optimal configurations.

### Example 8: Linux/macOS Testing

Test a mounted SMB share on Linux or macOS (syntax differs from Windows):

```bash
# Linux
python src/smb_bench.py /mnt/smbshare /home/user/smb_tests linux_test --large-mb 1000 --small-count 500

# macOS
python src/smb_bench.py /Volumes/SMBShare ~/smb_tests macos_test --large-mb 1000 --small-count 500
```

Note the forward slashes and different mount point conventions compared to Windows.

### Example 9: Batch Mode Testing (Windows)

Run the same test multiple times and get aggregate statistics (average, min, max):

```bash
# Run test 3 times
python src/smb_bench.py S:\SMBTarget C:\Temp\smb_tests batch_test --large-mb 1000 --small-count 500 --batch 3
```

This will:
- Execute the test 3 times
- Generate individual reports: `SMB_Report_batch_test_01_*.json`, `SMB_Report_batch_test_02_*.json`, `SMB_Report_batch_test_03_*.json`
- Generate an aggregate report: `SMB_Report_batch_test_AGGREGATE_*.json` with average, min, and max statistics
- Display aggregate console output showing performance ranges

Perfect for:
- Getting statistically reliable performance measurements
- Identifying performance variance
- Establishing performance baselines with confidence intervals
- Detecting intermittent performance issues

### Example 10: Batch Mode with No-Generation (Windows)

Combine batch mode with no-generation for consistent multi-run testing:

```bash
# First, generate files once
python src/smb_bench.py S:\SMBTarget C:\Temp\smb_tests consistent_test --large-mb 500 --small-count 250

# Then run 5 iterations using the same files
python src/smb_bench.py S:\SMBTarget C:\Temp\smb_tests consistent_test --no-gen --batch 5
```

This ensures all test runs use identical test data for the most accurate comparison.

## Understanding the Output

### Console Output

During the test, you'll see:

1. **Setup Phase**: Information about file generation or reuse
2. **Large File Test**: Upload/download speeds in MB/s and Mbps
3. **Small File Test**: Files per second and MB/s metrics
4. **Summary Table**: Consolidated results for both test types

Example output:
```
===========================================================================
SUMMARY: baseline_test
===========================================================================
TCP Latency (192.168.1.10:445): min=0.42ms | avg=0.55ms | max=0.71ms
---------------------------------------------------------------------------
Metric               | Upload                    | Download
---------------------------------------------------------------------------
Large File Seq       | 125.43 MB/s (1003.44 Mbps) | 142.67 MB/s (1141.36 Mbps)
---------------------------------------------------------------------------
Small File Rand      | 45.2 files/s (3.21 MB/s)   | 52.8 files/s (3.87 MB/s)
===========================================================================
```

### JSON Reports

Detailed reports are saved to `<source>/smb_bench_reports/SMB_Report_<name>_<timestamp>.json`

Report structure (no-gen example):
```json
{
    "test_name": "nogen_test",
    "timestamp": "2026-02-12T22:30:45.123456",
    "config": {
        "mode": "NO-GENERATION (Real Files)",
        "large_file_mb": 1000.0,
        "small_files_count": 1000,
        "small_min_kb": 10.05,
        "small_max_kb": 99.97,
        "total_small_files_mb": 53.58
    },
    "latency": {
        "server": "192.168.1.10",
        "port": 445,
        "count": 5,
        "successful": 5,
        "min_ms": 0.42,
        "avg_ms": 0.55,
        "max_ms": 0.71
    },
    "large_file": {
        "upload": {
            "seconds": 3.738,
            "mbps": 2244.39,
            "MB_s": 280.55,
            "MiB_s": 267.55,
            "files_sec": 0.3
        },
        "download": { ... }
    },
    "small_files": { ... }
}
```

### Batch Mode Reports

When using `--batch` mode (with value > 1), you'll get:

1. **Individual reports** for each run with batch suffix:
   - `SMB_Report_<name>_01_<timestamp>.json`
   - `SMB_Report_<name>_02_<timestamp>.json`
   - etc.

2. **Aggregate report** with statistics across all runs:
   - `SMB_Report_<name>_AGGREGATE_<timestamp>.json`

Aggregate report structure:
```json
{
    "batch_count": 3,
    "test_name": "batch_test",
    "timestamp": "2026-02-13T00:00:00.000000",
    "config": { ... },
    "latency": {
        "server": "192.168.1.10",
        "port": 445,
        "min_ms": 0.38,
        "avg_ms": 0.55,
        "max_ms": 0.82
    },
    "large_file": {
        "upload": {
            "MB_s_avg": 125.43,
            "MB_s_min": 120.15,
            "MB_s_max": 130.22,
            "mbps_avg": 1003.44,
            "mbps_min": 961.20,
            "mbps_max": 1041.76,
            ...
        },
        "download": { ... }
    },
    "small_files": { ... }
}
```

The aggregate report provides average (`_avg`), minimum (`_min`), and maximum (`_max`) for all metrics.

## Interpreting Results

### Large File Metrics

- **MB/s**: Megabytes per second (decimal, base-10)
- **MiB/s**: Mebibytes per second (binary, base-2)
- **Mbps**: Megabits per second (network speed)

**Good performance**: 100+ MB/s for gigabit networks, 1000+ MB/s for 10Gb networks

### Small File Metrics

- **files/sec**: Number of files transferred per second
- **MB/s**: Overall throughput including all small files

**Good performance**: 50+ files/sec indicates good metadata performance

### Performance Factors

Upload slower than download? Consider:
- Network congestion or asymmetric connection
- SMB server write caching policies
- Disk I/O on the server side

Download slower than upload? Consider:
- Read-ahead caching differences
- Client-side disk performance
- Network receive buffer sizes

## Test File Locations

The tool creates these directories:

- `<source>/smb_bench_staging/`: Local staging for test files
  - `large_test_file.bin`: The large test file
  - `small_files/`: Directory containing small test files
- `<source>/smb_bench_reports/`: JSON report files
- `<target>/smb_bench_target_<name>/`: Remote staging (cleaned up after test)

## Troubleshooting

### "No-Gen Mode enabled but file not found"

Run without `--no-gen` first to generate test files, then use `--no-gen` for subsequent runs.

### Permission denied errors

Ensure you have write access to both the source directory and target SMB share.

### Out of disk space

Reduce `--large-mb` or `--small-count` to fit available space. Default test requires ~1GB.

### Very slow small file tests

This is normal for high-latency connections or shares. Reduce `--small-count` for faster testing.

### Inconsistent results

- Run multiple tests and average the results (use `--batch` for automatic aggregation)
- Close other applications using the network/disk
- Use `--no-gen` to ensure consistent test files
- Test at different times to account for network load

## Tips for Effective Testing

1. **Baseline First**: Always run a baseline test with default parameters
2. **Multiple Runs**: Use `--batch 3` or `--batch 5` to automatically run tests multiple times and get aggregate statistics
3. **Latency Measurement**: Use `--server <hostname>` (or UNC paths like `\\server\share`) to include TCP latency metrics in results
4. **Isolate Variables**: Change one parameter at a time when comparing
5. **Document Conditions**: Note network load, time of day, and other factors
6. **Clean Tests**: Use `--no-gen` after initial generation for consistent comparisons
7. **Real-World Simulation**: Match your test parameters to your actual use case
8. **Statistical Confidence**: Batch mode provides min/max/average metrics to understand performance variance

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Author

Created by [jimmydoh](https://github.com/jimmydoh)
