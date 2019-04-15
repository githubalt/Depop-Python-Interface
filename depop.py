import requests
import bs4
import json
import datetime

#---[AWS Hashing]---#
import hashlib
import hmac
import base64

def make_digest(message, key):
    key = bytes(key, 'UTF-8')
    message = bytes(message, 'UTF-8')
    digester = hmac.new(key, message, hashlib.sha1)
    signature1 = digester.digest()
    signature2 = base64.urlsafe_b64encode(signature1)
    return str(signature2, 'UTF-8').replace("-", "+").replace("_", "/")

def generate_auth_s3(req_json, date):
    StringtoSign = ""
    StringtoSign += "PUT\n\n"
    StringtoSign += "image/jpeg\n"
    StringtoSign += date + "\n"
    StringtoSign += "x-amz-security-token:" + req_json["aws_credentials"]["session_token"] + "\n"
    StringtoSign += "/garage-pictures-0/" + req_json["aws_key"]
    auth = make_digest(StringtoSign, req_json["aws_credentials"]["secret_access_key"])
    return auth

def generate_uuid(): #device_id
    x = requests.get("https://www.uuidgenerator.net/version4")
    soup = bs4.BeautifulSoup(x.content, "lxml")
    return soup.find("span",{"id":"generated-uuid"}).text

#---[AWS Hashing]---#

#---[Globals]---#
DEPOP_CONFIG = open("info.cfg").read().split(":")
DEPOP_USERNAME = DEPOP_CONFIG[0]
DEPOP_PASSWORD = DEPOP_CONFIG[1]

IPHONE_CLIENT_SECRECT = ""
IPHONE_CLIENT_ID = ""
IPHONE_DEVICE_ID = generate_uuid()

API_URL = "https://api.depop.com"
USER_AGENT = "Depop 2.36.2 rv:23220 (iPhone; iOS 12.1.2; en_US)"
STANDARD_HEADERS = {
    "accept":"application/json",
    "content-type":"application/json",
    "accept-language":"en-US",
    "x-garage-bundle-id":"com.garageitaly.garage",
    "user-agent":USER_AGENT
}

session = requests.Session()
session.headers.update(STANDARD_HEADERS)
#---[Globals]---#

def login(username, password):
    data = {
        "client_secret": IPHONE_CLIENT_SECRECT,
        "idfv": IPHONE_DEVICE_ID,
        "grant_type": "password",
        "username": str(username),
        "password": str(password),
        "client_id": IPHONE_CLIENT_ID
    }
    lgn = session.post(API_URL + "/oauth2/access_token", json=data)
    session.headers.update({"authorization": "Bearer " + lgn.json()["access_token"]})
    return lgn

def generate_photo_s3():
    data = {
        "extension":"jpg",
        "picture_type":"P0"
    }
    return session.post(API_URL + "/api/v1/pictures/", json=data)

def post_picture(photo_s3, photo_name):
    req_json = photo_s3.json()

    date = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S EST")
    auth = generate_auth_s3(req_json, date)

    headers = {
        "Authorization": "AWS " + req_json["aws_credentials"]["access_key_id"] + ":" + auth,
        "x-amz-security-token":req_json["aws_credentials"]["session_token"],
        "User-Agent":"aws-sdk-iOS/1.7.1 iOS/12.1.2 en_US",
        "Content-Type":"image/jpeg",
        "Date": date
    }

    x = requests.put("http://garage-pictures-0.s3.amazonaws.com/" + req_json["aws_key"], headers=headers, data=open(photo_name, "rb"))
    return x
    
def post_item(pictures, price, description, categories, brand_id):
    db_pictures = []
    for item in pictures:
        req_json = item.json()
        db_pictures.append("/api/v1/pictures/"+ req_json["id"]  +"/")
    
    sample = {
        "variants": {
            "8": 1
        },
        "shipping_methods": None,
        "address": "",
        "categories": categories,
        "place_data": {
            "geometry": {
                "location": {
                    "lat": 0,
                    "lng": 0
                }
            },
            "formatted_address": "",
            "address_components": [{
                "short_name": "",
                "long_name": "",
                "types": ["country", "political"]
            }]
        },
        "brand_id": brand_id,
        "price_currency": "INR",
        "hand_delivery": False,
        "variant_set": 54,
        "national_shipping_cost": "1",
        "video_ids": None,
        "shippable": True,
        "description": description,
        "selling_mode": "CLASSIC",
        "international_shipping_cost": None,
        "share_on_tw": False,
        "pictures": db_pictures,
        "purchase_via_paypal": True,
        "price_amount": str(price)
    }
    
    x = session.post(API_URL + "/api/v1/products/", json=sample)

    return x

"""
def get_followers_list():
"""
