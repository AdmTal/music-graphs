import pretty_midi
from midi2audio import FluidSynth
from collections import defaultdict

# https://schristiancollins.com/generaluser.php
SOUND_FONT_FILE = "GeneralUser GS v1.471.sf2"


def convert_midi_to_wav(midi_file_path, wav_file_path, soundfont):
    fs = FluidSynth(soundfont)
    fs.midi_to_audio(midi_file_path, wav_file_path)


def get_note(number):
    return (number % 12) + 1


def get_note_start_times_in_frames(
    midi_file_path,
    fps,
    squash_tracks=False,
):
    # Load the MIDI file
    midi_data = pretty_midi.PrettyMIDI(midi_file_path)

    track_events_frames = defaultdict(lambda: defaultdict(list))

    for i, instrument in enumerate(midi_data.instruments):
        for note in instrument.notes:
            # Calculate the start time of the note in seconds and convert to frames
            start_time = note.start
            end_time = note.end
            frame = int(start_time * fps)
            note_length_in_frames = int((end_time - start_time) * fps)
            note_value = get_note(note.pitch)

            note_tuple = (
                note_value,
                note.velocity,
                note_length_in_frames,
            )
            if squash_tracks:
                track_events_frames[f"track_2"][frame].append(note_tuple)
            else:
                track_events_frames[f"track_{i + 2}"][frame].append(note_tuple)

    return track_events_frames