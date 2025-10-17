import importlib
import os
import sys

repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(repo_dir))

_accelerator = importlib.import_module("taidl.accelerator")
Accelerator = _accelerator.Accelerator

tpu = Accelerator("TPUv1")

# Define Constants
UNB_MAX_ROWS = 98304
ACC_MAX_ROWS = 4096

# Define Data Models
tpu.add_data_model("unb", "98304", "256xs8")
tpu.add_data_model("acc", "4096", "256xs32")
tpu.add_data_model("weights", "", "256x256xs8")
tpu.add_data_model("fifo", "4", "256x256xs8")

# Define State
tpu.add_initial_state("fifo_occupancy", 0)
tpu.add_initial_state("fifo_push", 0)
tpu.add_initial_state("fifo_pop", -1)
tpu.add_initial_state("preload", 0)

# Read
instr = tpu.add_instruction("read", ["hbm_addr", "unb_start", "nrows"])
instr.add_constraints(['@a.hbm_addr >= 0',
                      '@a.unb_start >= 0',
                       f'@a.unb_start + @a.nrows <= {UNB_MAX_ROWS}',
                       '@a.nrows >= 0'])
instr.add_update([])

instr.add_semantics(
    """
%In:`@a.nrows*256`xs8 <- hbm[`@a.hbm_addr`:`@a.hbm_addr + @a.nrows * 256`:1];
%Out:`@a.nrows`x256xs8 = reshape(%In);
%Out:`@a.nrows`x256xs8 -> unb[`@a.unb_start`,0];
"""
)


# Write
instr = tpu.add_instruction("write", ["hbm_addr", "unb_start", "nrows"])
instr.add_constraints(['@a.hbm_addr >= 0',
                      '@a.unb_start >= 0',
                       f'@a.unb_start + @a.nrows <= {UNB_MAX_ROWS}',
                       '@a.nrows >= 0'])
instr.add_update([])

instr.add_semantics(
    """
%In:`@a.nrows`x256xs8 <- unb[`@a.unb_start`:`@a.unb_start + @a.nrows`:1,0:256:1];
%Out:`@a.nrows*256`xs8 = reshape(%In);
%Out:`@a.nrows*256`xs8 -> hbm[`@a.hbm_addr`];
"""
)

# Read_weights
instr = tpu.add_instruction("read_weight", ["hbm_addr"])
instr.add_constraints(['@a.hbm_addr >= 0',
                      '@s.fifo_occupancy < 4'])
instr.add_update(['@s.fifo_occupancy += 1',
                 '@s.fifo_push = (@s.fifo_push + 1) % 4',
                  '@s.fifo_pop = 0 if @s.fifo_pop == -1 else @s.fifo_pop'])

instr.add_semantics(
    """
%In:`256*256`xs8 <- hbm[`@a.hbm_addr`:`@a.hbm_addr + 256 * 256`:1];
%Out:1x256x256xs8 = reshape(%In);
%Out:1x256x256xs8 -> fifo[`@s.fifo_push`,0,0];
"""
)

# Update_weights
instr = tpu.add_instruction("update_weight", [])
instr.add_constraints(['@s.fifo_occupancy > 0'])
instr.add_update(['@s.fifo_occupancy -= 1',
                 '@s.fifo_pop = (@s.fifo_pop + 1) % 4'])

instr.add_semantics(
    """
%In:1x256x256xs8 <- fifo[`@s.fifo_pop`:`@s.fifo_pop + 1`:1,0:256,0:256];
%Out:256x256xs8 = reshape(%In);
%Out:256x256xs8 -> weights[0, 0];
"""
)

# Matmul
instr = tpu.add_instruction("matmul", ["unb_start", "acc_start", "nrows"])
instr.add_constraints(['@s.preload == 0'])
instr.add_update(['@s.preload = 1'])

instr.add_semantics(
    """
%A.8:`@a.nrows`x256xs8 <- unb[`@a.unb_start`:`@a.unb_start + @a.nrows`:1,0:256:1];
%B.8:256x256xs8 <- weights[0:256:1,0:256:1];
%A.32:`@a.nrows`x256xs32 = convert(%A.8);
%B.32:256x256xs32 = convert(%B.8);
%C.32:`@a.nrows`x256xs32 = dot(%A.32, %B.32), lhs_batch_dims={}, lhs_contracting_dims={1}, rhs_batch_dims={}, rhs_contracting_dims={0};
%C.32:`@a.nrows`x256xs32 -> acc[`@a.acc_start`,0];
"""
)

# Activate
instr = tpu.add_instruction("activate", ["unb_start", "acc_start", "nrows", "function"])
instr.add_constraints(['@a.acc_start >= 0',
                      '@a.unb_start >= 0',
                       f'@a.unb_start + @a.nrows <= {UNB_MAX_ROWS}',
                       f'@a.acc_start + @a.nrows <= {UNB_MAX_ROWS}',
                       '@a.function == 1 or @a.function == 0',
                       '@a.nrows >= 0'])
instr.add_update([])

instr.add_semantics(
    """
%In:`@a.nrows`x256xs32 <- acc[`@a.acc_start`:`@a.acc_start + @a.nrows`:1, 0:256];
IF (@a.function == 0)
{
    %Out:`@a.nrows`x256xs8 = convert(%In);
}
ELSE
{
    %constant.0:`@a.nrows`x256xs32 = constant(0);
    %Out.32:`@a.nrows`x256xs32 = maximum(%In, %constant.0);
    %Out:`@a.nrows`x256xs8 = convert(%Out.32);
}
%Out:`@a.nrows`x256xs8 -> unb[@a.unb_start,0];
"""
)

tpu.generate_sim()
