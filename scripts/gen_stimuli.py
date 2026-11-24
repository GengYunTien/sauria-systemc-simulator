#!/usr/bin/env python3
"""
gen_stimuli.py — Generate SAURIA RTL stimuli and invoke Test-Sim.

Usage (run from inside the Docker container):
  cd /workspace/sauria-systemc-simulator
  python3 scripts/gen_stimuli.py [options]

Wraps sauria_lib.generate_and_run_test(), which:
  1. Creates random FP16 tensors from tensor_shapes
  2. Calls Conv2d_SAURIA() → writes 4 stimuli files
  3. Runs Test-Sim (Test-Sim binary in test/verilator/)

Options:
  --Ci, --Co   input / output channels       (default: 1)
  --Kx, --Ky   kernel width / height         (default: 1)
  --Ox, --Oy   output feature-map w / h      (default: 8)
  --stride     stride (x=y)                  (default: 1)
  --pad        zero-padding (x=y)            (default: 0)
  --hw         hardware version              (default: FP16_8x16)
  --vcd        generate VCD trace
"""

import sys, os, argparse

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
SAURIA_ROOT = os.path.join(REPO_ROOT, "3rdparty", "sauria")
SAURIA_PY_SRC = os.path.join(SAURIA_ROOT, "Python", "src")

sys.path.insert(0, SAURIA_PY_SRC)
sys.path.insert(0, os.path.join(SAURIA_ROOT, "Python"))

try:
    import hw_versions as hw
    import sauria_lib  as sl
except ImportError as e:
    sys.exit(f"[ERROR] Import failed: {e}\n"
             "Run inside the Docker container with deps installed.")

# CLI
def parse_args():
    p = argparse.ArgumentParser(
        description="Generate SAURIA RTL stimuli + run Test-Sim",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--Ci", type=int, default=1,  help="Input channels")
    p.add_argument("--Co", type=int, default=1,  help="Output channels")
    p.add_argument("--Kx", type=int, default=1,  help="Kernel width")
    p.add_argument("--Ky", type=int, default=1,  help="Kernel height")
    p.add_argument("--Ox", type=int, default=8,  help="Output feature-map width")
    p.add_argument("--Oy", type=int, default=8,  help="Output feature-map height")
    p.add_argument("--stride", type=int, default=1)
    p.add_argument("--pad", type=int, default=0)
    p.add_argument("--hw", type=str, default="FP16_8x16", choices=["FP16_8x16", "int8_8x16", "int8_32x32"])
    p.add_argument("--vcd", action="store_true", help="Dump VCD from Test-Sim")
    return p.parse_args()

# Main
def main():
    args = parse_args()
    s = args.stride
    p = args.pad
    d = 1  # dilation (extend with --dil later if needed)

    # Derived input spatial dims: Ix = Ox*s + Kx - 1 - 2p
    Ix = args.Ox * s + args.Kx - 1 - 2 * p
    Iy = args.Oy * s + args.Ky - 1 - 2 * p
    if Ix <= 0 or Iy <= 0:
        sys.exit(f"[ERROR] Input size Ix={Ix}, Iy={Iy} ≤ 0 — check Kx/Ky vs Ox/Oy/stride/pad.")

    # HOPTS
    HOPTS = hw.get_params(args.hw)
    X = HOPTS['X']   # 16 (SA output-channel columns)
    Y = HOPTS['Y']   # 8 (SA input-channel rows)

    # tensor_shapes = [A_shape, B_shape, C_shape]
    # A : [Ci, Iy, Ix] — input feature map
    # B : [Co, Ci, Ky, Kx] — weights
    # C : [Co, Oy, Ox] — output
    A_shape = (args.Ci, Iy, Ix)
    B_shape = (args.Co, args.Ci, args.Ky, args.Kx)
    C_shape = (args.Co, args.Oy, args.Ox)
    tensor_shapes = [A_shape, B_shape, C_shape]

    # TILING_DICT
    # C_tile_shape = [Co_tile, Oy_tile, Ox_tile]
    # tile_cin = Ci tile size
    # X_used = SA output-channel columns used (must equal X for full utilisation)
    # Y_used = SA input-channel rows used (must equal Y for full utilisation)
    if args.Co % X != 0:
        sys.exit(f"[ERROR] Co={args.Co} must be a multiple of X_used={X} (minimum Co={X})")
    if args.Ci % Y != 0:
        sys.exit(f"[ERROR] Ci={args.Ci} must be a multiple of Y_used={Y} (minimum Ci={Y})")
    if args.Ox % Y != 0:
        sys.exit(f"[ERROR] Ox={args.Ox} must be a multiple of Y_used={Y} (minimum Ox={Y})")

    TILING_DICT = {
        'C_tile_shape': [args.Co, args.Oy, args.Ox],
        'tile_cin': args.Ci,
        'X_used': X,
        'Y_used': Y,
    }

    print(f"[gen_stimuli] HW={args.hw}  X={X}  Y={Y}")
    print(f"[gen_stimuli] Ci={args.Ci}  Co={args.Co}  "
          f"K={args.Ky}x{args.Kx}  In={Iy}x{Ix}  Out={args.Oy}x{args.Ox}  "
          f"stride={s}  pad={p}  dil={d}")
    print(f"[gen_stimuli] TILING_DICT = {TILING_DICT}")
    print(f"[gen_stimuli] tensor_shapes: A{list(A_shape)} B{list(B_shape)} C{list(C_shape)}")

    # sauria_lib.generate_and_run_test() calls os.chdir("../../test/verilator")
    # internally, so CWD must be Python/src when we call it.
    orig_dir = os.getcwd()
    os.chdir(SAURIA_PY_SRC)
    print(f"[gen_stimuli] CWD → {SAURIA_PY_SRC}")

    try:
        outputs, stats, _ = sl.generate_and_run_test(
            tensor_shapes,
            TILING_DICT,
            d, s,
            HOPTS,
            preload = True,
            generate_vcd = args.vcd,
            print_statistics = True,
            silent = False,
        )
    finally:
        os.chdir(orig_dir)

    # Report stimuli files
    stim_dir = os.path.join(SAURIA_ROOT, "test", "stimuli")
    print(f"\n[gen_stimuli] Stimuli written to: {stim_dir}")
    for fname in ["initial_dram.txt", "gold_dram.txt", "tstcfg.txt", "GoldenStimuli.txt"]:
        fpath = os.path.join(stim_dir, fname)
        if os.path.isfile(fpath):
            lines = sum(1 for _ in open(fpath))
            kb = os.path.getsize(fpath) // 1024
            print(f"{fname:25s} {lines:6d} lines {kb:4d} KB")
        else:
            print(f" {fname:25s} *** NOT FOUND ***")

    if args.vcd:
        vcd_path = os.path.join(SAURIA_ROOT, "test", "verilator", "new.vcd")
        if os.path.isfile(vcd_path):
            kb = os.path.getsize(vcd_path) // 1024
            print(f"\n[gen_stimuli] VCD trace: {vcd_path} ({kb} KB)")
        else:
            print(f"\n[gen_stimuli] VCD not found — check verilator_run.log")

if __name__ == "__main__":
    main()