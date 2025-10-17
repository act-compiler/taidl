import argparse
import csv
import importlib
import os
import sys

import numpy as np

# Start: Importing the generated API module #
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(base_dir))

DIM = 256  # Fixed DIM for I-BERT

_decorator = importlib.import_module(f"sim_{DIM}.decorator")
kernel = _decorator.kernel
set_simulation_backend = _decorator.set_simulation_backend
gen_arguments = _decorator.gen_arguments
gpu_check = _decorator.gpu_check

_api = importlib.import_module(f"sim_{DIM}.api")
api = _api
# End: Importing the generated API module #

# Saving results as CSV
repo_dir = os.path.dirname(os.path.dirname(os.path.dirname(base_dir)))
csv_dir = os.path.join(repo_dir, "plots", "csv")
SPIKE_IBERT_LOG = "spike-ibert.log"
IBERT_CSV = "gemmini-ibert.csv"
csv_fields = [
    'model',
    'hbm',
    'cpu_runtime',
    'gpu_runtime',
    'spike_runtime'
]
csv_header = {
    'model': 'Model',
    'hbm': 'HBM size',
    'cpu_runtime': 'TAIDL-TO (CPU) (ms)',
    'gpu_runtime': 'TAIDL-TO (GPU) (ms)',
    'spike_runtime': 'Gemmini Spike (ms)'
}

# I-BERT model parameters
LAYERS = 12
SEQ_LEN = 512
HIDDEN_DIM = 768
EXPANSION_DIM = 3072
NUM_HEADS = 12
COMPRESSION_FACTOR = 1
HIDDEN_DIM_PER_HEAD = HIDDEN_DIM // NUM_HEADS  # = 64

# Memory layout
layer_input_addr = 0
layer_output_addr = layer_input_addr + SEQ_LEN * HIDDEN_DIM

# Weight addresses
wq_addr = layer_output_addr + SEQ_LEN * HIDDEN_DIM
wk_addr = wq_addr + HIDDEN_DIM * HIDDEN_DIM
wv_addr = wk_addr + HIDDEN_DIM * HIDDEN_DIM
wo_addr = wv_addr + HIDDEN_DIM * HIDDEN_DIM
ff1_w_addr = wo_addr + HIDDEN_DIM * HIDDEN_DIM
ff2_w_addr = ff1_w_addr + HIDDEN_DIM * EXPANSION_DIM

# Bias addresses
wq_b_addr = ff2_w_addr + EXPANSION_DIM * HIDDEN_DIM
wk_b_addr = wq_b_addr + HIDDEN_DIM
wv_b_addr = wk_b_addr + HIDDEN_DIM
wo_b_addr = wv_b_addr + HIDDEN_DIM
ff1_b_addr = wo_b_addr + HIDDEN_DIM
ff2_b_addr = ff1_b_addr + EXPANSION_DIM

# Intermediate buffers for each layer
q_buf_addr = ff2_b_addr + HIDDEN_DIM
k_buf_addr = q_buf_addr + SEQ_LEN * HIDDEN_DIM
v_buf_addr = k_buf_addr + SEQ_LEN * HIDDEN_DIM
attn_buf_addr = v_buf_addr + SEQ_LEN * HIDDEN_DIM
# Need space for both int8 attention scores and int32 accumulator versions
attn_acc_buf_base = attn_buf_addr + NUM_HEADS * SEQ_LEN * SEQ_LEN  # int32 attention scores
out_buf_addr = attn_acc_buf_base + NUM_HEADS * SEQ_LEN * SEQ_LEN * 4  # int8 output buffer
# int32 accumulator (max of hidden_dim and expansion_dim)
out_buf_acc_addr = out_buf_addr + SEQ_LEN * EXPANSION_DIM
resadd1_buf_addr = out_buf_acc_addr + SEQ_LEN * EXPANSION_DIM * 4  # acc_t is 32-bit
resadd2_buf_addr = resadd1_buf_addr + SEQ_LEN * HIDDEN_DIM

zero_addr = resadd2_buf_addr + SEQ_LEN * HIDDEN_DIM
total_hbm = zero_addr + 4096
A_SP = 0
B_SP = DIM
OUT_SP = DIM * 2


@kernel(hbm=total_hbm,
        input=[
            {'addr': layer_input_addr, 'shape': (SEQ_LEN, HIDDEN_DIM), 'dtype': np.int8},
            {'addr': wq_addr, 'shape': (HIDDEN_DIM, HIDDEN_DIM), 'dtype': np.int8},
            {'addr': wk_addr, 'shape': (HIDDEN_DIM, HIDDEN_DIM), 'dtype': np.int8},
            {'addr': wv_addr, 'shape': (HIDDEN_DIM, HIDDEN_DIM), 'dtype': np.int8},
            {'addr': wo_addr, 'shape': (HIDDEN_DIM, HIDDEN_DIM), 'dtype': np.int8},
            {'addr': ff1_w_addr, 'shape': (HIDDEN_DIM, EXPANSION_DIM), 'dtype': np.int8},
            {'addr': ff2_w_addr, 'shape': (EXPANSION_DIM, HIDDEN_DIM), 'dtype': np.int8},
            {'addr': wq_b_addr, 'shape': (HIDDEN_DIM,), 'dtype': np.int32},
            {'addr': wk_b_addr, 'shape': (HIDDEN_DIM,), 'dtype': np.int32},
            {'addr': wv_b_addr, 'shape': (HIDDEN_DIM,), 'dtype': np.int32},
            {'addr': wo_b_addr, 'shape': (HIDDEN_DIM,), 'dtype': np.int32},
            {'addr': ff1_b_addr, 'shape': (EXPANSION_DIM,), 'dtype': np.int32},
            {'addr': ff2_b_addr, 'shape': (HIDDEN_DIM,), 'dtype': np.int32},
        ],
        output=[
            {'addr': layer_output_addr, 'shape': (SEQ_LEN, HIDDEN_DIM), 'dtype': np.int8},
        ]
        )
def ibert() -> None:
    api.dataflow_config(dataflow=0)

    class counter:
        matmul_count = 0

    def tiled_matmul(
            A_base,
            B_base,
            C_base,
            M,
            N,
            K,
            stride_A,
            stride_B,
            stride_C,
            count,
            stride_D=None,
            bias_addr=None,
            transpose=False,
            use_acc=False,
            repeating_bias=False):
        tile_N = N // DIM
        tile_M = M // DIM
        tile_K = K // DIM
        if (transpose):
            api.transpose(rows=K, cols=N, src_hbm_addr=B_base, dst_hbm_addr=B_base)
        api.start_loop(f"i.{count.matmul_count}", 0, tile_M)
        api.start_loop(f"j.{count.matmul_count}", 0, tile_N)
        api.mvin_spad(tiles=1, stride=DIM, hbm_addr=zero_addr, sp_addr=OUT_SP)
        if (bias_addr is None):
            if (use_acc):
                api.mvin_acc(hbm_addr=zero_addr, rows=1, acc_addr=OUT_SP)
            else:
                api.bias_load(stride=DIM, hbm_addr=zero_addr, is_full_width=1)
        else:
            if repeating_bias:
                if (use_acc):
                    api.mvin_acc_stride(
                        stride=stride_D,
                        hbm_addr=f"{DIM * 4} * %j.{count.matmul_count} + {bias_addr}",
                        tiles=1,
                        acc_addr=OUT_SP,
                        repeating_bias=repeating_bias)
                else:
                    api.bias_load_repeat(
                        hbm_addr=f"{DIM} * %j.{count.matmul_count} + {bias_addr}",
                        is_full_width=1)
            else:
                if (use_acc):
                    api.mvin_acc_stride(
                        stride=stride_D,
                        hbm_addr=f"{stride_D * DIM * 4} * %i.{count.matmul_count} + {DIM * 4} * %j.{count.matmul_count} + {bias_addr}",
                        tiles=1,
                        acc_addr=OUT_SP,
                        repeating_bias=repeating_bias)
                else:
                    api.bias_load(
                        stride=stride_D,
                        hbm_addr=f"{stride_D * DIM} * %i.{count.matmul_count} + {DIM} * %j.{count.matmul_count} + {bias_addr}",
                        is_full_width=1)

        for k in range(tile_K):
            api.mvin_spad(
                tiles=1,
                stride=stride_A,
                hbm_addr=f"{stride_A * DIM} * %i.{count.matmul_count} + {DIM * k} + {A_base}",
                sp_addr=A_SP)
            api.mvin_spad(
                tiles=1,
                stride=stride_B,
                hbm_addr=f"{DIM} * %j.{count.matmul_count} + {stride_B * DIM * k} + {B_base}",
                sp_addr=B_SP)
            api.matmul_preload(rs1=B_SP, rs2=OUT_SP)
            if (use_acc):
                api.matmul32_compute_accumulated(rs1=A_SP, rs2=-1)
            else:
                api.matmul8_compute_accumulated(rs1=A_SP, rs2=-1)
        if (use_acc):
            api.mvout_acc_stride(
                stride=stride_C,
                hbm_addr=f"{stride_C * DIM * 4} * %i.{count.matmul_count} + {DIM * 4} * %j.{count.matmul_count} + {C_base}",
                acc_addr=OUT_SP)
        else:
            api.mvout_spad(
                stride=stride_C,
                rows=DIM,
                hbm_addr=f"{stride_C * DIM} * %i.{count.matmul_count} + {DIM} * %j.{count.matmul_count} + {C_base}",
                sp_addr=OUT_SP)
        api.end_loop()
        api.end_loop()
        if (transpose):
            api.transpose(rows=N, cols=K, src_hbm_addr=B_base, dst_hbm_addr=B_base)

        count.matmul_count += 1

    def attention_function(input_addr, output_addr, resadd_addr, count):
        # Q = input @ Wq + bias (seq_len x hidden_dim @ hidden_dim x hidden_dim ->
        # seq_len x hidden_dim)
        tiled_matmul(input_addr, wq_addr, q_buf_addr,
                     SEQ_LEN, HIDDEN_DIM, HIDDEN_DIM,
                     stride_A=HIDDEN_DIM, stride_B=HIDDEN_DIM, stride_C=HIDDEN_DIM, stride_D=0,
                     bias_addr=wq_b_addr, count=count, repeating_bias=True)

        # K = input @ Wk + bias
        tiled_matmul(input_addr, wk_addr, k_buf_addr,
                     SEQ_LEN, HIDDEN_DIM, HIDDEN_DIM,
                     stride_A=HIDDEN_DIM, stride_B=HIDDEN_DIM, stride_C=HIDDEN_DIM, stride_D=0,
                     bias_addr=wk_b_addr, count=count, repeating_bias=True)

        # V = input @ Wv + bias
        tiled_matmul(input_addr, wv_addr, v_buf_addr,
                     SEQ_LEN, HIDDEN_DIM, HIDDEN_DIM,
                     stride_A=HIDDEN_DIM, stride_B=HIDDEN_DIM, stride_C=HIDDEN_DIM, stride_D=0,
                     bias_addr=wv_b_addr, count=count, repeating_bias=True)

        for head1 in range(NUM_HEADS):
            attn_acc_addr = attn_buf_addr + SEQ_LEN * SEQ_LEN * 4 * head1
            tiled_matmul(q_buf_addr + HIDDEN_DIM_PER_HEAD * head1,
                         k_buf_addr + HIDDEN_DIM_PER_HEAD * head1,
                         attn_acc_addr,
                         SEQ_LEN, SEQ_LEN, HIDDEN_DIM_PER_HEAD,
                         stride_A=HIDDEN_DIM, stride_B=HIDDEN_DIM, stride_C=SEQ_LEN, stride_D=0,
                         bias_addr=None, count=count, transpose=True, use_acc=True)
            api.softmax(rs1=attn_acc_addr,
                        out_sp=attn_buf_addr + SEQ_LEN * SEQ_LEN * head1,
                        batch=SEQ_LEN, features=SEQ_LEN)

        for head2 in range(NUM_HEADS):
            tiled_matmul(attn_buf_addr + SEQ_LEN * SEQ_LEN * head2,
                         v_buf_addr + HIDDEN_DIM_PER_HEAD * head2,
                         out_buf_addr + HIDDEN_DIM_PER_HEAD * head2,
                         SEQ_LEN, HIDDEN_DIM_PER_HEAD, SEQ_LEN,
                         stride_A=SEQ_LEN, stride_B=HIDDEN_DIM, stride_C=HIDDEN_DIM, stride_D=0,
                         bias_addr=None, count=count)

        tiled_matmul(out_buf_addr, wo_addr, out_buf_acc_addr,
                     SEQ_LEN, HIDDEN_DIM, HIDDEN_DIM,
                     stride_A=HIDDEN_DIM, stride_B=HIDDEN_DIM, stride_C=HIDDEN_DIM, stride_D=0,
                     bias_addr=wo_b_addr, count=count, use_acc=True, repeating_bias=True)

        api.layernorm(rs1=out_buf_acc_addr, out_sp=output_addr,
                      batch=SEQ_LEN, features=HIDDEN_DIM)

        api.add(rows=SEQ_LEN, cols=HIDDEN_DIM,
                a_addr=output_addr, b_addr=input_addr, c_addr=resadd_addr)

    def ffn_function(input_addr, output_addr, count):
        ff1_acc_addr = out_buf_acc_addr  # Reuse accumulator buffer
        tiled_matmul(
            input_addr,
            ff1_w_addr,
            ff1_acc_addr,
            SEQ_LEN,
            EXPANSION_DIM,
            HIDDEN_DIM,
            stride_A=HIDDEN_DIM,
            stride_B=EXPANSION_DIM,
            stride_C=EXPANSION_DIM,
            stride_D=EXPANSION_DIM,
            bias_addr=ff1_b_addr,
            count=count,
            use_acc=True,
            repeating_bias=True)
        api.gelu(rs1=ff1_acc_addr, out_sp=out_buf_addr,
                 batch=SEQ_LEN, features=EXPANSION_DIM)

        tiled_matmul(
            out_buf_addr,
            ff2_w_addr,
            out_buf_acc_addr,
            SEQ_LEN,
            HIDDEN_DIM,
            EXPANSION_DIM,
            stride_A=EXPANSION_DIM,
            stride_B=HIDDEN_DIM,
            stride_C=EXPANSION_DIM,
            stride_D=EXPANSION_DIM,
            bias_addr=ff2_b_addr,
            count=count,
            use_acc=True,
            repeating_bias=True)
        api.layernorm(rs1=out_buf_acc_addr, out_sp=output_addr,
                      batch=SEQ_LEN, features=HIDDEN_DIM)

        api.add(rows=SEQ_LEN, cols=HIDDEN_DIM,
                a_addr=output_addr, b_addr=input_addr, c_addr=output_addr)

    matmul_count = counter()

    attention_function(layer_input_addr, out_buf_addr, resadd1_buf_addr, matmul_count)
    ffn_function(resadd1_buf_addr, layer_output_addr, matmul_count)

    api.start_loop("layer", 1, LAYERS)

    attention_function(layer_output_addr, out_buf_addr, resadd1_buf_addr, matmul_count)
    ffn_function(resadd1_buf_addr, layer_output_addr, matmul_count)

    api.end_loop()


def run_ibert(trials=5):
    inputs, compile_time = ibert("fsim-compile")()

    res = 0
    for _ in range(trials):
        ans, tmp_time = ibert("fsim")(*gen_arguments(inputs))
        res += tmp_time

    avg_runtime = res / trials
    print(f"I-BERT | Compile: {compile_time:.3f}ms | Runtime: {avg_runtime:.3f}ms")

    return avg_runtime


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--trials', type=int, default=1, help="Number of trail runs")
    args = parser.parse_args()
    trials = args.trials

    ibert_data = {
        'model': 'I-BERT',
        'hbm': total_hbm
    }

    # Check for Spike time log file
    spike_log_path = os.path.join(csv_dir, SPIKE_IBERT_LOG)
    if os.path.exists(spike_log_path):
        try:
            with open(spike_log_path, 'r') as f:
                spike_runtime = float(f.read().strip())
            ibert_data['spike_runtime'] = f'{spike_runtime:.3f}'
        except (ValueError, IOError):
            pass  # ignore

    # Run on CPU
    set_simulation_backend("CPU")
    print("\nSimulation Backend: \x1b[4mCPU\x1b[0m")
    cpu_runtime = run_ibert()
    ibert_data['cpu_runtime'] = f"{cpu_runtime:.3f}"

    # Run on GPU if available
    if gpu_check():
        set_simulation_backend("GPU")
        print("\nSimulation Backend: \x1b[4mGPU\x1b[0m")
        gpu_runtime = run_ibert()
        ibert_data['gpu_runtime'] = f"{gpu_runtime:.3f}"

    # Generate CSV file
    os.makedirs(csv_dir, exist_ok=True)
    ibert_csv_path = os.path.join(csv_dir, IBERT_CSV)
    with open(ibert_csv_path, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields, restval='NA', extrasaction='ignore')
        writer.writerow(csv_header)
        writer.writerow(ibert_data)

    print("\nCompleted benchmarking Gemmini(DIM=256) TAIDL-TO for end-to-end I-BERT model.")
    print(f"Results saved to plots/csv/{IBERT_CSV}.")

    # Clean up log file
    if os.path.exists(spike_log_path):
        os.remove(spike_log_path)
