import json
import logging
import os
import uuid
from dataclasses import dataclass, asdict

import requests
import time

import typer
from rich.logging import RichHandler, Console

console = Console()
logging.basicConfig(level="INFO", handlers=[RichHandler(console=console)])
logger = logging.getLogger("rich")
AIRFOLD_API_URL = os.environ.get("AIRFOLD_API_URL", "https://api.airfold.co")


@dataclass
class Event:
    id: str
    timestamp: int
    status_code: int
    latency: int


def instrumented(method: str, url: str, **kwargs) -> tuple[requests.Response, Event]:
    start_time = time.time()
    response = requests.request(method, url, **kwargs)
    latency = time.time() - start_time
    status_code = response.status_code

    event = Event(
        id=uuid.uuid4().hex,
        timestamp=int(start_time),
        status_code=status_code,
        latency=int(latency * 1000),  # in ms
    )

    logger.info("Request processed successfully.")
    logger.debug(f"Event: {json.dumps(asdict(event), indent=4)}")

    return response, event


def send_event(event: Event, airfold_url: str, api_key: str):
    logger.info("Sending event to Airfold API...")
    res = requests.post(
        airfold_url,
        json=asdict(event),
        headers={"Authorization": f"Bearer {api_key}"},
    )
    if not res.ok:
        logger.error(f"Failed to send event: {res.text}")
    else:
        logger.info("Event sent successfully.")


def main(
    num_requests: int = typer.Option(100, help="Number of requests to process."),
    source: str = typer.Option("events", help="Airfold source to send events to."),
    api_key: str = typer.Option(..., envvar="AIRFOLD_API_KEY", help="Airfold API key."),
    sample_api: str = typer.Option("https://jsonplaceholder.typicode.com/todos", help="Sample API URL")
):
    for i in range(num_requests):
        logger.info(f"Processing request {i + 1} of {num_requests}...")
        resp, event = instrumented("get", sample_api)
        send_event(event, f"{AIRFOLD_API_URL}/v1/events/{source}", api_key)
        logger.info(f"Completed request {i + 1} of {num_requests}.")


if __name__ == "__main__":
    typer.run(main)
