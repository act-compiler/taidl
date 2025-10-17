import numpy as np


def tiled_matmul(kernel, api, DIM=16, iterations=16, df=0, xla_while=0):
    hbm_size = (DIM * DIM) * (iterations * 3 + 1)
    a_addr = 0
    b_addr = iterations * DIM * DIM
    d_addr = (iterations + 1) * DIM * DIM

    c_addr = DIM * DIM * iterations * 2 + DIM * DIM

    @kernel(hbm=hbm_size,
            input=[
                {'addr': a_addr, 'shape': (DIM * iterations, DIM), 'dtype': np.int8},
                {'addr': b_addr, 'shape': (DIM, DIM), 'dtype': np.int8},
                {'addr': d_addr, 'shape': (DIM * iterations, DIM), 'dtype': np.int8},
            ],
            output=[
                {'addr': c_addr, 'shape': (iterations * DIM, DIM), 'dtype': np.int8},
            ]
            )
    def tiled_matmul_with_for() -> None:
        # A
        for i in range(0, iterations):
            api.mvin_spad(tiles=1, stride=DIM, hbm_addr=DIM * DIM * i, sp_addr=DIM * i)
        # B
        api.mvin_spad(
            tiles=1,
            stride=DIM,
            hbm_addr=DIM * DIM * iterations,
            sp_addr=DIM * iterations)
        # D
        for i in range(0, iterations):
            api.mvin_spad(tiles=1,
                          stride=DIM,
                          hbm_addr=DIM * DIM * i + (DIM * DIM * (iterations + 1)),
                          sp_addr=DIM * i + (DIM * (iterations + 1)))

        api.dataflow_config(dataflow=df)
        if (df == 0):
            for i in range(iterations):
                api.matmul_preload(rs1=DIM * (iterations + 1 + i),
                                   rs2=DIM * (2 * iterations + 1 + i))
                api.matmul8_compute_preloaded(rs1=i * DIM, rs2=iterations * DIM)
        elif (df == 1):
            api.matmul_preload(rs1=DIM * (iterations), rs2=DIM * (2 * iterations + 1))
            api.matmul8_compute_preloaded(rs1=0, rs2=(iterations + 1) * DIM)
            for i in range(1, iterations):
                api.matmul_preload(rs1=0, rs2=DIM * (2 * iterations + 1 + i))
                api.matmul8_compute_accumulated(rs1=DIM * (i), rs2=(iterations + i + 1) * DIM)
        for i in range(0, iterations):
            api.mvout_spad(stride=DIM,
                           hbm_addr=(i + iterations * 2 + 1) * DIM * DIM,
                           sp_addr=DIM * (i + iterations * 2 + 1),
                           rows=DIM)

    @kernel(hbm=hbm_size,
            input=[
                {'addr': a_addr, 'shape': (DIM * iterations, DIM), 'dtype': np.int8},
                {'addr': b_addr, 'shape': (DIM, DIM), 'dtype': np.int8},
                {'addr': d_addr, 'shape': (DIM * iterations, DIM), 'dtype': np.int8},
            ],
            output=[
                {'addr': c_addr, 'shape': (iterations * DIM, DIM), 'dtype': np.int8},
            ]
            )
    def tiled_matmul_api_loop() -> None:
        api.start_loop("j", 0, iterations * 2 + 1)
        api.mvin_spad(
            tiles=1,
            stride=DIM,
            hbm_addr=f"{DIM * DIM} * %j + {0}",
            sp_addr=f"{DIM} * %j + {0}")
        api.end_loop()
        api.dataflow_config(dataflow=df)
        if (df == 0):
            api.start_loop("i", 0, iterations)
            api.matmul_preload(rs1=f"{DIM} * %i + {DIM * (iterations + 1)}",
                               rs2=f"{DIM} * %i + {DIM * (2 * iterations + 1)}")
            api.matmul8_compute_preloaded(rs1=f"{DIM} * %i + 0", rs2=iterations * DIM)
            api.end_loop()
        elif (df == 1):
            api.matmul_preload(rs1=DIM * (iterations), rs2=DIM * (2 * iterations + 1))
            api.matmul8_compute_preloaded(rs1=0, rs2=(iterations + 1) * DIM)
            api.start_loop("i", 1, iterations)
            api.matmul_preload(rs1=0, rs2=f"{DIM} * %i + {DIM * (2 * iterations + 1)}")
            api.matmul8_compute_accumulated(
                rs1=f"{DIM} * %i + {0}",
                rs2=f"{DIM} * %i + {(iterations + 1) * DIM}")
            api.end_loop()
        api.start_loop("k", 0, iterations)
        api.mvout_spad(
            stride=DIM,
            hbm_addr=f"{DIM * DIM} * %k + {(iterations * 2 + 1) * DIM * DIM}",
            sp_addr=f"{DIM} * %k + {(iterations * 2 + 1) * DIM}",
            rows=DIM)
        api.end_loop()

    if (xla_while):
        return tiled_matmul_api_loop, hbm_size

    return tiled_matmul_with_for, hbm_size
