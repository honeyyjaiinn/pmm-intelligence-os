from __future__ import annotations

import os
import praw

from .base import Connector, Signal


class RedditConnector(Connector):
    def __init__(self):
        required = [
            "REDDIT_CLIENT_ID",
            "REDDIT_CLIENT_SECRET",
            "REDDIT_USER_AGENT",
        ]
        missing = [key for key in required if not os.getenv(key)]
        if missing:
            raise RuntimeError(
                "Missing Reddit credentials: " + ", ".join(missing)
            )

        self.client = praw.Reddit(
            client_id=os.environ["REDDIT_CLIENT_ID"],
            client_secret=os.environ["REDDIT_CLIENT_SECRET"],
            user_agent=os.environ["REDDIT_USER_AGENT"],
        )

    def fetch(
        self,
        subreddit: str = "Ebay",
        query: str = "seller listing",
        limit: int = 50,
        **kwargs,
    ) -> list[Signal]:
        signals: list[Signal] = []
        for post in self.client.subreddit(subreddit).search(
            query=query,
            sort="new",
            time_filter="year",
            limit=limit,
        ):
            text = f"{post.title}\n{post.selftext or ''}".strip()
            signals.append(
                Signal(
                    source=f"Reddit r/{subreddit}",
                    source_type="community",
                    text=text,
                    created_at=str(post.created_utc),
                    url=f"https://www.reddit.com{post.permalink}",
                    external_id=post.id,
                    metadata={"score": post.score, "num_comments": post.num_comments},
                )
            )
        return signals
