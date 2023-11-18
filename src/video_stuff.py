from contextlib import contextmanager
import os
import time

import click
import imageio
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip
from pydub import AudioSegment

from src.midi_stuff import convert_midi_to_wav
from src.cache_stuff import get_cache_dir, cleanup_cache_dir


@contextmanager
def initialize_video_writer(frame_rate):
    video_file_path = f"{get_cache_dir()}/video.mp4"
    writer = imageio.get_writer(video_file_path, fps=frame_rate)
    try:
        yield writer, video_file_path
    finally:
        writer.close()


def add_frame_to_video(writer, frame):
    writer.append_data(np.array(frame))


def finalize_video_with_music(
        writer,
        video_file_path,
        output_file_name,
        midi_file_path,
        frame_rate,
        soundfont_file,
        frames_written,
):
    writer.close()  # Ensure the writer is closed

    # Audio processing
    temp_music_file = os.path.join(get_cache_dir(), "temp_music.wav")
    open(temp_music_file, "ab").close()
    click.echo("Converting midi to wave...")
    convert_midi_to_wav(
        midi_file_path,
        temp_music_file,
        soundfont_file,
    )
    audio_clip = AudioSegment.from_file(temp_music_file)

    audio_duration = int((frames_written / frame_rate) * 1000)  # Duration in milliseconds
    audio_clip = audio_clip[:audio_duration]  # Truncate the audio

    temp_audio = f"{get_cache_dir()}/music.wav"
    audio_clip.export(temp_audio, format="wav")

    final_video = VideoFileClip(video_file_path)
    final_video_audio = AudioFileClip(temp_audio)
    final_video = final_video.set_audio(final_video_audio)

    timestamp = int(time.time())
    final_output_path = f"{output_file_name}_{timestamp}.mp4"
    final_video.write_videofile(final_output_path, codec="libx264", audio_codec="aac")

    cleanup_cache_dir(get_cache_dir())

    return final_output_path
