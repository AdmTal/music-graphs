import pretty_midi
from midi2audio import FluidSynth
from collections import defaultdict

# https://schristiancollins.com/generaluser.php
SOUND_FONT_FILE = "assets/GeneralUser GS 1.471/GeneralUser GS v1.471.sf2"

TRACK_NOTE_DELIMITER = '#'


def convert_midi_to_wav(midi_file_path, wav_file_path, soundfont):
    fs = FluidSynth(soundfont)
    fs.midi_to_audio(midi_file_path, wav_file_path)


def get_note(track, number):
    """
    Note is string that includes track number and MIDI note value, it is also the NODE KEY on the graphviz
    Purpose is to enable "group_notes_by_track"
    """
    return f'{track}{TRACK_NOTE_DELIMITER}{(number % 12) + 1}'


def get_note_start_times_in_frames(
        midi_file_path,
        fps,
        squash_tracks=False,
        group_notes_by_track=False,
):
    # Load the MIDI file
    midi_data = pretty_midi.PrettyMIDI(midi_file_path)

    track_events_frames = defaultdict(lambda: defaultdict(list))

    for i, instrument in enumerate(midi_data.instruments, start=1):
        for note in instrument.notes:
            # Calculate the start time of the note in seconds and convert to frames
            start_time = note.start
            end_time = note.end
            frame = int(start_time * fps)
            note_length_in_frames = int((end_time - start_time) * fps)

            track_name = 0
            if group_notes_by_track:
                track_name = i + 1
            note_value = get_note(track_name, note.pitch)

            note_tuple = (
                note_value,
                note.velocity,
                note_length_in_frames,
            )
            if squash_tracks:
                track_events_frames[f"track_2"][frame].append(note_tuple)
            else:
                track_events_frames[f"track_{track_name}"][frame].append(note_tuple)

    return track_events_frames
