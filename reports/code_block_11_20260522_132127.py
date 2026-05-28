from concurrent.futures import ThreadPoolExecutor, TimeoutError

def run_agent_with_timeout(agent_func, timeout=60):
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(agent_func)
        try:
            return future.result(timeout=timeout)
        except TimeoutError:
            logger.warning("Agente excedió el tiempo límite")
            return None