import asyncio
import io
import glob
import os
import urllib.request
from os import path
from pathlib import Path

import aiohttp
from tiktokapipy.async_api import AsyncTikTokAPI
from tiktokapipy.models.video import Video

directory = 'videos'

async def save_slideshow(video: Video):
    # this filter makes sure the images are padded to all the same size
    vf = "\"scale=iw*min(1080/iw\,1920/ih):ih*min(1080/iw\,1920/ih)," \
         "pad=1080:1920:(1080-iw)/2:(1920-ih)/2," \
         "format=yuv420p\""

    for i, image_data in enumerate(video.image_post.images):
        url = image_data.image_url.url_list[-1]
        # this step could probably be done with asyncio, but I didn't want to figure out how
        urllib.request.urlretrieve(url, path.join(directory, f"temp_{video.id}_{i:02}.jpg"))

    urllib.request.urlretrieve(video.music.play_url, path.join(directory, f"temp_{video.id}.mp3"))

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

    if not path.exists(path.join(directory, f"temp_{video.id}.mp4")):
        # optional ffmpeg logging step
        # logging.error(stderr.decode("utf-8"))
        for file in generated_files:
            os.remove(file)
        raise Exception("Something went wrong with piecing the slideshow together")

    with open(path.join(directory, f"temp_{video.id}.mp4"), "rb") as f:
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
    async with AsyncTikTokAPI(emulate_mobile=True) as api:
        
        # Check if the directory exists
        if not os.path.exists(os.path.join(directory, tag)):
            # If it doesn't exist, create it
            os.makedirs(os.path.join(directory, tag))
            # And make the directory for the descriptions
            os.makedirs(os.path.join(directory, tag, 'desc'))
        
        video: Video = await api.video(url)
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
            
async def do_something():
    async with AsyncTikTokAPI(navigation_timeout=120.0, navigation_retries=3) as api:
        tiktok_tag = 'ctilburypartner'
        challenge = await api.challenge(tiktok_tag, video_limit=100)
        
        # print(inspect.getmembers(api))
        async for video in challenge.videos:
            # print(video.is_ad)
            link = f'https://www.tiktok.com/@{video.author}/video/{video.id}'
            
            await download_video(link, tiktok_tag)
    
# run subroutine    
asyncio.run(do_something())