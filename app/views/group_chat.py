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

@app.route("/group_chat", methods=['GET', 'POST'])
def group_chat():
	groups = db.groups
	pending_name_queues=db.pending_name_queues
	from_number = request.values.get('From')
	broker= request.values.get('To')
	body=request.values.get('Body')
	group=groups.find_one(
				{"broker":broker}
				)
	pending_names=pending_name_queues.find_one({"broker":broker})['members']
	group_numbers=[x['number'] for x in group['members']]
	if from_number in pending_names:
		pending_name_queue=pending_name_queues.find_one(
				{"broker":broker}
				)
		#remove the user from pending_name_queue
		pending_name_queue['members']=[x for x in pending_name_queue['members'] if x!=from_number]
		pending_name_queues.update(
				{"_id":pending_name_queue['_id']},
				pending_name_queue)
		#add the user's name to the group document
		new_member={
				"name":body.strip(),
				"number":from_number
		}
		group['members'].append(new_member)
		groups.update(
				{"_id":group['_id']},
				group)
		#tell the user they are now part of the group
		client.messages.create( 
					from_=broker,
					to=from_number,
					body="Whatup, %s. Now you're free to message the group." % body.strip()
					)
		resp={
			"status":"success",
			"message":"%s is now in the group" % body
		}
		return json.dumps(resp)

	elif from_number not in group_numbers:
		#update group members
		pending_name_queue=pending_name_queues.find_one(
				{"broker":broker}
				)
		pending_name_queue['members'].append(from_number)
		pending_name_queues.update(
				{"_id":pending_name_queue['_id']},
				pending_name_queue)
		client.messages.create( 
					from_=broker,
					to=from_number,
					body="Welcome to the group, dawg! What's your name?"
					)
		return "New member added: %s" % (from_number)

	else:
		other_members=[x for x in group['members'] if x['number']!=from_number]
		for member in other_members:
			client.messages.create( 
				from_=broker,
				to=member['number'],
				body=body
				)
		resp={
			"source":from_number,
			"destination":other_members,
			"message":body,
			"status":"success"
			}
		print json.dumps(resp)
		return json.dumps(resp)


