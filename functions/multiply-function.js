'use strict'

const AWS = require('aws-sdk')
const DB = require('./database-functions.js');
var dynamoDb = new AWS.DynamoDB.DocumentClient()

function generateResponse (code, payload) {
  console.log(payload)
  return {
    statusCode: code,
    body: JSON.stringify(payload)
  }
}

function generateError (code, err) {
  console.error(err)
  return generateResponse(code, {
    message: err.message
  })
}

module.exports.handler = (event) => {
  var body = JSON.stringify(event.Records[0].body)
  var number = parseInt(body.substring(body.indexOf("number") + 11, body.indexOf("isBase64Encoded") - 6))
  var requestId = body.substr(body.indexOf("requestId") + 14, 36).replace(/['"]+/g, '')

  //Just a simple operation to show its working
  var resultant = String(number * 2.5)
  const params = {
    TableName: process.env.tableName,
    Item: {
      requestId: requestId,
      timestamp: Date.now(),
      resultant: resultant
    }
  }

  try {
    dynamoDb.put(params, function(err, data) {
      if (err) {
          console.error("Unable to dynamoDb.put. Error JSON:", JSON.stringify(err, null, 2));
      } else {
          console.log("dynamoDb.put succeeded:", JSON.stringify(data, null, 2));
      }
    })

    // We only return acknowledgement response
    return generateResponse(202, {
      message: 'Response wrote to dynamo',
      data: params
    })
  } catch (err) {
    console.log(err)
    return generateError(500, new Error('Error in multiplication function'))
  }
}
