'use strict'

const AWS = require('aws-sdk')
const sns = new AWS.SNS({ region: 'us-east-1' })
const DB = require('./database-functions.js');

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

async function publishSnsTopic (data) {
  console.log(">>>>>> data=" + JSON.stringify(data))
  const body = JSON.parse(data.body)

  const params = {
    Message: JSON.stringify(data),
    MessageAttributes: {
      'operation': {
        DataType: 'String',
        StringValue: body.operation // "multiply" or "divide"
      }
    },
    TopicArn: process.env.snsTopicArn
  }

  console.log(">>>>>> param=" + JSON.stringify(params))
  return sns.publish(params).promise().then(result => console.log("Success", result))
}

module.exports.handler = async (event) => {
  const data = JSON.parse(event.body)
  if (typeof data.number !== 'number') {
    return generateError(400, new Error('Invalid number.'))
  }

  try {
    const snsResponseMetadata = await publishSnsTopic(event)

    // We only return acknowledgement response
    return generateResponse(202, {
      message: 'Request published to SNS',
      data: snsResponseMetadata
    })
  } catch (err) {
    console.log(err)
    return generateError(500, new Error('Couldn\'t  add the calculation due an internal error. Please try again later.'))
  }
}
