from flask import Flask, request, Response, render_template, flash, redirect, url_for
from functools import wraps
import StringIO
import subprocess
from flask import jsonify
import string
from subprocess import call
from random import choice
from string import ascii_lowercase, digits
from time import sleep




app = Flask(__name__)
app.debug=True

YOUTUBE_RTMP="rtmp://a.rtmp.youtube.com/live2"
MEDIA_HOME="/opt/media/files/otts/files"
YT_STREAMKEY = ""
SELECT_PLAYLIST = ""

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'otts' and password == 'MzAxMjk1MjBk'

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def stream_start():
    '''Function to Start Streaming '''
    global YT_STREAMKEY
    global SELECT_PLAYLIST
    YT_STREAMKEY = request.form['yt_streamkey']
    SELECT_PLAYLIST = request.form['select_playlist']
    print(YT_STREAMKEY, SELECT_PLAYLIST)
    def randstr(size=10, chars=ascii_lowercase + digits):
        return ''.join(choice(chars) for _ in range(size))
        
    logstr = randstr()
    try:
        ffmpeg_process = subprocess.Popen(['bash', '-x', './stream.sh', MEDIA_HOME,         SELECT_PLAYLIST, YT_STREAMKEY,  'logs/' + logstr+ ".log"], stdout=subprocess.PIPE )
        msg  =  ffmpeg_process.communicate()[0].splitlines()
        print "Test1"
        return msg
    except subprocess.CalledProcessError as ffmpeg_error:
        print "Test2"
        return ffmpeg_error

        
        
def get_streaming_playlist():
    '''Get streaming Playlist running on the server'''
    cmd = "ps -e -o pid,command | grep -i stream.sh | grep -v grep"
    ps = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    output = [ w.replace('bash -x ./stream.sh /opt/media/files/otts/files', ' ') for w in  ps.communicate()[0].splitlines() ]
    stream_list = []
    for x in output:
        stream_list.append(x.split())
    return stream_list

def get_streaming_video():
    '''Get streaming videos running on the server'''
    cmd = "ps -e -o pid,command | grep -i ffmpeg | grep -v grep"
    ps = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    output = [ w.replace('ffmpeg -re -i /opt/media/files/otts/files/', ' ') for w in  ps.communicate()[0].splitlines()]
    output = [ w.replace('-pix_fmt yuv420p -deinterlace -vsync 1 -threads 2 -vcodec copy -r 30 -g 60 -sc_threshold 0 -b:v 3000k -bufsize 14600k -maxrate 4600k -preset slow -tune zerolatency -acodec copy -b:a 128k -ac 2 -ar 48000 -f flv', ' ') for w in  output ]
    video_stream_list = []
    for x in output:
        video_stream_list.append(x.split())
    return video_stream_list


def kill_process(pid):
    '''Function to kill the Process Playlist/Stream'''
    cmd = "sudo kill -9 " + str(pid)
    ps = subprocess.Popen(cmd,shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    msg = ps.communicate()[0]
    return msg


@app.route('/stream/status')
@requires_auth
def stream_status():
    '''Get Stream Status and Kill Action'''
    stream_list = get_streaming_playlist()
    video_list = get_streaming_video()
    return render_template("stream_status.html", stream_list=stream_list, video_list=video_list)


@app.route('/stream/kill', methods = ['POST'])
@requires_auth
def api_kill_playlist():
    '''Api to kill the Process Playlist/Stream'''
    if request.method == 'POST':
        pid = request.form['pid']
        kill_process(pid)
        return redirect("/stream/status", code=200)


@app.route('/stream/start', methods = ['POST'])
@requires_auth
def api_stream_start():
    '''Api to Start the Stream'''
    if request.method == 'POST':
        msg = stream_start()
        print(msg)
    return redirect("/stream/status", code=200)


@app.route('/')
@requires_auth
def home_page():
    '''Home Page'''
    try:
        playlist_all = subprocess.check_output(['find', MEDIA_HOME, '-mindepth', '1', '-maxdepth', '1', '-type', 'd', '-printf', "%f\n"]).splitlines()
        playlist_valid = []
        for x in playlist_all:
            temp_x = subprocess.check_output(['find', MEDIA_HOME + '/' + x, '-mindepth', '1', '-maxdepth', '1', '-type', 'f', '-printf', "%f\n"]).splitlines()
            if not temp_x:
                pass
            else:
                playlist_valid.append(x)
    except subprocess.CalledProcessError as playlist_error:
        playlist_all = ["No Playlist Found | Upload media on OwnCloud and Refresh"]
    return render_template("index.html", playlist_all = playlist_valid, youtube_rtmp = YOUTUBE_RTMP)


if __name__ == '__main__':
    app.run(host='0.0.0.0')

