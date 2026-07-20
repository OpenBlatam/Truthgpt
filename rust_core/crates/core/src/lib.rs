//! # TruthGPT Core — Foundation Crate
//!
//! This crate provides the foundational abstractions and utilities used across
//! all other crates in the `truthgpt-rust` workspace. It is intentionally
//! dependency-light, providing only:
//!
//! - **Error types** — A unified `TruthGPTError` enum and `Result<T>` alias.
//! - **Trait abstractions** — Generic `Cache`, `Compressor`, and `Quantizer` traits
//!   that downstream crates implement.
//! - **Utilities** — Performance measurement, atomic counters, histograms,
//!   ring buffers, data conversion, and formatting helpers.
//!
//! ## Design Philosophy
//!
//! All concrete implementations live in their own crates (`truthgpt-cache`,
//! `truthgpt-optimization`, etc.) and depend on `truthgpt-core` for shared types.
//! This prevents circular dependencies and keeps compile times fast.

pub mod error;
pub mod traits;
pub mod utils;

// ═══════════════════════════════════════════════════════════════════════════════
// RE-EXPORTS — Convenience access from `truthgpt_core::{...}`
// ═══════════════════════════════════════════════════════════════════════════════

pub use error::{TruthGPTError, Result};
pub use traits::{Cache, Compress, Quantize};
pub use utils::{
    Timer, AtomicCounter, Histogram, HistogramStats, MemoryStats,
    AlignedVec, RingBuffer, ExponentialMovingAverage,
    f32_to_bytes, bytes_to_f32, f16_to_f32_bytes, f32_to_f16_bytes,
    format_bytes, format_duration, measure, measure_us, memory_usage,
};
