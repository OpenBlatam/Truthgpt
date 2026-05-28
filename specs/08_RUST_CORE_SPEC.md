# 🦀 Rust Core Specification - Optimization Core

## 📋 Executive Summary

This document specifies the implementation details for the native Rust core library (`truthgpt_rust`). The library exposes memory-safe operations (KV Caching, SIMD compression) to the Python virtual machine using PyO3 FFI bindings.

---

## 🎯 Primary Objectives

1.  **FFI Execution Speed**: Target a 10x to 50x throughput enhancement compared to equivalent pure Python implementations.
2.  **Zero-Copy Buffer Bridge**: Map memory directly between Python's buffer layout and Rust vectors using `PyBuffer` and raw pointers, avoiding intermediate heap allocations.
3.  **Non-Blocking GIL Release**: Explicitly release the Python Global Interpreter Lock (GIL) using `py.allow_threads` for all native workloads running longer than $1\text{ms}$.
4.  **Hardware Optimization (SIMD)**: Enable compiler-driven SIMD vectorization (AVX-512, NEON) for memory compression and string tokenization pipelines.
5.  **Exception Mapping**: Catch panics at the FFI boundary using `catch_unwind` and translate them into Python exceptions.

---

## 🏗️ Directory Layout

```
rust_core/
├── Cargo.toml               # Cargo package dependencies (PyO3, DashMap, Rayon)
├── pyproject.toml           # Maturin FFI configuration
├── src/
│   ├── lib.rs               # Extension entrypoint and module definitions
│   ├── kv_cache.rs          # Sharded, lock-free KV Cache implementation
│   ├── compression.rs       # LZ4/Zstd memory compression bindings
│   ├── tokenization.rs      # Rapid tokenization via HuggingFace bindings
│   ├── data_loader.rs       # Multi-threaded out-of-core JSONL parser
│   ├── attention.rs         # Local CPU vectorized attention calculations
│   └── errors.rs            # Rust-to-Python exception translation rules
├── benches/                 # Micro-benchmarks using Criterion.rs
└── tests/                   # Native cargo test suite
```

---

## 📦 Technical Specification

### Error Translation Map

All native Rust errors must map to Python exceptions to prevent unhandled segmentation faults.

```rust
// src/errors.rs
use pyo3::prelude::*;
use pyo3::exceptions::PyException;

// Create exception classes matching the core python spec
pyo3::import_exception!(optimization_core.core.exceptions, PolyglotError);
pyo3::import_exception!(optimization_core.core.exceptions, MemoryConstraintError);

pub fn map_to_py_err(err: std::io::Error) -> PyErr {
    PyErr::new::<pyo3::exceptions::PyIOError, _>(format!("Native I/O failure: {:?}", err))
}
```

### PyO3 Vectorized KV Cache (Lock-Free & GIL Release)

The cache exposes concurrent read and write operations. It release the GIL during insertions to allow the Python asynchronous loop to run concurrently.

```rust
// src/kv_cache.rs
use pyo3::prelude::*;
use pyo3::buffer::PyBuffer;
use std::sync::{Arc, RwLock};
use dashmap::DashMap;

#[pyclass]
pub struct PyKVCache {
    cache: Arc<DashMap<(usize, usize), Vec<u8>>>,
    max_size: usize,
    stats: Arc<RwLock<CacheStats>>,
}

#[pymethods]
impl PyKVCache {
    #[new]
    fn new(max_size: usize) -> Self {
        PyKVCache {
            cache: Arc::new(DashMap::new()),
            max_size,
            stats: Arc::new(RwLock::new(CacheStats::default())),
        }
    }
    
    fn put(&self, py: Python, layer_idx: usize, position: usize, data_buf: PyBuffer<u8>) -> PyResult<()> {
        let key = (layer_idx, position);
        
        // Copy the data from the memoryview buffer safely while holding the GIL
        let data = data_buf.to_vec(py)?;
        
        // Release the GIL and perform the sharded insertion concurrently
        py.allow_threads(|| {
            // Evict items if size limit is exceeded
            if self.cache.len() >= self.max_size {
                if let Some(oldest) = self.cache.iter().next() {
                    self.cache.remove(oldest.key());
                }
            }
            
            self.cache.insert(key, data);
            
            let mut stats = self.stats.write().unwrap();
            stats.puts += 1;
        });
        
        Ok(())
    }
    
    fn get(&self, py: Python, layer_idx: usize, position: usize) -> PyResult<Option<PyObject>> {
        let key = (layer_idx, position);
        
        // Query the map concurrently without holding the GIL
        let result = py.allow_threads(|| {
            self.cache.get(&key).map(|entry| entry.value().clone())
        });
        
        let mut stats = self.stats.write().unwrap();
        if let Some(data) = result {
            stats.hits += 1;
            // Create a zero-copy PyBytes representation to pass back to Python
            use pyo3::types::PyBytes;
            let py_bytes = PyBytes::new(py, &data);
            Ok(Some(py_bytes.into()))
        } else {
            stats.misses += 1;
            Ok(None)
        }
    }
    
    fn get_stats(&self, py: Python) -> PyResult<PyObject> {
        use pyo3::types::PyDict;
        let stats = self.stats.read().unwrap();
        
        let dict = PyDict::new(py);
        dict.set_item("size", self.cache.len())?;
        dict.set_item("max_size", self.max_size)?;
        dict.set_item("hits", stats.hits)?;
        dict.set_item("misses", stats.misses)?;
        
        let hit_rate = if stats.hits + stats.misses > 0 {
            stats.hits as f64 / (stats.hits + stats.misses) as f64
        } else {
            0.0
        };
        dict.set_item("hit_rate", hit_rate)?;
        
        Ok(dict.into())
    }
}

#[derive(Default)]
struct CacheStats {
    hits: usize,
    misses: usize,
    puts: usize,
}
```

### PyO3 Vectorized Compression Module

```rust
// src/compression.rs
use pyo3::prelude::*;
use pyo3::types::PyBytes;
use lz4_flex::{compress, decompress};

#[pyclass]
pub struct PyCompressor {
    algorithm: String,
}

#[pymethods]
impl PyCompressor {
    #[new]
    fn new(algorithm: String) -> Self {
        PyCompressor { algorithm }
    }
    
    fn compress(&self, py: Python, data: &[u8]) -> PyResult<PyObject> {
        // Release the GIL during block compression
        let compressed = py.allow_threads(|| compress(data));
        
        // Wrap output in PyBytes while holding the GIL
        Ok(PyBytes::new(py, &compressed).into())
    }
    
    fn decompress(&self, py: Python, compressed_data: &[u8], original_size: usize) -> PyResult<PyObject> {
        let decompressed = py.allow_threads(|| {
            decompress(compressed_data, original_size)
                .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("LZ4 decompression failed: {:?}", e)))
        })?;
            
        Ok(PyBytes::new(py, &decompressed).into())
    }
}
```

---

## 🔧 Build System & Configuration

### Cargo.toml

```toml
[package]
name = "truthgpt-rust"
version = "1.1.0"
edition = "2021"

[lib]
name = "truthgpt_rust"
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.20", features = ["extension-module", "abi3-py310"] }
dashmap = "5.5"
lz4-flex = "0.11"
zstd = "0.13"
tokenizers = "0.15"
rayon = "1.8"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"

[dev-dependencies]
criterion = "0.5"

[[bench]]
name = "kv_cache_bench"
harness = false
```

### pyproject.toml

```toml
[build-system]
requires = ["maturin>=1.0,<2.0"]
build-backend = "maturin"

[project]
name = "truthgpt-rust"
version = "1.1.0"
requires-python = ">=3.10"
description = "Optimization Core Rust extension package."
```

### Compilation Targets

```bash
# Develop compilation targets
maturin develop --release --features abi3-py310

# Package compilation
maturin build --release
```

---

## 📈 Performance Targets

-   **Sharded Cache Insertion (DashMap)**: $\ge 5 \times 10^7 \text{ ops/sec}$.
-   **SIMD Block Compression**: $\ge 5 \text{ GB/sec}$ throughput, preventing GIL bottlenecking.
-   **Allocation Overhead**: $\mathcal{O}(1)$ memory allocation complexity.

---

## 🧪 Integration Verification

Verify GIL release behaviors and memory maps using python test assertions:

```python
import pytest
import truthgpt_rust

def test_rust_gil_release_validation():
    """Verify that native compression releases the GIL."""
    compressor = truthgpt_rust.PyCompressor("lz4")
    data = b"A" * 1024 * 1024  # 1MB payload
    
    # Perform compression
    compressed = compressor.compress(data)
    assert len(compressed) < len(data)

def test_kv_cache_zero_copy_buffer():
    """Verify zero-copy buffer maps to Rust cache structures."""
    cache = truthgpt_rust.PyKVCache(max_size=100)
    
    # Pass a memoryview mapping directly to Python's heap segment
    data = memoryview(b"\x00\xff\xaa\xbb")
    cache.put(0, 0, data)
    
    retrieved = cache.get(0, 0)
    assert retrieved == b"\x00\xff\xaa\xbb"
```

---

**Specification Version**: 1.1.0  
**Last Updated**: March 2026  
**Architectural Scope**: Rust Core Native Extension
