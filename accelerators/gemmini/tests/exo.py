import numpy as np


def matmul_6(kernel, api):
    res = 0
    a_addr = 0
    b_addr = 12544 * 256
    output_addr = b_addr + 256 * 64
    zero_addr = output_addr + 12544 * 64 * 4
    hbm_size = zero_addr + 2048

    A_SP = 0
    B_SP = (4096 / 256 * 7 + 4 * 3) * 16

    @kernel(hbm=hbm_size,
            input=[
                {'addr': a_addr, 'shape': (12544, 256), 'dtype': np.int8},
                {'addr': b_addr, 'shape': (256, 64), 'dtype': np.int8},
            ],
            output=[
                {'addr': output_addr, 'shape': (12544, 64), 'dtype': np.int32},
            ]
            )
    def matmul_6_() -> None:
        api.dataflow_config(dataflow=1)
        api.start_loop("io", 0, 98)
        api.start_loop("i", 0, 8)

        for l in range(4):  # noqa: E741
            api.mvin_acc(rows=1, hbm_addr=zero_addr, acc_addr=f"{64} * %i + {res + l * 16}")

        for ko in range(4):
            api.mvin_spad(
                tiles=4,
                stride=256,
                hbm_addr=f"{16*256} * %i + {128 *256} * %io + {64*ko + a_addr}",
                sp_addr=f"{4096/256 * 16} * %i + {4 * 16 * ko + A_SP}")
            for g in range(4):
                api.mvin_spad(tiles=4, stride=64, hbm_addr=64 * 64 * ko + 16 * 64 * g + b_addr,
                              sp_addr=16 * ko * 16 + B_SP + 4 * 16 * g)
            for h in range(16):
                api.matmul_preload(
                    rs1=4096 / 256 * 16 * ko + h * 16 + B_SP,
                    rs2=f"{4 * 16} * %i + {(h % 4) * 16 + res}")
                api.matmul32_compute_accumulated(
                    rs1=f"{4096/256 * 16} * %i + {4 * ko * 16 + int(h/4) * 16 + A_SP}", rs2=-1)

            for p in range(4):
                api.mvout_acc_stride(
                    stride=64,
                    hbm_addr=f"{16*64*4} * %i + {64*128*4} * %io + {output_addr + p * 64}",
                    acc_addr=f"{4 * 16 } * %i + {res + p * 16}")

        api.end_loop()
        api.end_loop()

    return matmul_6_, hbm_size


def matmul_4(kernel, api):
    res = 0
    a_addr = 0
    b_addr = 12544 * 64
    output_addr = b_addr + 256 * 64
    zero_addr = output_addr + 12544 * 256 * 4
    hbm_size = zero_addr + 2048

    A_SP = 0
    B_SP = 4 * 195 * 16

    @kernel(hbm=hbm_size,
            input=[
                {'addr': a_addr, 'shape': (12544, 64), 'dtype': np.int8},
                {'addr': b_addr, 'shape': (64, 256), 'dtype': np.int8},
            ],
            output=[
                {'addr': output_addr, 'shape': (12544, 256), 'dtype': np.int32},
            ]
            )
    def matmul_4_() -> None:
        api.dataflow_config(dataflow=1)
        api.start_loop("io", 0, 4)
        api.start_loop("i", 0, 196)

        for j in range(4):

            for l in range(4):  # noqa: E741
                api.mvin_acc(rows=1, hbm_addr=zero_addr, acc_addr=(res + j * 4 * 16 + l * 16))

            api.mvin_spad(
                tiles=4,
                stride=64,
                hbm_addr=f"{16*64} * %i + {3136 *64} * %io + {a_addr}",
                sp_addr=f"{1024/256 * 16} * %i + {A_SP}")

            for g in range(4):
                api.mvin_spad(tiles=4, stride=256, hbm_addr=64 * j + 16 * 256 * g + b_addr,
                              sp_addr=16 * 16 * j + B_SP + 4 * 16 * g)
            for h in range(16):
                api.matmul_preload(rs1=4096 / 16 * j + h * 16 + B_SP,
                                   rs2=4 * 16 * j + (h % 4) * 16 + res)
                api.matmul32_compute_accumulated(rs1=f"{1024/256*16} * %i + {int(h/4) * 16 + A_SP}",
                                                 rs2=-1)

            for p in range(4):
                api.mvout_acc_stride(
                    stride=256,
                    hbm_addr=f"{16*256*4} * %i + {256*3136*4} * %io + {64*4 * j + output_addr + p * 64}",  # noqa: E501
                    acc_addr=4 * j * 16 + res + p * 16)

        api.end_loop()
        api.end_loop()

    return matmul_4_, hbm_size


def matmul_27(kernel, api):
    res = 0
    a_addr = 0
    b_addr = 784 * 256
    output_addr = b_addr + 256 * 1024
    zero_addr = output_addr + 784 * 1024 * 4
    hbm_size = zero_addr + 2048

    A_SP = 0
    B_SP = (4096 / 256 * 6 + 4 * 3) * 16

    @kernel(hbm=zero_addr + 4096,
            input=[
                {'addr': a_addr, 'shape': (784, 256), 'dtype': np.int8},
                {'addr': b_addr, 'shape': (256, 1024), 'dtype': np.int8},
            ],
            output=[
                {'addr': output_addr, 'shape': (784, 1024), 'dtype': np.int32},
            ]
            )
    def matmul_27_() -> None:
        api.dataflow_config(dataflow=1)
        api.start_loop("io", 0, 7)
        api.start_loop("jo", 0, 2)
        api.start_loop("i", 0, 7)

        for j in range(8):

            for l in range(4):  # noqa: E741
                api.mvin_acc(rows=1, hbm_addr=zero_addr, acc_addr=(res + j * 4 * 16 + l * 16))

            for ko in range(4):
                api.mvin_spad(
                    tiles=4,
                    stride=256,
                    hbm_addr=f"{16*256} * %i + {112 *256} * %io + {64 * ko + a_addr}",
                    sp_addr=f"{4096/16} * %i + {64 * ko + A_SP}")
                for g in range(4):
                    api.mvin_spad(
                        tiles=4,
                        stride=1024,
                        hbm_addr=f"{512} * %jo + {64*1024 * ko + 64 * j + 16 * 1024 * g + b_addr}",
                        sp_addr=16384 / 16 * j + 16 * 16 * ko + B_SP + 4 * 16 * g)
                for h in range(16):
                    api.matmul_preload(rs1=16384 / 16 * j + 16 * 16 * ko + h * 16 + B_SP,
                                       rs2=16 * 4 * j + (h % 4) * 16 + res)
                    api.matmul32_compute_accumulated(
                        rs1=f"{4096/16} * %i + {4 * 16 * ko + int(h/4) * 16 + A_SP}",
                        rs2=-1)

            for p in range(4):
                api.mvout_acc_stride(
                    stride=1024,
                    hbm_addr=f"{16*1024*4} * %i + {112*1024*4} * %io + {512*4} * %jo + {64*4 * j + output_addr + p * 64}",  # noqa: E501
                    acc_addr=4 * 16 * j + res + p * 16)

        api.end_loop()
        api.end_loop()
        api.end_loop()

    return matmul_27_, hbm_size


def matmul_14(kernel, api):
    res = 0
    a_addr = 0
    b_addr = 3136 * 128
    output_addr = b_addr + 128 * 512
    zero_addr = output_addr + 3136 * 512 * 4
    hbm_size = zero_addr + 2048

    A_SP = 0
    B_SP = (2048 / 256 * 48 + 4 * 1) * 16

    @kernel(hbm=hbm_size,
            input=[
                {'addr': a_addr, 'shape': (3136, 128), 'dtype': np.int8},
                {'addr': b_addr, 'shape': (128, 512), 'dtype': np.int8},
            ],
            output=[
                {'addr': output_addr, 'shape': (3136, 512), 'dtype': np.int32},
            ]
            )
    def matmul_14_() -> None:
        api.dataflow_config(dataflow=1)
        api.start_loop("io", 0, 4)
        api.start_loop("i", 0, 49)

        for j in range(8):

            for l in range(4):  # noqa: E741
                api.mvin_acc(rows=1, hbm_addr=zero_addr, acc_addr=(res + j * 4 * 16 + l * 16))

            for ko in range(2):
                api.mvin_spad(
                    tiles=4,
                    stride=128,
                    hbm_addr=f"{16*128} * %i + {784 *128} * %io + {64 * ko + a_addr}",
                    sp_addr=f"{2048/16} * %i + {4 * 16 * ko + A_SP}")
                for g in range(4):
                    api.mvin_spad(
                        tiles=4,
                        stride=512,
                        hbm_addr=64 * 512 * ko + 16 * 512 * g + 64 * j + b_addr,
                        sp_addr=8192 / 16 * j + 16 * 16 * ko + B_SP + 4 * 16 * g)
                for h in range(16):
                    api.matmul_preload(rs1=8192 / 16 * j + 16 * 16 * ko + h * 16 + B_SP,
                                       rs2=4 * j * 16 + (h % 4) * 16 + res)
                    api.matmul32_compute_accumulated(
                        rs1=f"{2048/16} * %i + {4 * 16 *  ko + int(h/4) * 16+ A_SP}",
                        rs2=-1)

            for p in range(4):
                api.mvout_acc_stride(
                    stride=512,
                    hbm_addr=f"{16*512*4} * %i + {784*512*4} * %io + {64*4 * j + output_addr + p * 64}",  # noqa: E501
                    acc_addr=4 * j * 16 + res + p * 16)

        api.end_loop()
        api.end_loop()

    return matmul_14_, hbm_size


def matmul_16(kernel, api):
    res = 0
    a_addr = 0
    b_addr = 1605632
    output_addr = 1671168
    zero_addr = output_addr + 3136 * 128 * 4
    hbm_size = zero_addr + 2048

    A_SP = 0
    B_SP = (8192 / 256 * 13 + 4 * 7) * 16

    @kernel(hbm=hbm_size,
            input=[
                {'addr': a_addr, 'shape': (3136, 512), 'dtype': np.int8},
                {'addr': b_addr, 'shape': (512, 128), 'dtype': np.int8},
            ],
            output=[
                {'addr': output_addr, 'shape': (3136, 128), 'dtype': np.int32},
            ]
            )
    def matmul_16_() -> None:
        api.dataflow_config(dataflow=1)
        api.start_loop("io", 0, 14)
        api.start_loop("i", 0, 14)

        for j in range(2):

            for l in range(4):  # noqa: E741
                api.mvin_acc(rows=1, hbm_addr=zero_addr, acc_addr=(res + j * 4 * 16 + l * 16))

            for ko in range(8):
                api.mvin_spad(
                    tiles=4,
                    stride=512,
                    hbm_addr=f"{512*16} * %i + {224 *512} * %io + {64 * ko + a_addr}",
                    sp_addr=f"{8192/16} * %i + {4 * 16 * ko + A_SP}")
                for g in range(4):
                    api.mvin_spad(
                        tiles=4,
                        stride=128,
                        hbm_addr=64 * ko * 128 + 16 * 128 * g + 64 * j + b_addr,
                        sp_addr=32768 / 16 * j + 4096 / 16 * ko + B_SP + 4 * 16 * g)
                for h in range(16):
                    api.matmul_preload(rs1=32768 / 16 * j + 16 * 16 * ko + h * 16 + B_SP,
                                       rs2=4 * 16 * j + (h % 4) * 16 + res)
                    api.matmul32_compute_accumulated(
                        rs1=f"{8192/16} * %i + {4 * 16 * ko + int(h/4) * 16 + A_SP}",
                        rs2=-1)

            for p in range(4):
                api.mvout_acc_stride(
                    stride=128,
                    hbm_addr=f"{16*128*4} * %i + {224*128*4} * %io + {64*4 * j + output_addr + p * 64}",  # noqa: E501
                    acc_addr=4 * 16 * j + res + p * 16)

        api.end_loop()
        api.end_loop()

    return matmul_16_, hbm_size


def matmul_512(kernel, api):
    res = 0

    a_addr = 0
    b_addr = 262144
    output_addr = 524288
    zero_addr = 524288 + 262144 * 4
    hbm_size = zero_addr + 2048

    A_SP = 0
    B_SP = (256 * 1 + 32 * 7 + 4 * 3) * 16

    @kernel(hbm=zero_addr + 4 * 512,
            input=[
                {'addr': a_addr, 'shape': (512, 512), 'dtype': np.int8},
                {'addr': b_addr, 'shape': (512, 512), 'dtype': np.int8},
            ],
            output=[
                {'addr': output_addr, 'shape': (512, 512), 'dtype': np.int32},
            ]
            )
    def matmul_512_() -> None:
        api.dataflow_config(dataflow=1)
        api.start_loop("ioo", 0, 2)
        api.start_loop("jo", 0, 2)
        api.start_loop("io", 0, 2)
        api.start_loop("i", 0, 8)

        for ji in range(4):

            for l in range(4):  # noqa: E741
                api.mvin_acc(rows=1, hbm_addr=zero_addr, acc_addr=(res + ji * 16 * 4 + l * 16))

            for ko in range(8):
                api.mvin_spad(
                    tiles=4,
                    stride=512,
                    hbm_addr=f"{512*16} * %i + {128 *512} * %io + {256*512} * %ioo + {64 * ko + a_addr}",  # noqa: E501
                    sp_addr=f"{256 * 16} * %io + {32 * 16} * %i + {4 * 16 * ko + A_SP}")
                for g in range(4):
                    api.mvin_spad(
                        tiles=4,
                        stride=512,
                        hbm_addr=f"256 * %jo + {64 * ji + 64 *512 * ko + b_addr + 16 * 512 * g}",
                        sp_addr=128 * 16 * ji + 16 * 16 * ko + B_SP + 4 * 16 * g)
                    for h in range(4):
                        api.matmul_preload(
                            rs1=128 * 16 * ji + 16 * 16 * ko + B_SP + 4 * 16 * g + 16 * h,
                            rs2=4 * 16 * ji + 16 * h + res)
                        api.matmul32_compute_accumulated(
                            rs1=f"{256 * 16} * %io + {32 * 16} * %i + {4 * 16 * ko + 16 * g + A_SP}",  # noqa: E501
                            rs2=-1)

            for p in range(4):
                api.mvout_acc_stride(
                    stride=512,
                    hbm_addr=f"{8192*4} * %i + {65536*4} * %io + {131072*4} * %ioo + {256*4} * %jo + {64*4 * ji + output_addr + p * 64}",  # noqa: E501
                    acc_addr=4 * 16 * ji + res + p * 16)

        api.end_loop()
        api.end_loop()
        api.end_loop()
        api.end_loop()

    return matmul_512_, hbm_size
