import argparse
import importlib
import os
import sys

repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(repo_dir))

_accelerator = importlib.import_module("taidl.accelerator")
Accelerator = _accelerator.Accelerator

# Parse command line arguments
parser = argparse.ArgumentParser(description='Generate TAIDL for Gemmini accelerator')
parser.add_argument('--size', type=int, default=16, help='Size parameter (default: 16)')
args = parser.parse_args()

SIZE = args.size

acc = Accelerator(f"Gemmini(DIM={SIZE})")

# Define Data Models
acc.add_data_model("sp", f"{1024*SIZE}", f"{SIZE}xs8")
acc.add_data_model("acc", f"{64 * SIZE}", f"{SIZE}xs32")
acc.add_data_model("weights", f"{SIZE}x{SIZE}", "s8")
acc.add_data_model("bias", f"{SIZE}x{SIZE}", "s32")

# Define Control Registers
acc.add_initial_state("dataflow", 0)
acc.add_initial_state("preload", 0)
acc.add_initial_state("rs1", -1)
acc.add_initial_state("rs2", 0)

instr = acc.add_instruction("mvin_spad", ["tiles", "stride", "hbm_addr", "sp_addr"])
instr.add_semantics(f"""
%In1:`@a.stride*{SIZE}`xs8 <- hbm[@a.hbm_addr];
%data:`(@a.stride/@a.tiles)`x`@a.tiles`x{SIZE}xs8 = reshape(%In1);
%tmp:{SIZE}x`@a.tiles`x{SIZE}xs8 = slice(%data), slice={{[0:`@a.stride/@a.tiles`:`(@a.stride)/{SIZE}/@a.tiles`], [0:@a.tiles:1], [0:{SIZE}:1]}};
%fin:`@a.tiles`x{SIZE}x{SIZE}xs8 = transpose(%tmp), dimensions={{1, 0, 2}};
%Out0:`@a.tiles*{SIZE}`x{SIZE}xs8 = reshape(%fin);
%Out0:`@a.tiles*{SIZE}`x{SIZE}xs8 -> sp[@a.sp_addr, 0];
""")

instr = acc.add_instruction("mvin_acc_stride",
                            ["tiles", "stride", "hbm_addr", "acc_addr", "repeating_bias"])
instr.add_semantics(f"""
IF(@a.repeating_bias == 0)
{{
    %In1:`@a.stride*{SIZE}*4`xs8 <- hbm[@a.hbm_addr];
    %datas8:`(@a.stride/@a.tiles)`x`@a.tiles`x{SIZE}x4xs8 = reshape(%In1);
    %data:`(@a.stride/@a.tiles)`x`@a.tiles`x{SIZE}xs32 = bitcast_convert(%datas8);
    %tmp:{SIZE}x`@a.tiles`x{SIZE}xs32 = slice(%data), slice={{[0:`@a.stride/@a.tiles`:`(@a.stride)/{SIZE}/@a.tiles`], [0:@a.tiles:1], [0:{SIZE}:1]}};
    %fin:`@a.tiles`x{SIZE}x{SIZE}xs32 = transpose(%tmp), dimensions={{1, 0, 2}};
    %Out0:`@a.tiles*{SIZE}`x{SIZE}xs32 = reshape(%fin);
    %Out0:`@a.tiles*{SIZE}`x{SIZE}xs32 -> acc[@a.acc_addr, 0];
}}
ELSE
{{
    %In1:`{SIZE}*4`xs8 <- hbm[@a.hbm_addr];
    %In1_r:`{SIZE}`x4xs8 = reshape(%In1);
    %In1.s32:`{SIZE}`xs32 = bitcast_convert(%In1_r);
    %Out0:`{SIZE}`x{SIZE}xs32 = broadcast_dim(%In1.s32, {{0}});
    %Out0:`{SIZE}`x{SIZE}xs32 -> acc[@a.acc_addr, 0];
}}
""")

instr = acc.add_instruction("mvin_acc", ["rows", "hbm_addr", "acc_addr"])
instr.add_semantics(f"""
%In1:`@a.rows*{SIZE*SIZE*4}`xs8 <- hbm[@a.hbm_addr];
%r:`@a.rows*{SIZE}`x{SIZE}x4xs8 = reshape(%In1);
%Out0:`@a.rows*{SIZE}`x{SIZE}xs32 = bitcast_convert(%r);
%Out0:`@a.rows*{SIZE}`x{SIZE}xs32 -> acc[@a.acc_addr, 0];
""")

instr = acc.add_instruction("mvout_acc_stride", ["stride", "hbm_addr", "acc_addr"])
instr.add_semantics(f"""
%In1:{SIZE}x{SIZE}xs32 <- acc[@a.acc_addr, 0];
%In2:`{SIZE*4}*@a.stride`xs8 <- hbm[@a.hbm_addr];
%orig:{SIZE}x`(@a.stride)/{SIZE}`x{SIZE}x4xs8 = reshape(%In2);
%tmp:{SIZE}x1x{SIZE}xs32 = reshape(%In1);
%tmp_clamped:{SIZE}x1x{SIZE}xs32 = clamp(-128, %tmp, 127);
%data:{SIZE}x1x{SIZE}x4xs8 = bitcast_convert(%tmp_clamped);
%fin:{SIZE}x`@a.stride/{SIZE}`x{SIZE}x4xs8 = dynamic_update_slice(%orig, %data, s32[] constant(0), s32[] constant(0), s32[] constant(0), s32[] constant(0));
%Out0:`{SIZE}*@a.stride*4`xs8 = reshape(%fin);
%Out0:`{SIZE}*@a.stride*4`xs8 -> hbm[@a.hbm_addr];
""")

instr = acc.add_instruction("mvout_spad", ["stride", "hbm_addr", "sp_addr", "rows"])
instr.add_semantics(f"""
%In:`@a.rows`x{SIZE}xs8 <- sp[@a.sp_addr:@a.sp_addr + @a.rows:1,0:{SIZE}:1];
%In2:`@a.rows*@a.stride`xs8 <- hbm[@a.hbm_addr:@a.hbm_addr + @a.rows * @a.stride:1];
%orig:`@a.rows`x`@a.stride / {SIZE}`x{SIZE}xs8 = reshape(%In2);
%data:`@a.rows`x1x{SIZE}xs8 = reshape(%In);
%fin:`@a.rows`x`@a.stride / {SIZE}`x{SIZE}xs8 = dynamic_update_slice(%orig, %data, s32[] constant(0), s32[] constant(0), s32[] constant(0));
%Out:`@a.rows*@a.stride`xs8 = reshape(%fin);
%Out:`@a.rows*@a.stride`xs8 -> hbm[@a.hbm_addr];
""")


instr = acc.add_instruction("bias_load", ["stride", "hbm_addr", "is_full_width"])
instr.add_semantics(f"""
IF(@a.is_full_width == 1)
{{
    %In1:`@a.stride*{SIZE}*4`xs8 <- hbm[@a.hbm_addr];
    %datas8:`(@a.stride)`x1x{SIZE}x4xs8 = reshape(%In1);
    %data:`(@a.stride)`x1x{SIZE}xs32 = bitcast_convert(%datas8);
    %tmp:{SIZE}x1x{SIZE}xs32 = slice(%data), slice={{[0:`@a.stride`:`(@a.stride)/{SIZE}`], [0:1:1], [0:{SIZE}:1]}};
    %fin:1x{SIZE}x{SIZE}xs32 = transpose(%tmp), dimensions={{1, 0, 2}};
    %Out.32:{SIZE}x{SIZE}xs32 = reshape(%fin);
}}
ELSE
{{
    %In1:`@a.stride*{SIZE}`xs8 <- hbm[@a.hbm_addr];
    %data:`(@a.stride)`x1x{SIZE}xs8 = reshape(%In1);
    %tmp:{SIZE}x1x{SIZE}xs8 = slice(%data), slice={{[0:`@a.stride`:`(@a.stride)/{SIZE}`], [0:1:1], [0:{SIZE}:1]}};
    %fin:`1`x{SIZE}x{SIZE}xs8 = transpose(%tmp), dimensions={{1, 0, 2}};
    %Out.8:{SIZE}x{SIZE}xs8 = reshape(%fin);
    %Out.32:{SIZE}x{SIZE}xs8 = convert(%Out.32);
}}
%Out.32:{SIZE}x{SIZE}xs32 -> bias[0,0];
""")

instr = acc.add_instruction("bias_load_repeat", ["hbm_addr", "is_full_width"])
instr.add_semantics(f"""
IF(@a.is_full_width == 1)
{{
    %In1:`{SIZE}*4`xs8 <- hbm[@a.hbm_addr];
    %datas8:{SIZE}x4xs8 = reshape(%In1);
    %data:{SIZE}xs32 = bitcast_convert(%datas8);
    %Out.32:{SIZE}x{SIZE}xs32 = broadcast_dim(%data, {{0}});
}}
ELSE
{{
    %In1:{SIZE}xs8 <- hbm[@a.hbm_addr];
    %data:{SIZE}xs32 = convert(%In1);
    %Out.32:{SIZE}x{SIZE}xs32 = broadcast_dim(%data, {{0}});
}}
%Out.32:{SIZE}x{SIZE}xs32 -> bias[0,0];
""")

instr = acc.add_instruction("dataflow_config", ["dataflow"])
instr.add_constraints([])
instr.add_update(["@s.dataflow = @a.dataflow"])

instr = acc.add_instruction("matmul_preload", ["rs1", "rs2"])
instr.add_constraints(["@s.preload == 0"])
instr.add_update(["@s.rs1 = @a.rs1", "@s.rs2= @a.rs2", "@s.preload = 1"])

instr = acc.add_instruction("matmul8_compute_preloaded", ["rs1", "rs2"])
instr.add_constraints(["@s.preload == 1"])
instr.add_update(["@s.preload = 0"])
instr.add_semantics(f"""
%A.8:{SIZE}x{SIZE}xs8 <- sp[@a.rs1:@a.rs1 + {SIZE}:1,0:{SIZE}];
IF(@s.dataflow == 0)
{{
    %B.8:{SIZE}x{SIZE}xs8 <- sp[@a.rs2:@a.rs2 + {SIZE}:1,0:{SIZE}];
    %D.8:{SIZE}x{SIZE}xs8 <- sp[@s.rs1:@s.rs1 + {SIZE}:1,0:{SIZE}];
}}
ELSE
{{
    %B.8:{SIZE}x{SIZE}xs8 <- sp[@s.rs1:@s.rs1 + {SIZE}:1,0:{SIZE}];
    %D.8:{SIZE}x{SIZE}xs8 <- sp[@a.rs2:@a.rs2 + {SIZE}:1,0:{SIZE}];
}}

%A.32:{SIZE}x{SIZE}xs32 = convert(%A.8);
%B.32:{SIZE}x{SIZE}xs32 = convert(%B.8);
%D.32:{SIZE}x{SIZE}xs32 = convert(%D.8);

%dot.32:{SIZE}x{SIZE}xs32 = dot(%A.32, %B.32), lhs_batch_dims={{}}, lhs_contracting_dims={{1}}, rhs_batch_dims={{}}, rhs_contracting_dims={{0}};
%C.32:{SIZE}x{SIZE}xs32 = add(%dot.32, %D.32);
%C.clamp:{SIZE}x{SIZE}xs32 = clamp(-128, %C.32, 127);
%C.8:{SIZE}x{SIZE}xs8 = convert(%C.clamp);

%C.32:{SIZE}x{SIZE}xs32 -> bias[0,0];
%B.8:{SIZE}x{SIZE}xs8 -> weights[0,0];
%C.8:{SIZE}x{SIZE}xs8 -> sp[@s.rs2,0];
""")

instr = acc.add_instruction("matmul8_compute_accumulated", ["rs1", "rs2"])
instr.add_constraints(["@s.preload == 1"])
instr.add_update(["@s.preload = 0"])
instr.add_semantics(f"""
%A.8:{SIZE}x{SIZE}xs8 <- sp[@a.rs1:@a.rs1 + {SIZE}:1,0:{SIZE}];
IF(@s.dataflow == 0)
{{
    %B.8:{SIZE}x{SIZE}xs8 <- sp[@s.rs1:@s.rs1 + {SIZE}:1,0:{SIZE}];
    %D.32:{SIZE}x{SIZE}xs32 <- bias[0:{SIZE},0:{SIZE}];
}}
ELSE
{{
    %B.8:{SIZE}x{SIZE}xs8 <- weights[0:{SIZE},0:{SIZE}];
    %D.8:{SIZE}x{SIZE}xs8 <- sp[@a.rs2:@a.rs2 + {SIZE}:1,0:{SIZE}];
    %D.32:{SIZE}x{SIZE}xs32 = convert(%D.8);
}}

%A.32:{SIZE}x{SIZE}xs32 = convert(%A.8);
%B.32:{SIZE}x{SIZE}xs32 = convert(%B.8);

%dot.32:{SIZE}x{SIZE}xs32 = dot(%A.32, %B.32), lhs_batch_dims={{}}, lhs_contracting_dims={{1}}, rhs_batch_dims={{}}, rhs_contracting_dims={{0}};
%C.32:{SIZE}x{SIZE}xs32 = add(%dot.32, %D.32);
%C.clamp:{SIZE}x{SIZE}xs32 = clamp(-128, %C.32, 127);
%C.8:{SIZE}x{SIZE}xs8 = convert(%C.clamp);

%C.32:{SIZE}x{SIZE}xs32 -> bias[0,0];
%B.8:{SIZE}x{SIZE}xs8 -> weights[0,0];
%C.8:{SIZE}x{SIZE}xs8 -> sp[@s.rs2,0];
""")

instr = acc.add_instruction("matmul32_compute_accumulated", ["rs1", "rs2"])
instr.add_constraints(["@s.preload == 1 and @s.dataflow == 1"])
instr.add_update(["@s.preload = 0"])
instr.add_semantics(f"""
%A.8:{SIZE}x{SIZE}xs8 <- sp[@a.rs1:@a.rs1 + {SIZE}:1,0:{SIZE}];
%B.8:{SIZE}x{SIZE}xs8 <- sp[@s.rs1:@s.rs1 + {SIZE}:1,0:{SIZE}];
%A.32:{SIZE}x{SIZE}xs32 = convert(%A.8);
%B.32:{SIZE}x{SIZE}xs32 = convert(%B.8);
%C.old:{SIZE}x{SIZE}xs32 <- acc[@s.rs2:@s.rs2 + {SIZE}:1,0:{SIZE}];

%dot.32:{SIZE}x{SIZE}xs32 = dot(%A.32, %B.32), lhs_batch_dims={{}}, lhs_contracting_dims={{1}}, rhs_batch_dims={{}}, rhs_contracting_dims={{0}};
%C.32:{SIZE}x{SIZE}xs32 = add(%dot.32, %C.old);
%C.32:{SIZE}x{SIZE}xs32 -> acc[@s.rs2,0];
""")

# Activations for I-BERT
instr = acc.add_instruction("softmax", ["rs1", "out_sp", "batch", "features"])
instr.add_semantics("""
%In:`@a.batch * @a.features * 4`xs8 <- hbm[@a.rs1:@a.rs1 + @a.batch * @a.features];
%In.reshaped:`@a.batch`x`@a.features`x4xs8 = reshape(%In);
%In.conv:`@a.batch`x`@a.features`xs32 = bitcast_convert(%In.reshaped);
%min:s32 = constant(-128);
%max_val:`@a.batch`xs32 = reduce(%In.conv, %min, {1}, max_func_s32);
%max_bcast:`@a.batch`x`@a.features`xs32 = broadcast_dim(%max_val, {0});
%max_bcast_f32:`@a.batch`x`@a.features`xf32 = convert(%max_bcast);
%In.f32:`@a.batch`x`@a.features`xf32 = convert(%In.conv);
%shifted:`@a.batch`x`@a.features`xf32 = subtract(%In.f32, %max_bcast_f32);
%exp:`@a.batch`x`@a.features`xf32 = exp(%shifted);
%zero_val:f32 = constant(0);
%sum_exp:`@a.batch`xf32 = reduce(%exp, %zero_val, {1}, add_func_f32);
%sum_exp_bcast:`@a.batch`x`@a.features`xf32 = broadcast_dim(%sum_exp, {0});
%div:`@a.batch`x`@a.features`xf32 = divide(%exp, %sum_exp_bcast);
%c128:f32 = constant(128);
%c128_bcast:`@a.batch`x`@a.features`xf32 = broadcast_dim(%c128, {0});
%scaled:`@a.batch`x`@a.features`xf32 = multiply(%c128_bcast, %div);
%Out:`@a.batch`x`@a.features`xs8 = convert(%scaled);
%Out.8:`@a.batch * @a.features`xs8 = reshape(%Out);
%Out.8:`@a.batch * @a.features`xs8 -> hbm[@a.out_sp];
""")

instr = acc.add_instruction("gelu", ["rs1", "out_sp", "batch", "features"])
instr.add_semantics("""
%x:`@a.batch * @a.features * 4`xs8 <- hbm[@a.rs1:@a.rs1 + @a.batch * @a.features];
%x.reshaped8:`@a.batch * @a.features`x4xs8 = reshape(%x);
%x.s32:`@a.batch * @a.features`xs32 = bitcast_convert(%x.reshaped8);
%x.f32:`@a.batch * @a.features`xf32 = convert(%x.s32);
%x.reshaped:`@a.batch`x`@a.features`xf32 = reshape(%x.f32);
%c0_5:f32 = constant(float0.5);
%c0_5_bcast:`@a.batch`x`@a.features`xf32 = broadcast(%c0_5);
%c1:f32 = constant(1);
%c044715:f32 = constant(float0.044715);
%sqrt_2_over_pi:f32 = constant(float0.7978845);
%x2:`@a.batch`x`@a.features`xf32 = multiply(%x.reshaped, %x.reshaped);
%x3:`@a.batch`x`@a.features`xf32 = multiply(%x2, %x.reshaped);
%c044715_bcast:`@a.batch`x`@a.features`xf32 = broadcast(%c044715);
%term:`@a.batch`x`@a.features`xf32 = multiply(%c044715_bcast, %x3);
%inner:`@a.batch`x`@a.features`xf32 = add(%x.reshaped, %term);
%sqrt_2_over_pi_bcast:`@a.batch`x`@a.features`xf32 = broadcast(%sqrt_2_over_pi);
%inner_scaled:`@a.batch`x`@a.features`xf32 = multiply(%inner, %sqrt_2_over_pi_bcast);
%tanh_inner:`@a.batch`x`@a.features`xf32 = tanh(%inner_scaled);
%one_bcast:`@a.batch`x`@a.features`xf32 = broadcast(%c1);
%one_plus_tanh:`@a.batch`x`@a.features`xf32 = add(%tanh_inner, %one_bcast);
%half_times_x:`@a.batch`x`@a.features`xf32 = multiply(%c0_5_bcast, %x.reshaped);
%out:`@a.batch`x`@a.features`xf32 = multiply(%half_times_x, %one_plus_tanh);
%out.c:`@a.batch`x`@a.features`xs8 = convert(%out);
%out.8:`@a.batch * @a.features`xs8 = reshape(%out.c);
%out.8:`@a.batch * @a.features`xs8 -> hbm[@a.out_sp];
""")

instr = acc.add_instruction("layernorm", ["rs1", "out_sp", "batch", "features"])
instr.add_semantics("""
%In:`@a.batch * @a.features * 4`xs8 <- hbm[@a.rs1:@a.rs1 + @a.batch * @a.features];
%In.reshaped:`@a.batch`x`@a.features`x4xs8 = reshape(%In);
%In.conv:`@a.batch`x`@a.features`xs32 = bitcast_convert(%In.reshaped);
%In.f32:`@a.batch`x`@a.features`xf32 = convert(%In.conv);
%zero_val:f32 = constant(0);
%sum_vals:`@a.batch`xf32 = reduce(%In.f32, %zero_val, {1}, add_func_f32);
%feat_count_scalar:f32 = constant(@a.features);
%feat_count:`@a.batch`xf32 = broadcast_dim(%feat_count_scalar, {0});
%mean:`@a.batch`xf32 = divide(%sum_vals, %feat_count);
%mean_bcast:`@a.batch`x`@a.features`xf32 = broadcast_dim(%mean, {0});
%diff:`@a.batch`x`@a.features`xf32 = subtract(%In.f32, %mean_bcast);
%sq:`@a.batch`x`@a.features`xf32 = multiply(%diff, %diff);
%sum_sq:`@a.batch`xf32 = reduce(%sq, %zero_val, {1}, add_func_f32);
%var:`@a.batch`xf32 = divide(%sum_sq, %feat_count);
%eps_scalar:f32 = constant(float0.00001);
%eps:`@a.batch`xf32 = broadcast_dim(%eps_scalar, {0});
%var_eps:`@a.batch`xf32 = add(%var, %eps);
%inv_std:`@a.batch`xf32 = rsqrt(%var_eps);
%inv_std_bcast:`@a.batch`x`@a.features`xf32 = broadcast_dim(%inv_std, {0});
%normed:`@a.batch`x`@a.features`xf32 = multiply(%diff, %inv_std_bcast);
%Out:`@a.batch`x`@a.features`xs8 = convert(%normed);
%Out.8:`@a.batch * @a.features`xs8 = reshape(%Out);
%Out.8:`@a.batch * @a.features`xs8 -> hbm[@a.out_sp];
""")

instr = acc.add_instruction("add", ["rows", "cols", "a_addr", "b_addr", "c_addr"])
instr.add_semantics("""
%a:`@a.rows*@a.cols`xs8 <- hbm[@a.a_addr:@a.a_addr + @a.rows * @a.cols:1];
%b:`@a.rows*@a.cols`xs8 <- hbm[@a.b_addr:@a.b_addr + @a.rows * @a.cols:1];
%a_r:`@a.rows`x`@a.cols`xs8 = reshape(%a);
%b_r:`@a.rows`x`@a.cols`xs8 = reshape(%b);
%c_r:`@a.rows`x`@a.cols`xs8 = add(%a_r, %b_r);
%c:`@a.rows*@a.cols`xs8 = reshape(%c_r);
%c:`@a.rows*@a.cols`xs8 -> hbm[@a.c_addr];
""")

instr = acc.add_instruction("transpose", ["rows", "cols", "src_hbm_addr", "dst_hbm_addr"])
instr.add_semantics(f"""
%In:`@a.rows*@a.cols`xs8 <- hbm[@a.src_hbm_addr:@a.src_hbm_addr + @a.rows * @a.cols:1];
%In_reshaped:`@a.rows`x`@a.cols`xs8 = reshape(%In);
%Out:`@a.cols`x`@a.rows`xs8 = transpose(%In_reshaped), dimensions={{1, 0}};
%Out_flat:`@a.cols*@a.rows`xs8 = reshape(%Out);
%Out_flat:`@a.cols*@a.rows`xs8 -> hbm[@a.dst_hbm_addr];
""")

acc.generate_sim(f"sim_{SIZE}")
