def system_health_check():
    if quick_metrics.outlier_percentage > 0.1:
        run_deep_diagnostic()
    else:
        run_lite_check()