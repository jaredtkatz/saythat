from flask import Flask, request, redirect, session
from app import app
import twilio.twiml
from twilio.rest import TwilioRestClient
import json, datetime 
from bson.json_util import dumps
from pymongo import MongoClient


MONGO_URL=app.config['MONGO_URL']

account = app.config['TWILIO_ACC']
token = app.config['TWILIO_TOKEN']
client = TwilioRestClient(account, token)
# The session object makes use of a secret key.
SECRET_KEY = 'a secret key'

mongo_client = MongoClient()
mongo_client = MongoClient(MONGO_URL)
db = mongo_client.saythat


# parties = {
# 	"A":{
# 		"number":"+16107169757",
# 		"name":"Rafic"
# 		},
# 	"B":{
# 		"number":"+14843432432",
# 		"name":"Jared"
# 		}
# 	}


@app.route("/create_pair", methods=['POST'])
def create_pair():
	collection = db.pairs

	user_name = request.values.get('user_name')
	user_number = request.values.get('user_number')
	recipient_name= request.values.get('recipient_name')
	recipient_number= request.values.get('recipient_number')

	pair={
		"user":{
			"name":"%s" % (user_name),
			"number":"%s" % (user_number)
			},
		"recipient":{
			"name":"%s" % (recipient_name),
			"number":"%s" % (recipient_number)
			},
		"broker":"+14843263461",
		"date":str(datetime.datetime.utcnow())
	}
	resp_pair=pair.copy()
	objectId=collection.insert(pair)

	resp={
		"status":"success",
		"pair":resp_pair,
		"objectId":objectId
	}
	return dumps(resp)



@app.route("/", methods=['GET', 'POST'])
def chat():
	"""relays chat message between two parties"""
	collection = db.pairs
	from_number = request.values.get('From')
	broker= request.values.get('To')
	body=request.values.get('Body')

	parties=collection.find_one(
				{"$or":
					[{"broker":broker,"user.number":from_number},
					{"broker":broker,"recipient.number":from_number}]})
	if not parties:
		message="Sorry, I think you have the wrong number"
		resp = twilio.twiml.Response()
		resp.sms(message)
		return str(resp)

	if from_number==parties['user']['number']:
		source=parties['user']
		dest=parties['recipient']
	elif from_number==parties['recipient']['number']:
		source=parties['recipient']
		dest=parties['user']
	else:
		message="Sorry, I think you have the wrong number"
		resp = twilio.twiml.Response()
		resp.sms(message)
		return str(resp)

	source_name = source['name']
	with open('dialogue.txt','a') as f:
		f.write(source_name+'\n')
		f.write(body.encode('utf8')+'\n')
		f.write('\n')

#forwards incoming message to destination 
	client.messages.create( 
		from_=broker,
		to=dest['number'],
		body=body
		)
	resp={
		"source":source,
		"destination":dest,
		"message":body,
		"status":"success"
	}
	print json.dumps(resp)
	return json.dumps(resp)




