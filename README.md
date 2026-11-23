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

### Prerequisites
- Docker

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

## Validation Methodology

The SystemC model is validated cycle-by-cycle against Verilator-generated C++
simulation of the SAURIA RTL. VCD waveforms from both simulations are compared
to verify cycle-accurate behavioral equivalence.

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