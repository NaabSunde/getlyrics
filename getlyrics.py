from bs4 import BeautifulSoup
import urllib3
import re
import time
import dbus
import unidecode
import os
import sys
from os import system
from os import path

bus = dbus.SessionBus()
url = None
oldUrl = None
cache = '.cache/getlyrics'
http = urllib3.PoolManager() # Something important

# Do whacky stuff to text so the link has a change to work
def urlify(text):

    deUmlaut = unidecode.unidecode(text) # Remove umlauts
    removeRemastered = re.sub("\((.*)| - (.*)", "",deUmlaut) # Remove hopefully unnecessary information from the title
    replaceSlashes = re.sub("/","-",removeRemastered) # Genius wants 'AC/DC' as 'ac-dc' for some reason
    addAnd = re.sub("&","and", replaceSlashes) # Genius wants these as text
    deSpecial = re.sub("[^a-zA-Z0-9- \n]", "", addAnd) # Remove special characters such as dots, brackets, etc
    addLines = re.sub(" ", "-", deSpecial) # Replace spaces with lines
    removeDuplicateLines = re.sub("---|--","-", addLines) # Gets rid of possible duplicate lines
    removeTrailingLine = removeDuplicateLines.rstrip('-') # Gets rid of possible trailing lines
    return removeTrailingLine.lower() + "-lyrics"

# Gets the lyrics from Genius or from the HDD.
def lyrics(url):

    global oldUrl
    condition = True
    filepath = cache + "/" + url.removeprefix("https://www.genius.com/")
    oldUrl = url # Set oldUrl as current url so that we don't reload the same lyrics

    if path.isfile(filepath): # We won't reaload the same lyrics if they're already stored in cache

        print(f"Loaded lyrics from {filepath} \n")
        file = open(filepath)
        contents = file.read()
        print(contents)
        file.close()

    else: # We'll have to load the lyrics if we haven't done it to this particular song yet

        print(f"Loading lyrics from {url} \n")

        while condition: # Sometimes Genius won't load up the page correctly, so we'll load the page as many times as necessary

            if hasSongChanged() == True: # This is my half-ass attempt to load the correct lyrics if the user has changed the song while Genius is acting up 
                
                system('clear')
                url = createUrl()
                oldUrl = url
                print(f"Song has changed, loading lyrics from {url} \n")
                
            page = http.request('GET',url)
            soup = BeautifulSoup (page.data, 'html.parser')
            condition = soup.find("div", {"id": "lyrics"}) is not None
            time.sleep(0.1)

        print(soup.p.get_text()) # Prints the lyrics
        file = open(filepath, "w+") # Makes and opens a file
        file.write(soup.p.get_text()) # Writes the lyrics to the file
        file.close()


# Creates the URL with the help of urlify
def createUrl():

    try:

            spotify_bus = bus.get_object("org.mpris.MediaPlayer2.spotify","/org/mpris/MediaPlayer2") # Connect to local Spotify client
            spotify_properties = dbus.Interface(spotify_bus,"org.freedesktop.DBus.Properties") # Get properties
            metadata = spotify_properties.Get("org.mpris.MediaPlayer2.Player", "Metadata") # Get metadata
            url = "https://www.genius.com/" + urlify(metadata.get('xesam:artist')[0] + " " + metadata.get('xesam:title')) # Create the URL
            sys.stdout.write("\33]0;%s - %s\a" % (metadata.get('xesam:artist')[0], metadata.get('xesam:title'))) # Change the terminal title to 'Artist - Title'

    except dbus.exceptions.DBusException:

        print("Spotify is not running.")
        exit(1)

    return url

# Function to check wheter the song has changed
def hasSongChanged():

    url = createUrl()

    if url != oldUrl:
        
        return True
    
    return False

# Main
def main():

    
    if not os.path.exists(cache): # If cache folder does not exist..
        os.makedirs(cache) # then create it

    try:

        while True:

            if hasSongChanged() == True:

                system('clear')
                lyrics(createUrl())

            time.sleep(1)

    except KeyboardInterrupt:

        pass

if __name__ == "__main__":

    main()