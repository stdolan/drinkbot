from xml.etree import ElementTree
import re
import boto3
from boto3.dynamodb import conditions
import uuid
import time
from decimal import Decimal


DRINKS_PER_HOUR = 1.0
DRINKS_PER_SECOND = (DRINKS_PER_HOUR / 60.0) / 60.0


def build_response(*, response_text="", response_media=[]):
    response = ElementTree.Element("Response")
    message = ElementTree.SubElement(response, "Message")
    body = ElementTree.SubElement(message, "Body")
    body.text = response_text
    for media in response_media:
        media_tag = ElementTree.SubElement(message, "Media")
        media_tag.text = media
    return ElementTree.tostring(
        response, xml_declaration=True, encoding="UTF-8"
    )


def calculate_drinks(user):
    end = Decimal(str(time.time() - (24.0 * 60 * 60)))
    dynamodb = boto3.resource("dynamodb")
    drinks_table = dynamodb.Table("drink-tracker-drinks")
    items = drinks_table.scan(
        FilterExpression=conditions.Attr("user").eq(user)
        & conditions.Attr("timestamp").gte(end)
    )["Items"]
    items.sort(key=lambda item: item["timestamp"])
    if not items:
        return f"You have no drinks in you"
    current_time = items[0]["timestamp"]
    current_drinks = items[0]["drinks"]
    for item in items[1:]:
        delta_time = item["timestamp"] - current_time
        delta_drinks = Decimal(str(DRINKS_PER_SECOND)) * delta_time
        current_drinks -= delta_drinks
        if current_drinks < Decimal(0):
            current_drinks = 0
        current_drinks += item["drinks"]
        current_time = item["timestamp"]
    delta_time = Decimal(str(time.time())) - items[-1]["timestamp"]
    delta_drinks = Decimal(str(DRINKS_PER_SECOND)) * delta_time
    current_drinks -= delta_drinks
    if current_drinks < Decimal(0):
        current_drinks = 0
    return f"You have {round(current_drinks, 1)} drink(s) in you"


def add_drinks(user, drinks):
    client = boto3.client("dynamodb")
    x = time
    client.put_item(
        TableName="drink-tracker-drinks",
        Item={
            "id": {"S": str(uuid.uuid4())},
            "user": {"S": user},
            "timestamp": {"N": str(time.time())},
            "drinks": {"N": str(drinks)},
        },
    )
    return f"Added {drinks} drink(s)\n{calculate_drinks(user)}"


def handler(event, context):
    print("Received event: " + str(event))
    received_message = event["Body"]
    sender = event["From"]

    if received_message == "%3F" or received_message == "%3F+":  # AKA "?"
        return build_response(response_text=calculate_drinks(sender))

    trump_match = re.search("trump", received_message.lower())
    digit_match = re.search(r"(\d+\.)?(\d+)", received_message)
    if trump_match:
        return build_response(
            response_media=[
                "https://drink-bot.s3.us-west-2.amazonaws.com/trump.jpg"
            ]
        )
    elif digit_match:
        return build_response(
            response_text=add_drinks(
                sender,
                Decimal(
                    f"{digit_match.group(1) if digit_match.group(1) else ''}{digit_match.group(2)}"
                ),
            )
        )
    elif re.search(r"howdy", received_message.lower()):
        return build_response("https://www.youtube.com/watch?v=VGF4ibgcHQE")

    return build_response(
        'Command not recognized, input a decimal number (e.g. "0.5", "1", "1.5") to add drinks or "?" to check how many you\'ve had'
    )
