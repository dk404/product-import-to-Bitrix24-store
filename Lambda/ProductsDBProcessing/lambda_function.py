import os
import json
import boto3
#Bitrix24 lib - in Layers
from bitrix24 import Bitrix24

domain=os.environ['domain']
key=os.environ['key']
        
bx24 = Bitrix24(domain, user_id=1)

DYNAMODB = boto3.resource('dynamodb','us-east-1')
TABLE = DYNAMODB.Table('B24_products')

calls_add=dict()
calls_update=dict()

def add_b24_product(name, price, file_url, xml_id):
  
  import requests
  import base64
  
  content1=requests.get(file_url).content
  image_64_encode = str(base64.b64encode(content1))[2:-1]
  
  product_data = {
    "fields" : {
      "iblockId": 1,
      "NAME" : name,
      "CURRENCY_ID": "RUB",
      "PRICE" : price,
      "XML_ID":xml_id,
      "PREVIEW_PICTURE": {
        "fileData":dict()
        }
      }
    }
        
  product_data["fields"]["PREVIEW_PICTURE"]["fileData"]['0']="1.png"
  product_data["fields"]["PREVIEW_PICTURE"]["fileData"]['1']=image_64_encode

  return product_data
  
  
def update_b24_product(bitrix_id, name, price, file_url, xml_id):
  
  import requests
  import base64
  import boto3
  
  content1=requests.get(file_url).content
  image_64_encode = str(base64.b64encode(content1))[2:-1]
  
  product_data = {
    "id":bitrix_id,
    "fields" : {
      "iblockId": 1,
      "NAME" : name,
      "CURRENCY_ID": "RUB",
      "PRICE" : price,
      "XML_ID":xml_id,
      "PREVIEW_PICTURE": {
        "fileData":dict()
        }
      }
    }
        
  product_data["fields"]["PREVIEW_PICTURE"]["fileData"]['0']="1.png"
  product_data["fields"]["PREVIEW_PICTURE"]["fileData"]['1']=image_64_encode
  
  return product_data
    
def lambda_handler(event, context):
    # TODO implement
    
    print(event)
    
    calls_add.clear()
    calls_update.clear()

    
    for Record in event["Records"]:
        #print(Record["eventName"])
        #print(Record["dynamodb"]["NewImage"]["bitrix_id"]["N"])
        if Record["eventName"]=="INSERT" and int(Record["dynamodb"]["NewImage"]["bitrix_id"]["N"])==0:
            
            offer=Record["dynamodb"]["NewImage"]
            
            #collect the batch
            product_data=add_b24_product(offer["product_name"]["S"], offer["product_price"]["S"], offer["product_picture"]["S"], offer["id"]["N"])
            
            calls_add[offer["id"]["N"]]={
                          'method': 'crm.product.add',
                          'params': product_data
                      }
            
        if Record["eventName"]=="MODIFY":
          
            offer=Record["dynamodb"]["NewImage"]
            offer_old=Record["dynamodb"]["OldImage"]
            
            #We update the price only if it has changed
            if offer["product_price"]["S"]!=offer_old["product_price"]["S"]:
              
              #collect the batch
              product_data=update_b24_product(offer_old["bitrix_id"]["N"], offer["product_name"]["S"], offer["product_price"]["S"], offer["product_picture"]["S"], offer["id"]["N"])
              
              calls_update[offer["id"]["N"]]={
                          'method': 'crm.product.update',
                          'params': product_data
                      }
                      
            #return bitrix_id to the place
            if int(offer_old["bitrix_id"]["N"])>0 and int(offer["bitrix_id"]["N"])==0:
             TABLE.update_item(
                Key={
                    'id': int(offer["id"]["N"]),
                 },
               UpdateExpression="set bitrix_id = :r",
               ExpressionAttributeValues={
                    ':r': int(offer_old["bitrix_id"]["N"]),
               },
               ReturnValues="UPDATED_NEW"
             )
    
    
    #execute a batch request for all additions
    if len(calls_add)>0:
      
      result = bx24.call_batch_webhook(calls_add, key, True)
      print(result['result']['result'])
      
      #add Bitrix24 product id to the product table
      for Record in event["Records"]:
        if Record["eventName"]=="INSERT" and int(Record["dynamodb"]["NewImage"]["bitrix_id"]["N"])==0:
          offer=Record["dynamodb"]["NewImage"]
          TABLE.update_item(
              Key={
                  'id': int(offer["id"]["N"]),
                },
              UpdateExpression="set bitrix_id = :r",
              ExpressionAttributeValues={
                  ':r': int(result['result']['result'][offer["id"]["N"]]),
              },
              ReturnValues="UPDATED_NEW"
            )
    
    
    #execute a batch request for all updates
    if len(calls_update)>0:
  
      result = bx24.call_batch_webhook(calls_update, key, True)
      print(result['result'])
    
            
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
