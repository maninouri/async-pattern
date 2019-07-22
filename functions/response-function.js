'use strict';

const AWS = require('aws-sdk'); // eslint-disable-line import/no-extraneous-dependencies
const dynamoDb = new AWS.DynamoDB.DocumentClient()

module.exports.handler = async (event, context) => {
  if (!("pathParameters" in event) || !(event.pathParameters)) {
    return {
      statusCode: 404,
      error: `No pathParameters`
    };
  }
  if (!(event.pathParameters.requestId)) {
    return {
      statusCode: 404,
      error: `No requestId in Query String: ${JSON.stringify(event.pathParameters)}`
    };
  }

  var requestId = event.pathParameters.requestId
  const params = {
    TableName: process.env.tableName,
    KeyConditionExpression: "#requestId = :requestId",
        ExpressionAttributeNames:{
            "#requestId": "requestId"
        },
        ExpressionAttributeValues: {
            ":requestId":requestId
        }
    };

  try {
    const data = await dynamoDb.query(params).promise();
    console.log(`GetResponse data=${JSON.stringify(data.Items)}`);
    return { statusCode: 200, body: JSON.stringify(data.Items) };
  } catch (error) {
    console.log(`GetResponse ERROR=${error.stack}`);
    return {
      statusCode: 400,
      error: `Could not query messages with requestId ${event.pathParameters.requestId}: ${error.stack}`
    };
  }
};
