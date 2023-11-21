# Music Graphs

👋 Hey there! Welcome to Music Graphs 🎵📊

This is where the magic happens for the videos I post on [TikTok](https://tiktok.com/@music_graphs).

Check it out if you haven't already!

<a href="https://www.tiktok.com/@music_graphs">
  <img width="200px" 
       src="https://img.shields.io/badge/TikTok-000000?style=for-the-badge&logo=tiktok&logoColor=white"
  />
</a>

🤩 Follow me! Like my videos! Make me famous!

## Example Videos

https://github.com/AdmTal/music-graphs/assets/3382568/7015cbc8-77ca-498a-968b-6dce2f908ad0

https://github.com/AdmTal/music-graphs/assets/3382568/a9af3ec7-0f6f-46b7-a603-4834e2707553

https://github.com/AdmTal/music-graphs/assets/3382568/7e3be7e1-6a9a-4c50-b3fd-a3d3a150c578

---

## Install

Alright, let's get you set up. This baby runs on Python, so let's prep your environment.

```commandline
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

```

You'll also need [ffmpeg](https://formulae.brew.sh/formula/ffmpeg).

```commandline
brew install ffmpeg
```

## Generate a Video

Ready to roll? Start with this example:

```commandline
python music_graphs.py --midi examples/wii-music.mid
```

This command churns out a video. But hold up, it's kinda vanilla, right? Let's jazz it up!

Run it with a Theme file:

```commandline
python music_graphs.py \
  --midi examples/wii-music.mid \
  --theme examples/wii-theme.yaml
```

Boom! Looks way cooler, doesn't it?

For all the nitty-gritty on customizing your video, peek at [default_theme.yaml](assets%2Fdefault_theme.yaml). There's a
bunch you can tweak!

See the help command for full options:

```commandline
Usage: music_graphs.py [OPTIONS]

Options:
  --midi PATH             Path to a MIDI file.  [required]
  --theme PATH            Path to a YAML theme file.
  --output_filename PATH  Output filename (path).
  --soundfont_file PATH   Path to a Soundfont file
  --help                  Show this message and exit.
```

## What's a "Sound Font" file?

For more details, check out [the wiki](https://en.wikipedia.org/wiki/SoundFont), but the gist is: while a MIDI file
outlines the notes of a piece, a SoundFont file fills in the sound - it's what makes the notes come to life with actual
timbre and tone.
You can find better, more realistic sound fonts online.

For example - Look for "SGM-V2.01.sf2" on https://www.doomworld.com/forum/post/1827928.

---

🙏Thanks for stopping by!

