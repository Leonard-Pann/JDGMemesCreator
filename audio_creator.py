import os
import subprocess
import tqdm

def extract_audio_from_video(video_path:str, output_audio_path:str):
    subprocess.run(["ffmpeg", "-y", "-i", video_path, "-b:a", "192K", "-vn", output_audio_path], capture_output=True)

def main():
    cwd_name: str = os.path.dirname(os.path.abspath(__file__))
    videos_dir:str = os.path.join(cwd_name, "videos")
    videos_path:list[str] = os.listdir(videos_dir)

    with tqdm.tqdm(total=len(videos_path), desc="Processing") as pbar:
        for i in range(0, len(videos_path)):
            video_name:str = videos_path[i]
            extract_audio_from_video(os.path.join(videos_dir, video_name), os.path.join(cwd_name, "audio", video_name.replace(".mp4", ".mp3")))
            pbar.update(1)

if __name__ == '__main__':
    main()
