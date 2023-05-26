import asyncio
import io
import glob
import os
import urllib.request
from pathlib import Path
import pandas as pd
import numpy as np

import aiohttp
from tiktokapipy.async_api import AsyncTikTokAPI
from tiktokapipy.models.video import Video

directory = 'videos'
video_data_file = 'product1.csv'
video_tag = 'ctilbury'
url_list = []
video_id_list = []

async def save_slideshow(video: Video):
    # this filter makes sure the images are padded to all the same size
    vf = "\"scale=iw*min(1080/iw\,1920/ih):ih*min(1080/iw\,1920/ih)," \
         "pad=1080:1920:(1080-iw)/2:(1920-ih)/2," \
         "format=yuv420p\""

    for i, image_data in enumerate(video.image_post.images):
        url = image_data.image_url.url_list[-1]
        # this step could probably be done with asyncio, but I didn't want to figure out how
        urllib.request.urlretrieve(url, os.path.join(directory, f"temp_{video.id}_{i:02}.jpg"))

    urllib.request.urlretrieve(video.music.play_url, os.path.join(directory, f"temp_{video.id}.mp3"))

    # use ffmpeg to join the images and audio
    command = [
        "ffmpeg",
        "-r 2/5",
        f"-i {directory}/temp_{video.id}_%02d.jpg",
        f"-i {directory}/temp_{video.id}.mp3",
        "-r 30",
        f"-vf {vf}",
        "-acodec copy",
        f"-t {len(video.image_post.images) * 2.5}",
        f"{directory}/temp_{video.id}.mp4",
        "-y"
    ]
    ffmpeg_proc = await asyncio.create_subprocess_shell(
        " ".join(command),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await ffmpeg_proc.communicate()
    generated_files = glob.glob(path.join(directory, f"temp_{video.id}*"))

    if not os.path.exists(os.path.join(directory, f"temp_{video.id}.mp4")):
        # optional ffmpeg logging step
        # logging.error(stderr.decode("utf-8"))
        for file in generated_files:
            os.remove(file)
        raise Exception("Something went wrong with piecing the slideshow together")

    with open(os.path.join(directory, f"temp_{video.id}.mp4"), "rb") as f:
        ret = io.BytesIO(f.read())

    for file in generated_files:
        os.remove(file)

    return ret
        
async def save_video(video: Video, api: AsyncTikTokAPI):
    # Carrying over this cookie tricks TikTok into thinking this ClientSession was the Playwright instance
    # used by the AsyncTikTokAPI instance
    async with aiohttp.ClientSession(cookies={cookie["name"]: cookie["value"] for cookie in await api.context.cookies() if cookie["name"] == "tt_chain_token"}) as session:
        # Creating this header tricks TikTok into thinking it made the request itself
        async with session.get(video.video.download_addr, headers={"referer": "https://www.tiktok.com/"}) as resp:
            return io.BytesIO(await resp.read())

async def download_video(url, tag):
    # mobile emulation is necessary to retrieve slideshows
    # if you don't want this, you can set emulate_mobile=False and skip if the video has an image_post property
    async with AsyncTikTokAPI(emulate_mobile=True, navigation_timeout=120.0, navigation_retries=3) as api:
        
        # Check if the directory exists
        if not os.path.exists(os.path.join(directory, tag)):
            # If it doesn't exist, create it
            os.makedirs(os.path.join(directory, tag))
            # And make the directory for the descriptions
            os.makedirs(os.path.join(directory, tag, 'desc'))
        
        video: Video = await api.video(url)
        url_list.append(url)
        video_id_list.append(video.id)
        
        # check if video already exists
        if os.path.exists(os.path.join(directory, tag, str(video.id) + '.mp4')):
            print(f'already processed {video.id}')
            return
        print(f'processing {video.id} of url {url}')
        
        # print(video)
        if video.image_post:
            # downloaded = await save_slideshow(video)
            # do nothing
            print('image post...')
        else:
            downloaded = await save_video(video, api)
            
            # Save mp4 to file
            # print(video_ad)
            pathname = f'{directory}/{tag}/{video.id}_{video.author.unique_id}'
            # print that the video is an ad
            Path(pathname + '.mp4') \
                .write_bytes(downloaded \
                    .getbuffer() \
                        .tobytes())
                
            # Save description to file
            f = open(f'{directory}/{tag}/desc/{video.id}_description.txt',"w")
            f.write(video.desc)
            f.close()
    
        
async def extract_tiktoks():
    
    video_data = pd.read_csv(os.path.join(directory, video_data_file), sep = ';')
        
    # iterate over the urls to extract the videos
    for index, row in video_data.iterrows():
        link = row.URL   
        try:     
            await download_video(link, video_tag)
        except:
            print(f'could not load {link}')
        
    pd.DataFrame(np.transpose([url_list, video_id_list]), columns=['urls', 'video_ids']).to_csv('output.csv')
    
# run subroutine    
asyncio.run(extract_tiktoks())