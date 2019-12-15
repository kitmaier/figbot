# decrypt Twitter OAuth keys
import boto3
import os
from base64 import b64decode
ENCRYPTED = {}
ENCRYPTED['OAuth1ConsumerKey'] = os.environ['OAuth1ConsumerKey']
ENCRYPTED['OAuth1ConsumerSecret'] = os.environ['OAuth1ConsumerSecret']
ENCRYPTED['OAuth1AccessToken'] = os.environ['OAuth1AccessToken']
ENCRYPTED['OAuth1TokenSecret'] = os.environ['OAuth1TokenSecret']
DECRYPTED = {}
for key in ENCRYPTED:
    DECRYPTED[key] = (boto3.client('kms').decrypt(CiphertextBlob=b64decode(ENCRYPTED[key]))['Plaintext']).decode('utf-8')


# TODO: make the upload schedule somewhat randomized
# TODO: handle when we get to the end of the book!!!
# TODO: send notification to email address on error

import io
import json
import random
import requests
from requests_oauthlib import OAuth1
import urllib.parse
def lambda_handler(event, context):
    # get current pointer
    s3client = boto3.client('s3')
    bucketName = 'generic-use'
    pointerObjectName = 'finite-infinite-games-bot/pointer.txt'
    with open('/tmp/pointer.txt', 'wb') as f:
        s3client.download_fileobj(bucketName, pointerObjectName, f)
    with open('/tmp/pointer.txt', 'r') as f:
        pointer = int(f.read())
    # pull message from s3
    bookObjectName = 'finite-infinite-games-bot/finite_and_infinite_games_cleaned.txt'
    with open('/tmp/finite_and_infinite_games_cleaned.txt', 'wb') as f:
        s3client.download_fileobj(bucketName, bookObjectName, f)
    with open('/tmp/finite_and_infinite_games_cleaned.txt', 'r') as f:
        lines = f.read().splitlines()
    message = lines[pointer]
    # send message to twitter
    client_key = DECRYPTED['OAuth1ConsumerKey']
    client_secret = DECRYPTED['OAuth1ConsumerSecret']
    resource_owner_key = DECRYPTED['OAuth1AccessToken']
    resource_owner_secret = DECRYPTED['OAuth1TokenSecret']
    headeroauth = OAuth1(client_key, client_secret,
                     resource_owner_key, resource_owner_secret,
                     signature_type='auth_header')
    url = 'https://api.twitter.com/1.1/statuses/update.json?status='+urllib.parse.quote(message)
    response = requests.post(url,auth=headeroauth)
    # increment and store pointer
    pointer += 1
    pointerFile = io.BytesIO(str(pointer).encode('utf-8'))
    s3client.upload_fileobj(pointerFile,bucketName,pointerObjectName)
    return {
        'statusCode': 200,
        'body': json.dumps(response.content.decode('utf-8'))
    }

comment='''
These are the special setup needed to support the Lambda function
    created CloudWatch rule trigger
    created Customer Managed Key
    put Twitter OAuth credentials in Lambda function Environment Variables and encrypted
    gave Lambda function permission to read/write S3
    upload dependencires for requests and requests_oauthlib into lambda function
This is how the cleaned file was created, starting from an OCR of a PDF of the book. 
    Trim beginning and end
    Manually break up all long lines that contain "FINITE AND INFINITE GAMES"
    Remove all lines that contain "FINITE AND INFINITE GAMES"
    Search for numbers, manually remove all that are inappropriate but not by themselves on a line
    Remove all lines that are just a number
    Search for and manually resolve all instances where there are two capital letters in a row
    Write in chapter headers
    Convert all whitespace to single spaces
    Verify there are no special characters [^A-Z .,?:;"'!@(){}_<>~1-9-]
    Manually remove many instances of OCR errors showing as rare punctuation
    Break lines by replacing ([.][^ ]*) * with \1\r\n
    Manually review and fix any broken words with the below python script using pyspellchecker library
        from spellchecker import SpellChecker
        spell = SpellChecker()
        misspelled = spell.unknown(['something', 'is', 'hapenning', 'here'])
        with open('finite_and_infinite_games_cleaned.txt') as file:
            data = file.read().splitlines()
        linenum = 0
        for line in data:
            linenum += 1
            line = line.replace(".","")
            line = line.replace("-"," ")
            line = line.replace("(","")
            line = line.replace(")","")
            line = line.replace("@","")
            line = line.replace("!","")
            line = line.replace("?","")
            line = line.replace('"',"")
            line = line.replace(";","")
            line = line.replace(":","")
            line = line.replace(",","")
            words = line.split(' ')
            misspelled = spell.unknown(words)
            for badword in misspelled:
                print(linenum,badword)
    Search for and resolve instances of Mr. and Dr.
    Search for and resolve instances of [a-z]\.[a-z]
    Search for and resolve instances of ^[a-z] [a-z] 
    Search for and resolve very short lines
    Search for and resolve lines longer than 280 chars
    Combine short lines with this script
        with open('finite_and_infinite_games_cleaned.txt') as file:
            data = file.read().splitlines()
        outline = ""
        for line in data:
            if outline=="":
                outline = line
                continue
            if "Chapter" in outline or "Chapter" in line or "..." in outline or "..." in line or len(outline)+len(line)>200:
                print(outline)
                outline = line
                continue
            outline += " " + line
        if outline!="":
            print(outline)
'''

