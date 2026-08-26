load("@rules_python//python:defs.bzl", "py_library")

py_library(
    name = "optimizers",
    srcs = [
        "__init__.py",
        "advanced_optimizations.py",
        "base_truthgpt_optimizer.py",
        "modern_truthgpt_optimizer.py",
        "modular_optimizer.py",
        "pytorch_optimizer_base.py",
        "unified_optimizer.py",
    ],
    deps = [
        "//core/ops:ops",
        "//core/util:util",
        "//core/framework:framework",
    ],
    visibility = ["//visibility:public"],
)
