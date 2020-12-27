from bs4 import BeautifulSoup
import urllib3
import re
import time
import dbus
import unidecode
from os import system

bus = dbus.SessionBus()
url = None
oldUrl = None
http = urllib3.PoolManager() # Something important

# Do whacky stuff to text so the link has a change to work
def urlify(text):

    deUmlaut = unidecode.unidecode(text) # Remove umlauts
    removeRemastered = re.sub("\((.*)| - (.*)", "",deUmlaut) # Remove hopefully unnecessary information from the title
    addAnd = re.sub("&","and", removeRemastered) # Genius wants these as text
    deSpecial = re.sub("[^a-zA-Z0-9 \n]", '', addAnd) # Remove special characters such as dots, brackets, etc
    addLines = re.sub(" ", "-", deSpecial) # Replace spaces with lines
    removeDuplicateLines = re.sub("--","-", addLines) # Gets rid of possible duplicate lines
    removeTrailingLine = removeDuplicateLines.rstrip('-') # Gets rid of possible trailing lines

    return removeTrailingLine + "-lyrics"

# Gets the lyrics from Genius
def lyrics(url):

    global oldUrl
    condition = True
    print(url) # Prints the URL for the user

    while condition: # Sometimes Genius won't load up the page correctly, so we'll load the page as many times as necessary

        page = http.request('GET',url)
        soup = BeautifulSoup (page.data, 'html.parser')
        condition = soup.find("div", {"id": "lyrics"}) is not None
        time.sleep(0.1)

    print(soup.p.get_text()) # Prints the lyrics
    oldUrl = url # Set oldUrl as current url so that we don't reload the same lyrics


# Creates the URL with the help of urlify
def createUrl():

    try:

            spotify_bus = bus.get_object("org.mpris.MediaPlayer2.spotify","/org/mpris/MediaPlayer2") # Connect to local Spotify client
            spotify_properties = dbus.Interface(spotify_bus,"org.freedesktop.DBus.Properties") # Get properties
            metadata = spotify_properties.Get("org.mpris.MediaPlayer2.Player", "Metadata") # Get metadata
            url = "https://genius.com/" + urlify(metadata.get('xesam:artist')[0] + " " + metadata.get('xesam:title')) # Create the URL

    except dbus.exceptions.DBusException:

        print("Spotify is not running.")
        exit(1)

    return url

# Main
def main():

    try:

        while True:

            url = createUrl()

            if url != oldUrl:

                system('clear')
                lyrics(url)

            time.sleep(1)

    except KeyboardInterrupt:

        pass

if __name__ == "__main__":

    main()