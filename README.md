<img src="https://www.dropbox.com/s/bzks0d314giwg70/Decoupled%20Invocation.png>

# Asynchronous Decoupled Invocation Pattern
### Design considerations and Priorities:
1) Asynchronous Messaging and Topology
2) Near realtime communication

### High-Level Objectives:
Proof of concept project to the ability of asynchronously fan-out multiple message types received from a secured APIGateway, routed through an SNS Topic and using SQS Queues for better error handling and protect against spikes in loads, along with a set of Dead Letter Queues to protect SLA.

For the Write Journey and Fan Out pattern, Lambda, SNS topics, and SQS queues have been used to invoke the worker lambdas.

For the Read Journey Lambda and DynamoDB and has been used to communicate results back to the Client asynchronously.

### Explanation
- The `inbound` and `response` function are the only exposed functions `post` and `get` respectively, which are hooked up to API Gateway.
- `inbound` takes the following format input and `number` parameter.
```
    { "operation" : "division", "number": 1000 }
  OR
    { "operation" : "multiplication", "number": 1000 }
```

- The Dispatcher lambda validates the input and dispatches all the messages on an SNS Topic for fanning out, and sends an acknowledgment back to caller including the APIGateway `requestId` with response code `202`.

- An associated SQS with each operation type is subscribed to SNS via SNS MessageFilter Policy, to consume only destined payload with operation type: 1)`division` or 2)`multiplication`.

- SNS MessageFilter Subscription policy saves cost and performance of downstream lambdas from unnecessary invocation

- SQS queues protect the downstream system from getting over overloaded and spiked, also against temporary outages

- If either of the worker lambdas fail 3 times, the dead letter queue topic will receive the message for further action (to be defined and configured as per requirement).

- Each worker lambda receives the message from each SQS and processes the request and records the result in DynamoDB, using the `requestId` included in the message, assigned by APIGateway

- Client, upon receiving the acknowledgement response from `post` method, will invoke the `get response` method by including the `requestId` as a parameter in the request headers

- Client will continue polling in a set interval until the result of the call is retrieved.  The timestamp returned from acknowledgment response could be used to avoid polling indefinitely and to enforce the SLA.

### Preparing the environment:
#### Install Node.js in one of the following 2 ways:
```
brew install node
```
OR
```
curl "https://nodejs.org/dist/latest/node-${VERSION:-$(wget -qO  https://nodejs.org/dist/latest/ | sed -nE 's|.*>node-(.*)\.pkg</a>.*|\1|p')}.pkg" > "$HOME/Downloads/node-latest.pkg" && sudo installer -store -pkg "$HOME/Downloads/node-latest.pkg" -target "/"
```

#### Install the following packages:
```
  npm install npm@latest -g
  npm install serverless-pseudo-parameters
```
#### Configure serverless AWS credentials:
```
serverless config credentials --provider aws --key AKIAIOSFODNN7EXAMPLE --secret wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

#### Deploy the stack to AWS via:
execute `serverless deploy`

#### Install Amazon AWS Command Line CLI
```
curl "https://s3.amazonaws.com/aws-cli/awscli-bundle.zip" -o "awscli-bundle.zip"
unzip awscli-bundle.zip
sudo ./awscli-bundle/install -i /usr/local/aws -b /usr/local/bin/aws
```

#### Configure your AWS CLI
It is needed to configure SNS MessagaFilter and subscription policy
```
$ aws configure
AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
Default region name [None]: us-west-2
Default output format [None]: json
```

#### Configure SNS Subscription MessageFilter
Update the region, accountId, service name, env, topic name, and ARN before executing, for each of the queues. See the following sample:
```
aws sns set-subscription-attributes --region {$region} --subscription-arn arn:aws:sns:{$region}:{$accountId}:{$serviceName}-{$env}-calculate-sns-topic:{$topicArn} --attribute-name FilterPolicy --attribute-value '{"operation": ["multiplication"]}'
aws sns set-subscription-attributes --region us-east-1 --subscription-arn arn:aws:sns:us-east-1:361066465741:async-invocation-dev-calculate-sns-topic:ffa6c9bf-af67-4564-951e-6fcc47044f35 --attribute-name FilterPolicy --attribute-value '{"operation": ["multiplication"]}'
aws sns set-subscription-attributes --region {$region} --subscription-arn arn:aws:sns:{$region}:{$accountId}:{$serviceName}-{$env}-calculate-sns-topic:{$topicArn} --attribute-name FilterPolicy --attribute-value '{"operation": ["division"]}'
aws sns set-subscription-attributes --region us-east-1 --subscription-arn arn:aws:sns:us-east-1:361066465741:async-invocation-dev-calculate-sns-topic:ffa6c9bf-af67-4564-951e-6fcc47044f35 --attribute-name FilterPolicy --attribute-value '{"operation": ["division"]}'
```


### Security
The 2 exposed endpoints ideally, as per the diagram will be protected via Client getting authenticated via Amazon Cognito, and retrieving the temporary token, which gets verified for access level at APIGateway to invoke any API.

For the purpose of this POC and simplicity, API Keys is used to secure exposed http services. However, all necessary security stack `cognito-identity-pool` and `cognito-user-pool` is configured and created.

Define APIAccess Key in AWS and assign it to the functions of this interface through the following steps:
  1. Login to AWS console and under APIGateway create an API Keys
  2. Create usage plan to prevent malicious attacks or usage
  3. Associate the usage plan to the generated API Key
  4. Copy the created API Key as it will be used by the Client in the next step

### Configure the Client
Edit the `\client\client.py` and update the following parameter:
This section of the code for security purposes will be emailed as git is a public repository.
```
# Our IAM creds
access_key = ''
secret_key = ''

# API Key
api_key = ''
```
There is a vanilla test payload created for each of the operations: `divideTest.json` and `multiplyTest.json`.  For additional test scenarios, create new test files or modify these files.

### Execution
The `\client\client.py` as input receives the test file name and returns the result.
Example:
```
python client.py divideTest.json
python client.py multiplyTest.json
```

# Design Pros and Cons:
## Approach 1 (Implemented)
### Request: APIGatway -> Lambda -> SNS -> SQS -> Lambda -> DynamoDB
### Response: APIGateway -> Lambda -> DynamoDb
As there is an obvious need of a message broker here.  There are multiple ways of designing and implementing it.  The choice of stack used in this pattern is SNS Topic to fan out asynchronously and to leverage SQS queues to add another decoupled layer of buffer and protection against unexpected spikes and loads or if the lambda workers temporarily become unavailable.

DeadLetterQueus are used to catch 3 repeated invocation of lambdas.

#### Message Broker: SNS
    3 attempts, then DLQ
    SNS Pushes Message to Queues
##### Advantages:
- Maximizes system throughput
- As close to realtime as possible
- 1 Invocation per published message
- Errors in-result of short bursts over max throughput resolved with retries
- Protects against reaching lambda limits reached on concurrent executions in a region
- Protects against exceeding throttling limits
##### Disadvantages:
- Unit of order for messages is not guaranteed
- SQS does not guarantee QoS of Exactly-Once, will make the best attempt, but not guaranteed
- Higher cost for high usage compare to Kinesis

### NOTE:
As noted above, we need to be aware of the fact, due to shared network space and infrastructure, there is no guaranty with respect to unit of order, as this is a sacrifice made to achieve maximum throughput and stay as close as possible to the realtime SLA.

In the following alternative design, we explore the pros and cons of Kinesis as Message Broker.

## Approach 2
### Request: APIGateway -> Kinesis -> Lambda -> DynamoDB
### Response: APIGateway -> Lambda -> DynamoDb
In this approach, the only difference is the replacement of SNS and SQS instances with Kinesis streams, which has some pros and some cons.  The biggest upsides of Kinesis as the choice of our stream is managing Unit of Order, but it comes at the cost of operating on shards basis.  This means there are some complexities in error handling.  Kinesis makes it easier to handle downstream errors by providing 7 days of retention and also it retries the entire failed shard.  In asynchronous communication, there is no rollback, so partial errors might cause retrying lots of messages which were successful, leading to slower throughput and higher latency.  Kinesis does not natively support Dead Letter Queues. There are ways of getting the poison message out.  However, that will require additional SQS queues and retry mechanisms which again brings us back to the 1st square, what is the priority? High throughput or message ordering and retention for a longer period.

#### Message Broker: Kinesis
  Lambda polls Kinesis records for up to 5 times/sec
##### Advantages:
- Records are received in batches
- Unit of Order could be maintained
- If an error occurs, the same batch of records will keep being retried
- Downstream outage or bursts are handled better than SNS due to retention
- 7 days data retention of streams (Do we need it?)
- Lower cost with high usage compare to SNS
- A lot more customizable for different subscribers
##### Disadvantages:
- More complex partial failures, due to retry of the whole batch
- Lack of support for DLQ
- In cases of error, could increase the latency of the system lead to missed realtime SLA

### NOTE:
We should also acknowledge there are other ways of achieving Message Broker and Fan Out pattern, such as using DynamoDB streams instead of Kinesis, or simply using Lambda and write custom code.  Each pattern has to be thoroughly examined based on the requirements and priorities.
