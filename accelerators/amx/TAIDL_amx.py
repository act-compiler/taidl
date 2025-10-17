import importlib
import os
import sys

repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(repo_dir))

_accelerator = importlib.import_module("taidl.accelerator")
Accelerator = _accelerator.Accelerator

acc = Accelerator("AMX")

# Define Constants
NUM_TMM = 8
NUM_ZMM = 32
MAX_ROWS = 16
MAX_COLSB = 64
ZMM_WIDTH_8b = 64
ZMM_WIDTH_32b = 16

# Define Data Models
acc.add_data_model("tiles", "8", "16x64xs8")
acc.add_data_model("zmm", "32", "16xf32")

instr = acc.add_instruction("tilezero", ["dst"])
instr.add_semantics(f"""
%zerost:1x`{MAX_ROWS}`x`{MAX_COLSB}`xs8 = constant(0);
%zerost:1x`{MAX_ROWS}`x`{MAX_COLSB}`xs8 -> tiles[@a.dst,0,0];
""")

instr = acc.add_instruction("tileloadd", ["dst", "addr", "stride"])
instr.add_semantics(f"""
%tmp:`{MAX_ROWS}*@a.stride`xs8 <- hbm[@a.addr:@a.addr+ ({MAX_ROWS}) * @a.stride];
%data:1x`{MAX_ROWS}`x`@a.stride`xs8 = reshape(%tmp);
%data:1x`{MAX_ROWS}`x`@a.stride`xs8 -> tiles[@a.dst, 0, 0];
IF({MAX_COLSB} - @a.stride > 0)
{{
    %zeros:1x`{MAX_ROWS}`x`{MAX_COLSB} - @a.stride`xs8 = constant(0);
    %zeros:1x`{MAX_ROWS}`x`{MAX_COLSB} - @a.stride`xs8 -> tiles[@a.dst, 0, @a.stride];
}}
""")

instr = acc.add_instruction("tilestored", ["src", "addr", "stride"])
instr.add_semantics(f"""
%tmp:1x`{MAX_ROWS}`x`@a.stride`xs8 <- tiles[@a.src:@a.src+1, 0:{MAX_ROWS}, 0:@a.stride:1];
%data:`{MAX_ROWS}*@a.stride`xs8 = reshape(%tmp);
%data:`{MAX_ROWS}*@a.stride`xs8 -> hbm[@a.addr];
""")

instr = acc.add_instruction("tdpbusd", ["dst", "src1", "src2"])
instr.add_semantics(f"""
%tile1:1x`{MAX_ROWS}`x`{MAX_COLSB}`xs8 <- tiles[@a.src1:@a.src1+1, 0:{MAX_ROWS}, 0:{MAX_COLSB}];
%tile2:1x`{MAX_ROWS}`x`{MAX_COLSB}`xs8 <- tiles[@a.src2:@a.src2+1, 0:{MAX_ROWS}, 0:{MAX_COLSB}];
%dst:1x`{MAX_ROWS}`x`{MAX_COLSB}`xs8 <- tiles[@a.dst:@a.dst+1, 0:{MAX_ROWS}, 0:{MAX_COLSB}];
%dst.r:`{MAX_ROWS}`x`{MAX_COLSB}//4`x4xs8 = reshape(%dst);
%dst.32:`{MAX_ROWS}`x`{MAX_COLSB}//4`xs32 = bitcast_convert(%dst.r);
%a.8:`{MAX_ROWS}`x`{MAX_COLSB}`xs8 = reshape(%tile1);
%a.u:`{MAX_ROWS}`x`{MAX_COLSB}`xu8 = bitcast_convert(%a.8);
%b1.8:`{MAX_ROWS}`x`{MAX_COLSB}//4`x4xs8 = reshape(%tile2);
%b2.8:`{MAX_ROWS}`x4x`{MAX_COLSB}//4`xs8 = transpose(%b1.8),dimensions={{0,2,1}};
%b.8:`{MAX_ROWS}*4`x`{MAX_COLSB}//4`xs8 = reshape(%b2.8);
%a.32:`{MAX_ROWS}`x`{MAX_COLSB}`xs32 = convert(%a.u);
%b.32:`{MAX_ROWS}*4`x`{MAX_COLSB}//4`xs32 = convert(%b.8);
%c.32:`{MAX_ROWS}`x`{MAX_COLSB}//4`xs32 = dot(%a.32, %b.32), lhs_batch_dims={{}}, lhs_contracting_dims={{1}}, rhs_batch_dims={{}}, rhs_contracting_dims={{0}};
%out_f:`{MAX_ROWS}`x`{MAX_COLSB}//4`xs32 = add(%c.32, %dst.32);
%c.8:`{MAX_ROWS}`x`{MAX_COLSB}//4`x4xs8 = bitcast_convert(%out_f);
%out:1x`{MAX_ROWS}`x`{MAX_COLSB}`xs8 = reshape(%c.8);
%out:1x`{MAX_ROWS}`x`{MAX_COLSB}`xs8 -> tiles[@a.dst, 0, 0];
""")

instr = acc.add_instruction("tdpbusd_repeat", ["dst", "src1", "src2"])

instr.add_semantics(f"""
REPEAT(m, {MAX_ROWS})
{{
    REPEAT(n, {MAX_COLSB} // 4)
    {{
        REPEAT(k, {MAX_COLSB} // 4)
        {{
            %A:1x1x4xs8 <- tiles[@a.src1:@a.src1+1, @l.m:@l.m+1, 4*@l.k:4*(@l.k+1)];
            %B:1x1x4xs8 <- tiles[@a.src2:@a.src2+1, @l.k:@l.k+1, 4*@l.n:4*(@l.n+1)];
            %A.32:1x1x4xs32 = convert(%A);
            %B.32:1x1x4xs32 = convert(%B);
            %C.32:1x1x1x1xs32 = dot(%A.32, %B.32),lhs_batch_dims={{}}, lhs_contracting_dims={{2}}, rhs_batch_dims={{}}, rhs_contracting_dims={{2}};
            %Old:1x1x4xs8 <- tiles[@a.dst:@a.dst+1, @l.m:@l.m+1, @l.n:@l.n+4];
            %Old.32:1x1xs32 = bitcast_convert(%Old);
            %tmp:1x1xs32 = reshape(%C.32);
            %New.32:1x1xs32 = add(%Old.32, %tmp);
            %New:1x1x4xs8 = bitcast_convert(%New.32);
            %New:1x1x4xs8 -> tiles[@a.dst, @l.m, @l.n];
        }}
    }}
}}

""")

instr = acc.add_instruction("mm512_add", ["dst", "src1", "src2"])
instr.add_semantics(f"""
%a:1x`{ZMM_WIDTH_32b}`xf32 <- zmm[@a.src1:@a.src1+1, 0:{ZMM_WIDTH_32b}];
%b:1x`{ZMM_WIDTH_32b}`xf32 <- zmm[@a.src2:@a.src2+1, 0:{ZMM_WIDTH_32b}];
%c:1x`{ZMM_WIDTH_32b}`xf32 = add(%a, %b);
%c:1x`{ZMM_WIDTH_32b}`xf32 -> zmm[@a.dst, 0];
""")

instr = acc.add_instruction("mm512_sub", ["dst", "src1", "src2"])
instr.add_semantics(f"""
%a:1x`{ZMM_WIDTH_32b}`xf32 <- zmm[@a.src1:@a.src1+1, 0:{ZMM_WIDTH_32b}];
%b:1x`{ZMM_WIDTH_32b}`xf32 <- zmm[@a.src2:@a.src2+1, 0:{ZMM_WIDTH_32b}];
%c:1x`{ZMM_WIDTH_32b}`xf32 = subtract(%a, %b);
%c:1x`{ZMM_WIDTH_32b}`xf32 -> zmm[@a.dst, 0];
""")

instr = acc.add_instruction("mm512_add_mem", ["dst", "addr", "src2"])
instr.add_semantics(f"""
%a:`{ZMM_WIDTH_8b}`xs8 <- hbm[@a.addr:@a.addr + {ZMM_WIDTH_8b}];
%t:1x`{ZMM_WIDTH_32b}`x4xs8 = reshape(%a);
%b:1x`{ZMM_WIDTH_32b}`xf32 = bitcast_convert(%t);
%c:1x`{ZMM_WIDTH_32b}`xf32 <- zmm[@a.src2:@a.src2+1, 0:{ZMM_WIDTH_32b}];
%d:1x`{ZMM_WIDTH_32b}`xf32 = add(%b, %c);
%d:1x`{ZMM_WIDTH_32b}`xf32 -> zmm[@a.dst, 0];
""")

instr = acc.add_instruction("mm512_mul", ["dst", "src1", "src2"])
instr.add_semantics(f"""
%a:1x`{ZMM_WIDTH_32b}`xf32 <- zmm[@a.src1:@a.src1+1, 0:{ZMM_WIDTH_32b}];
%b:1x`{ZMM_WIDTH_32b}`xf32 <- zmm[@a.src2:@a.src2+1, 0:{ZMM_WIDTH_32b}];
%c:1x`{ZMM_WIDTH_32b}`xf32 = multiply(%a, %b);
%c:1x`{ZMM_WIDTH_32b}`xf32 -> zmm[@a.dst, 0];
""")


instr = acc.add_instruction("mm512_fmadd", ["dst", "src1", "src2"])
instr.add_semantics(f"""
%a:1x`{ZMM_WIDTH_32b}`xf32 <- zmm[@a.src1:@a.src1+1, 0:{ZMM_WIDTH_32b}];
%b:1x`{ZMM_WIDTH_32b}`xf32 <- zmm[@a.src2:@a.src2+1, 0:{ZMM_WIDTH_32b}];
%c:1x`{ZMM_WIDTH_32b}`xf32 <- zmm[@a.dst:@a.dst+1, 0:{ZMM_WIDTH_32b}];
%d:1x`{ZMM_WIDTH_32b}`xf32 = multiply(%a, %b);
%e:1x`{ZMM_WIDTH_32b}`xf32 = add(%d, %c);
%e:1x`{ZMM_WIDTH_32b}`xf32 -> zmm[@a.dst, 0];
""")


instr = acc.add_instruction("mm512_max", ["dst", "src1", "src2"])
instr.add_semantics(f"""
%a:1x`{ZMM_WIDTH_32b}`xf32 <- zmm[@a.src1:@a.src1+1, 0:{ZMM_WIDTH_32b}];
%b:1x`{ZMM_WIDTH_32b}`xf32 <- zmm[@a.src2:@a.src2+1, 0:{ZMM_WIDTH_32b}];
%c:1x`{ZMM_WIDTH_32b}`xf32 = maximum(%a, %b);
%c:1x`{ZMM_WIDTH_32b}`xf32 -> zmm[@a.dst, 0];
""")

instr = acc.add_instruction("mm512_max_mem", ["dst", "addr", "src2"])
instr.add_semantics(f"""
%a:`{ZMM_WIDTH_8b}`xs8 <- hbm[@a.addr:@a.addr + {ZMM_WIDTH_8b}];
%t:1x`{ZMM_WIDTH_32b}`x4xs8 = reshape(%a);
%b:1x`{ZMM_WIDTH_32b}`xf32 = bitcast_convert(%t);
%c:1x`{ZMM_WIDTH_32b}`xf32 <- zmm[@a.src2:@a.src2+1, 0:{ZMM_WIDTH_32b}];
%d:1x`{ZMM_WIDTH_32b}`xf32 = maximum(%b, %c);
%d:1x`{ZMM_WIDTH_32b}`xf32 -> zmm[@a.dst, 0];
""")

instr = acc.add_instruction("mm512_min", ["dst", "src1", "src2"])
instr.add_semantics(f"""
%a:1x`{ZMM_WIDTH_32b}`xf32 <- zmm[@a.src1:@a.src1+1, 0:{ZMM_WIDTH_32b}];
%b:1x`{ZMM_WIDTH_32b}`xf32 <- zmm[@a.src2:@a.src2+1, 0:{ZMM_WIDTH_32b}];
%c:1x`{ZMM_WIDTH_32b}`xf32 = minimum(%a, %b);
%c:1x`{ZMM_WIDTH_32b}`xf32 -> zmm[@a.dst, 0];
""")

instr = acc.add_instruction("mm512_xor", ["dst", "src1", "src2"])
instr.add_semantics(f"""
%a:1x`{ZMM_WIDTH_32b}`xf32 <- zmm[@a.src1:@a.src1+1, 0:{ZMM_WIDTH_32b}];
%b:1x`{ZMM_WIDTH_32b}`xf32 <- zmm[@a.src2:@a.src2+1, 0:{ZMM_WIDTH_32b}];
%ai:1x`{ZMM_WIDTH_32b}`xs32 = convert(%a);
%bi:1x`{ZMM_WIDTH_32b}`xs32 = convert(%b);
%c:1x`{ZMM_WIDTH_32b}`xs32 = xor(%ai, %bi);
%cf:1x`{ZMM_WIDTH_32b}`xf32 = convert(%c);
%cf:1x`{ZMM_WIDTH_32b}`xf32 -> zmm[@a.dst, 0];
""")

instr = acc.add_instruction("mm512_load", ["dst", "addr"])
instr.add_semantics(f"""
%tmp:`{ZMM_WIDTH_32b}*4`xs8 <- hbm[@a.addr:@a.addr + {ZMM_WIDTH_8b}];
%tmp3:`{ZMM_WIDTH_32b}`x4xs8 = reshape(%tmp);
%tmp2:`{ZMM_WIDTH_32b}`xf32 = bitcast_convert(%tmp3);
%data:1x`{ZMM_WIDTH_32b}`xf32 = reshape(%tmp2);
%data:1x`{ZMM_WIDTH_32b}`xf32 -> zmm[@a.dst, 0];
""")

instr = acc.add_instruction("mm512_store", ["addr", "src"])
instr.add_semantics(f"""
%a:1x`{ZMM_WIDTH_32b}`xf32 <- zmm[@a.src:@a.src+1, 0:{ZMM_WIDTH_32b}];
%b:1x`{ZMM_WIDTH_32b}`x4xs8 = bitcast_convert(%a);
%c:`{ZMM_WIDTH_8b}`xs8 = reshape(%b);
%c:`{ZMM_WIDTH_8b}`xs8 -> hbm[@a.addr];
""")

instr = acc.add_instruction("mm512_cvt_i32", ["dst", "src"])
instr.add_semantics(f"""
%data_f32:1x`{ZMM_WIDTH_32b}`xf32 <- zmm[@a.src:@a.src+1, 0:{ZMM_WIDTH_32b}];
%hat:1x1xf32 = constant(float0.5);
%ha:1x`{ZMM_WIDTH_32b}`xf32 = broadcast(%hat);
%si:1x`{ZMM_WIDTH_32b}`xf32 = sign(%data_f32);
%toadd:1x`{ZMM_WIDTH_32b}`xf32 = multiply(%ha, %si);
%data_added:1x`{ZMM_WIDTH_32b}`xf32 = add(%toadd, %data_f32);
%data_i32:1x`{ZMM_WIDTH_32b}`xs32 = convert(%data_added);
%data:1x`{ZMM_WIDTH_32b}`xf32 = bitcast_convert(%data_i32);
%data:1x`{ZMM_WIDTH_32b}`xf32 -> zmm[@a.dst, 0];
""")

instr = acc.add_instruction("mm512_cvt_i8_store", ["addr", "src",])
instr.add_semantics(f"""
%data_f32:1x`{ZMM_WIDTH_32b}`xf32 <- zmm[@a.src:@a.src+1, 0:{ZMM_WIDTH_32b}];
%data_tmpf:`{ZMM_WIDTH_32b}`xf32 = reshape(%data_f32);
%data2:`{ZMM_WIDTH_32b}`xs32 = bitcast_convert(%data_tmpf);
%data:`{ZMM_WIDTH_32b}`xs8 = convert(%data2);
%data:`{ZMM_WIDTH_32b}`xs8 -> hbm[@a.addr];
""")

instr = acc.add_instruction("mm128_loadi", ["dst", "val"])
instr.add_semantics("""
%val_u32:1x1xu32 = constant(@a.val);
%val_f32:1x1xf32 = bitcast_convert(%val_u32);
%val_f32:1x1xf32 -> zmm[@a.dst, 0];
%zero:1x3xf32 = constant(0);
%zero:1x3xf32 -> zmm[@a.dst, 1];
""")

instr = acc.add_instruction("mm512_broadcast", ["dst", "src"])
instr.add_semantics(f"""
%in:1x1xf32 <- zmm[@a.src:@a.src+1, 0:1];
%value:f32 = reshape(%in);
%data:1x`{ZMM_WIDTH_32b}`xf32 = broadcast_type(%value);
%data:1x`{ZMM_WIDTH_32b}`xf32 -> zmm[@a.dst, 0];
""")

instr = acc.add_instruction("mm512_broadcast_mem", ["dst", "addr"])
instr.add_semantics(f"""
%a:4xs8 <- hbm[@a.addr:@a.addr + 4];
%b:1x4xs8 = reshape(%a);
%tmp2:1xf32 = bitcast_convert(%b);
%d:f32 = reshape(%tmp2);
%f:1x`{ZMM_WIDTH_32b}`xf32 = broadcast_type(%d);
%f:1x`{ZMM_WIDTH_32b}`xf32 -> zmm[@a.dst, 0];
""")

instr = acc.add_instruction("select", ["dst", "src1", "src2", "src3"])
instr.add_semantics(f"""
%a:1x`{ZMM_WIDTH_32b}`xf32 <- zmm[@a.src1:@a.src1+1, 0:{ZMM_WIDTH_32b}];
%b:1x`{ZMM_WIDTH_32b}`xf32 <- zmm[@a.src2:@a.src2+1, 0:{ZMM_WIDTH_32b}];
%c:1x`{ZMM_WIDTH_32b}`xf32 <- zmm[@a.src3:@a.src3+1, 0:{ZMM_WIDTH_32b}];
%f:1x`{ZMM_WIDTH_32b}`xf32 = select_lt(%b, %c, %a, %c);
%f:1x`{ZMM_WIDTH_32b}`xf32 -> zmm[@a.dst, 0];
""")

acc.generate_sim()
