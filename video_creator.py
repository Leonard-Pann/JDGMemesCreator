import os
import subprocess
import json, os, time, math
from dataclasses import dataclass
from pydub import AudioSegment
from typing import List
import tqdm

@dataclass
class AudioSample:
    video_name:str
    audio_name:str
    start:float
    end:float
    enable:bool
    video_only:bool

    def __init__(self, video_name: str,  audio_name: str, start: float, end: float, enable: bool, video_only:bool):
        self.video_name = video_name
        self.audio_name = audio_name
        self.start = start
        self.end = end
        self.enable = enable
        self.video_only = video_only

@dataclass
class AudioSamples:
    convert_to_mono:bool
    enable_all:bool
    create_arduino_file:bool
    audio_samples:List[AudioSample]

    @staticmethod
    def from_json(json_str: str) -> 'AudioSamples':
        data = json.loads(json_str)
        audio_samples = [AudioSample(**sample) for sample in data["audio_samples"]]
        return AudioSamples(data["convert_to_mono"], data["enable_all"], data["create_arduino_file"], audio_samples)

    def __init__(self, convert_to_mono:bool, enable_all:bool, create_arduino_file:bool, audio_samples:List[AudioSample]):
        self.convert_to_mono = convert_to_mono
        self.enable_all = enable_all
        self.create_arduino_file = create_arduino_file
        self.audio_samples = audio_samples

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o :o.__dict__, indent=4)

def extract_video_sample_ffmpeg(video_path:str, start_video_sec:float, end_video_sec:float, output_video_path:str, convert_to_mono:bool, video_quality:int, gain_db:float) -> None:
    args:list[str] = [
        "ffmpeg", "-y",
        "-ss", str(start_video_sec),
        "-to", str(end_video_sec),
        "-i", video_path,
    ]

    if abs(gain_db) >= 0.1:
        args += ["-filter:a", f"volume={gain_db}dB"]

    if convert_to_mono:
        args += ["-ac", "1"]

    if video_quality > 0:
        args += ["-crf", str(video_quality)]

    args.append(output_video_path)
    subprocess.run(args, capture_output=True)

def get_meme_dBFS(sample:AudioSample, convert_to_mono:bool) -> float:
    audio_path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio", sample.video_name.replace(".mp4", ".mp3"))
    audio: AudioSegment = AudioSegment.from_mp3(audio_path)
    if convert_to_mono:
        audio = audio.set_channels(1)

    start = int(sample.start * 1000.0)
    end = int(sample.end * 1000.0)
    meme = audio[start:end]
    return meme.dBFS

def extract_video_sample(sample:AudioSample, convert_to_mono:bool, video_quality:int, target_dBFS:float):
    current_dBFS: float = get_meme_dBFS(sample, convert_to_mono)
    audio_gain_db: float = target_dBFS - current_dBFS
    video_path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos", sample.video_name)
    output_path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memes_video", sample.audio_name.replace(".mp3", ".mp4"))

    extract_video_sample_ffmpeg(video_path, sample.start, sample.end, output_path, convert_to_mono, video_quality, audio_gain_db)

def main():
    SAMPLE_QUALITY:int = -1 # <= 0 raw, 25 good quality, 28 medium, 35+ low
    TARGET_DBFS:float = -16.0

    start: float = time.time()
    cwd_name: str = os.path.dirname(os.path.abspath(__file__))

    memes_path:str = os.path.join(cwd_name, "memes_video")
    for meme_path in os.listdir(memes_path):
        os.remove(os.path.join(memes_path, meme_path))

    content:str = ""
    with open(os.path.join(cwd_name, "memes.json"), encoding="utf-8") as file:
        content = file.read()

    samples: AudioSamples = AudioSamples.from_json(content)
    if not samples.enable_all:
        samples.audio_samples = [sample for sample in samples.audio_samples if sample.enable]

    with tqdm.tqdm(total=len(samples.audio_samples), desc="Processing") as pbar:
        for sample in samples.audio_samples:
            extract_video_sample(sample, samples.convert_to_mono, SAMPLE_QUALITY, TARGET_DBFS)
            pbar.update(1)

    duration: float = math.floor((time.time() - start) * 100.0) / 100.0
    print(f"Terminated in {duration} sec!")

if __name__ == "__main__":
    main()
