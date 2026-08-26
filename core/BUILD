load("@rules_python//python:defs.bzl", "py_library")

py_library(
    name = "core",
    srcs = [
        "__init__.py",
    ],
    deps = [
        "//core/adapters:adapters",
        "//core/common_runtime:common_runtime",
        "//core/composition:composition",
        "//core/data:data",
        "//core/distributed_runtime:distributed_runtime",
        "//core/framework:framework",
        "//core/kernel:kernel",
        "//core/kernels:kernels",
        "//core/lib:lib",
        "//core/ops:ops",
        "//core/optimizers:optimizers",
        "//core/platform:platform",
        "//core/runtime_fallback:runtime_fallback",
        "//core/services:services",
        "//core/systems:systems",
        "//core/util:util",
        "//core/validation:validation",
    ],
    visibility = ["//visibility:public"],
)
