import sys, os, base64, datetime, hashlib, hmac, time
import requests # pip install requests

# Hold our JSON payload to be use with our request
json_payload = ""
if len(sys.argv) < 2:
        print("Please pass JSON input file!")
        exit(1)
json_file = open(str(sys.argv[1]), "r")
json_payload = json_file.read()

# Our IAM creds
access_key = ''
secret_key = ''
# API Key
api_key = ''

# ADJUST
NL = '\n'
service = 'execute-api'
region = 'us-east-1'
domain = '.execute-api.us-east-1.amazonaws.com'
host = domain
content_type = 'text/plain'
amz_target = ''
# Custom HTTP headers
extra_header_001_key = 'x-test-key123'
extra_header_001_val = 'test-value1234'

query_parameters=''
payload = json_payload
resource_uri = 'dev/inbound' #no / at the begining

# http://docs.aws.amazon.com/general/latest/gr/signature-v4-examples.html#signature-v4-examples-python
def sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

def getSignatureKey(key, date_stamp, regionName, serviceName):
    kDate = sign(('AWS4' + key).encode('utf-8'), date_stamp)
    kRegion = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, 'aws4_request')
    return kSigning


def postCall():
    # The Url, payload, headers etc that we want to call in AWS API Gateway
    method = 'POST' # Also change the POST method at the end of the file accordingly

    # The endpoint url we want to call
    endpoint_url = 'https://' + domain + '/' + resource_uri + '?' + query_parameters

    # Create a date for headers and the credential string
    # Date w/o time, used in credential scope
    t = datetime.datetime.utcnow()
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = t.strftime('%Y%m%d')

    # CREATE A CANONICAL REQUEST
    # http://docs.aws.amazon.com/general/latest/gr/sigv4-create-canonical-request.html
    # Step 1 is to define the verb (GET, POST, etc.) --already done.
    # Step 2: Create canonical URI string (use '/' if no path) --the part of the URI from domain to query
    # Step 3: Create the canonical query string.
    # Step 4: Create the canonical headers.
    # Step 5: Create the list of signed headers.
    # Step 6: Create payload hash.
    # Step 7: Combine elements to create canonical request
    canonical_uri = '/' + resource_uri
    canonical_querystring = query_parameters
    canonical_headers =  'content-type:' + content_type + NL + 'host:' + host + NL + 'x-amz-date:' + amz_date + NL +  'x-amz-target:' + amz_target + NL
    signed_headers = 'content-type;host;x-amz-date;x-amz-target'
    payload_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()
    canonical_request = method + NL + canonical_uri + NL + canonical_querystring + NL + canonical_headers + NL + signed_headers + NL + payload_hash

    # CREATE THE STRING TO SIGN AND CALCULATE THE SIGNATURE
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = date_stamp + '/' + region + '/' + service + '/' + 'aws4_request'
    string_to_sign = algorithm + NL +  amz_date + NL +  credential_scope + NL +  hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
    signing_key = getSignatureKey(secret_key, date_stamp, region, service)
    signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()

    # ADD SIGNING INFORMATION TO THE REQUEST
    authorization_header = algorithm + ' ' + 'Credential=' + access_key + '/' + credential_scope + ', ' +  'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature

    headers = {'Content-Type':content_type,
               'X-Amz-Date':amz_date,
               'Authorization':authorization_header,
               'x-api-key': api_key,
               extra_header_001_key: extra_header_001_val
               }

    # Send the request
    r = requests.post(endpoint_url, data=payload, headers=headers)
    print(r.text)
    print(r.headers['x-amzn-RequestId'])
    return r.headers['x-amzn-RequestId']



def getCall(returnedRequestId):
    method = 'GET'
    resource_uri = 'dev/response/' + returnedRequestId #no / at the begining
    query_parameters=''
    payload = ""

    endpoint_url = 'https://' + domain + '/' + resource_uri + '?' + query_parameters
    t = datetime.datetime.utcnow()
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = t.strftime('%Y%m%d')

    canonical_uri = '/' + resource_uri
    canonical_querystring = query_parameters
    canonical_headers =  'content-type:' + content_type + NL + 'host:' + host + NL + 'x-amz-date:' + amz_date + NL +  'x-amz-target:' + amz_target + NL
    signed_headers = 'content-type;host;x-amz-date;x-amz-target'
    payload_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()
    canonical_request = method + NL + canonical_uri + NL + canonical_querystring + NL + canonical_headers + NL + signed_headers + NL + payload_hash

    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = date_stamp + '/' + region + '/' + service + '/' + 'aws4_request'
    string_to_sign = algorithm + NL +  amz_date + NL +  credential_scope + NL +  hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
    signing_key = getSignatureKey(secret_key, date_stamp, region, service)
    signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()

    authorization_header = algorithm + ' ' + 'Credential=' + access_key + '/' + credential_scope + ', ' +  'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature

    headers = {'Content-Type':content_type,
               'X-Amz-Date':amz_date,
               'Authorization':authorization_header,
               'x-api-key': api_key,
               extra_header_001_key: extra_header_001_val
               }

    r = requests.get(endpoint_url, data=payload, headers=headers)
    print(r.text)


requestIreturnedFromPost = postCall()
time.sleep (3)
query_parameters=''
payload = ""
getCall(requestIreturnedFromPost)
