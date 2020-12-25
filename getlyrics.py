from bs4 import BeautifulSoup
import urllib3
import re
import time
import dbus
import unidecode
from os import system, name

bus = dbus.SessionBus()
url = None
oldUrl = None
http = urllib3.PoolManager() # Something something

# Do whacky stuff to text so the link has a change to work
def urlify(text):

    deUmlaut = unidecode.unidecode(text) # Remove umlauts
    addAnd = deUmlaut.replace("&","and") # Genius wants these as text
    deSpecial = re.sub("[^a-zA-Z0-9 \n]", '', addAnd) # Remove special characters such as dots, brackets, etc
    addLines = deSpecial.replace(" ", "-") # Replace spaces with lines
    removeDuplicateLines = addLines.replace("--","-") # Gets rid of possible duplicate lines
    removeTrailingLine = removeDuplicateLines.rstrip('-') # Gets rid of possible trailing lines

    return removeTrailingLine

# Define clear function 
def clear(): 
  
    # For Windows 
    if name == 'nt': 
        _ = system('cls') 
  
    # For Mac and Linux(here, os.name is 'posix') 
    else: 
        _ = system('clear') 

# Gets the lyrics from Genius
def lyrics(url):

    global oldUrl
    condition = True

    while condition: # Sometimes Genius won't load up the page correctly, so we'll load the page as many times as necessary
        page = http.request('GET',url)
        soup = BeautifulSoup (page.data, 'html.parser')
        condition = soup.find("div", {"id": "lyrics"}) is not None
        time.sleep(0.5)

    print(page._request_url) # Prints the URL for the user
    print(soup.p.get_text()) # Prints the lyrics
    oldUrl = url # Set oldUrl as new url so that we don't reload the same lyrics


# Creates the URL with the help of urlify
def createUrl():

    try:

            spotify_bus = bus.get_object("org.mpris.MediaPlayer2.spotify","/org/mpris/MediaPlayer2")
            spotify_properties = dbus.Interface(spotify_bus,"org.freedesktop.DBus.Properties")
            metadata = spotify_properties.Get("org.mpris.MediaPlayer2.Player", "Metadata")

            url = "https://www.genius.com/" + urlify(metadata.get('xesam:artist')[0]) + "-" + urlify(metadata.get('xesam:title')) + "-lyrics"
            

    except dbus.exceptions.DBusException:
        print("Spotify is not running.")
    return url

# Main
def main():
    while True:
        url = createUrl()
        if url != oldUrl:
            clear()
            lyrics(url)
        time.sleep(1)

if __name__ == "__main__":
    main()


