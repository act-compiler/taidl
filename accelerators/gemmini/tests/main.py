import argparse
import csv
import importlib
import os
import sys

import numpy as np
import pandas as pd
from exo import matmul_4, matmul_6, matmul_14, matmul_16, matmul_27, matmul_512
from tiled_matmul import tiled_matmul

# Start: Importing the generated API module #
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(base_dir))

kernel_decorator = {}
set_simulation_backend = {}
gen_arguments = {}
verifier = {}
gpu_check = {}
oracle_api = {}

for DIM in [16, 64, 256, 1024]:
    _decorator = importlib.import_module(f"sim_{DIM}.decorator")
    kernel_decorator[DIM] = _decorator.kernel
    set_simulation_backend[DIM] = _decorator.set_simulation_backend
    gen_arguments[DIM] = _decorator.gen_arguments
    verifier[DIM] = _decorator.verifier
    gpu_check[DIM] = _decorator.gpu_check

    _api = importlib.import_module(f"sim_{DIM}.api")
    oracle_api[DIM] = _api
# End: Importing the generated API module #

# List of kernels to benchmark (defined in exo.py and tiled_matmul.py)
tiled_matmul_kernel = tiled_matmul
exo_kernels = [
    (matmul_6, 12544, 64, 256),
    (matmul_4, 12544, 256, 64),
    (matmul_27, 784, 1024, 256),
    (matmul_14, 3136, 512, 128),
    (matmul_16, 3136, 128, 512),
    (matmul_512, 512, 512, 512),
]

# Golden Input-output pairs to validate the simulations
golden_validation_dir = os.path.join(base_dir, "data")

# Saving results as CSV
repo_dir = os.path.dirname(os.path.dirname(os.path.dirname(base_dir)))
csv_dir = os.path.join(repo_dir, "plots", "csv")

GEMMINI_MATMUL_CSV = "gemmini-tiled-matmul.csv"
tiled_matmul_csv_fields = [
    'DIM',
    'I',
    'df',
    'hbm',
    'cpu_runtime',
    'gpu_runtime',
    'spike_runtime'
]
tiled_matmul_csv_header = {
    'DIM': 'DIM',
    'I': 'I',
    'df': 'Dataflow',
    'hbm': 'HBM size',
    'cpu_runtime': 'TAIDL-TO (CPU) (ms)',
    'gpu_runtime': 'TAIDL-TO (GPU) (ms)',
    'spike_runtime': 'Gemmini Spike (ms)'
}

GEMMINI_EXO_CSV = "gemmini-exo.csv"
exo_csv_fields = [
    'kernel',
    'N',
    'M',
    'K',
    'hbm',
    'cpu_runtime',
    'gpu_runtime',
]
exo_csv_header = {
    'kernel': 'Kernel',
    'N': 'N',
    'M': 'M',
    'K': 'K',
    'hbm': 'HBM size',
    'cpu_runtime': 'TAIDL-TO (CPU) (ms)',
    'gpu_runtime': 'TAIDL-TO (GPU) (ms)',
}


def load_file_inputs(kernel_name):
    kernel_dir = os.path.join(base_dir, "data", kernel_name)
    if not os.path.exists(kernel_dir):
        print(f"Error: Kernel directory {kernel_dir} not found")
        return []

    data_files = [f for f in os.listdir(kernel_dir) if f.endswith('.txt')]
    if not data_files:
        print(f"Error: No data files found in {kernel_dir}")
        return []

    all_test_data = []

    for file_name in sorted(data_files):
        data = []
        try:
            file_path = os.path.join(kernel_dir, file_name)
            with open(file_path, "r") as f:
                lines = f.readlines()
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if not line:
                    i += 1
                    continue
                parts = line.split()
                if len(parts) < 2:
                    print(f"Warning: Invalid line format at line {i + 1}: {line}.")
                    i += 1
                    continue
                var_name = parts[0]
                shape = [int(DIM) for DIM in parts[1:]]
                total_elements = np.prod(shape)
                data_values = []
                i += 1
                while i < len(lines) and len(data_values) < total_elements:
                    line = lines[i].strip()
                    if line:
                        values = line.split()
                        data_values.extend([float(val) for val in values])
                    i += 1
                if len(data_values) < total_elements:
                    print(
                        f"Warning: Not enough data for variable {var_name}. Expected {total_elements}, got {len(data_values)}."
                    )
                    continue
                elif len(data_values) > total_elements:
                    print(
                        f"Warning: Too much data for variable {var_name}. Expected {total_elements}, got {len(data_values)}."
                    )
                    data_values = data_values[:total_elements]
                array = np.array(data_values, dtype=np.float64)
                array = array.reshape(shape)
                data.append(array)
        except FileNotFoundError:
            print(f"Error: File {file_name} not found")
            continue
        except Exception as e:
            print(f"Error reading file {file_name}: {e}")
            continue

        if data:
            inputs = data[:-1]
            inputs = [i.astype(np.int8) for i in inputs]
            gold = data[-1]
            gold = [gold.astype(np.int32)]
            all_test_data.append((inputs, gold, file_name))

    return all_test_data


def run_benchmark(benchmark, trials, kernel_type):
    kernel = benchmark['benchmark']
    DIM = benchmark['DIM']

    if kernel_type == "tiled_matmul":
        name = f"matmul_{DIM}_{benchmark['I']}"
    else:  # kernel_type == "exo"
        name = f"exo_{benchmark['N']}x{benchmark['M']}x{benchmark['K']}"

    inputs, compile_time = kernel('fsim-compile')()

    # Load and verify test data
    test_data = load_file_inputs(name)
    verified = 0

    if not test_data:
        print(f"Warning: No test data found for {name}, cannot verify.")

    for file_inputs, outputs, _ in test_data:
        ans, _ = kernel('fsim')(*file_inputs)
        if verifier[DIM](ans, outputs):
            verified += 1

    # Performance measurement
    total_time = 0
    for _ in range(trials):
        test_inputs = gen_arguments[DIM](inputs)
        _, run_time = kernel('fsim')(*test_inputs)
        total_time += run_time

    avg_runtime = total_time / trials
    verified_stat = f"{verified}/{len(test_data)}" if test_data else "0/0"
    if test_data:
        verified_summary = "VERIFIED" if verified == len(test_data) else "VERIFICATION FAILED"
    else:
        verified_summary = "NOT VERIFIED"

    if kernel_type == "tiled_matmul":
        print(
            f"matmul_{benchmark['df']} DIM:{benchmark['DIM']} I:{benchmark['I']} | "
            f"Compile: {compile_time:.3f}ms | Runtime: {avg_runtime:.3f}ms | "
            f"{verified_summary} {verified_stat}"
        )
    else:  # kernel_type == "exo"
        print(
            f"{benchmark['kernel']} N:{benchmark['N']} M:{benchmark['M']} K:{benchmark['K']} | "
            f"Compile: {compile_time:.3f}ms | Runtime: {avg_runtime:.3f}ms | "
            f"{verified_summary} {verified_stat}"
        )

    return avg_runtime


def save_results(results, kernel_type):
    os.makedirs(csv_dir, exist_ok=True)

    if kernel_type == "tiled_matmul":
        csv_path = os.path.join(csv_dir, GEMMINI_MATMUL_CSV)
        csv_fields = tiled_matmul_csv_fields
        csv_header = tiled_matmul_csv_header
    else:  # kernel_type == "exo"
        csv_path = os.path.join(csv_dir, GEMMINI_EXO_CSV)
        csv_fields = exo_csv_fields
        csv_header = exo_csv_header

    with open(csv_path, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields, restval='NA', extrasaction='ignore')
        writer.writerow(csv_header)
        writer.writerows(results)

    if kernel_type == "tiled_matmul":
        print("\nCompleted benchmarking all Gemmini(DIM=*) TAIDL-TOs for Tiled MatMul kernels.")
        print(f"Results saved to plots/csv/{GEMMINI_MATMUL_CSV}.")
    else:  # kernel_type == "exo"
        print("\nCompleted benchmarking Gemmini(DIM=16) TAIDL-TO for Exo kernels.")
        print(f"Results saved to plots/csv/{GEMMINI_EXO_CSV}.")


# Start: Tiled MatMul specific functions #
def tiled_matmul_init(DIM, log2I_max):
    benchmarks = []
    use_loop = 4

    for df in [0, 1]:
        for i in range(0, log2I_max + 1):
            benchmark, hbm_size = tiled_matmul_kernel(kernel_decorator[DIM],
                                                      oracle_api[DIM],
                                                      DIM=DIM,
                                                      iterations=2**i,
                                                      df=df,
                                                      xla_while=(i > use_loop))
            benchmarks.append({
                'benchmark': benchmark,
                'DIM': DIM,
                'I': 2**i,
                'df': "WS" if df == 1 else "OS",
                'hbm': hbm_size,
            })

    tiled_matmul_preload_spike(benchmarks)

    return benchmarks


def tiled_matmul_preload_spike(benchmarks):
    csv_path = os.path.join(csv_dir, GEMMINI_MATMUL_CSV)
    if not os.path.exists(csv_path):
        return

    data = pd.read_csv(csv_path)
    for benchmark in benchmarks:
        matching_rows = data[
            (data[tiled_matmul_csv_header['DIM']] == benchmark['DIM']) &
            (data[tiled_matmul_csv_header['I']] == benchmark['I']) &
            (data[tiled_matmul_csv_header['df']] == benchmark['df'])
        ]
        name = f"matmul_{benchmark['DIM']}_{benchmark['I']}"
        if matching_rows.empty:
            print(f"Warning: No matching Gemmini Spike for {name}, skipping.")
            continue

        benchmark['spike_runtime'] = matching_rows[tiled_matmul_csv_header['spike_runtime']].values[0]  # noqa: E501
# End: Tiled MatMul specific functions #


# Start: Exo specific functions #
def exo_init(DIM=16):
    benchmarks = []

    for exo_kernel in exo_kernels:
        kernel_func, N, M, K = exo_kernel
        benchmark, hbm_size = kernel_func(kernel_decorator[DIM], oracle_api[DIM])
        benchmarks.append({
            'benchmark': benchmark,
            'DIM': DIM,
            'kernel': kernel_func.__name__,
            'N': N,
            'M': M,
            'K': K,
            'hbm': hbm_size,
        })

    return benchmarks
# End: Exo specific functions #


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--trials', type=int, default=1, help="number of trial runs")
    parser.add_argument(
        '--kernel_type',
        type=str,
        choices=['tiled_matmul', 'exo'],
        required=True,
        help="which type of kernel to benchmark")

    args = parser.parse_args()
    trials = args.trials

    if args.kernel_type == 'tiled_matmul':
        DIMS = [16, 64, 256, 1024]
        log2I_max = {16: 8, 64: 6, 256: 4, 1024: 0}

        benchmarks = {}
        for DIM in DIMS:
            benchmarks[DIM] = tiled_matmul_init(DIM, log2I_max[DIM])

        # CPU Backend
        print("\nSimulation Backend: \x1b[4mCPU\x1b[0m")
        for DIM in DIMS:
            set_simulation_backend[DIM]("CPU")
            for benchmark in benchmarks[DIM]:
                cpu_runtime = run_benchmark(benchmark, trials, "tiled_matmul")
                benchmark['cpu_runtime'] = f'{cpu_runtime:.3f}'

        # GPU Backend (if available)
        if gpu_check[DIM]():
            print("\nSimulation Backend: \x1b[4mGPU\x1b[0m")
            for DIM in DIMS:
                set_simulation_backend[DIM]("GPU")
                for benchmark in benchmarks[DIM]:
                    gpu_runtime = run_benchmark(benchmark, trials, "tiled_matmul")
                    benchmark['gpu_runtime'] = f'{gpu_runtime:.3f}'

        results = []
        for DIM in DIMS:
            results.extend(benchmarks[DIM])

        results = sorted(results, key=lambda x: x['df'])
        save_results(results, "tiled_matmul")

        exit(0)

    else:  # args.kernel_type == 'exo'
        DIM = 16  # Exo kernels are only run with DIM=16

        benchmarks = exo_init(DIM)

        # CPU Backend
        print("\nSimulation Backend: \x1b[4mCPU\x1b[0m")
        set_simulation_backend[DIM]("CPU")
        for benchmark in benchmarks:
            cpu_runtime = run_benchmark(benchmark, trials, "exo")
            benchmark['cpu_runtime'] = f'{cpu_runtime:.3f}'

        # GPU Backend (if available)
        if gpu_check[DIM]():
            print("\nSimulation Backend: \x1b[4mGPU\x1b[0m")
            set_simulation_backend[DIM]("GPU")
            for benchmark in benchmarks:
                gpu_runtime = run_benchmark(benchmark, trials, "exo")
                benchmark['gpu_runtime'] = f'{gpu_runtime:.3f}'

        save_results(benchmarks, "exo")

        exit(0)
