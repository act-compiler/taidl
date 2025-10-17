import argparse
import csv
import importlib
import os
import sys

import numpy as np
import pandas as pd
from kernels import (cnn_inference_amx, cnn_inference_mix, mem_format_prop_avx,
                     rnn_inference_amx, sgemm_avx)

# Start: Importing the generated API module #
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(base_dir))

_decorator = importlib.import_module("sim.decorator")
kernel_decorator = _decorator.kernel
set_simulation_backend = _decorator.set_simulation_backend
gen_arguments = _decorator.gen_arguments
verifier = _decorator.verifier
gpu_check = _decorator.gpu_check

_api = importlib.import_module("sim.api")
oracle_api = _api
# End: Importing the generated API module #


# List of kernels to benchmark (defined in kernels.py)
kernels = [
    cnn_inference_amx,
    cnn_inference_mix,
    mem_format_prop_avx,
    rnn_inference_amx,
    sgemm_avx,
]
block_sizes = [2**i for i in range(2, 9)]

# Golden Input-output pairs to validate the simulations
golden_validation_dir = os.path.join(base_dir, "data")

# Saving results as CSV
repo_dir = os.path.dirname(os.path.dirname(os.path.dirname(base_dir)))
csv_dir = os.path.join(repo_dir, "plots", "csv")
AMX_ONEDNN_CSV = "amx-oneDNN.csv"
csv_fields = [
    'kernel',
    'blocks',
    'hbm',
    'cpu_runtime',
    'gpu_runtime',
    'sde_runtime'
]
csv_header = {
    'kernel': 'Kernel',
    'blocks': 'Blocks',
    'hbm': 'HBM size',
    'cpu_runtime': 'TAIDL-TO (CPU) (ms)',
    'gpu_runtime': 'TAIDL-TO (GPU) (ms)',
    'sde_runtime': 'Intel SDE (ms)'
}


def parse_file_data(file_path):
    data = []
    var_names = []
    dtype_map = {'i8': np.int8, 'i32': np.int32, 'f32': np.float32, 'u8': np.uint8}

    with open(file_path, "r") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        parts = line.split()
        if len(parts) >= 3 and parts[-1] in dtype_map:
            var_name = parts[0]
            ndims = int(parts[1])
            dtype_str = parts[-1]
            shape = [int(x) for x in parts[2:2 + ndims]]
            numpy_dtype = dtype_map[dtype_str]

            # Read data from next line
            i += 1
            if i >= len(lines):
                continue

            values = lines[i].strip().split()
            if numpy_dtype in [np.int8, np.int32, np.uint8]:
                data_values = [int(val) for val in values]
            else:
                data_values = [float(val) for val in values]

            array = np.array(data_values, dtype=numpy_dtype).reshape(shape)
            data.append(array)
            var_names.append(var_name)

        i += 1

    return data, var_names


def load_test_data(kernel_name):
    kernel_validation_dir = os.path.join(golden_validation_dir, kernel_name)
    if not os.path.exists(kernel_validation_dir):
        return []

    data_files = [f for f in os.listdir(kernel_validation_dir) if f.endswith('.txt')]
    if not data_files:
        return []

    all_test_data = []
    for file_name in sorted(data_files):
        try:
            file_path = os.path.join(kernel_validation_dir, file_name)
            data, var_names = parse_file_data(file_path)

            if data:
                inputs = [
                    array for array, var_name in zip(
                        data, var_names) if not var_name.startswith("out")]
                outputs = [
                    array for array, var_name in zip(
                        data, var_names) if var_name.startswith("out")]
                all_test_data.append((inputs, outputs, file_name))
        except Exception as e:
            print(f"Error reading file {file_name}: {e}")

    return all_test_data


def run_benchmark(benchmark, trials):
    kernel = benchmark['benchmark']
    name = f"{benchmark['kernel']}_{benchmark['blocks']}"

    inputs, compile_time = kernel('fsim-compile')()

    # Load and verify test data
    test_data = load_test_data(name)
    verified = 0

    if not test_data:
        print(f"Warning: No test data found for {name}, cannot verify.")

    for file_inputs, outputs, file_name in test_data:
        ans, _ = kernel('fsim')(*file_inputs)
        if verifier(ans, outputs):
            verified += 1

    # Performance measurement
    total_time = 0
    for _ in range(trials):
        test_inputs = gen_arguments(inputs)
        _, run_time = kernel('fsim')(*test_inputs)
        total_time += run_time

    avg_runtime = total_time / trials
    verified_stat = f"{verified}/{len(test_data)}" if test_data else "0/0"
    if test_data:
        verified_summary = "VERIFIED" if verified == len(test_data) else "VERIFICATION FAILED"
    else:
        verified_summary = "NOT VERIFIED"
    print(
        f"{benchmark['kernel']} SIZE:{benchmark['blocks']} | "
        f"Compile: {compile_time:.3f}ms | Runtime: {avg_runtime:.3f}ms | "
        f"{verified_summary} {verified_stat}"
    )

    return avg_runtime


def init():
    benchmarks = []

    for kernel_func in kernels:
        for block_size in block_sizes:
            benchmark, hbm_size = kernel_func(kernel_decorator, oracle_api, block_size)
            benchmarks.append({
                'benchmark': benchmark,
                'kernel': kernel_func.__name__,
                'blocks': block_size,
                'hbm': hbm_size,
            })

    preload_sde(benchmarks)

    return benchmarks


def preload_sde(benchmarks):
    csv_path = os.path.join(csv_dir, AMX_ONEDNN_CSV)
    if not os.path.exists(csv_path):
        return

    data = pd.read_csv(csv_path)
    for benchmark in benchmarks:
        matching_rows = data[
            (data[csv_header['kernel']] == benchmark['kernel']) &
            (data[csv_header['blocks']] == benchmark['blocks'])
        ]
        name = f"{benchmark['kernel']}_{benchmark['blocks']}"
        if matching_rows.empty:
            print(f"Warning: No matching Intel SDE data for {name}, skipping.")
            continue

        hbm_size = matching_rows[csv_header['hbm']].values[0]
        if hbm_size != benchmark['hbm']:
            print(f"Warning: HBM size mismatch for {name}.")
            print(f"Kernel written using Intel Intrinsics uses HBM size: {hbm_size}")
            print(f"Kernel written using TAIDL-TO uses HBM size: {benchmark['hbm']}")
            continue

        benchmark['sde_runtime'] = matching_rows[csv_header['sde_runtime']].values[0]


def save_results(results):
    os.makedirs(csv_dir, exist_ok=True)
    csv_path = os.path.join(csv_dir, AMX_ONEDNN_CSV)
    with open(csv_path, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields, restval='NA', extrasaction='ignore')
        writer.writerow(csv_header)
        writer.writerows(results)

    print("\nCompleted benchmarking AMX TAIDL-TO for oneDNN kernels.")
    print(f"Results saved to plots/csv/{AMX_ONEDNN_CSV}.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--trials', type=int, default=1, help="Number of trail runs")
    args = parser.parse_args()
    trials = args.trials

    benchmarks = init()

    # CPU Backend
    print("\nSimulation Backend: \x1b[4mCPU\x1b[0m")
    set_simulation_backend("CPU")
    for benchmark in benchmarks:
        cpu_runtime = run_benchmark(benchmark, trials)
        benchmark['cpu_runtime'] = f'{cpu_runtime:.3f}'

    # GPU Backend (if available)
    if gpu_check():
        print("\nSimulation Backend: \x1b[4mGPU\x1b[0m")
        set_simulation_backend("GPU")
        for benchmark in benchmarks:
            gpu_runtime = run_benchmark(benchmark, trials)
            benchmark['gpu_runtime'] = f'{gpu_runtime:.3f}'

    save_results(benchmarks)
