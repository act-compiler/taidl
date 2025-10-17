import numpy as np


def debug_test(kernel, api):
    hbm_size = 3072

    @kernel(
        hbm=hbm_size,
        input=[
            {"addr": 0, "shape": (16, 64), "dtype": np.int8},
            {"addr": 1024, "shape": (16, 64), "dtype": np.int8},
        ],
        output=[
            {"addr": 2048, "shape": (16, 16), "dtype": np.int32},
        ],
    )
    def _kernel() -> None:
        api.tilezero(0)
        api.tileloadd(dst=4, addr=0, stride=64)
        api.tileloadd(dst=6, addr=1024, stride=64)
        api.tdpbusd(0, 4, 6)
        api.debug(prefix="tmm0", data="tiles[0]")
        api.tilestored(src=0, addr=2048, stride=64)

    return _kernel, hbm_size


def cnn_inference_amx(kernel, api, NUM_BLOCKS=1):
    size_in_t4 = 1024 + 0x40 * (NUM_BLOCKS - 1)
    size_in_t5 = 1024 + 0x40 * (NUM_BLOCKS - 1)
    size_in_t6 = 0x800 * NUM_BLOCKS
    size_out = 4 * 1024

    _in_t4 = 0
    _in_t5 = _in_t4 + size_in_t4
    _in_t6 = _in_t5 + size_in_t5
    _in_t7 = _in_t6 + 0x40
    _out = _in_t6 + size_in_t6
    hbm_size = _out + size_out

    @kernel(
        hbm=hbm_size,
        input=[
            {"addr": _in_t4, "shape": (size_in_t4,), "dtype": np.int8},
            {"addr": _in_t5, "shape": (size_in_t5,), "dtype": np.int8},
            {"addr": _in_t6, "shape": (size_in_t6,), "dtype": np.int8},
        ],
        output=[
            {"addr": _out, "shape": (4, 256), "dtype": np.int32},
        ],
    )
    def _kernel() -> None:
        api.tilezero(0)
        api.tilezero(1)
        api.tilezero(2)
        api.tilezero(3)

        api.start_loop("i", 0, NUM_BLOCKS)
        api.tileloadd(dst=4, addr=f"{64} * %i + {_in_t4}", stride=64)
        api.tileloadd(dst=6, addr=f"{2048} * %i + {_in_t6}", stride=64)
        api.tileloadd(dst=7, addr=f"{2048} * %i + {_in_t7}", stride=64)
        api.tdpbusd(0, 4, 6)
        api.tileloadd(dst=5, addr=f"{64} * %i + {_in_t5}", stride=64)
        api.tdpbusd(1, 4, 7)
        api.tdpbusd(2, 5, 6)
        api.tdpbusd(3, 5, 7)
        api.end_loop()

        api.tilestored(src=0, addr=_out + 0 * 1024, stride=64)
        api.tilestored(src=1, addr=_out + 1 * 1024, stride=64)
        api.tilestored(src=2, addr=_out + 2 * 1024, stride=64)
        api.tilestored(src=3, addr=_out + 3 * 1024, stride=64)

    return _kernel, hbm_size


def cnn_inference_mix(kernel, api, NUM_BLOCKS=1):
    size_t4 = 1024 + 0x40 * (NUM_BLOCKS - 1)
    size_t5 = 1024 + 0x40 * (NUM_BLOCKS - 1)
    size_t6 = 0x800 * NUM_BLOCKS
    size_max = 16
    size_in_z0 = 4
    size_in_z10 = 16
    size_in_z15 = 16
    size_avx_in = NUM_BLOCKS * 3 * 16
    size_amx_out = 4 * 1024
    size_avx_out = NUM_BLOCKS * 3 * 16

    _in_t4 = 0
    _in_t5 = _in_t4 + size_t4
    _in_t6 = _in_t5 + size_t5
    _in_t7 = _in_t6 + 0x40
    _max = _in_t6 + size_t6
    _in_z0 = _max + size_max * 4
    _in_z10 = _in_z0 + size_in_z0 * 4
    _in_z15 = _in_z10 + size_in_z15 * 4
    _avx_in = _in_z15 + size_in_z15 * 4
    _amx_out = _avx_in + size_avx_in * 4
    _avx_out = _amx_out + size_amx_out
    hbm_size = _avx_out + size_avx_out

    @kernel(
        hbm=hbm_size,
        input=[
            {"addr": _in_t4, "shape": (size_t4,), "dtype": np.int8},
            {"addr": _in_t5, "shape": (size_t5,), "dtype": np.int8},
            {"addr": _in_t6, "shape": (size_t6,), "dtype": np.int8},
            {"addr": _max, "shape": (size_max,), "dtype": np.float32},
            {"addr": _in_z0, "shape": (size_in_z0,), "dtype": np.float32},
            {"addr": _in_z10, "shape": (size_in_z10,), "dtype": np.float32},
            {"addr": _in_z15, "shape": (size_in_z15,), "dtype": np.float32},
            {"addr": _avx_in, "shape": (NUM_BLOCKS, 3, 16), "dtype": np.float32},
        ],
        output=[
            {"addr": _amx_out, "shape": (4, 256), "dtype": np.int32},
            {"addr": _avx_out, "shape": (NUM_BLOCKS, 3, 16), "dtype": np.uint8},
        ],
    )
    def _kernel() -> None:
        api.mm512_load(dst=10, addr=_in_z10)
        api.mm512_load(dst=15, addr=_in_z15)
        api.mm512_xor(8, 8, 8)
        api.mm128_loadi(dst=9, val=0x437F0000)
        api.mm512_broadcast(dst=9, src=9)

        api.tilezero(0)
        api.tilezero(1)
        api.tilezero(2)
        api.tilezero(3)

        api.start_loop("i", 0, NUM_BLOCKS)
        api.tileloadd(dst=4, addr=f"{0x40} * %i + {_in_t4}", stride=64)
        api.tileloadd(dst=6, addr=f"{0x800} * %i + {_in_t6}", stride=64)
        api.tileloadd(dst=7, addr=f"{0x800} * %i + {_in_t7}", stride=64)
        api.tdpbusd(0, 4, 6)

        api.mm512_load(dst=31, addr=f"{192} * %i +{_avx_in +  2*64}")
        api.mm512_load(dst=30, addr=f"{192} * %i +{_avx_in +  1*64}")
        api.mm512_load(dst=29, addr=f"{192} * %i +{_avx_in +  0*64}")

        api.mm512_mul(31, 15, 31)
        api.mm512_mul(30, 15, 30)
        api.mm512_mul(29, 15, 29)

        api.mm512_add(31, 10, 31)
        api.mm512_add(30, 10, 30)
        api.mm512_add(29, 10, 29)

        api.mm512_max_mem(29, _max, 29)
        api.mm512_max_mem(30, _max, 30)
        api.mm512_max_mem(31, _max, 31)

        api.mm512_broadcast_mem(dst=0, addr=_in_z0)
        api.mm512_mul(31, 0, 31)
        api.mm512_mul(30, 0, 30)
        api.mm512_mul(29, 0, 29)

        api.mm512_max(31, 8, 31)
        api.mm512_min(31, 9, 31)
        api.mm512_cvt_i32(dst=31, src=31)
        api.mm512_cvt_i8_store(addr=f"{48} * %i + {_avx_out + 2*16}", src=31)
        api.tileloadd(dst=5, addr=f"{0x40} * %i + {_in_t5}", stride=64)
        api.tdpbusd(1, 4, 7)

        api.mm512_max(30, 8, 30)
        api.mm512_min(30, 9, 30)
        api.mm512_cvt_i32(dst=30, src=30)
        api.mm512_cvt_i8_store(addr=f"{48} * %i + {_avx_out + 1*16}", src=30)
        api.tdpbusd(2, 5, 6)

        api.mm512_max(29, 8, 29)
        api.mm512_min(29, 9, 29)
        api.mm512_cvt_i32(dst=29, src=29)
        api.mm512_cvt_i8_store(addr=f"{48} * %i + {_avx_out + 0*16}", src=29)
        api.tdpbusd(3, 5, 7)
        api.end_loop()

        api.tilestored(src=0, addr=_amx_out + 0 * 1024, stride=64)
        api.tilestored(src=1, addr=_amx_out + 1 * 1024, stride=64)
        api.tilestored(src=2, addr=_amx_out + 2 * 1024, stride=64)
        api.tilestored(src=3, addr=_amx_out + 3 * 1024, stride=64)

    return _kernel, hbm_size


def mem_format_prop_avx(kernel, api, NUM_BLOCKS=1):
    BLOCK_SIZE = 14
    size_in_z0 = BLOCK_SIZE * 4
    size_in_z2_3 = NUM_BLOCKS * 2 * 16
    size_out = 32 * 16

    _in_z0 = 0
    _in_z2_3 = _in_z0 + size_in_z0 * 4
    _out = _in_z2_3 + size_in_z2_3 * 4
    hbm_size = _out + size_out * 4

    @kernel(
        hbm=hbm_size,
        input=[
            {"addr": _in_z0, "shape": (BLOCK_SIZE, 4), "dtype": np.float32},
            {"addr": _in_z2_3, "shape": (NUM_BLOCKS, 2, 16), "dtype": np.float32},
        ],
        output=[
            {"addr": _out, "shape": (32, 16), "dtype": np.float32},
        ],
    )
    def _kernel() -> None:
        for i in range(31, 3, -1):
            api.mm512_xor(i, i, i)

        api.start_loop("i", 0, NUM_BLOCKS)
        api.mm512_load(dst=3, addr=f"{128} * %i + {_in_z2_3 + 1*64}")
        api.mm512_load(dst=2, addr=f"{128} * %i + {_in_z2_3 + 0*64}")

        api.start_loop("j", 0, BLOCK_SIZE)
        api.mm512_broadcast_mem(dst=0, addr=f"{16} * %j + {_in_z0}")
        api.mm512_fmadd(f"{-2} * %j + {31}", 0, 3)
        api.mm512_fmadd(f"{-2} * %j + {30}", 0, 2)

        api.end_loop()
        api.end_loop()

        for i in range(31, 3, -1):
            api.mm512_store(addr=_out + i * 64, src=i)

    return _kernel, hbm_size


def rnn_inference_amx(kernel, api, NUM_BLOCKS=1):
    size_in_t2 = 1024 + 0x40 * (NUM_BLOCKS - 1)
    size_in_t3 = 0x800 * NUM_BLOCKS
    size_out = 2 * 1024

    _in_t2 = 0
    _in_t3 = _in_t2 + size_in_t2
    _in_t4 = _in_t3 + 0x40
    _out = _in_t3 + size_in_t3
    hbm_size = _out + size_out

    @kernel(
        hbm=hbm_size,
        input=[
            {"addr": _in_t2, "shape": (size_in_t2,), "dtype": np.int8},
            {"addr": _in_t3, "shape": (size_in_t3,), "dtype": np.int8},
        ],
        output=[
            {"addr": _out, "shape": (2, 256), "dtype": np.int32},
        ],
    )
    def _kernel() -> None:
        api.tilezero(0)
        api.tilezero(1)

        api.start_loop("i", 0, NUM_BLOCKS)
        api.tileloadd(dst=2, addr=f"{0x40} * %i + {_in_t2}", stride=64)
        api.tileloadd(dst=3, addr=f"{0x800} * %i + {_in_t3}", stride=64)
        api.tdpbusd(0, 2, 3)
        api.tileloadd(dst=4, addr=f"{0x800} * %i + {_in_t4}", stride=64)
        api.tdpbusd(1, 2, 4)
        api.end_loop()

        api.tilestored(src=0, addr=_out + 0 * 1024, stride=64)
        api.tilestored(src=1, addr=_out + 1 * 1024, stride=64)

    return _kernel, hbm_size


def sgemm_avx(kernel, api, NUM_BLOCKS=1):
    BLOCK_SIZE = 4
    size_in = NUM_BLOCKS * 3 * 16
    size_in_z6_7 = (BLOCK_SIZE + 1) * 2 * 4
    size_offset = 32 * 16
    size_out = 32 * 16

    _in = 0
    _in_z6_7 = _in + size_in * 4
    _offset = _in_z6_7 + size_in_z6_7 * 4
    _out = _offset + size_offset * 4
    hbm_size = _out + size_out * 4

    @kernel(
        hbm=hbm_size,
        input=[
            {"addr": _in, "shape": (NUM_BLOCKS, 3, 16), "dtype": np.float32},
            {"addr": _in_z6_7, "shape": (BLOCK_SIZE + 1, 2, 4), "dtype": np.float32},
            {"addr": _offset, "shape": (32, 16), "dtype": np.float32},
        ],
        output=[
            {"addr": _out, "shape": (32, 16), "dtype": np.float32},
        ],
    )
    def _kernel() -> None:
        for i in range(8, 32):
            api.mm512_xor(i, i, i)
        api.mm512_broadcast_mem(dst=6, addr=_in_z6_7 + BLOCK_SIZE * 32 + 0 * 16)
        api.mm512_broadcast_mem(dst=7, addr=_in_z6_7 + BLOCK_SIZE * 32 + 1 * 16)

        api.start_loop("i", 0, NUM_BLOCKS)
        api.mm512_load(dst=0, addr=f"{192} * %i + {_in + 0*64}")
        api.mm512_load(dst=1, addr=f"{192} * %i + {_in + 1*64}")
        api.mm512_load(dst=2, addr=f"{192} * %i + {_in + 2*64}")

        api.start_loop("j", 0, BLOCK_SIZE)
        api.mm512_fmadd(f"{2} * %j + {8}", 0, 6)
        api.mm512_fmadd(f"{2} * %j + {16}", 1, 6)
        api.mm512_fmadd(f"{2} * %j + {24}", 2, 6)
        api.mm512_broadcast_mem(dst=6, addr=f"32 * %j + {_in_z6_7 + 0*16}")

        api.mm512_fmadd(f"{2} * %j + {9}", 0, 7)
        api.mm512_fmadd(f"{2} * %j + {17}", 1, 7)
        api.mm512_fmadd(f"{2} * %j + {25}", 2, 7)
        api.mm512_broadcast_mem(dst=7, addr=f"32 * %j + {_in_z6_7 + 1*16}")

        api.end_loop()
        api.end_loop()

        for i in range(8):
            api.mm512_add_mem(8 + i, _offset + (8 + i) * 64, 8 + i)
            api.mm512_add_mem(16 + i, _offset + (16 + i) * 64, 16 + i)
            api.mm512_add_mem(24 + i, _offset + (24 + i) * 64, 24 + i)

            api.mm512_store(addr=_out + (8 + i) * 64, src=8 + i)
            api.mm512_xor(8 + i, 8 + i, 8 + i)
            api.mm512_store(addr=_out + (16 + i) * 64, src=16 + i)
            api.mm512_xor(16 + i, 16 + i, 16 + i)
            api.mm512_store(addr=_out + (24 + i) * 64, src=24 + i)
            api.mm512_xor(24 + i, 24 + i, 24 + i)

    return _kernel, hbm_size
