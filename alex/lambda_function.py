import urllib2
import json
import boto3
from boto3.dynamodb.conditions import Key, Attr


# from sklearn import cross_validation as cv


def lambda_handler(event, context):
    if (event["session"]["application"]["applicationId"] !=
            "amzn1.ask.skill.000bcc87-aba1-414d-aeec-cc40b1e7f245"):
        raise ValueError("Invalid Application ID")

    if event["session"]["new"]:
        on_session_started({"requestId": event["request"]["requestId"]}, event["session"])

    if event["request"]["type"] == "LaunchRequest":
        return on_launch(event["request"], event["session"])
    elif event["request"]["type"] == "IntentRequest":
        return on_intent(event["request"], event["session"])
    elif event["request"]["type"] == "SessionEndedRequest":
        return on_session_ended(event["request"], event["session"])


def on_session_started(session_started_request, session):
    print
    "Starting new session."


def on_launch(launch_request, session):
    return get_welcome_response()


def on_intent(intent_request, session):
    intent = intent_request["intent"]
    intent_name = intent_request["intent"]["name"]

    if intent_name == "getFunc":
        return get_Func()
    elif intent_name == "getID":
        return get_ID(intent)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    print
    "Ending session."
    # Cleanup goes here...


def handle_session_end_request():
    card_title = "movie - Thanks"
    speech_output = "Thank you for using the movie skill.  See you next time!"
    should_end_session = True

    return build_response({}, build_speechlet_response(card_title, speech_output, None, should_end_session))


def get_welcome_response():
    session_attributes = {}
    card_title = "movie"
    speech_output = "Welcome to the movie recommendation system. " \
                    "what can I do for you?"
    reprompt_text = "Welcome to the movie recommendation system. " \
                    "what can I do for you?"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def get_Func():
    session_attributes = {}
    card_title = "movie Status"
    reprompt_text = ""
    should_end_session = False

    speech_output = "Ok cool. Please tell me your ID and how many movies do you want"

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def get_ID(intent):
    session_attributes = {}
    card_title = "movie recommend"
    speech_output = ""
    reprompt_text = ""
    should_end_session = False

    id_num = int(intent["slots"]["ID"]["value"])
    amount = int(intent["slots"]["Amount"]["value"])

    # corner case
    if id_num <= 0 or amount <= 0:
        speech_output = "Sorry, but both id number and amount number should be large than 0, please try again"
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('movie')
    # another corner case
    status = int(table.query(KeyConditionExpression=Key('userID').eq(id_num))['Count'])
    if status == 0:
        speech_output = "Thanks for using, but Sorry, I can't find your record in the database, please visit our website firstly"
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))

        # get movies
    response = table.get_item(
        Key={
            'userID': id_num,
        }
    )
    movies = response['Item']['movies']

    if amount > 10:
        speech_output = "Thanks for using, but Sorry, you could just get 10 movies at most from echo, please visit our website for more.  "
        amount = min(10, len(movies))
    if amount == 1:
        speech_output = speech_output + " I would like to recommend you. " + movies[0] + ". Enjoy yourself"
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))

    speech_output = speech_output + " I would like to recommend you the following movies. "

    count = 1
    for m in movies:
        if count == amount and amount != 1:
            speech_output = speech_output + " and "
        speech_output = speech_output + getOrder(count) + m
        count += 1
        if count == amount + 1:
            speech_output += ". That's it.  "
            break

    reprompt_text = ""
    speech_output = speech_output + ". Enjoy yourself"
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        "outputSpeech": {
            "type": "PlainText",
            "text": output
        },
        "card": {
            "type": "Simple",
            "title": title,
            "content": output
        },
        "reprompt": {
            "outputSpeech": {
                "type": "PlainText",
                "text": reprompt_text
            }
        },
        "shouldEndSession": should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        "version": "1.0",
        "sessionAttributes": session_attributes,
        "response": speechlet_response
    }


def getOrder(order):
    dict = {
        1: " the first one is ",
        2: " the second one is",
        3: " the third one is ",
        4: " the fourth one is ",
        5: " the fifth one is ",
        6: " the sixth one is ",
        7: " the seventh one is ",
        8: " the eighth one is ",
        9: " the ninth one is ",
        10: " the tenth one is ",
    }
    return dict[order]






