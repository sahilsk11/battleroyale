import requests
import pprint

def lambda_handler(event, context):
    headers = {"TRN-Api-Key":"07e80b10-398c-4d66-9078-00fcae0d6b25"}
    #Finds the user in the event
    (url, default) = parse_user(event)
    try:
        #Retrieves the data from the url
        html_response = requests.get(url, headers=headers)
    #If it cannot connect to URL, catch error
    except requests.exceptions.ConnectionError:
        return build_json("There was an error connecting to the tracker.", {"title":"Error", "content":"Could not connect to tracker."})
    try:
        #Convert response object to JSON
        player_data = html_response.json()
    #If it cannot be converted to JSON, there was an error accessing data
    except ValueError:
        return build_json("There was an error retrieving player data.", {"title":"Error", "content":"Could not find player."})
    #pprint.pprint(player_data)
    
    #Parse response
    (mode, individual_stat, shouldEndSession) = parse_request(event) #Returns tuple with (game mode, individual stat = None)
    (response_txt, stat_json) = build_text_response(player_data, mode, individual_stat) #Returns tuple with (response txt, stat json)
    if (default and mode != "start" and mode != "stop" and mode != "help"):
        response_txt = "I think this is who you are looking for. " + response_txt
    card = build_card(mode, stat_json) #Returns dict of card data
    
    return_obj = build_json(response_txt, card, shouldEndSession) #Returns json response
    #pprint.pprint(return_obj)
    return return_obj

#Takes in event and finds the user
#Default to Sahil if no user found
def parse_user(event):
    default = False
    try:
        name = event["request"]["intent"]["slots"]["user"]["resolutions"]["resolutionsPerAuthority"][0]["values"][0]["value"]["name"]
    except KeyError:
        name = "Sahil"
        default = True
    users = {"Sahil":["xbl", "sk11hasil"], "Neeraj":["pc", "lifegood141"], "Ninja":["pc", "ninja"], "Neil":["psn","nileriver41"], "Gautham":["pc","GothmCity2"], "Sushant":["pc", "sooshbag69"], "Rajiv":["pc", "happiiface"]}
    user = users[name]
    url = "https://api.fortnitetracker.com/v1/profile/%s/%s" % (user[0], user[1])
    return (url, default)

#Builds the card dict using player stats
def build_card(mode, player_data):
    if (mode == "start"):
        return {"title":"Welcome!", "content":"How can I help you?"}
    if (mode == "stop"):
        return {"title":"Goodbye!", "content":""}
    if (mode == "help"):
        return {"title":"Example", "content":"\"Tell me how many squad wins I have\"\n \
        \"What is my solo KD?\" \n \"What are my duo stats?\""}
    title = player_data["name"] + " " + mode + " stats:"
    content = "Wins: " + player_data["wins"] +\
             "\nKills: " + player_data["kills"] + "\nMatches: " + player_data["matches"] + "\nKD: " + player_data["kd"]
    return {"title": title, "content":content}

#Builds the text response for the command
#Returns (text, stat_data)
def build_text_response(player_data, mode="solo", individual_stat= None):
    if (mode == "start"):
        return ("Hello! Welcome to the Unofficial Fortnite Battle Royale Tracker. How can I help you?", None)
    if (mode == "stop"):
        return ("See you next time!", None)
    if (mode == "help"):
        return ("I can find your Battle Royale Statistics. You can ask me for your current season stats in solo, duo, and squad game modes.\
         You can say: tell me how many squad wins I have or what is my KD", None)
    
    stat_data = parse_stat_data(player_data, mode)
    
    f_season = "season 4 "
    overall_str = ""
    if (mode == "overall"):
        overall_str = "Overall, "
        f_season = ""
        mode = ""
    
    if (individual_stat == None):
        response = overall_str + stat_data["name"] + " has " + stat_data["wins"] + " " + mode + " " + f_season + "wins, with " + stat_data["kills"] + \
        " kills in " + stat_data["matches"] + " matches with a KD of " + stat_data["kd"]
    else:
        if (individual_stat == "wins"):
            response = stat_data["name"] + " has " + stat_data["wins"] + " " + mode + " wins."
        elif (individual_stat == "kills"):
            response = stat_data["name"] + " has " + stat_data["kills"] + " " + mode + " kills."
        elif (individual_stat == "matches"):
            response = stat_data["name"] + " has played " + stat_data["matches"] + " " + mode + " matches" +  "."
        elif (individual_stat == "KD"):
            response = stat_data["name"] + "'s " + mode + " KD is " + stat_data["kd"] +"."
    return (response, stat_data)


#Parses the complete JSON from TRN and finds statistics
#stats:
    #    p10 is for duos
    #    p2 is for solos
    #    p9 is for squads
    #    cur is for current season
def parse_stat_data(player_data, mode, lifetime=False):
    if (mode == "overall"):
        return get_lifetime_data(player_data)
    
    str = "curr_"
    if (lifetime):
        str = ""
    if (mode == "solo"):
        str = str + "p2"
    elif (mode == "duo"):
        str = str + "p10"
    else:
        str = str + "p9"
        
    name = player_data["epicUserHandle"]
    wins = player_data["stats"][str]["top1"]["value"]
    kd = player_data["stats"][str]["kd"]["value"]
    kills = player_data["stats"][str]["kills"]["value"]
    matches = player_data["stats"][str]["matches"]["value"]
    
    return {"name":name, "wins":wins, "kd":kd, "kills":kills, "matches":matches}

#Finds information for overall statistics because this is stored in different part of JSON file
def get_lifetime_data(player_data):
    name = player_data["epicUserHandle"]
    wins = player_data["lifeTimeStats"][8]["value"]
    kd = player_data["lifeTimeStats"][11]["value"]
    kills = player_data["lifeTimeStats"][10]["value"]
    matches = player_data["lifeTimeStats"][7]["value"]
    
    return {"name":name, "wins":wins, "kd":kd, "kills":kills, "matches":matches}

#Finds the intent
#Returns (mode, stat, shouldEndSession)
def parse_request(event):
    try:
        intent = event["request"]["intent"]["name"]
    except KeyError:
        intent = event["request"]["type"]
    shouldEndSession = True
    if (event["session"]["new"] == False):
        shouldEndSession = False
    
    if (intent == "CustomStatIntent"):
        mode = event["request"]["intent"]["slots"]["type"]["resolutions"]["resolutionsPerAuthority"][0]["values"][0]["value"]["name"]
        stat = event["request"]["intent"]["slots"]["stat"]["resolutions"]["resolutionsPerAuthority"][0]["values"][0]["value"]["name"]
        return (mode, stat, shouldEndSession)
    elif (intent == "SoloIntent"):
        return ("solo", None, shouldEndSession)
    elif (intent == "DuoIntent"):
        return ("duo", None, shouldEndSession)
    elif (intent == "SquadIntent"):
        return ("squad", None, shouldEndSession)
    elif (intent == "LifetimeIntent"):
        return ("overall", None, shouldEndSession)
    elif (intent == "LaunchRequest"):
        return ("start", None, False)
    elif (intent == "AMAZON.StopIntent" or intent == "AMAZON.CancelIntent"):
        return ("stop", None, True)
    elif (intent == "AMAZON.HelpIntent"):
        return ("help", None, shouldEndSession)
    else:
        return None

#Builds the JSON response
def build_json(text, card, shouldEndSession=True):
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": text
            },
            "card": {
                "type": "Simple",
                "title": card["title"],
                "content":card["content"]
            },
            "reprompt": {
                "outputSpeech": {
                    "type": "PlainText"
                }
            },
            "shouldEndSession": shouldEndSession
        },
        "sessionAttributes": {}
    }
    
    
    
    
json = {
    "version": "1.0",
    "session": {
        "new": False,
        "sessionId": "amzn1.echo-api.session.bea591f3-15b7-422d-9583-aefb24e71e8a",
        "application": {
            "applicationId": "amzn1.ask.skill.b82a1943-8fce-4eeb-a37e-a46fdcc5d096"
        },
        "user": {
            "userId": "amzn1.ask.account.AHMLSXSQ6I7UNHGIZLPNMOFUXA47NJTZTPX74F4VQYQ3WRCAIGRPTRVHRGKL5GEUUKOOLFR66XUWMLQHOQCI7SNABQP4F622PMLAOHQWIUQKK4H55OQ4SHIWX2OQN3MS36O3W56VPSHRZMV2ORQ2ILHVGEUYV4XJRMDXNASOV4LBKOMUG33POLE46M3R5QUMWIBDKFC5ASL7TBA"
        }
    },
    "context": {
        "AudioPlayer": {
            "playerActivity": "IDLE"
        },
        "Display": {
            "token": ""
        },
        "System": {
            "application": {
                "applicationId": "amzn1.ask.skill.b82a1943-8fce-4eeb-a37e-a46fdcc5d096"
            },
            "user": {
                "userId": "amzn1.ask.account.AHMLSXSQ6I7UNHGIZLPNMOFUXA47NJTZTPX74F4VQYQ3WRCAIGRPTRVHRGKL5GEUUKOOLFR66XUWMLQHOQCI7SNABQP4F622PMLAOHQWIUQKK4H55OQ4SHIWX2OQN3MS36O3W56VPSHRZMV2ORQ2ILHVGEUYV4XJRMDXNASOV4LBKOMUG33POLE46M3R5QUMWIBDKFC5ASL7TBA"
            },
            "device": {
                "deviceId": "amzn1.ask.device.AHB4ZVSFU7PTORUZXJUXEDHRUMF6XY55ULKYNJ47VKXY67IH7RTXKVHBPRSZ6RE4UE3AZ3SWQQO4RTAXPZGPZHLVS3622E54NCFRPNYV7CH42YOLJIXUMA7KWAHKW4MUC3LUAXAHFRDQ3M5XM7OFMLYPNF6Q",
                "supportedInterfaces": {
                    "AudioPlayer": {},
                    "Display": {
                        "templateVersion": "1.0",
                        "markupVersion": "1.0"
                    }
                }
            },
            "apiEndpoint": "https://api.amazonalexa.com",
            "apiAccessToken": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6IjEifQ.eyJhdWQiOiJodHRwczovL2FwaS5hbWF6b25hbGV4YS5jb20iLCJpc3MiOiJBbGV4YVNraWxsS2l0Iiwic3ViIjoiYW16bjEuYXNrLnNraWxsLmI4MmExOTQzLThmY2UtNGVlYi1hMzdlLWE0NmZkY2M1ZDA5NiIsImV4cCI6MTUyODE2MjkwMSwiaWF0IjoxNTI4MTU5MzAxLCJuYmYiOjE1MjgxNTkzMDEsInByaXZhdGVDbGFpbXMiOnsiY29uc2VudFRva2VuIjpudWxsLCJkZXZpY2VJZCI6ImFtem4xLmFzay5kZXZpY2UuQUhCNFpWU0ZVN1BUT1JVWlhKVVhFREhSVU1GNlhZNTVVTEtZTko0N1ZLWFk2N0lIN1JUWEtWSEJQUlNaNlJFNFVFM0FaM1NXUVFPNFJUQVhQWkdQWkhMVlMzNjIyRTU0TkNGUlBOWVY3Q0g0MllPTEpJWFVNQTdLV0FIS1c0TVVDM0xVQVhBSEZSRFEzTTVYTTdPRk1MWVBORjZRIiwidXNlcklkIjoiYW16bjEuYXNrLmFjY291bnQuQUhNTFNYU1E2STdVTkhHSVpMUE5NT0ZVWEE0N05KVFpUUFg3NEY0VlFZUTNXUkNBSUdSUFRSVkhSR0tMNUdFVVVLT09MRlI2NlhVV01MUUhPUUNJN1NOQUJRUDRGNjIyUE1MQU9IUVdJVVFLSzRINTVPUTRTSElXWDJPUU4zTVMzNk8zVzU2VlBTSFJaTVYyT1JRMklMSFZHRVVZVjRYSlJNRFhOQVNPVjRMQktPTVVHMzNQT0xFNDZNM1I1UVVNV0lCREtGQzVBU0w3VEJBIn19.E6flGTPB_xDFZq39h76d6KSyv4qxnuwd4qT3MH5odCeJQNFV7BfRimmqtSRyRgWfOwdNjcDw4p7HT6CE8H3Um5fp6XBP3l63fG7F1tF9QQBZAx-fST9g0E8gXyz8ByNeXjfPwd93M8AlLEU9664tlDAOnaXk6p4KkxCzu9DTjtjk9kfZKalDhn_fNdIui80dflrCMNTT5QpWbaU8yelLmOv_tWONn838NIiPtx5pYEv3tnDzzSdpvrHMskCEHIpQGKF7WuPDW6V_WAb_x3HseBygFNaX7aeFWodsDhYyoooj0Kq4JAfkz5BGJqEE4c-t8I8_N3S61LVTG2KccwNFFQ"
        }
    },
    "request": {
        "type": "IntentRequest",
        "requestId": "amzn1.echo-api.request.1e45afae-0ac6-4b6d-bfcc-deb66c7a7152",
        "timestamp": "2018-06-05T00:41:41Z",
        "locale": "en-US",
        "intent": {
            "name": "AMAZON.StopIntent",
            "confirmationStatus": "NONE"
        }
    }
}
print(lambda_handler(json, None))


def basic_response(title, resp_str):
    session_attributes = {}
    reprompt_text = None
    speech_output = resp_str
    should_end_session = True
    return build_response(session_attributes, title, speech_output, reprompt_text, should_end_session)
'''
def build_response(session_attributes, title, output, reprompt_text, should_end_session, card_type='Simple', addtl_response={}):
    return_data = {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': output
            },
            'card': {
                'type': card_type,
                'title':  title,
                'content': output
            },
            'reprompt': {
                'outputSpeech': {
                    'type': 'PlainText',
                    'text': reprompt_text
                }
            },
            'shouldEndSession': should_end_session
        }
    }
    
    # Typically use by audio item
    for key, value in addtl_response.items():
        return_data['response'][key] = value
        
    return return_data
    '''