import os

from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Load environment variables from a .env file
load_dotenv()


def send_message_to_channel(text: str):
    # Get your Slack token and channel ID from the environment variables
    SLACK_TOKEN = os.getenv("SLACK_TOKEN")
    SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")
    if not SLACK_TOKEN or not SLACK_CHANNEL_ID:
        raise EnvironmentError(
            "SLACK_TOKEN and SLACK_CHANNEL_ID must be set in your .env file. "
            "See .env.example for reference."
        )
    client = WebClient(token=SLACK_TOKEN)

    try:
        # Send a message to the channel
        response = client.chat_postMessage(
            channel=SLACK_CHANNEL_ID,
            text=text,
        )
        return response
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")


if __name__ == "__main__":
    # Example usage
    message = "Hello, world! This is a test message from the Slack Helper."
    response = send_message_to_channel(message)
    if response:
        print("Message sent successfully!")
    else:
        print("Failed to send message.")
