# -*- coding: utf-8 -*-
from __future__ import print_function   # for compatibility with both python 2 and 3

import urllib
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup as soup
from os import listdir
from os.path import isfile, join
import os
import html
from subprocess import call             # for calling mplayer and lame
from sys import argv                    # allows user to specify input and output directories
from pytube import YouTube
import pytube
import subprocess
import ffmpeg

my_url = 'https://open.spotify.com/playlist/37i9dQZF1DX4FcAKI5Nhzq'
youtube = 'https://www.youtube.com/results?search_query='
song_list = []
queue = []
"""
song naming convention: NAME-artist1-artist2-artist3
"""

class Song:

    def __init__(self, title, artist):
        self.title = title
        self.artist = []
        self.artist.extend(artist)

def set_songs_from_file():
    f = open("music_list.txt", "r")
    lines = f.readlines()
    for line in lines:
        foo = line.split('-')
        song = Song(foo[0], foo[1:])
        song_list.append(song)
    f.close()
    
def add_song(song):
    f = open("music_list.txt", "a+")
    artist = ''
    for b in song.artist:
        artist += ','+b
    artist.trim()
    f.write("\n"+ song.title + '-'+ artist)
    f.close
    
def compare_song_list():
    set_songs_from_file()
    files = os.listdir(path)
    
    for name in files:
        foo = line.split(',')
        title,artist = foo[0], foo[1:]
        if not in_song_list(title):
            add_song(title, artist)

def in_song_list(name, art):
    for song in song_list:
        if song.title == name:
            for artist in song.artist:
                if art.lower().trim() == artist.lower().trim():
                    return True
    return False


def spot_scrape(my_url):
    req = Request(my_url)
    web_byte = urlopen(req).read()
    webpage = web_byte.decode('utf-8')
    queue = []

    page_soup = soup(webpage, "html.parser")
    
    table = page_soup.find_all('ol')
    tables = table[0].find_all('li')
    for i in range(len(tables)):
        tab = tables[i].find_all('div', class_='tracklist-col name')
        title = tab[0].div.get_text()
        artists = tab[0].find_all('a')
        lst = []
        lst.append(title)
        for artist in artists:
            artist = artist.get_text()
            artist = html.unescape(artist)
            artist = artist.replace(',','')
            lst.append(artist)
        a = title.find(lst[1])
        if a == 0:
            a = title.find(lst[1], 2)
        title = title[:a]
        for artist in lst:
            if title in artist:
                lst.remove(artist)        
        try:
            song = Song(title,lst)
            queue.append(song)
        except:
            print('name error with song: ' + str(i))
    #for song in queue:
        #print(song.title, song.artist)
    print("Added playlist~")
    return queue

def match_class(target):                                                        
    def do_match(tag):                                                          
        classes = tag.get('class', [])                                          
        return all(c in classes for c in target)                                
    return do_match 

def yt_formatter(soup, song):
    banned = ['dance', 'acoustic', 'remix', 'live']
    title = ''
    time = 0
    try:
        a = str(soup)
        start = a.find("title=")
        title = a[start+7: a.find('>', start) - 1]
        b = a.find('minutes,',start)
        minute = int(a[b-3:b-1].strip())
        c = a.find('second', b)
        second = 0
        if c >= 0: 
            second = int(a[c - 3:c - 1].strip())
        time = minute * 60 + second
        href =  a.find('href')
        start = a.find('\"', href)
        end = a.find('\"', href + 7)
        href = a[start + 1:end]
        if 'watch' not in href:
            raise Exception('I know Python!')
        
        for item in banned:
            if item in title.lower() and item not in song.title:
                raise Exception('I know Python!')
            
    except:
        return 'error', 30000, ''
    
    return title, time, href

def yt_scrape(song):
    url = song.title + ' ' + song.artist[0]
    url = urllib.parse.quote_plus(url)
    url = youtube + url
    req = Request(url)
    web_byte = urlopen(req).read()
    webpage = web_byte.decode('utf-8')
    page_soup = soup(webpage, "html.parser")
    
    yt_links = page_soup.find_all("a", class_ = "yt-uix-tile-link")
    
    candidates = []
    i = 0
    while len(candidates) < 3 and i <7:
        i += 1
        title, time, href = yt_formatter(yt_links[i], song)
        if title != 'error':
            candidates.append([time, title, href])
    #candidates.sort()
    #for candidate in candidates:
    print('Aquired link~')
    return candidates[0][2]

def progress_func(self, stream, chunk, file_handle,bytes_remaining):
    #yt = YouTube(video_link, on_progress_callback=progress_function)    
    size = self.video.filesize
    progress = (float(abs(bytes_remaining-size)/size))*float(100)
    self.loadbar.setValue(progress)

def get_song(link, song):
    name = song.title
    for artist in song.artist:
        name += '-'+artist

    #yt = YouTube("https://www.youtube.com"+link)
    yt = pytube.YouTube("https://www.youtube.com" + link)
    print('Downloading: ' + song.title+ ' ref: '+ link)
    stream = yt.streams.filter(only_audio=True).first()
    stream.download(filename=name)
    

def check_file_exists(directory, filename, extension):
    path = directory + "/" + filename + extension
    return os.path.isfile(path)

def main(indir, outdir):

    try:
        # check specified folders exist
        if not os.path.exists(indir):
            exit("Error: Input directory \'" + indir + "\' does not exist. (try prepending './')")
        if not os.path.exists(outdir):
            exit("Error: Output directory \'" + outdir + "\' does not exist.")
        if not os.access(outdir, os.W_OK):
            exit("Error: Output directory \'" + outdir + "\' is not writeable.")

        print("[{0}/*.mp4] --> [{1}/*.mp3]".format(indir, outdir))
        files = [] # files for exporting
            
        # get a list of all convertible files in the input directory
        filelist = [ f for f in os.listdir(indir) if f.endswith(".mp4") ]
        for path in filelist:
            basename = os.path.basename(path) 
            filename = os.path.splitext(basename)[0]
            files.append(filename)
        # remove files that have already been outputted from the list
        files[:] = [f for f in files if not check_file_exists(outdir, f, ".mp3")]
    except OSError as e:
        exit(e)
    if len(files) == 0:
        return
        #exit("Could not find any files to convert that have not already been converted.")
    try:
        # convert all unconverted files
        for filename in files:
            print("-- converting {0}/{2}.mp4 to {1}/{2}.mp3 --".format(indir, outdir, filename))
            directory =os.getcwd()
            #filename = filename.replace(' ', '_')
            print("ffmpeg -i " + filename+".mp4" + " " + filename+".mp3")
            
            os.system("ffmpeg -i " + filename+".mp4" + " " + filename+".wav")
            
            #call(["mplayer", "-novideo", "-nocorrect-pts", "-ao", "pcm:waveheader", indir + "/" + filename + ".mp4"])
            #call(["lame", "-v", "audiodump.wav", outdir + "/" + filename + ".mp3"])
            #os.remove(filename+".mp4")
            #print('removed ' + filename + '.mp4')
    except:
        return

# set the default directories and try to get input directories
args = [".", "."]
#for i in range(1, min(len(argv), 3)):
    #args[i - 1] = argv[i]

# if only input directory is set, make the output directory the same
if len(argv) == 2:
    args[1] = args[0]

def convert_files():
    main(args[0], args[1])

def convert_video(video_input):
    cmds = ['ffmpeg', '-i', video_input+".mp4", video_input+".mp3"]
    subprocess.Popen(cmds)

def add_playlist(my_url):
    queue = spot_scrape(my_url)
    for song in queue:
        try:
            link = yt_scrape(song)
            get_song(link, song)
            add_song(song)
            convert_files()
        except:
            print(song.title)
    convert_files()
set_songs_from_file()
