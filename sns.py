import boto3
import json
import secrets


def publish_to_sns(oldNumber, newNumber):
    message = {
        'oldChangeNumber': oldNumber,
        'newChangeNumber': newNumber
    }
    client = boto3.client('sns')
    response = client.publish(
        TopicArn=secrets.sns_topic,
        Message=json.dumps(message)
    )
    return response
