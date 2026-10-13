"""Ollama 生成速度与用户实际等待速度采用不同计时范围。"""
import math


def seconds(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value / 1e9 if math.isfinite(value) and value > 0 else None


def rate(tokens, duration):
    if duration is None or duration <= 0 or not math.isfinite(duration):
        return None
    return round(tokens / duration, 2)


def finish_metrics(job, event, started, now):
    """按生成耗时加权，未知耗时的调用不能混入速度分子。"""
    duration = seconds(event.get('eval_duration'))
    generated = event.get('eval_count', 0)
    if duration is not None:
        job.rated_generated += generated
        job.total_decode_seconds += duration
    elapsed = max(0, now - job.started)
    return {
        'metrics_version': 2,
        'tokens_per_second': rate(generated, duration),
        'decode_seconds': duration,
        'aggregate_tokens_per_second': rate(job.rated_generated, job.total_decode_seconds),
        'total_decode_seconds': job.total_decode_seconds,
        'rated_generated_tokens': job.rated_generated,
        'task_tokens_per_second': rate(job.total_generated, elapsed) if not job.unmeasured_calls else None,
        'unmeasured_calls':job.unmeasured_calls,
        'call_tokens_per_second': rate(generated, max(0, now - started)),
        'call_elapsed_seconds': round(max(0, now - started), 2),
        'elapsed_seconds': round(elapsed, 2),
        'load_seconds': seconds(event.get('load_duration')),
        'prompt_eval_seconds': seconds(event.get('prompt_eval_duration')),
        'engine_total_seconds': seconds(event.get('total_duration')),
    }
