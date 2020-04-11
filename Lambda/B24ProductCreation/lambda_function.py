import json
import requests
from urllib.parse import parse_qs
import base64
import os

def http_build_query(params, topkey = ''):
  from urllib.parse import quote
 
  if len(params) == 0:
    return ""
 
  result = ""
 
  # is a dictionary?
  if type (params) is dict:
    for key in params.keys():
      newkey = quote (key)
      if topkey != '':
        newkey = topkey + quote('[' + key + ']')
 
      if type(params[key]) is dict:
        result += http_build_query (params[key], newkey)
 
      elif type(params[key]) is list:
        i = 0
        for val in params[key]:
          result += newkey + quote('[' + str(i) + ']') + "=" + quote(str(val)) + "&"
          i = i + 1
 
      # boolean should have special treatment as well
      elif type(params[key]) is bool:
        result += newkey + "=" + quote (str(int(params[key]))) + "&"
 
      # assume string (integers and floats work well)
      else:
        result += newkey + "=" + quote (str(params[key])) + "&"
 
  # remove the last '&'
  if (result) and (topkey == '') and (result[-1] == '&'):
    result = result[:-1]
 
  return result

def add_b24_product(key, name, price, file_url):
  
  import requests
  import base64
  
  content1=requests.get(file_url).content
  print(len(content1))
  print('\n')
  image_64_encode = str(base64.b64encode(content1))[2:-1]
  
  print(len(image_64_encode))
  print('\n')

  product_data = {
    "fields" : {
      "iblockId": 1,
      "NAME" : name,
      "CURRENCY_ID": "RUB",
      "PRICE" : price,
      "PREVIEW_PICTURE": {
        "fileData":dict()
        }
      }
    }
        
  product_data["fields"]["PREVIEW_PICTURE"]["fileData"]['0']="1.png"
  product_data["fields"]["PREVIEW_PICTURE"]["fileData"]['1']=image_64_encode

  response = requests.post(key+"crm.product.add",http_build_query(product_data))
  result=response.json()
  
  return result      
  
  
def lambda_handler(event, context):
    

        url=os.environ['TestUrl']
        key=os.environ['B24key']
        
        result=add_b24_product(key,'Test',300,url)
        
        print(result)
        
        return {
            'statusCode': 200,
            'body': json.dumps('Hello from Lambda!')
        }

