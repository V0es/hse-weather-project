import time
from functools import wraps
from typing import Any, Callable


def async_timeit(
    func: Callable,
):
    """Декоратор для подсчёта времени исполнения асинхронной функции

    Args:
        func (Callable): Декорируемая функция

    Returns:
        _type_: Обёртка функции
    """

    @wraps(func)
    async def async_wrapper(*args, **kwargs) -> tuple[Any, float]:
        start_time = time.time()
        result = await func(*args, **kwargs)
        time_elapsed = time.time() - start_time
        return result, time_elapsed

    return async_wrapper


def sync_timeit(
    func: Callable,
):
    """Декоратор для подсчёта времени исполнения синхронной функции

    Args:
        func (Callable): Декорируемая функция

    Returns:
        _type_: Обёртка функции
    """

    @wraps(func)
    def sync_wrapper(*args, **kwargs) -> tuple[Any, float]:
        start_time = time.time()
        result = func(*args, **kwargs)
        time_elapsed = time.time() - start_time
        return result, time_elapsed

    return sync_wrapper
