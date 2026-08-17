//! Trait Abstractions for TruthGPT Rust Core
//!
//! Generic trait boundaries that enable polymorphism across cache backends,
//! compression algorithms, and quantization strategies.

use crate::error::Result;
use std::collections::HashMap;
use std::fmt::Debug;

// ═══════════════════════════════════════════════════════════════════════════════
// CACHE TRAIT
// ═══════════════════════════════════════════════════════════════════════════════

/// A generic key-value cache.
///
/// Implementors provide their own eviction strategy, optional compression,
/// and thread-safety guarantees.
///
/// # Type Parameters
/// - `K` — Cache key type (must be hashable and cloneable).
/// - `V` — Cache value type.
pub trait Cache<K, V>: Send + Sync
where
    K: Eq + std::hash::Hash + Clone + Debug,
    V: Clone + Debug,
{
    /// Retrieve a reference or clone of the cached value, if present.
    fn get(&self, key: &K) -> Option<V>;

    /// Insert or update a value in the cache.
    fn put(&self, key: K, value: V);

    /// Remove a specific key from the cache.
    fn remove(&self, key: &K) -> Option<V>;

    /// Remove all entries.
    fn clear(&self);

    /// Current number of entries.
    fn len(&self) -> usize;

    /// Whether the cache is empty.
    fn is_empty(&self) -> bool {
        self.len() == 0
    }

    /// Return implementation-specific statistics as a string-keyed map.
    fn stats(&self) -> HashMap<String, f64>;
}

// ═══════════════════════════════════════════════════════════════════════════════
// COMPRESSION TRAIT
// ═══════════════════════════════════════════════════════════════════════════════

/// Compression / decompression contract.
///
/// Implementors wrap a specific algorithm (LZ4, Zstd, etc.) and expose a
/// uniform API.
pub trait Compress: Send + Sync {
    /// Compress raw bytes and return the compressed output.
    fn compress(&self, data: &[u8]) -> Result<Vec<u8>>;

    /// Decompress previously-compressed bytes.
    fn decompress(&self, data: &[u8]) -> Result<Vec<u8>>;

    /// Human-readable name for the algorithm (e.g. `"lz4"`, `"zstd"`).
    fn algorithm_name(&self) -> &'static str;
}

// ═══════════════════════════════════════════════════════════════════════════════
// QUANTIZATION TRAIT
// ═══════════════════════════════════════════════════════════════════════════════

/// Quantization / dequantization contract.
///
/// Implementors convert floating-point tensors into lower-precision
/// representations and back.
pub trait Quantize: Send + Sync {
    /// The quantized representation type (e.g. `Vec<i8>`, `Vec<u8>`).
    type Quantized;

    /// Quantize an f32 slice into the lower-precision format.
    fn quantize(&self, data: &[f32]) -> Self::Quantized;

    /// Dequantize back to f32.
    fn dequantize(&self, data: &Self::Quantized) -> Vec<f32>;

    /// Memory reduction factor compared to FP32 (e.g. `4.0` for INT8).
    fn compression_ratio(&self) -> f32;
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_compress_trait_object_safety() {
        fn _accepts_boxed(_c: Box<dyn Compress>) {}
    }

    #[test]
    fn test_cache_trait_compiles() {
        fn _accepts_cache(_c: &dyn Cache<String, Vec<u8>>) {}
    }
}
