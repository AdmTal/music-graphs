import io
import json
import tempfile
import PySimpleGUI as sg

from src.generate_music_graph import generate_music_graph
from src.midi_stuff import SOUND_FONT_FILE
from src.theme_stuff import DARK_THEME_FILE, LIGHT_THEME_FILE, Theme


# Function to generate image data using PIL
def get_image_data(image, max_size=(400, 400)):
    """Generate image data using PIL"""
    image.thumbnail(max_size)
    bio = io.BytesIO()
    image.save(bio, format="PNG")
    return bio.getvalue()


# Define the layout of the window
def create_layout():
    theme = Theme(DARK_THEME_FILE, DARK_THEME_FILE)
    theme_controls = create_theme_control_section(theme)

    layout = [
        [
            sg.Column(
                [[sg.Image(data=None, key="-VIDEO-", size=(400, 400))]],
                element_justification="center",
            ),
            sg.VSeperator(),
            sg.Column(
                [
                    [sg.Text("Select a MIDI File:")],
                    [
                        sg.Input(key="-MIDI-", enable_events=True),
                        sg.FileBrowse(file_types=(("MIDI Files", "*.mid"),)),
                    ],
                    [sg.Button("Generate Video", key="-GENERATE-")],
                    [
                        sg.Column(
                            theme_controls,
                            scrollable=True,
                            vertical_scroll_only=True,
                            size=(500, 400),
                        )
                    ],
                ]
            ),
        ],
    ]
    return layout


def create_theme_control_section(theme: Theme):
    layout = [
        [
            sg.Radio("Dark Theme", "THEME", default=True, key="-DARK_THEME-"),
            sg.Radio("Light Theme", "THEME", key="-LIGHT_THEME-"),
        ],
        [
            sg.Text("Background Color:"),
            sg.InputText(
                key="-BACKGROUND_COLOR-",
                default_text=theme.background_color,
            ),
        ],
        [
            sg.Text("Font Size:"),
            sg.InputText(
                key="-FONT_SIZE-",
                default_text=theme.font_size,
            ),
        ],
    ]
    return layout


# Create the window with the layout
window = sg.Window("MIDI to Video App", create_layout())


def create_temp_theme_file(values):
    theme = {
        "background_color": values["-BACKGROUND_COLOR-"],
        "font_size": int(values["-FONT_SIZE-"]),
        # Add other parameters here...
        "debug": {"max_frames": 60},
    }

    # Create a temporary file to store the theme
    temp_theme_file = tempfile.NamedTemporaryFile(delete=False, suffix=".yml")
    with open(temp_theme_file.name, "w") as file:
        json.dump(theme, file)

    return temp_theme_file.name


frame_idx = 0
video_frames = []

while True:
    fps = 60
    event, values = window.read(timeout=1000 // fps)

    if event == sg.WIN_CLOSED:
        break

    if event == "-MIDI-":
        midi_file = values["-MIDI-"]

    if event == "-GENERATE-":
        temp_theme_file = create_temp_theme_file(values)
        base_theme = DARK_THEME_FILE if values["-DARK_THEME-"] else LIGHT_THEME_FILE

        video_frames = generate_music_graph(
            midi_file,
            base_theme,
            theme_file_path=temp_theme_file,
            output_path=None,
            soundfont_file=SOUND_FONT_FILE,
            just_get_frames=True,
        )

    # Update the video frame
    if frame_idx < len(video_frames):
        frame = video_frames[frame_idx]
        img_data = get_image_data(frame)
        window["-VIDEO-"].update(data=img_data)
        frame_idx = (frame_idx + 1) % len(video_frames)

# Close the window
window.close()
