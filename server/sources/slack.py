import datetime
import os
from fastapi import HTTPException, status
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from server.db_utils import connect_db


def summarize_conversation(conversation):
    """
    Summarize a conversation based on its raw messages
    """
    # TODO
    pass


async def get_slack_data(channel):
    """
    Fetch data from the slack API based on the query string queryStr
    """
    try:
        db = await connect_db()
        if not db:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Database connection failed")

        slack_token = os.getenv("SLACK_API_TOKEN")
        if not slack_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No slack API token found",
            )

        # Create a client instance
        client = WebClient(token=slack_token)

        # Specify the channel to fetch conversations from
        try:
            # Fetch conversations from the specified channel
            result = client.conversations_history(channel=channel)
        except SlackApiError as e:
            print("Error fetching result for channel: ", e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error: {e.response['error']}",
            )

        try:
            # Fetch conversations from the specified channel
            result = client.conversations_history(channel=channel)
        except SlackApiError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error: {e.response['error']}",
            )

        # Create a list to hold the processed conversations
        processed_conversations = []
        all_raw_messages = []

        # Iterate over each message in the channel's history
        for message in result["messages"]:
            # Create a list to hold the raw messages of this conversation
            raw_messages = []
            slack_user_id = str(message["ts"].replace(".", ""))

            # check if user with slackId exists in database
            # TODO
            user = await db.user.find_first(where={"slackId": slack_user_id, "email": email})
            if not user:
                # create user
                user = await db.user.create({"slackId": slack_user_id, "name": email})

            # Transform the message into a raw message dictionary and add it to the list
            raw_message = {
                # Use the timestamp as a unique ID
                "id": user["id"],
                "email": user["email"],
                "slackId": slack_user_id,
                "text": message["text"],
                "time": datetime.datetime.fromtimestamp(float(message["ts"])),
                "user": message["user"],
                "userId": message["user"],  # Assume user ID is like 'U12345'
            }
            raw_messages.append(raw_message)

            # Initialize the conversation's end time with the message's timestamp
            end_time = datetime.datetime.fromtimestamp(float(message["ts"]))

            # If the message has replies, fetch them and update the conversation's end time
            if "thread_ts" in message:
                thread_result = client.conversations_replies(
                    channel=channel, ts=message["thread_ts"])
                for reply in thread_result["messages"]:
                    if reply["ts"] == message["ts"]:
                        continue  # Skip the message itself

                    # Transform each reply into a raw message dictionary and add it to the list
                    reply_raw_message = {
                        # Use the timestamp as a unique ID
                        "id": int(reply["ts"].replace(".", "")),
                        "text": reply["text"],
                        "time": datetime.datetime.fromtimestamp(float(reply["ts"])),
                        "user": reply["user"],
                        # Assume user ID is like 'U12345'
                        "userId": reply["user"],
                    }
                    raw_messages.append(reply_raw_message)

                    # Update the conversation's end time with the reply's timestamp
                    end_time = datetime.datetime.fromtimestamp(
                        float(reply["ts"]))

            # Transform the thread into a processed conversation dictionary
            processed_conversation = {
                # Use the timestamp as a unique ID
                "id": int(message["ts"].replace(".", "")),
                "summary": "",  # You need to implement how to generate a summary
                "startTime": datetime.datetime.fromtimestamp(float(message["ts"])),
                "endTime": end_time,
                "rawMsgs": raw_messages,
                "users": list(set([raw_message["user"] for raw_message in raw_messages])),
                # Assume user ID is like 'U12345'
                "userIds": list(set([raw_message["userId"] for raw_message in raw_messages])),
            }
            processed_conversations.append(processed_conversation)
            # append all raw messages to all_row_messages
            all_raw_messages.extend(raw_messages)

        data = {
            "processed_conversations": processed_conversations,
            "raw_messages": all_raw_messages
        }

        # Write the processed conversation to the database
        return data

    except Exception as ex:
        print(ex)
        raise ex
