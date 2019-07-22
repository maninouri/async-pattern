'use strict'

const AWS = require('aws-sdk')
var dynamoDb = new AWS.DynamoDB.DocumentClient()

function PutItem(params) {
  dynamoDb.put(params, function(err, data) {
      if (err) {
          console.error("Unable to PutItem item. Error JSON:", JSON.stringify(err, null, 2));
      } else {
          console.log("PutItem succeeded:", JSON.stringify(data, null, 2));
      }
  })
}

module.exports = {
  PutItem,
};
