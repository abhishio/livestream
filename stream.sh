#!/bin/bash
MEDIA_HOME="$1"
RTMP_URL="$2"
PLAYLIST_NAME="$3"
RTMP_STREAM="$4"
logfile="$5"

export PATH=$PATH:/opt/ffmpeg/bin

mkdir -p $(dirname "$0")/logs

#RTMP_URL="rtmp://a.rtmp.youtube.com/live2"


STREAM_URL="$RTMP_URL/$RTMP_STREAM"


PLAYLIST_PATH="$MEDIA_HOME/$PLAYLIST_NAME"
MEDIA_PATH="$PLAYLIST_PATH/$MEDIA_NAME"

if [[  -z "$RTMP_URL" && -z "$RTMP_STREAM"  ]]
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
    ffmpeg  -re -i $self_media_path -pix_fmt yuv420p -deinterlace  -vsync 1 -threads 2 -vcodec copy -r 30 -g 60 -sc_threshold 0 -b:v 3000k -bufsize 14600k -maxrate 4600k -preset slow -tune zerolatency -acodec copy -b:a 128k -ac 2 -ar 48000  -f flv $STREAM_URL >> $logfile 2>&1
    
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
