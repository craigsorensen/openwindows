import http.client, urllib

def send(token, user, message):
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
      urllib.parse.urlencode({
        "token": token,
        "user": user,
        "message": message,
      }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()

