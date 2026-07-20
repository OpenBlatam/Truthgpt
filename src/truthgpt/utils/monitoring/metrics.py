import math


def perplexity_from_loss(val_loss: float) -> float:
    try:
        return float(math.exp(val_loss))
    except Exception:
        return float("nan")


def tokens_per_second(num_tokens: int, seconds: float) -> float:
    if seconds <= 0:
        return float("inf")
    return float(num_tokens) / float(seconds)





