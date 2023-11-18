import os

import click

from src.generate_music_graph import generate_music_graph
from src.midi_stuff import SOUND_FONT_FILE
from src.theme_stuff import DEFAULT_THEME_FILE


def get_filename_without_extension(path):
    filename_with_extension = os.path.basename(path)
    filename_without_extension, _ = os.path.splitext(filename_with_extension)
    return filename_without_extension


@click.command()
@click.option(
    "--midi",
    required=True,
    type=click.Path(exists=True),
    help="Path to a MIDI file.",
)
@click.option(
    "--theme",
    type=click.Path(exists=True),
    help="Path to a YAML theme file.",
    default=DEFAULT_THEME_FILE,
)
@click.option(
    "--output_filename",
    type=click.Path(),
    help="Output filename (path).",
    default=None,
)
@click.option(
    "--soundfont_file",
    type=click.Path(),
    help="Path to a Soundfont file",
    default=SOUND_FONT_FILE,
)
def main(midi, theme, output_filename, soundfont_file):
    if not output_filename:
        output_filename = get_filename_without_extension(midi)
    generate_music_graph(midi, theme, output_filename, soundfont_file)


if __name__ == "__main__":
    main()
