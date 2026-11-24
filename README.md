# sauria-systemc-simulator

Cycle-accurate SystemC model of the [SAURIA](https://github.com/bsc-loca/sauria)
systolic-array convolution accelerator, validated against Verilator RTL simulation.

## Overview

SAURIA is an output-stationary systolic array accelerator with on-the-fly im2col,
published at IEEE TVLSI 2023. This project builds a cycle-accurate behavioral model
in SystemC C++17, using Verilator-generated RTL simulation as the validation ground truth.

## Architecture

```
Data Feeder ──┐
              ├──→ Systolic Array ──→ PSM (Partial Sums Manager)
Weight Feeder ┘
        ↑
  Main Controller
```

| Module | Description |
|--------|-------------|
| Data Feeder | On-the-fly im2col; 5-counter Global Index, per-lane Feed Lanes, stall logic |
| Weight Feeder | 3-counter address generation, no stall |
| Systolic Array | Output-stationary PE mesh; 1-bit zero-overhead context switch |
| PSM | 3-phase partial sum management with Scan FSM |
| Main Controller | 3 FSMs: Feeders FSM + Context FSM + Stalls FSM |

## Implementation Status

| Module | SystemC model | Verilator validation |
|--------|:---:|:---:|
| Data Feeder | 🚧 | ⬜ |
| Weight Feeder | 🚧 | ⬜ |
| Systolic Array | 🚧 | ⬜ |
| PSM | 🚧 | ⬜ |
| Main Controller | 🚧 | ⬜ |

## Getting Started

### Clone

```bash
git clone --recurse-submodules https://github.com/GengYunTien/sauria-systemc-simulator.git
cd sauria-systemc-simulator
```

### Build dev environment

```bash
make docker-build
```

### Enter dev environment

```bash
make dev
```

### Build RTL Test-Sim (once, inside container)

```bash
make test-sim-build
```

Verify: `ls -lh 3rdparty/sauria/test/verilator/Test-Sim`

### Generate RTL stimuli & validate

```bash
python3 scripts/gen_stimuli.py --Ci 32 --Co 32 --Kx 3 --Ky 3 --Ox 16 --Oy 16
# add --vcd to also capture a waveform trace
```

## Validation Methodology

The SystemC model is validated cycle-by-cycle against Verilator-generated C++
simulation of the SAURIA RTL. VCD waveforms from both simulations are compared
to verify cycle-accurate behavioral equivalence.

### RTL Ground Truth — Benchmark Results

Hardware configuration: `FP16_8x16`, Systolic Array X=16 (output-channel columns) × Y=8 (input-channel rows).

The following four workloads were run against the Verilator RTL to establish ground-truth
cycle counts and stall profiles that the SystemC model must match.

| Test | Conv params | Total ops | Total cycles | SA utilization | Core stall | Mem/CGF stall |
|------|-------------|----------:|-------------:|---------------:|-----------:|--------------:|
| T1 | Ci=8, Co=16, K=1×1, Out=4×8 | 8,192 | 899 | 3.56% | 52.17% | 43.27% |
| T2 | Ci=8, Co=16, K=3×3, Out=8×8 | 147,456 | 1,600 | 36.00% | 25.12% | 38.56% |
| T3 | Ci=16, Co=16, K=3×3, Out=16×16 | 1,179,648 | 6,199 | 74.33% | 2.19% | 23.39% |
| T4 | Ci=32, Co=32, K=3×3, Out=16×16 | 4,718,592 | 21,423 | 86.04% | 0.63% | 13.30% |

SA peak throughput = X × Y × 2 = 256 OP/cycle.

**Key findings from the RTL ground truth:**

- **Pipeline bubble is a fixed constant.** T3 and T4 both show exactly 136 core-stall
  cycles regardless of workload size. This is the irreducible bubble from SA pipeline
  fill and PSM shift-chain drain — a hard anchor the SystemC model must reproduce.

- **AXI4-Lite config overhead is workload-independent.** `GoldenStimuli.txt` is 120
  lines across all four tests. The Main Controller's register-write sequence for
  Data Feeder, Weight Feeder and PSM is fixed regardless of conv shape, so this
  overhead dominates utilization on small workloads (T1: 3.56%).

- **Bottleneck shifts from Core stall to Memory stall as workload grows.** At T4
  the SA runs at 86% utilization; the remaining 13.3% Memory stall reflects the
  AXI-4 bandwidth limit of ReDMA, not pipeline inefficiency.

- **Increasing Ci/Co beyond the CBUF capacity (32 KB each) triggers tiling
  (tiles > 1)** and introduces a qualitatively different cycle pattern. The four
  benchmarks above are all single-tile (tiles = 1); multi-tile behavior is a
  separate validation target.

**Recommended validation order:** Start with T4 (Core stall ≈ 0, SA throughput
dominates), then T3 (confirms the 136-cycle pipeline bubble), then T2 and T1
(test overhead modeling: ReDMA setup and AXI4-Lite config cycles).

## Known RTL Issues

The following open issues in the upstream SAURIA repository affect specific edge cases.

- [#6](https://github.com/bsc-loca/sauria/issues/6) — Lost activation final-push
  on short, no-preload feeds
- [#7](https://github.com/bsc-loca/sauria/issues/7) — Stale weights at K-sub-tile
  boundary (counter advances one stage late)

Initial test cases are scoped to avoid these edge cases.

## References

- SAURIA RTL: https://github.com/bsc-loca/sauria (Solderpad Hardware License v2.1)
- Y. Hern et al., "An Energy-Efficient GeMM-Based Convolution Accelerator With
  On-the-Fly im2col," *IEEE TVLSI*, 2023. DOI: 10.1109/TVLSI.2023.3286122

## License

Apache License 2.0.
SAURIA RTL is included as a git submodule under its original
[Solderpad Hardware License v2.1](https://github.com/bsc-loca/sauria/blob/main/LICENSE).