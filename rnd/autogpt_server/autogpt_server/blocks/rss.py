import ipaddress
import socket
import time
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse

import feedparser
import pydantic

from autogpt_server.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from autogpt_server.data.model import SchemaField


class RSSEntry(pydantic.BaseModel):
    title: str
    link: str
    description: str
    pub_date: datetime
    author: str
    categories: list[str]


class ReadRSSFeedBlock(Block):
    class Input(BlockSchema):
        rss_url: str = SchemaField(
            description="The URL of the RSS feed to read",
            placeholder="https://example.com/rss",
        )
        time_period: int = SchemaField(
            description="The time period to check in minutes relative to the run block runtime, e.g. 60 would check for new entries in the last hour.",
            placeholder="1440",
            default=1440,
        )
        polling_rate: int = SchemaField(
            description="The number of seconds to wait between polling attempts.",
            placeholder="300",
        )
        run_continuously: bool = SchemaField(
            description="Whether to run the block continuously or just once.",
            default=True,
        )

    class Output(BlockSchema):
        entry: RSSEntry = SchemaField(description="The RSS item")

    def __init__(self):
        super().__init__(
            id="c6731acb-4105-4zp1-bc9b-03d0036h370g",
            input_schema=ReadRSSFeedBlock.Input,
            output_schema=ReadRSSFeedBlock.Output,
            categories={BlockCategory.INPUT},
            test_input={
                "rss_url": "https://example.com/rss",
                "time_period": 10_000_000,
                "polling_rate": 1,
                "run_continuously": False,
            },
            test_output=[
                (
                    "entry",
                    RSSEntry(
                        title="Example RSS Item",
                        link="https://example.com/article",
                        description="This is an example RSS item description.",
                        pub_date=datetime(2023, 6, 23, 12, 30, 0, tzinfo=timezone.utc),
                        author="John Doe",
                        categories=["Technology", "News"],
                    ),
                ),
            ],
            test_mock={
                "parse_feed": lambda *args, **kwargs: {
                    "entries": [
                        {
                            "title": "Example RSS Item",
                            "link": "https://example.com/article",
                            "summary": "This is an example RSS item description.",
                            "published_parsed": (2023, 6, 23, 12, 30, 0, 4, 174, 0),
                            "author": "John Doe",
                            "tags": [{"term": "Technology"}, {"term": "News"}],
                        }
                    ]
                }
            },
        )

    @staticmethod
    def validate_rss_url(url: str) -> str:
        parsed_url = urlparse(url)
        if parsed_url.scheme not in {"http", "https"}:
            raise ValueError("Only http and https URLs are allowed.")

        hostname = parsed_url.hostname
        if not hostname:
            raise ValueError("RSS URL must include a valid host.")

        if hostname == "localhost" or hostname.endswith(".localhost"):
            raise ValueError("RSS URL host is not allowed.")

        try:
            ip = ipaddress.ip_address(hostname)
        except ValueError:
            ip = None

        if ip is not None:
            if not ip.is_global:
                raise ValueError("RSS URL host is not allowed.")
            return url

        try:
            addresses = socket.getaddrinfo(hostname, None)
        except socket.gaierror as exc:
            raise ValueError("Unable to resolve RSS URL host.") from exc

        for _, _, _, _, sockaddr in addresses:
            resolved_ip = ipaddress.ip_address(sockaddr[0])
            if not resolved_ip.is_global:
                raise ValueError("RSS URL host is not allowed.")

        return url

    @staticmethod
    def parse_feed(url: str) -> dict[str, Any]:
        return feedparser.parse(ReadRSSFeedBlock.validate_rss_url(url))  # type: ignore

    def run(self, input_data: Input) -> BlockOutput:
        keep_going = True
        start_time = datetime.now(timezone.utc) - timedelta(
            minutes=input_data.time_period
        )
        while keep_going:
            keep_going = input_data.run_continuously

            feed = self.parse_feed(input_data.rss_url)

            for entry in feed["entries"]:
                pub_date = datetime(*entry["published_parsed"][:6], tzinfo=timezone.utc)

                if pub_date > start_time:
                    yield (
                        "entry",
                        RSSEntry(
                            title=entry["title"],
                            link=entry["link"],
                            description=entry.get("summary", ""),
                            pub_date=pub_date,
                            author=entry.get("author", ""),
                            categories=[tag["term"] for tag in entry.get("tags", [])],
                        ),
                    )

            time.sleep(input_data.polling_rate)
