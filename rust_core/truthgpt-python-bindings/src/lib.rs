//! # TruthGPT Rust Core
//!
//! High-performance Rust backend for TruthGPT optimization core.
//!
//! ## Features
//!
//! - **KV Cache**: Ultra-efficient key-value caching with LRU/LFU/Adaptive eviction
//! - **Compression**: LZ4 (~5GB/s) and Zstd for tensor/cache compression
//! - **Attention**: Optimized attention implementations (standard, flash, sparse)
//! - **Tokenization**: Fast parallel tokenization via HuggingFace tokenizers
//! - **Data Loading**: Multi-threaded data loading with prefetching

pub mod bindings;

pub use truthgpt_core::error::{TruthGPTError, Result};
pub use truthgpt_core::utils::{
    Timer, AtomicCounter, Histogram, HistogramStats, MemoryStats,
    AlignedVec, RingBuffer, ExponentialMovingAverage,
    f32_to_bytes, bytes_to_f32, f16_to_f32_bytes, f32_to_f16_bytes,
    format_bytes, format_duration, measure, measure_us, memory_usage
};

pub use truthgpt_models::attention::{
    scaled_dot_product_attention, scaled_dot_product_attention_causal,
    flash_attention_block, flash_attention_causal, sparse_attention, sliding_window_attention,
    create_causal_mask, create_padding_mask, softmax_1d, batch_matmul, batch_matmul_transpose,
    AttentionConfig, AttentionStats
};
pub use truthgpt_models::paged_attention::{BlockManager, PagedAttentionMetadata, BlockManagerStats, BlockTable, BLOCK_SIZE};
pub use truthgpt_models::rope::{RoPE, RoPEConfig, RoPEScaling, ALiBi, YaRN};

pub use truthgpt_inference::batch_inference::{InferenceRequest, InferenceResponse, BatchScheduler, BatchConfig, Priority, FinishReason, ContinuousBatcher, SchedulerStats};
pub use truthgpt_inference::speculative::{SpeculativeDecoder, SpeculativeConfig, DraftResult, VerificationResult, SpeculativeStats, TreeSpeculation, kl_divergence};

pub use truthgpt_cache::kv_cache::{KVCache, KVCacheConfig, EvictionStrategy, ConcurrentKVCache};

pub use truthgpt_data::data_loader::{JsonlDataLoader, DataLoaderConfig, DataSample, BatchIterator, LengthBucketer};
pub use truthgpt_data::json_processor::{JsonProcessor, fast_parse, fast_stringify};
pub use truthgpt_data::tokenizer_wrapper::{FastTokenizer, TokenizationResult, TokenizationConfig, BatchTokenizer};

pub use truthgpt_optimization::compression::{Compressor, CompressionAlgorithm, CompressionStats, StreamingCompressor, BatchCompressor, compress, decompress, compress_with_stats, compress_zstd_level};
pub use truthgpt_optimization::quantization::{
    QuantizationType, QuantizationParams, QuantizedTensor,
    quantize_int8, dequantize_int8, quantize_int4, dequantize_int4,
    quantize_fp16, dequantize_fp16, quantize_bf16, dequantize_bf16,
    quantize_grouped_int8, dequantize_grouped_int8, matmul_int8, matmul_fp16
};
pub use truthgpt_optimization::hyperparameter_optimizer::{
    HyperparameterOptimizer, SearchStrategy, HyperparameterRange, HyperparameterConfig,
    TrialResult
};

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_compression_roundtrip() {
        let data = b"Hello, World! This is a test of the compression system.".to_vec();
        let compressed = compress(&data, &CompressionAlgorithm::LZ4).unwrap();
        let decompressed = decompress(&compressed, &CompressionAlgorithm::LZ4).unwrap();
        assert_eq!(data, decompressed);
    }
    
    #[test]
    fn test_kv_cache() {
        let config = KVCacheConfig::default();
        let mut cache = KVCache::new(config);
        
        cache.put(0, 0, vec![1, 2, 3, 4]);
        let result = cache.get(0, 0);
        
        assert!(result.is_some());
        assert_eq!(result.unwrap(), &[1, 2, 3, 4]);
    }
    
    #[test]
    fn test_error_types() {
        let err = TruthGPTError::cache("test error");
        assert!(err.to_string().contains("Cache error"));
    }
}
