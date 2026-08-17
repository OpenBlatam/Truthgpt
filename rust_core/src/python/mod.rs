//! Python bindings via PyO3 for TruthGPT Rust Core

use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use ndarray::Array3;
use parking_lot::RwLock;
use std::collections::HashMap;
use std::sync::Arc;

use crate::{
    attention::{self, AttentionConfig},
    compression::{self, CompressionAlgorithm},
    data_loader,
    kv_cache::{self, EvictionStrategy, KVCacheConfig},
    quantization::{self, QuantizationParams},
    tokenizer_wrapper,
};

// ═══════════════════════════════════════════════════════════════════════════════
// PYTHON MODULE DEFINITION
// ═══════════════════════════════════════════════════════════════════════════════

/// TruthGPT Rust Core - Python Module
#[pymodule]
pub fn truthgpt_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    // Register classes
    m.add_class::<PyKVCache>()?;
    m.add_class::<PyCompressor>()?;
    m.add_class::<PyFastTokenizer>()?;
    m.add_class::<PyDataLoader>()?;
    
    // Register functions
    m.add_function(wrap_pyfunction!(fast_lz4_compress, m)?)?;
    m.add_function(wrap_pyfunction!(fast_lz4_decompress, m)?)?;
    m.add_function(wrap_pyfunction!(fast_zstd_compress, m)?)?;
    m.add_function(wrap_pyfunction!(fast_zstd_decompress, m)?)?;
    m.add_function(wrap_pyfunction!(parallel_tokenize, m)?)?;
    m.add_function(wrap_pyfunction!(flash_attention_block_py, m)?)?;
    m.add_function(wrap_pyfunction!(quantize_int8_py, m)?)?;
    m.add_function(wrap_pyfunction!(dequantize_int8_py, m)?)?;
    m.add_function(wrap_pyfunction!(fast_json_parse, m)?)?;
    m.add_function(wrap_pyfunction!(fast_json_stringify, m)?)?;
    m.add_function(wrap_pyfunction!(get_version, m)?)?;
    m.add_function(wrap_pyfunction!(get_system_info, m)?)?;
    
    // Module metadata
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add("__author__", "TruthGPT Team")?;
    m.add("RUST_AVAILABLE", true)?;
    
    Ok(())
}

// ═══════════════════════════════════════════════════════════════════════════════
// MODULE INFO FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════════

/// Get version information
#[pyfunction]
pub fn get_version() -> String {
    format!("truthgpt-rust v{}", env!("CARGO_PKG_VERSION"))
}

/// Get system information
#[pyfunction]
pub fn get_system_info() -> HashMap<String, String> {
    HashMap::from([
        ("version".to_string(), env!("CARGO_PKG_VERSION").to_string()),
        ("cpu_count".to_string(), num_cpus::get().to_string()),
        ("rayon_threads".to_string(), rayon::current_num_threads().to_string()),
        #[cfg(feature = "cuda")]
        ("cuda_available".to_string(), "true".to_string()),
        #[cfg(not(feature = "cuda"))]
        ("cuda_available".to_string(), "false".to_string()),
        #[cfg(feature = "metal")]
        ("metal_available".to_string(), "true".to_string()),
        #[cfg(not(feature = "metal"))]
        ("metal_available".to_string(), "false".to_string()),
    ])
}

// ═══════════════════════════════════════════════════════════════════════════════
// KV CACHE PYTHON WRAPPER
// ═══════════════════════════════════════════════════════════════════════════════

/// Python-exposed KV Cache with ultra-fast operations and GIL release
#[pyclass]
pub struct PyKVCache {
    inner: Arc<RwLock<kv_cache::KVCache>>,
}

#[pymethods]
impl PyKVCache {
    /// Create a new KV Cache
    #[new]
    #[pyo3(signature = (max_size=8192, eviction_strategy="lru", enable_compression=true, compression_threshold=1024))]
    fn new(
        max_size: usize,
        eviction_strategy: &str,
        enable_compression: bool,
        compression_threshold: usize,
    ) -> PyResult<Self> {
        let strategy = match eviction_strategy {
            "lru" => EvictionStrategy::LRU,
            "lfu" => EvictionStrategy::LFU,
            "fifo" => EvictionStrategy::FIFO,
            "adaptive" => EvictionStrategy::Adaptive,
            _ => EvictionStrategy::LRU,
        };
        
        let config = KVCacheConfig {
            max_size,
            eviction_strategy: strategy,
            enable_compression,
            compression_threshold,
        };
        
        Ok(Self {
            inner: Arc::new(RwLock::new(kv_cache::KVCache::new(config))),
        })
    }
    
    /// Get cached value by layer index and position
    fn get<'py>(&self, py: Python<'py>, layer_idx: usize, position: usize) -> Option<&'py pyo3::types::PyBytes> {
        let inner = Arc::clone(&self.inner);
        let data = py.allow_threads(move || {
            let cache = inner.read();
            cache.get(layer_idx, position).map(|v| v.to_vec())
        })?;
        
        Some(pyo3::types::PyBytes::new(py, &data))
    }
    
    /// Put value in cache (accepts byte slice)
    fn put(&self, py: Python, layer_idx: usize, position: usize, data: &[u8]) {
        let inner = Arc::clone(&self.inner);
        let data_vec = data.to_vec();
        py.allow_threads(move || {
            let mut cache = inner.write();
            cache.put(layer_idx, position, data_vec);
        });
    }
    
    /// Check if key exists
    fn contains(&self, py: Python, layer_idx: usize, position: usize) -> bool {
        let inner = Arc::clone(&self.inner);
        py.allow_threads(move || {
            let cache = inner.read();
            cache.get(layer_idx, position).is_some()
        })
    }
    
    /// Clear all cached data
    fn clear(&self, py: Python) {
        let inner = Arc::clone(&self.inner);
        py.allow_threads(move || {
            let mut cache = inner.write();
            cache.clear();
        });
    }
    
    /// Get cache statistics
    fn stats(&self, py: Python) -> HashMap<String, f64> {
        let inner = Arc::clone(&self.inner);
        py.allow_threads(move || {
            let cache = inner.read();
            cache.get_stats()
        })
    }
    
    /// Get current cache size
    fn size(&self, py: Python) -> usize {
        let inner = Arc::clone(&self.inner);
        py.allow_threads(move || {
            let cache = inner.read();
            cache.size()
        })
    }
    
    /// Get maximum cache size
    fn max_size(&self, py: Python) -> usize {
        let inner = Arc::clone(&self.inner);
        py.allow_threads(move || {
            let cache = inner.read();
            cache.max_size()
        })
    }
    
    fn __repr__(&self) -> String {
        let cache = self.inner.read();
        format!("PyKVCache(size={}/{})", cache.size(), cache.max_size())
    }
    
    fn __len__(&self, py: Python) -> usize {
        self.size(py)
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// COMPRESSION PYTHON WRAPPER
// ═══════════════════════════════════════════════════════════════════════════════

/// Python-exposed compressor with LZ4 and Zstd support & non-blocking GIL release
#[pyclass]
pub struct PyCompressor {
    algorithm: CompressionAlgorithm,
    level: i32,
}

#[pymethods]
impl PyCompressor {
    /// Create a new compressor
    #[new]
    #[pyo3(signature = (algorithm="lz4", level=3))]
    fn new(algorithm: &str, level: i32) -> PyResult<Self> {
        let algo = match algorithm {
            "lz4" => CompressionAlgorithm::LZ4,
            "zstd" => CompressionAlgorithm::Zstd,
            "none" => CompressionAlgorithm::None,
            _ => CompressionAlgorithm::LZ4,
        };
        Ok(Self { algorithm: algo, level })
    }
    
    /// Compress data (accepts byte slice)
    fn compress<'py>(&self, py: Python<'py>, data: &[u8]) -> PyResult<&'py pyo3::types::PyBytes> {
        let algo = self.algorithm;
        let data_vec = data.to_vec();
        let compressed = py.allow_threads(move || {
            compression::compress(&data_vec, &algo)
        }).map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        
        Ok(pyo3::types::PyBytes::new(py, &compressed))
    }
    
    /// Decompress data (accepts byte slice)
    fn decompress<'py>(&self, py: Python<'py>, data: &[u8]) -> PyResult<&'py pyo3::types::PyBytes> {
        let algo = self.algorithm;
        let data_vec = data.to_vec();
        let decompressed = py.allow_threads(move || {
            compression::decompress(&data_vec, &algo)
        }).map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        
        Ok(pyo3::types::PyBytes::new(py, &decompressed))
    }
    
    /// Compress with statistics
    fn compress_with_stats<'py>(&self, py: Python<'py>, data: &[u8]) -> PyResult<(&'py pyo3::types::PyBytes, HashMap<String, f64>)> {
        let algo = self.algorithm;
        let data_vec = data.to_vec();
        let (compressed, stats) = py.allow_threads(move || {
            compression::compress_with_stats(&data_vec, &algo)
        }).map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        
        let stats_map = HashMap::from([
            ("original_size".to_string(), stats.original_size as f64),
            ("compressed_size".to_string(), stats.compressed_size as f64),
            ("ratio".to_string(), stats.compression_ratio()),
            ("savings".to_string(), stats.space_savings()),
            ("time_us".to_string(), stats.compression_time_us as f64),
        ]);
        
        let bytes = pyo3::types::PyBytes::new(py, &compressed);
        Ok((bytes, stats_map))
    }
    
    fn __repr__(&self) -> String {
        format!("PyCompressor(algorithm={:?}, level={})", self.algorithm, self.level)
    }
}

/// Fast LZ4 compression (standalone function)
#[pyfunction]
pub fn fast_lz4_compress<'py>(py: Python<'py>, data: &[u8]) -> PyResult<&'py pyo3::types::PyBytes> {
    let data_vec = data.to_vec();
    let compressed = py.allow_threads(move || {
        compression::compress(&data_vec, &CompressionAlgorithm::LZ4)
    }).map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    Ok(pyo3::types::PyBytes::new(py, &compressed))
}

/// Fast LZ4 decompression (standalone function)
#[pyfunction]
pub fn fast_lz4_decompress<'py>(py: Python<'py>, data: &[u8]) -> PyResult<&'py pyo3::types::PyBytes> {
    let data_vec = data.to_vec();
    let decompressed = py.allow_threads(move || {
        compression::decompress(&data_vec, &CompressionAlgorithm::LZ4)
    }).map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    Ok(pyo3::types::PyBytes::new(py, &decompressed))
}

/// Fast Zstd compression (standalone function)
#[pyfunction]
#[pyo3(signature = (data, level=3))]
pub fn fast_zstd_compress<'py>(py: Python<'py>, data: &[u8], level: i32) -> PyResult<&'py pyo3::types::PyBytes> {
    let data_vec = data.to_vec();
    let compressed = py.allow_threads(move || {
        compression::compress_zstd_level(&data_vec, level)
    }).map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    Ok(pyo3::types::PyBytes::new(py, &compressed))
}

/// Fast Zstd decompression (standalone function)
#[pyfunction]
pub fn fast_zstd_decompress<'py>(py: Python<'py>, data: &[u8]) -> PyResult<&'py pyo3::types::PyBytes> {
    let data_vec = data.to_vec();
    let decompressed = py.allow_threads(move || {
        compression::decompress(&data_vec, &CompressionAlgorithm::Zstd)
    }).map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    Ok(pyo3::types::PyBytes::new(py, &decompressed))
}

// ═══════════════════════════════════════════════════════════════════════════════
// TOKENIZATION PYTHON WRAPPER
// ═══════════════════════════════════════════════════════════════════════════════

/// Python-exposed fast tokenizer wrapper with non-blocking GIL release
#[pyclass]
pub struct PyFastTokenizer {
    inner: tokenizer_wrapper::FastTokenizer,
}

#[pymethods]
impl PyFastTokenizer {
    /// Create a tokenizer from a file
    #[new]
    fn new(tokenizer_path: &str) -> PyResult<Self> {
        let inner = tokenizer_wrapper::FastTokenizer::from_file(tokenizer_path)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        Ok(Self { inner })
    }
    
    /// Create from pretrained model
    #[staticmethod]
    fn from_pretrained(identifier: &str) -> PyResult<Self> {
        let inner = tokenizer_wrapper::FastTokenizer::from_pretrained(identifier)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        Ok(Self { inner })
    }
    
    /// Encode text to tokens
    #[pyo3(signature = (text, add_special_tokens=true))]
    fn encode(&self, py: Python, text: &str, add_special_tokens: bool) -> PyResult<Vec<u32>> {
        let inner = self.inner.clone();
        let text_str = text.to_string();
        py.allow_threads(move || {
            inner.encode(&text_str, add_special_tokens)
        }).map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }
    
    /// Decode tokens to text
    #[pyo3(signature = (tokens, skip_special_tokens=true))]
    fn decode(&self, py: Python, tokens: Vec<u32>, skip_special_tokens: bool) -> PyResult<String> {
        let inner = self.inner.clone();
        py.allow_threads(move || {
            inner.decode(&tokens, skip_special_tokens)
        }).map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }
    
    /// Batch encode multiple texts (parallel, GIL released)
    #[pyo3(signature = (texts, add_special_tokens=true))]
    fn encode_batch(&self, py: Python, texts: Vec<String>, add_special_tokens: bool) -> PyResult<Vec<Vec<u32>>> {
        let inner = self.inner.clone();
        py.allow_threads(move || {
            inner.encode_batch(&texts, add_special_tokens)
        }).map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }
    
    /// Batch decode (parallel, GIL released)
    #[pyo3(signature = (token_batches, skip_special_tokens=true))]
    fn decode_batch(&self, py: Python, token_batches: Vec<Vec<u32>>, skip_special_tokens: bool) -> PyResult<Vec<String>> {
        let inner = self.inner.clone();
        py.allow_threads(move || {
            inner.decode_batch(&token_batches, skip_special_tokens)
        }).map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }
    
    /// Get vocabulary size
    fn vocab_size(&self) -> usize {
        self.inner.vocab_size()
    }
    
    /// Get token ID
    fn token_to_id(&self, token: &str) -> Option<u32> {
        self.inner.token_to_id(token)
    }
    
    /// Get token string
    fn id_to_token(&self, id: u32) -> Option<String> {
        self.inner.id_to_token(id)
    }
    
    fn __repr__(&self) -> String {
        format!("PyFastTokenizer(vocab_size={})", self.vocab_size())
    }
}

/// Parallel tokenization (standalone function)
#[pyfunction]
#[pyo3(signature = (tokenizer_path, texts, add_special_tokens=true))]
pub fn parallel_tokenize(
    py: Python,
    tokenizer_path: &str,
    texts: Vec<String>,
    add_special_tokens: bool,
) -> PyResult<Vec<Vec<u32>>> {
    let path = tokenizer_path.to_string();
    py.allow_threads(move || {
        let tokenizer = tokenizer_wrapper::FastTokenizer::from_file(&path)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        tokenizer.encode_batch(&texts, add_special_tokens)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    })
}

// ═══════════════════════════════════════════════════════════════════════════════
// ATTENTION & QUANTIZATION PYTHON WRAPPERS
// ═══════════════════════════════════════════════════════════════════════════════

/// Fast Flash Attention block calculation for Python
#[pyfunction(name = "flash_attention_block")]
#[pyo3(signature = (q, k, v, batch_size, num_heads, seq_len, head_dim, causal=true))]
pub fn flash_attention_block_py(
    py: Python,
    q: Vec<f32>,
    k: Vec<f32>,
    v: Vec<f32>,
    batch_size: usize,
    num_heads: usize,
    seq_len: usize,
    head_dim: usize,
    causal: bool,
) -> PyResult<Vec<f32>> {
    py.allow_threads(move || {
        let total_elements = batch_size * num_heads * seq_len * head_dim;
        if q.len() < total_elements || k.len() < total_elements || v.len() < total_elements {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "Input buffer sizes ({}, {}, {}) smaller than expected total_elements ({})",
                q.len(), k.len(), v.len(), total_elements
            )));
        }

        let q_arr = Array3::from_shape_vec((batch_size * num_heads, seq_len, head_dim), q[..total_elements].to_vec())
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        let k_arr = Array3::from_shape_vec((batch_size * num_heads, seq_len, head_dim), k[..total_elements].to_vec())
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        let v_arr = Array3::from_shape_vec((batch_size * num_heads, seq_len, head_dim), v[..total_elements].to_vec())
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

        let config = AttentionConfig {
            num_heads,
            head_dim,
            use_flash: true,
            use_causal_mask: causal,
            ..Default::default()
        };

        let result = attention::flash_attention_block(&q_arr, &k_arr, &v_arr, &config);
        Ok(result.into_raw_vec())
    })
}

/// INT8 Quantization for Python
#[pyfunction(name = "quantize_int8")]
pub fn quantize_int8_py(py: Python, data: Vec<f32>) -> PyResult<(Vec<u8>, f32, i32)> {
    py.allow_threads(move || {
        let params = QuantizationParams::from_tensor(&data, quantization::QuantizationType::INT8);
        let quantized = quantization::quantize_int8(&data, &params);
        let u8_data: Vec<u8> = quantized.into_iter().map(|x| x as u8).collect();
        Ok((u8_data, params.scale, params.zero_point))
    })
}

/// INT8 Dequantization for Python
#[pyfunction(name = "dequantize_int8")]
pub fn dequantize_int8_py(py: Python, data: Vec<u8>, scale: f32, zero_point: i32) -> PyResult<Vec<f32>> {
    py.allow_threads(move || {
        let params = QuantizationParams {
            scale,
            zero_point,
            min_val: -127,
            max_val: 127,
        };
        let i8_data: Vec<i8> = data.into_iter().map(|x| x as i8).collect();
        Ok(quantization::dequantize_int8(&i8_data, &params))
    })
}

/// Fast JSON Parse for Python
#[pyfunction]
pub fn fast_json_parse(py: Python, json_str: &str) -> PyResult<String> {
    let s = json_str.to_string();
    py.allow_threads(move || {
        let val: serde_json::Value = serde_json::from_str(&s)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        Ok(val.to_string())
    })
}

/// Fast JSON Stringify for Python
#[pyfunction]
pub fn fast_json_stringify(py: Python, json_str: &str) -> PyResult<String> {
    let s = json_str.to_string();
    py.allow_threads(move || {
        let val: serde_json::Value = serde_json::from_str(&s)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        serde_json::to_string(&val)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))
    })
}

// ═══════════════════════════════════════════════════════════════════════════════
// DATA LOADER PYTHON WRAPPER
// ═══════════════════════════════════════════════════════════════════════════════

/// Python-exposed data loader
#[pyclass]
pub struct PyDataLoader {
    inner: Arc<RwLock<data_loader::JsonlDataLoader>>,
}

#[pymethods]
impl PyDataLoader {
    /// Create a new data loader
    #[new]
    #[pyo3(signature = (num_workers=None, shuffle=true))]
    fn new(num_workers: Option<usize>, shuffle: bool) -> Self {
        let config = data_loader::DataLoaderConfig {
            num_workers: num_workers.unwrap_or_else(num_cpus::get),
            shuffle,
            ..Default::default()
        };
        Self {
            inner: Arc::new(RwLock::new(data_loader::JsonlDataLoader::new(config))),
        }
    }
    
    /// Add file to load
    fn add_file(&self, path: &str) {
        let mut inner = self.inner.write();
        inner.add_file(path);
    }
    
    /// Load all samples
    fn load_all(&self, py: Python) -> PyResult<Vec<HashMap<String, String>>> {
        let inner = Arc::clone(&self.inner);
        let samples = py.allow_threads(move || {
            let loader = inner.read();
            loader.load_all()
        }).map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;
        
        Ok(samples.into_iter().map(|s| {
            let mut map = HashMap::new();
            map.insert("text".to_string(), s.text);
            if let Some(label) = s.label {
                map.insert("label".to_string(), label.to_string());
            }
            map
        }).collect())
    }
}
