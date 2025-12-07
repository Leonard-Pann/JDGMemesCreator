import os, sys
import time
import math
import json
from pydub import AudioSegment
from dataclasses import dataclass
from typing import List
import shutil
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

def extract_audio_sample(sample:AudioSample, convert_to_mono:bool, target_dBFS:float):
    audio_path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio", sample.video_name.replace(".mp4", ".mp3"))
    output_path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memes", sample.audio_name)
    audio: AudioSegment = AudioSegment.from_mp3(audio_path)
    if convert_to_mono:
        audio = audio.set_channels(1)

    start = int(sample.start * 1000.0)
    end = int(sample.end * 1000.0)

    meme = audio[start:end]

    change_in_dBFS:float = target_dBFS - meme.dBFS
    meme = meme.apply_gain(change_in_dBFS)
    meme.export(output_path, format="mp3")

#all samples need to have same video name
def batch_extract_audio_samples(samples:list[AudioSample], convert_to_mono:bool, target_dBFS:float):
    audio_path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio", samples[0].video_name.replace(".mp4", ".mp3"))
    audio: AudioSegment = AudioSegment.from_mp3(audio_path)
    if convert_to_mono:
        audio = audio.set_channels(1)

    for sample in samples:
        output_path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memes", sample.audio_name)

        start = int(sample.start * 1000.0)
        end = int(sample.end * 1000.0)

        meme = audio[start:end]
        change_in_dBFS:float = target_dBFS - meme.dBFS
        meme = meme.apply_gain(change_in_dBFS)
        meme.export(output_path, format="mp3")

def main():

    TARGET_DBFS:float = -16.0

    start: float = time.time()
    cwd_name: str = os.path.dirname(os.path.abspath(__file__))

    memes_path:str = os.path.join(cwd_name, "memes")
    if not os.path.exists(memes_path):
        print(f"Memes path '{memes_path}' does not exist. Please download the videos with the 'download.sh' script")
        sys.exit(1)
    for meme_path in os.listdir(memes_path):
        os.remove(os.path.join(memes_path, meme_path))

    content:str = ""
    with open(os.path.join(cwd_name, "memes.json"), encoding="utf-8") as file:
        content = file.read()

    samples: AudioSamples = AudioSamples.from_json(content)

    # Compute remaining videos
    # video_path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos")
    # videos:list[str] = os.listdir(video_path)
    # for i in range(len(videos) - 1, -1, -1):
    #     video_str:str = videos[i]
    #     contains:bool = False
    #     for sample in samples.audio_samples:
    #         if sample.video_name == video_str:
    #             contains = True
    #             break
    #     if contains:
    #         videos.pop(i)

    if not samples.enable_all:
        samples.audio_samples = [sample for sample in samples.audio_samples if sample.enable]

    audio_samples:list[AudioSample] = [sample for sample in samples.audio_samples if not sample.video_only]

    # with tqdm.tqdm(total=len(audio_samples), desc="Processing") as pbar:
    #     for sample in audio_samples:
    #         extract_audio_sample(sample, samples.convert_to_mono)
    #         pbar.update(1)

    with tqdm.tqdm(total=len(audio_samples), desc="Processing") as pbar:
        while len(audio_samples) > 0:
            batch: list[AudioSample] = [sample for sample in audio_samples if sample.video_name == audio_samples[0].video_name]
            if len(batch) > 1:
                batch_extract_audio_samples(batch, samples.convert_to_mono, TARGET_DBFS)
                pbar.update(len(batch))
                for sample in batch:
                    audio_samples.remove(sample)
            else:
                extract_audio_sample(audio_samples.pop(0), samples.convert_to_mono, TARGET_DBFS)
                pbar.update(1)

            #remove this
            # break

    if samples.create_arduino_file:
        arduino_path:str = os.path.join(cwd_name, "arduino_files")
        for arduino_meme_path in os.listdir(arduino_path):
            os.remove(os.path.join(arduino_path, arduino_meme_path))

        def itoa(i:int) -> str:
            res:str = str(i)
            nb_0:int = 4 - len(res)
            return (max(0, nb_0) * "0") + res

        i:int = 1
        for local_meme_path in os.listdir(memes_path):
            meme:str = os.path.join(memes_path, local_meme_path)
            arduino_meme_path:str = os.path.join(arduino_path, itoa(i) + "_" + local_meme_path)
            shutil.copy(meme, arduino_meme_path)
            i += 1

    duration: float = math.floor((time.time() - start) * 100.0) / 100.0
    print(f"Terminated in {duration} sec!")
    # if samples.enable_all:
    #     print(f"Missing {len(videos)} vidéos : {videos}")

if __name__ == "__main__":
    main()
