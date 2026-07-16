import os
import logging
from typing import Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SlackClient:
    def __init__(self):
        token = os.getenv("SLACK_BOT_TOKEN")
        if not token:
            raise ValueError("SLACK_BOT_TOKEN environment variable is not set.")
        self.client = WebClient(token=token)

    def send_message(self, target_id: str, text: str) -> Optional[dict]:
        """
        Send a message to a channel or a specific user.
        :param target_id: The Channel ID (e.g., 'C12345') or User ID (e.g., 'U12345').
        :param text: The message content.
        :return: The Slack API response dictionary, or None if it fails.
        """
        try:
            response = self.client.chat_postMessage(
                channel=target_id,
                text=text
            )
            logger.info(f"Message successfully sent to {target_id}")
            return response.data
        except SlackApiError as e:
            logger.error(f"Error sending message to Slack: {e.response['error']}")
            return None

    def auth_test(self) -> Optional[dict]:
        """
        Verify credentials and connection to Slack.
        :return: The API response data if successful, None otherwise.
        """
        try:
            response = self.client.auth_test()
            return response.data
        except SlackApiError as e:
            logger.error(f"Slack auth test failed: {e.response['error']}")
            return None

    def reply_to_thread(self, channel_id: str, thread_ts: str, text: str) -> Optional[dict]:
        """
        Reply to a specific message thread.
        :param channel_id: The Channel ID where the original message lives.
        :param thread_ts: The timestamp (ts) of the parent message.
        :param text: The reply content.
        :return: The Slack API response dictionary, or None if it fails.
        """
        try:
            response = self.client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text=text
            )
            logger.info(f"Thread reply successfully sent to channel {channel_id}")
            return response.data
        except SlackApiError as e:
            logger.error(f"Error replying to thread in Slack: {e.response['error']}")
            return None
