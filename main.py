'''Main Function'''
from functools import wraps
from random import choice
from subprocess import Popen, CalledProcessError, PIPE, STDOUT, check_output
from string import ascii_lowercase, digits
from flask import Flask, request, Response, render_template, redirect


MAIN_APP = Flask(__name__)
MAIN_APP.debug = True

#YOUTUBE_RTMP = "rtmp://a.rtmp.youtube.com/live2"
RTMP_LIST = ["rtmp://a.rtmp.youtube.com/live2", "rtmp://live-api-s.facebook.com:80/rtmp"]
MEDIA_HOME = "/opt/media/files/otts/files"

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'otts' and password == 'MzAxMjk1MjBk'

def authenticate():
    """Sends a 401 response that enables basic auth"""
    msg_1 = "Could not verify access.\n" + "You have to login with proper"
    msg_2 = {'WWW-Authenticate': 'Basic realm="Login Required"'}
    return Response(msg_1, 401, msg_2)

def requires_auth(req_auth):
    '''Checks Authenctication'''
    @wraps(req_auth)
    def decorated(*args, **kwargs):
        '''Decorator Function for Authentication'''
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return req_auth(*args, **kwargs)
    return decorated

def stream_start():
    '''Function to Start Streaming '''
    print request.form
    yt_rtmp = request.form['yt_rtmp']
    yt_streamkey = request.form['yt_streamkey']
    select_playlist = request.form['select_playlist']
    def randstr(size=10, chars=ascii_lowercase + digits):
        '''Random String for logfiles'''
        return ''.join(choice(chars) for _ in range(size))

    logstr = randstr()
    try:
        cmd = "bash -x ./stream.sh " + " " + MEDIA_HOME + " " + yt_rtmp + " " + select_playlist + " " + yt_streamkey + " " + " logs/" + logstr+ ".log"
        print "Stream Cmd: " + cmd
        Popen(['bash', '-x', './stream.sh', MEDIA_HOME, yt_rtmp, select_playlist, yt_streamkey, 'logs/' + logstr+ ".log"], close_fds=True, stdout=PIPE, stderr=STDOUT)
        return "Stream Started"
    except  CalledProcessError as ffmpeg_error:
        return ffmpeg_error


def get_streaming_playlist():
    '''Get streaming Playlist running on the server'''
    cmd = "ps -e -o pid,command | grep -i stream.sh | grep -v grep"
    ps_out = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT)
    ps_out = [w.replace('bash -x ./stream.sh /opt/media/files/otts/files', ' ') for w in  ps_out.communicate()[0].splitlines()]
    stream_list = []
    for temp_x in ps_out:
        stream_list.append(temp_x.split())
    print stream_list
    return stream_list

def get_streaming_video():
    '''Get streaming videos running on the server'''
    cmd = "ps -e -o pid,command | grep -i ffmpeg | grep -v grep"
    ps_out = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT)
    ps_out = [w.replace('ffmpeg -re -i /opt/media/files/otts/files/', ' ') for w in  ps_out.communicate()[0].splitlines()]
    ps_out = [w.replace('-pix_fmt yuv420p -deinterlace -vsync 1 -threads 2 -vcodec copy -r 30 -g 60 -sc_threshold 0 -b:v 3000k -bufsize 14600k -maxrate 4600k -preset slow -tune zerolatency -acodec copy -b:a 128k -ac 2 -ar 48000 -f flv', ' ') for w in  ps_out]
    video_stream_list = []
    for temp_x in ps_out:
        video_stream_list.append(temp_x.split())
    return video_stream_list


def stop_process(pid):
    '''Function to stop the Process Playlist/Stream'''
    cmd = "sudo kill -9 " + str(pid)
    ps_out = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT)
    return ps_out.communicate()[0].splitlines()


@MAIN_APP.route('/stream/status')
@requires_auth
def stream_status():
    '''Get Stream Status and stop Action'''
    stream_list = get_streaming_playlist()
    video_list = get_streaming_video()
    return render_template("stream_status.html", stream_list=stream_list, video_list=video_list)


@MAIN_APP.route('/stream/stop', methods=['POST'])
@requires_auth
def api_stop_playlist():
    '''Api to stop the Process Playlist/Stream'''
    if request.method == 'POST':
        pid = request.form['pid']
        stop_process(pid)
        return redirect("/stream/status", code=200)


@MAIN_APP.route('/stream/start', methods=['POST'])
@requires_auth
def api_stream_start():
    '''Api to Start the Stream'''
    if request.method == 'POST':
        stream_start()
    return redirect("/stream/status", code=200)


@MAIN_APP.route('/')
@requires_auth
def home_page():
    '''Home Page'''
    try:
        playlist_all = check_output(['find', MEDIA_HOME, '-mindepth', '1', '-maxdepth', '1', '-type', 'd', '-printf', "%f\n"]).splitlines()
        playlist_valid = []
        for list_x in playlist_all:
            temp_x = check_output(['find', MEDIA_HOME + '/' + list_x, '-mindepth', '1', '-maxdepth', '1', '-type', 'f', '-printf', "%f\n"]).splitlines()
            if not temp_x:
                pass
            else:
                playlist_valid.append(list_x)
    except  CalledProcessError as playlist_error:
        print playlist_error
    return render_template("index.html", playlist_all=playlist_valid, rtmp_list=RTMP_LIST)


if __name__ == '__main__':
    MAIN_APP.run(host='0.0.0.0')
