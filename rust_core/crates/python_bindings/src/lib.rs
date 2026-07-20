use pyo3::prelude::*;
use std::collections::HashMap;
use std::sync::{Arc, RwLock};

use crate::{
    CompressionAlgorithm, KVCacheConfig, EvictionStrategy,
};

// ═══════════════════════════════════════════════════════════════════════════════
// PYTHON MODULE
// ═══════════════════════════════════════════════════════════════════════════════

/// TruthGPT Rust Core - Python Module
#[pymodule]
fn truthgpt_rust(py: Python, m: &PyModule) -> PyResult<()> {
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
fn get_version() -> String {
    format!("truthgpt-rust v{}", env!("CARGO_PKG_VERSION"))
}

/// Get system information
#[pyfunction]
fn get_system_info() -> HashMap<String, String> {
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
// 🔥 KV CACHE PYTHON WRAPPER
// ═══════════════════════════════════════════════════════════════════════════════

/// Python-exposed KV Cache with ultra-fast operations
#[pyclass]
pub struct PyKVCache {
    inner: Arc<RwLock<truthgpt_cache::kv_cache::KVCache>>,
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
            inner: Arc::new(RwLock::new(truthgpt_cache::kv_cache::KVCache::new(config))),
        })
    }
    
    /// Get cached value by layer index and position
    fn get(&self, layer_idx: usize, position: usize) -> Option<Vec<u8>> {
        let cache = self.inner.read().unwrap();
        cache.get(layer_idx, position).map(|v| v.to_vec())
    }
    
    /// Put value in cache
    fn put(&self, layer_idx: usize, position: usize, data: Vec<u8>) {
        let mut cache = self.inner.write().unwrap();
        cache.put(layer_idx, position, data);
    }
    
    /// Check if key exists
    fn contains(&self, layer_idx: usize, position: usize) -> bool {
        let cache = self.inner.read().unwrap();
        cache.get(layer_idx, position).is_some()
    }
    
    /// Clear all cached data
    fn clear(&self) {
        let mut cache = self.inner.write().unwrap();
        cache.clear();
    }
    
    /// Get cache statistics
    fn stats(&self) -> HashMap<String, f64> {
        let cache = self.inner.read().unwrap();
        cache.get_stats()
    }
    
    /// Get current cache size
    fn size(&self) -> usize {
        let cache = self.inner.read().unwrap();
        cache.size()
    }
    
    /// Get maximum cache size
    fn max_size(&self) -> usize {
        let cache = self.inner.read().unwrap();
        cache.max_size()
    }
    
    fn __repr__(&self) -> String {
        let cache = self.inner.read().unwrap();
        format!("PyKVCache(size={}/{})", cache.size(), cache.max_size())
    }
    
    fn __len__(&self) -> usize {
        self.size()
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// 🗜️ COMPRESSION PYTHON WRAPPER
// ═══════════════════════════════════════════════════════════════════════════════

/// Python-exposed compressor with LZ4 and Zstd support
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
    
    /// Compress data
    fn compress(&self, data: Vec<u8>) -> PyResult<Vec<u8>> {
        truthgpt_optimization::compression::compress(&data, &self.algorithm)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }
    
    /// Decompress data
    fn decompress(&self, data: Vec<u8>) -> PyResult<Vec<u8>> {
        truthgpt_optimization::compression::decompress(&data, &self.algorithm)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }
    
    /// Compress with statistics
    fn compress_with_stats(&self, data: Vec<u8>) -> PyResult<(Vec<u8>, HashMap<String, f64>)> {
        let (compressed, stats) = truthgpt_optimization::compression::compress_with_stats(&data, &self.algorithm)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        
        let stats_map = HashMap::from([
            ("original_size".to_string(), stats.original_size as f64),
            ("compressed_size".to_string(), stats.compressed_size as f64),
            ("ratio".to_string(), stats.compression_ratio()),
            ("savings".to_string(), stats.space_savings()),
            ("time_us".to_string(), stats.compression_time_us as f64),
        ]);
        
        Ok((compressed, stats_map))
    }
    
    fn __repr__(&self) -> String {
        format!("PyCompressor(algorithm={:?}, level={})", self.algorithm, self.level)
    }
}

/// Fast LZ4 compression (standalone function)
#[pyfunction]
fn fast_lz4_compress(data: Vec<u8>) -> PyResult<Vec<u8>> {
    truthgpt_optimization::compression::compress(&data, &CompressionAlgorithm::LZ4)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
}

/// Fast LZ4 decompression (standalone function)
#[pyfunction]
fn fast_lz4_decompress(data: Vec<u8>) -> PyResult<Vec<u8>> {
    truthgpt_optimization::compression::decompress(&data, &CompressionAlgorithm::LZ4)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
}

/// Fast Zstd compression (standalone function)
#[pyfunction]
#[pyo3(signature = (data, level=3))]
fn fast_zstd_compress(data: Vec<u8>, level: i32) -> PyResult<Vec<u8>> {
    truthgpt_optimization::compression::compress_zstd_level(&data, level)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
}

/// Fast Zstd decompression (standalone function)
#[pyfunction]
fn fast_zstd_decompress(data: Vec<u8>) -> PyResult<Vec<u8>> {
    truthgpt_optimization::compression::decompress(&data, &CompressionAlgorithm::Zstd)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
}

// ═══════════════════════════════════════════════════════════════════════════════
// ⚡ TOKENIZATION PYTHON WRAPPER
// ═══════════════════════════════════════════════════════════════════════════════

/// Python-exposed fast tokenizer wrapper
#[pyclass]
pub struct PyFastTokenizer {
    inner: truthgpt_data::tokenizer_wrapper::FastTokenizer,
}

#[pymethods]
impl PyFastTokenizer {
    /// Create a tokenizer from a file
    #[new]
    fn new(tokenizer_path: &str) -> PyResult<Self> {
        let inner = truthgpt_data::tokenizer_wrapper::FastTokenizer::from_file(tokenizer_path)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        Ok(Self { inner })
    }
    
    /// Create from pretrained model
    #[staticmethod]
    fn from_pretrained(identifier: &str) -> PyResult<Self> {
        let inner = truthgpt_data::tokenizer_wrapper::FastTokenizer::from_pretrained(identifier)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        Ok(Self { inner })
    }
    
    /// Encode text to tokens
    #[pyo3(signature = (text, add_special_tokens=true))]
    fn encode(&self, text: &str, add_special_tokens: bool) -> PyResult<Vec<u32>> {
        self.inner.encode(text, add_special_tokens)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }
    
    /// Decode tokens to text
    #[pyo3(signature = (tokens, skip_special_tokens=true))]
    fn decode(&self, tokens: Vec<u32>, skip_special_tokens: bool) -> PyResult<String> {
        self.inner.decode(&tokens, skip_special_tokens)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }
    
    /// Batch encode multiple texts (parallel)
    #[pyo3(signature = (texts, add_special_tokens=true))]
    fn encode_batch(&self, texts: Vec<String>, add_special_tokens: bool) -> PyResult<Vec<Vec<u32>>> {
        self.inner.encode_batch(&texts, add_special_tokens)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }
    
    /// Batch decode (parallel)
    #[pyo3(signature = (token_batches, skip_special_tokens=true))]
    fn decode_batch(&self, token_batches: Vec<Vec<u32>>, skip_special_tokens: bool) -> PyResult<Vec<String>> {
        self.inner.decode_batch(&token_batches, skip_special_tokens)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
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
fn parallel_tokenize(
    tokenizer_path: &str,
    texts: Vec<String>,
    add_special_tokens: bool,
) -> PyResult<Vec<Vec<u32>>> {
    let tokenizer = truthgpt_data::tokenizer_wrapper::FastTokenizer::from_file(tokenizer_path)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    
    tokenizer.encode_batch(&texts, add_special_tokens)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
}

// ═══════════════════════════════════════════════════════════════════════════════
// 📊 DATA LOADER PYTHON WRAPPER
// ═══════════════════════════════════════════════════════════════════════════════

/// Python-exposed data loader
#[pyclass]
pub struct PyDataLoader {
    inner: truthgpt_data::data_loader::JsonlDataLoader,
}

#[pymethods]
impl PyDataLoader {
    /// Create a new data loader
    #[new]
    #[pyo3(signature = (num_workers=None, shuffle=true))]
    fn new(num_workers: Option<usize>, shuffle: bool) -> Self {
        let config = truthgpt_data::data_loader::DataLoaderConfig {
            num_workers: num_workers.unwrap_or_else(num_cpus::get),
            shuffle,
            ..Default::default()
        };
        Self {
            inner: truthgpt_data::data_loader::JsonlDataLoader::new(config),
        }
    }
    
    /// Add file to load
    fn add_file(&mut self, path: &str) {
        self.inner.add_file(path);
    }
    
    /// Load all samples
    fn load_all(&self) -> PyResult<Vec<HashMap<String, String>>> {
        let samples = self.inner.load_all()
            .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;
        
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
