
# yt_md

yt_md stands for _YouTube Music Downloader_. It is a library for python. It downloads a youtube playlist as mp3 files into a Music folder. It gets the last version of the list and only saves the ones which are on the playlist. Therefore, if a music is removed from the playlist, the music will also be removed from the Music folder.

### Setup

Install the packages in the '_requirements.txt_'. The code will not work without them. You can run the following command in terminal to install them: 

    pip install -r requirements.txt

Also, you'll need a Youtube API key in order to use this library. It is free and easy to get it. For more information, please search it on Google.


### Usage

    import yt_md

    api_key = 'AAAAAzzzzzzz_AAAAAzzzzzzzAAAAAAAzzzzzzz'

    playlist_id = 'PL4fA_8ZlMlYQThfkXDINC5FrmhECFxxSi'

    path = '/Users/@user/Desktop/music'

    dw = yt_md.yt_md(api_key, path, playlist_id)

    dw.download_all()

`dw.download_all()` will check the playlist on youtube, create a 'source.json', and download the musics into a folder called 'music'. If either the 'music' folder or the 'source.json' file are missing, it will automatically create new ones. 

`dw.print_links()` will print downloaded musics' names and links in the terminal.

`dw.set_format(*format='mp3'*)` will set the format of the file. Currently, you can either use **mp3** or **mp4**.

`dw.download_video(*id*)` will download the video mathces the video id.

`dw.download_video_terminal(*id*)` works same as *download_video()*. However, it is safier to use this one. 

If the script is terminated while running, it may not download some musics properly.

_Tested on MacOS Ventura 13.1_