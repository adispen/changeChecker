import boto3
from secrets import aws_region, dynamo_table
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource('dynamodb', region_name=aws_region)

table = dynamodb.Table(dynamo_table)

def getMostRecent():
    scanned = table.scan(
        Select='SPECIFIC_ATTRIBUTES',
        ProjectionExpression='changenumber, mostRecent',
        FilterExpression=Attr('mostRecent').eq(True)
    )

    if not scanned['Items']:
        return None
    else:
        return int(scanned['Items'][0]['changenumber'])

def addMostRecent(newChangeNum):
    oldChangeNum = getMostRecent()
    if oldChangeNum:
        resp = table.update_item(
            Key={
                'changenumber' : oldChangeNum
            },        
            UpdateExpression='SET mostRecent = :mostRecent',
            ExpressionAttributeValues={':mostRecent': False}
        )
    table.put_item(
        Item={
            'changenumber' : newChangeNum,
            'mostRecent' : True
        }        
    )
