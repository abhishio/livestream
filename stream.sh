#!/bin/bash
MEDIA_HOME="$1"
PLAYLIST_NAME="$2"
YOUTUBE_STREAMKEY="$3"
MEDIA_NAME=""
logfile="$4"

export PATH=$PATH:/opt/ffmpeg/bin

mkdir -p $(dirname "$0")/

YOUTUBE_RTMP="rtmp://a.rtmp.youtube.com/live2"


YOUTUBE_STREAM="$YOUTUBE_RTMP/$YOUTUBE_STREAMKEY"


PLAYLIST_PATH="$MEDIA_HOME/$PLAYLIST_NAME"
MEDIA_PATH="$PLAYLIST_PATH/$MEDIA_NAME"

if [[  -z "$YOUTUBE_RTMP" && -z "$YOUTUBE_STREAMKEY"  ]]
then
    echo "ERROR: Stream settings is empty!" 
    exit 1
fi

if [[   ! -d "$PLAYLIST_PATH"     ]]
then
        echo "ERROR: Playlist Dont exits on server!"   
        exit 1
fi


PLAYLIST_MENU="$(find "$PLAYLIST_PATH" -mindepth 1 -maxdepth 1 -type f -printf '%f\n')"


if [[  -z "$PLAYLIST_MENU" ]]
then
    echo "ERROR: Playlist is empty!"  
    exit 1
else
    echo "Available Media in $PLAYLIST_NAME"   
    for temp_x in $PLAYLIST_MENU
    do  
        echo "$temp_x"   
    done
fi


stream_media() {
    self_media_path="$1"
    ffmpeg  -re -i $self_media_path -pix_fmt yuv420p -deinterlace  -vsync 1 -threads 2 -vcodec copy -r 30 -g 60 -sc_threshold 0 -b:v 3000k -bufsize 14600k -maxrate 4600k -preset slow -tune zerolatency -acodec copy -b:a 128k -ac 2 -ar 48000  -f flv $YOUTUBE_STREAM > $logfile 2>&1
    cat $logfile
    
}


stream_playlist() {
       
    for self_media in $PLAYLIST_MENU
    do
        echo "**** Streaming media: $self_media ****"    
        stream_media "$PLAYLIST_PATH/$self_media"
    done
}

if [[ -z $MEDIA_NAME ]]
then
    
    stream_playlist
else
    if [[   ! -f "$MEDIA_PATH"     ]]
    then
            echo "ERROR: Media Dont exits on server"   
            exit 1
    fi
    echo "Streaming Media $MEDIA_NAME from Playlist $PLAYLIST_NAME" 
    stream_media "$MEDIA_PATH"
fi