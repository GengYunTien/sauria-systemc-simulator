// include/types.h
#pragma once

#include <cstdint>
#include <cmath>

//  Data type
//  Phase 1-3  : float  (focus on timing / data-flow)
//  Phase 4+   : swap to bit-exact fp16
//               #include "half.hpp"
//               using fp16_t = half_float::half;
using fp16_t = float;

//  Hardware parameters  (FP16_8x16)
static constexpr int SA_X = 16;   // systolic array columns (output-channel lanes)
static constexpr int SA_Y = 8;    // systolic array rows (spatial lanes)

static constexpr int IA_W = 16;   // activation  bit-width
static constexpr int IB_W = 16;   // weight      bit-width
static constexpr int OC_W = 16;   // accumulator bit-width

//  Golden comparison tolerance
//  float(32-bit) vs RTL fp16 will differ in LSBs
static constexpr float CMP_EPS = 1e-3f;