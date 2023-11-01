import asyncio
import os
import time

import yaml
from itertools import cycle
from loguru import logger
from src.main import Parser


def validate_settings() -> str or None:
    timeout = config.get("timeout")

    if not timeout or not isinstance(timeout, int):
        raise ValueError("Timeout in settings must be an integer")

    if config.get("use_proxy"):
        proxies_path = os.path.join(os.getcwd(), "proxies.txt")
        if os.path.exists(proxies_path) and os.path.getsize(proxies_path) > 0:
            with open(proxies_path, "r") as proxies_file:
                proxies = proxies_file.read().splitlines()

            for proxy in proxies:
                parts = proxy.split(":")
                if len(parts) != 4:
                    raise ValueError("Proxy must be in format ip:port:user:password")

            return proxies_path
        else:
            raise FileNotFoundError("Proxies file not found or empty")
    else:
        return None


def run() -> None:
    proxies_path = validate_settings()

    if proxies_path and config.get("use_proxy"):
        with open(proxies_path, "r") as proxies_file:
            proxies = proxies_file.read().splitlines()

        proxy_cycle = cycle(proxies)
        while True:
            time.sleep(1)
            proxy = next(proxy_cycle)
            logger.info(f"Parser started | Proxy: {proxy}")
            parser = Parser(
                proxy=proxy, timeout=config["timeout"]
            )
            asyncio.run(parser.start())

    else:
        while True:
            time.sleep(1)
            logger.info("Parser started | Proxy: None")
            parser = Parser(timeout=config["timeout"])
            asyncio.run(parser.start())


if __name__ == "__main__":
    with open("settings.yaml", "r") as config_file:
        config = yaml.safe_load(config_file)

    run()
