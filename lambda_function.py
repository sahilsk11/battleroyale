import requests
import pprint

def lambda_handler(event, context):
    headers = {"TRN-Api-Key":"07e80b10-398c-4d66-9078-00fcae0d6b25"}
    #Finds the user in the event
    url = parse_user(event)
    if (url == "e0"):
        #User not found in event
        return error_message("e0")
    try:
        #Retrieves the data from the url
        html_response = requests.get(url, headers=headers)
    #If it cannot connect to URL, catch error
    except requests.exceptions.ConnectionError:
        return error_message("e1")
    try:
        #Convert response object to JSON
        player_data = html_response.json()
    #If it cannot be converted to JSON, there was an error accessing data
    except ValueError:
        return error_message("e2")
    
    #Parse response
    (mode, individual_stat, shouldEndSession) = parse_request(event) #Returns tuple with (game mode, individual stat = None, shouldEndSession)
    (response_txt, stat_json) = build_text_response(player_data, mode, individual_stat) #Returns tuple with (response txt, stat json)
    card = build_card(mode, stat_json) #Returns dict of card data
    
    return_obj = build_json(response_txt, card, shouldEndSession) #Returns json response
    #pprint.pprint(return_obj)
    return return_obj

#Takes in event and finds the user
#Default to Sahil if no user found
def parse_user(event):
    try:
        name = event["session"]["user"]["accessToken"]
    except KeyError:
        return "e0"
    user = decodeToken(name)
    url = "https://api.fortnitetracker.com/v1/profile/%s/%s" % (name[0], name[1])
    return url

def decodeToken(access_token):
    return access_token.split("#")

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
        response = overall_str + stat_data["name"] + " has " + stat_data["wins"] + " " + mode + " "\
         + f_season + "wins, with " + stat_data["kills"] + \
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
    
def error_message(message):
    if (message == "e0"):
        return build_json("There was a problem finding the current user. Please check the Alexa app and make sure your Epic Games account is linked.",
                   {"title":"Error", "content":"Please link account."})
    elif (message == "e1"):
        return build_json("There was an error connecting to the tracker.", {"title":"Error", "content":"Could not connect to tracker."})
    elif (message == "e2"):
        return build_json("There was an error retrieving player data.", {"title":"Error", "content":"Could not find player."})
    
    
json = {
    "version": "1.0",
    "session": {
        "new": True,
        "sessionId": "amzn1.echo-api.session.68301eed-e484-404e-b37f-451489eac054",
        "application": {
            "applicationId": "amzn1.ask.skill.b82a1943-8fce-4eeb-a37e-a46fdcc5d096"
        },
        "user": {
            "userId": "amzn1.ask.account.AE7BGIK65L2D4YEN4GHWSLVXQ3CPKCMYJYALAN3WNZHEETTTDBGQNIUMKROIVLG43SXUWJJIZQJFOQH3HLT6URCQVYW54PI67BK6K5FFBPMKAVQJFT56GQSLQXAMM32HNTO7W6CQHY6ZIT6HD4NVAODMDVHFLAGQRI2D6WG2RHCXP65LMCCICUAQMNS4HSQIWSE6LPMRANVP4YY",
            "accessToken": "xblsk11hasil"
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
                "userId": "amzn1.ask.account.AE7BGIK65L2D4YEN4GHWSLVXQ3CPKCMYJYALAN3WNZHEETTTDBGQNIUMKROIVLG43SXUWJJIZQJFOQH3HLT6URCQVYW54PI67BK6K5FFBPMKAVQJFT56GQSLQXAMM32HNTO7W6CQHY6ZIT6HD4NVAODMDVHFLAGQRI2D6WG2RHCXP65LMCCICUAQMNS4HSQIWSE6LPMRANVP4YY",
                "accessToken": "xblsk11hasil"
            },
            "device": {
                "deviceId": "amzn1.ask.device.AGCT3RPEP5EFTXTD7E37RYZ6VDMQMJFY3LE2XSTF6FIZIEOBNH5EQG2ZCQP6ZCUZDWURVTK5WNXNDG7UD6CHOROVY5D3I5NNFDFRWV2ESAJD2EURGAZC4C5VKZ65GIWV6WIZSGMPAEAHBDQVQMG57RMC7JOQ",
                "supportedInterfaces": {
                    "AudioPlayer": {},
                    "Display": {
                        "templateVersion": "1.0",
                        "markupVersion": "1.0"
                    }
                }
            },
            "apiEndpoint": "https://api.amazonalexa.com",
            "apiAccessToken": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6IjEifQ.eyJhdWQiOiJodHRwczovL2FwaS5hbWF6b25hbGV4YS5jb20iLCJpc3MiOiJBbGV4YVNraWxsS2l0Iiwic3ViIjoiYW16bjEuYXNrLnNraWxsLmI4MmExOTQzLThmY2UtNGVlYi1hMzdlLWE0NmZkY2M1ZDA5NiIsImV4cCI6MTUyODI2NDU2MSwiaWF0IjoxNTI4MjYwOTYxLCJuYmYiOjE1MjgyNjA5NjEsInByaXZhdGVDbGFpbXMiOnsiY29uc2VudFRva2VuIjpudWxsLCJkZXZpY2VJZCI6ImFtem4xLmFzay5kZXZpY2UuQUdDVDNSUEVQNUVGVFhURDdFMzdSWVo2VkRNUU1KRlkzTEUyWFNURjZGSVpJRU9CTkg1RVFHMlpDUVA2WkNVWkRXVVJWVEs1V05YTkRHN1VENkNIT1JPVlk1RDNJNU5ORkRGUldWMkVTQUpEMkVVUkdBWkM0QzVWS1o2NUdJV1Y2V0laU0dNUEFFQUhCRFFWUU1HNTdSTUM3Sk9RIiwidXNlcklkIjoiYW16bjEuYXNrLmFjY291bnQuQUU3QkdJSzY1TDJENFlFTjRHSFdTTFZYUTNDUEtDTVlKWUFMQU4zV05aSEVFVFRUREJHUU5JVU1LUk9JVkxHNDNTWFVXSkpJWlFKRk9RSDNITFQ2VVJDUVZZVzU0UEk2N0JLNks1RkZCUE1LQVZRSkZUNTZHUVNMUVhBTU0zMkhOVE83VzZDUUhZNlpJVDZIRDROVkFPRE1EVkhGTEFHUVJJMkQ2V0cyUkhDWFA2NUxNQ0NJQ1VBUU1OUzRIU1FJV1NFNkxQTVJBTlZQNFlZIn19.Ac9J5Q3C5Do0cEXIyd5kTXsv8jPbN1e8iP3D6D6EVyVd6AhCU99RUSRPScA13G0YAgyqwUui0UD7AgAsWgjTPKgBkmLxC7dCZkCIKZJL9GgA8gj9G4gLtlGOpRbptnfS5Cbq3HeVn_lyj_a7ixj7XVRu1kXPQGSgstiXXVZXgyaZ0no6FynvZ2lyi9BtvjL5ESenFdlrB40FXBKPmcfZul7HpH9iYwFnDXAmtGVIoKtAqFtqPSKfI46i3FR52r_IK_AbATCPSge6CnOyiVbtwPH97KwZmQgSMx_sKJVjg5uNu74IwxY9nUTyMfXJtxT-SjWnL0eobxOGegGgiTudXA"
        }
    },
    "request": {
        "type": "IntentRequest",
        "requestId": "amzn1.echo-api.request.3cfbe518-1b3c-4eef-b5b9-bd8d99c68b0e",
        "timestamp": "2018-06-06T04:56:01Z",
        "locale": "en-US",
        "intent": {
            "name": "AMAZON.FallbackIntent",
            "confirmationStatus": "NONE"
        }
    }
}
print(lambda_handler(json, None))