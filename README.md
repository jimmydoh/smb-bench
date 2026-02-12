# SMB Bench - SMB/Network Share Performance Testing Tool

A comprehensive Python-based benchmarking tool for testing SMB (Server Message Block) and network share performance. This tool measures both throughput (large file transfers) and latency/metadata operations (small file operations) to provide a complete picture of your network share performance.

## Features

- **Large File Throughput Testing**: Measures sequential read/write speeds with large files
- **Small File Latency Testing**: Measures metadata operation speeds with many small files
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

## Example Usage Scenarios

### Example 1: Basic Default Test

Test a mounted SMB share with default parameters (1GB large file, 500 small files):

```bash
python src/smb_bench.py /mnt/myshare ~/smb_tests baseline_test
```

This creates a baseline performance measurement with standard settings.

### Example 2: Quick Small Test

Run a faster test with smaller file sizes for quick validation:

```bash
python src/smb_bench.py /mnt/myshare ~/smb_tests quick_test --large-mb 100 --small-count 100
```

Useful for quick checks or when testing in resource-constrained environments.

### Example 3: Large File Throughput Focus

Focus on large file throughput with a 5GB test file:

```bash
python src/smb_bench.py /mnt/myshare ~/smb_tests large_throughput --large-mb 5000 --small-count 0
```

Ideal for measuring maximum sequential transfer speeds (note: small file test will be skipped with 0 count).

### Example 4: Small File Latency Focus

Focus on metadata and small file operations with many tiny files:

```bash
python src/smb_bench.py /mnt/myshare ~/smb_tests metadata_test --large-mb 100 --small-count 5000 --small-min-kb 1 --small-max-kb 10
```

Excellent for testing scenarios with many small files like code repositories or configuration directories.

### Example 5: Mid-Size File Testing

Test with medium-sized files that are common in real-world scenarios:

```bash
python src/smb_bench.py /mnt/myshare ~/smb_tests midsize_test --large-mb 2000 --small-count 1000 --small-min-kb 50 --small-max-kb 500
```

Simulates typical office document and media file transfers.

### Example 6: No-Generation Mode (Reuse Existing Files)

Run tests using previously generated files without regenerating them:

```bash
python src/smb_bench.py /mnt/myshare ~/smb_tests repeat_test --no-gen
```

Useful for:
- Consistent test conditions across multiple runs
- Avoiding time spent generating files
- Testing with specific pre-created file content

### Example 7: Windows Share Testing

Test a Windows network share (adjust path format for your OS):

```bash
# Linux/macOS (mounted share)
python src/smb_bench.py /mnt/windows_share ~/local_staging production_test --large-mb 2000 --small-count 1000

# Windows (UNC path)
python src/smb_bench.py "\\\\server\\share" C:\\temp\\staging production_test --large-mb 2000 --small-count 1000
```

### Example 8: Comparative Testing

Run multiple tests with different parameters to compare performance:

```bash
# Test 1: Baseline
python src/smb_bench.py /mnt/myshare ~/smb_tests baseline --large-mb 1000 --small-count 500

# Test 2: Many small files
python src/smb_bench.py /mnt/myshare ~/smb_tests many_small --large-mb 1000 --small-count 2000 --small-min-kb 5 --small-max-kb 20

# Test 3: Large throughput
python src/smb_bench.py /mnt/myshare ~/smb_tests large_files --large-mb 3000 --small-count 200
```

Then compare the JSON reports to identify optimal configurations.

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
Metric               | Upload                    | Download
---------------------------------------------------------------------------
Large File Seq       | 125.43 MB/s (1003.44 Mbps) | 142.67 MB/s (1141.36 Mbps)
---------------------------------------------------------------------------
Small File Rand      | 45.2 files/s (3.21 MB/s)   | 52.8 files/s (3.87 MB/s)
===========================================================================
```

### JSON Reports

Detailed reports are saved to `<source>/smb_bench_reports/SMB_Report_<name>_<timestamp>.json`

Report structure:
```json
{
    "test_name": "baseline_test",
    "timestamp": "2026-02-12T22:30:45.123456",
    "config": {
        "large_file_mb": 1000,
        "small_files_count": 500,
        "small_min_kb": 10,
        "small_max_kb": 100,
        "no_generation": false
    },
    "large_file": {
        "upload": {
            "seconds": 8.234,
            "mbps": 1003.44,
            "MB_s": 125.43,
            "MiB_s": 119.65,
            "files_sec": 0.1
        },
        "download": { ... }
    },
    "small_files": { ... }
}
```

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

- Run multiple tests and average the results
- Close other applications using the network/disk
- Use `--no-gen` to ensure consistent test files
- Test at different times to account for network load

## Tips for Effective Testing

1. **Baseline First**: Always run a baseline test with default parameters
2. **Multiple Runs**: Run tests 3-5 times and average results for accuracy
3. **Isolate Variables**: Change one parameter at a time when comparing
4. **Document Conditions**: Note network load, time of day, and other factors
5. **Clean Tests**: Use `--no-gen` after initial generation for consistent comparisons
6. **Real-World Simulation**: Match your test parameters to your actual use case

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Author

Created by [jimmydoh](https://github.com/jimmydoh)
