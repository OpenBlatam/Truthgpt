if anomaly_score > 0.8 or time_since_deep > 300:
    deep_report = await health_deep()
else:
    quick_metrics = await health_light()