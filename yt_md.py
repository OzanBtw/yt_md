import json
import requests as r
import os
import shutil
from tqdm import tqdm
import yt_dlp
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error
from mutagen.easyid3 import EasyID3

class loggerOutputs:
    def error(msg):
        pass
        #print("Captured Error: "+msg)

    def warning(msg):
        pass
        #print("Captured Warning: "+msg)

    def debug(msg):
        pass
        #print("Captured Log: "+msg)


class yt_md():  # youtube music download
    def __init__(self, api_key: str, playlist_id: str, path: str, print_ = True, debug = False):
        self.music_path = f'{path}/music'
        self.cache_path = f'{path}/_cache'
        self.path = path
        self.api_key = api_key
        self.playlist_id = playlist_id
        self.print_ = print_
        self.debug = debug
        self.cache_channel_name = 'Unknown Artist'

        self.check_source()

    def printt(self, message):
       if self.print_:
          print(message)

    def get_artist(self, url):
      site = r.get(url)
      text = site.text

      start = ['{"simpleText":"ARTIST"},"defaultMetadata":{"simpleText":"', '{"simpleText":"ARTIST"},"defaultMetadata":{"runs":[{"text":"']
      end = ['"}','",']

      for i in range(2):
        cache_text = text[text.find(start[i])+len(start[i]):text.find(end[i], text.find(start[i])+len(start[i]))]

        if len(cache_text) > 65:
          continue
          
        else:
          return str(cache_text)

      return str(self.cache_channel_name)

    def download_video_and_get_title(self, url):
        ydl_opts = {
            'logger': loggerOutputs,
            'format': 'bestaudio/best',
            'outtmpl': f'{self.cache_path}/cache.%(ext)s',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3'}]
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # Download the video and extract its info
                video_info = ydl.extract_info(url, download=True)
                self.cache_channel_name = video_info['channel']
                return True
            except:
                return False

    # Sorting source file
    def sort_source(self):
        with open(f'{self.path}/source.json', 'r') as f:
            dic = json.load(f)

            cache1 = sorted(dic['video_name'])
            cache2 = [x for _, x in sorted(
                zip(dic['video_name'], dic['video_link']))]

            dic['video_name'] = cache1
            dic['video_link'] = cache2

        with open(f'{self.path}/source.json', 'w') as f:
            json.dump(dic, f, indent=2)

    def change_title(self, title):
        return title.replace('/', '-')
        return title.replace('é', 'e')

    def download_and_set_image(self, thumbnail, path, url):
        cover_path = f'{self.cache_path}/image_cache.png'

        try:
            link = r.get(thumbnail['standard']['url'])
        except:
            try:
                link = r.get(thumbnail['high']['url'])
            except:
                link = r.get(thumbnail['default']['url'])

        with open(cover_path, 'wb') as f:
            f.write(link.content)
        
        audio_path = path

        audio = EasyID3(audio_path)
        audio['artist'] = self.get_artist(url)
        audio.save()

        audio = MP3(audio_path, ID3=ID3)

        try:
            audio.add_tags()
        except error:
            pass

        audio.tags.add(APIC(mime='image/jpeg', type=3,
                       desc=u'Cover', data=open(cover_path, 'rb').read()))
        
        audio.save()

    def get_video_info(self):
      #get videos
      videos = []
      info = r.get(f'https://www.googleapis.com/youtube/v3/playlistItems?playlistId={self.playlist_id}&key={self.api_key}&fields=nextPageToken,pageInfo,items(snippet(title,resourceId,thumbnails))&part=snippet&maxResults=50').json()
      if 'error' in info.keys():
         raise ValueError("Invalid id for playlist! Please make sure you entered the correct id number.")
      videos.extend([[x['snippet']['title'], x['snippet']['resourceId']['videoId'], x['snippet']['thumbnails']] for x in info['items']])

      if 'nextPageToken' in info.keys():
          info_nextPageToken = info["nextPageToken"]
          # Getting video more
          while True:
            info = r.get(f'https://www.googleapis.com/youtube/v3/playlistItems?playlistId={self.playlist_id}&key={self.api_key}&pageToken={info_nextPageToken}&fields=nextPageToken,pageInfo,items(snippet(title,resourceId,thumbnails))&part=snippet&maxResults=50').json()
            videos.extend([[x['snippet']['title'], x['snippet']['resourceId']['videoId'], x['snippet']['thumbnails']] for x in info['items']])
            if 'nextPageToken' not in info.keys():
              break
            else:
              info_nextPageToken = info["nextPageToken"]
          self.videos = videos
      else:
         self.videos = videos

    def check_source(self):
      if os.path.isdir(self.music_path) == False:
        os.mkdir(self.music_path)

      if os.path.isdir(self.cache_path) == False:
        os.mkdir(self.cache_path)

      if os.path.exists(f'{self.path}/source.json') == False:
        cache = {"video_name": [],
                "video_link": []}

        self.printt('Creating Json File')
        with open(f'{self.path}/source.json', 'w') as f:
          json.dump(cache, f, indent=2)

    def get_new_videos(self):
        with open(f'{self.path}/source.json', 'r') as f:
            dic = json.load(f)

        return  [x for x in self.videos if x[0] not in dic['video_name']]

    def check_missing_videos(self):
      files = [x[:-4] for x in os.listdir(self.music_path)]
      videos_names = [x[0] for x in self.videos]

      missing = []

      for video in videos_names:
        if self.change_title(video) not in files:
          missing.append(video)

      if len(missing) > 0:
        required_videos = [x for x in self.videos if x[0] in missing]

        return required_videos

      return []

    def remove_unlisted(self, videos):
      with open(f'{self.path}/source.json', 'r') as f:
        dic = json.load(f)

      # Removing Musics

      videos_names = [x[0] for x in videos]
      deleted = []

      for video in dic['video_name']:
        if video not in videos_names:
          deleted.append(video)

          cache = f"{self.change_title(video)}.mp3"
          try:
            os.remove(f"{self.music_path}/{cache}")
          except:
            pass

          index = dic['video_name'].index(video)
          dic['video_name'].remove(video)
          dic['video_link'].remove(f"{dic['video_link'][index]}")


          with open(f'{self.path}/source.json', 'w') as f:
            json.dump(dic, f, indent=2)

      if len(deleted) > 0:
        self.printt(f"The following musics are removed from the folder \nbecause they are no longer a part of the list:")

        for i in range(len(deleted)):
          text = f"\t* {deleted[i]}"
          self.printt(text)

    def download_listed(self, videos):
      with open(f'{self.path}/source.json', 'r') as f:
        dic = json.load(f)

      # Adding Musics
      self.printt('\nAdding & Fixing...')

      unadded_videos = []
      unadded_video_links = []


      videos.extend([x for x in self.check_missing_videos() if x not in videos])

      if self.print_:
        bar = tqdm(total=len(videos),position=0, unit='video', leave=False, ascii=" ▖▘▝▗▚▞█")

      for video in videos:
        if self.print_:
          bar.set_postfix({'Downloading': video[0]})
          bar.refresh()

        title = video[0]
        cache_url = f'https://youtube.com/watch?v={video[1]}'

        if self.download_video_and_get_title(cache_url) == False:
          unadded_videos.append(title)
          unadded_video_links.append(cache_url)
          continue

        self.download_and_set_image(video[2], f"{self.cache_path}/cache.mp3", cache_url)

        title = self.change_title(title)

        shutil.move(f"{self.cache_path}/cache.mp3", f"{self.music_path}/{title}.mp3")

        if video[0] not in dic['video_name']:
          dic['video_name'].append(video[0])
          dic['video_link'].append(cache_url)

        with open(f'{self.path}/source.json', 'w') as f:
          json.dump(dic, f, indent=2)

        if self.print_:
          bar.update(1)

      if self.print_:
        bar.close()

      if len(unadded_videos) > 0:
        self.printt("\n--------------\n")
        self.printt(f"There are videos that could not be download with the given url... \nPlease find a different video for each of them and add them to the playlist on YouTube:\n")

        for i in range(len(unadded_videos)):
          text = f"\t* {unadded_videos[i]} => {unadded_video_links[i]}"
          self.printt(text)
      # ------


    def download_all(self):
        self.check_source()
        self.get_video_info() # gets self.video

        with open(f'{self.path}/source.json', 'r') as f:
          dic = json.load(f)

        self.printt(f"There are {len(dic['video_name'])} music links in the source file!")
        self.printt("--------------")

        self.remove_unlisted(self.videos)

        self.download_listed(self.get_new_videos())

        with open(f'{self.path}/source.json', 'r') as f:
          dic = json.load(f)

        self.printt(f"\nAll done! There are currently {len(dic['video_name'])} musics!")

        self.sort_source()


    def print_links(self):
      with open(f'{self.path}/source.json', 'r') as f:
        dic = json.load(f)

      for video, link in zip(dic['video_name'], dic['video_link']):
          text = f"\t* {video} => {link}"
          print(text)
