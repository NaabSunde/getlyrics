#!/usr/bin/env python   
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
player = None
cache = os.path.expanduser('~/.cache/getlyrics')
http = urllib3.PoolManager() # Something important

# Do whacky stuff to text so the link has a change to work
def urlify(text):

    de_umlaut = unidecode.unidecode(text) # Remove umlauts
    remove_remastered = re.sub("\((.*)| - (.*)", "",de_umlaut) # Remove hopefully unnecessary information from the title
    replace_slashes = re.sub("/","-",remove_remastered) # Genius wants 'AC/DC' as 'ac-dc' for some reason
    add_and = re.sub("&","and", replace_slashes) # Genius wants these as text
    despecial = re.sub("[^a-zA-Z0-9- \n]", "", add_and) # Remove special characters such as dots, brackets, etc
    add_lines = re.sub(" ", "-", despecial) # Replace spaces with lines
    remove_duplicate_lines = re.sub("---|--","-", add_lines) # Gets rid of possible duplicate lines
    remove_trailing_line = remove_duplicate_lines.rstrip('-') # Gets rid of possible trailing lines
    return remove_trailing_line.lower() + "-lyrics"

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

            if has_song_changed() == True: # This is my half-ass attempt to load the correct lyrics if the user has changed the song while Genius is acting up 
                
                system('clear')
                url = create_url()
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
def create_url():

    global player

    try:
            
            player_bus = bus.get_object(player,"/org/mpris/MediaPlayer2") # Connect to local music player
            player_properties = dbus.Interface(player_bus,"org.freedesktop.DBus.Properties") # Get properties
            metadata = player_properties.Get("org.mpris.MediaPlayer2.Player", "Metadata") # Get metadata
            url = "https://www.genius.com/" + urlify(metadata.get('xesam:artist')[0] + " " + metadata.get('xesam:title')) # Create the URL
            sys.stdout.write("\33]0;%s - %s\a" % (metadata.get('xesam:artist')[0], metadata.get('xesam:title'))) # Change the terminal title to 'Artist - Title'

    except dbus.exceptions.DBusException:

        print(f"{player} is not running.")
        exit(1)

    return url

# Function to get all MPRIS players. Returns a list of 
def get_players():

    services = bus.list_names() # Get all services
    players = []

    for i in services:

        if "org.mpris.MediaPlayer2" in i:

            players.append(i) # Create a list of MPRIS-mediaplayers

    return players

# Function to ask the user for the desired player. Writes it to the global variable 'player'
def ask_which_player():

    global player
    user_input = int(-1)
    players = get_players()

    print("Welcome to getlyrics!")
    
    if len(players) == 0:
        
        print("No player is running")
        exit(1)

    for i in range(len(players)):

        print(f"{i}. {players[i]}")

    while (user_input < 0) or (len(players) -1 < user_input ):

        print("Please input the number of the desired player")
        user_input = int(input())

    player = players[user_input]


# Function to check wheter the song has changed
def has_song_changed():

    url = create_url()

    if url != oldUrl:
        
        return True
    
    return False

# Main
def main():

    global player

    if not os.path.exists(cache): # If cache folder does not exist..

        os.makedirs(cache) # then create it

    if(len(sys.argv)) == 1: # If an argument was not given we'll ask from the user

        ask_which_player()

    else:

        x = "org.mpris.MediaPlayer2."+str(sys.argv[1])
        if x in get_players():

            player = x

        else:

            print("Incorrect player given as argument.")
            exit(1)

    try:

        while True:

            if has_song_changed():

                system('clear')
                lyrics(create_url())

            time.sleep(1)

    except KeyboardInterrupt:

        pass

if __name__ == "__main__":

    main()