import click
import psutil
from graphviz import Graph
from hurry.filesize import size

from src.animation_stuff import AnimationFrames
from src.graph_stuff import (
    animate_bezier_point,
    animate_ellipsis_blur,
    draw_fading_bezier_curve,
    parse_graph,
)
from src.midi_stuff import get_note_start_times_in_frames
from src.theme_stuff import Theme
from src.video_stuff import (
    add_frame_to_video,
    finalize_video_with_music,
    initialize_video_writer,
)


def midi_note_to_pitch_class(midi_note):
    note_names = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
    return note_names[(midi_note - 1) % 12]


def overlapping_pairs(lst):
    return list(zip(lst, lst[1:])) + [(lst[-2], lst[-1])] if len(lst) > 1 else []


def generate_music_graph(midi_file_path, theme_file_path, output_path, soundfont_file):
    theme = Theme(theme_file_path)
    track_events_frames = get_note_start_times_in_frames(
        midi_file_path,
        theme.frame_rate,
        squash_tracks=theme.squash_tracks,
    )

    song_graph = Graph(
        "G",
        engine=theme.graphviz_engine,
        format="xdot",
        strict=True,
        node_attr=theme.graphviz_node_attrs,
        graph_attr=theme.graphviz_graph_attrs,
        edge_attr=theme.graphviz_edge_attrs,
    )

    for track, note_tuples in track_events_frames.items():
        notes = [
            [note_tuple[0] for note_tuple in list_of_note_tuples]
            for frame_num, list_of_note_tuples in note_tuples.items()
        ]
        melody_pairs = overlapping_pairs(notes)
        for a_notes, b_notes in melody_pairs:
            for a in a_notes:
                song_graph.node(str(a), label=midi_note_to_pitch_class(a))
                for b in b_notes:
                    song_graph.node(str(b), label=midi_note_to_pitch_class(b))
                    song_graph.edge(str(a), str(b))

    base_image, nodes, edges, offsets = parse_graph(song_graph, theme)

    if theme.debug_show_base_image:
        base_image.show()
        exit()

    FRAMES = AnimationFrames()

    click.echo("Planning out frames...", nl=False)

    for track in track_events_frames.keys():
        if theme.skip_track(track):
            continue
        curr_track = track_events_frames[track]
        curr_frame = min(curr_track) - 1
        prev_notes = None
        prev_notes_frame = None
        num_notes_processed = 0
        click.echo()  # NL

        max_notes = len(track_events_frames[track])

        while num_notes_processed < max_notes and curr_frame <= max(curr_track):
            curr_frame += 1

            if curr_frame not in curr_track:
                continue

            usage = size(psutil.Process().memory_info().rss)
            click.echo(
                f"\r[{track}] Processing {num_notes_processed + 1} of {max_notes} notes... (memory usage={usage})",
                nl=False,
            )

            num_notes_processed += 1
            curr_note_tuples = curr_track[curr_frame]

            # Animate the Node pulses
            for (
                current_note,
                curr_note_velocity,
                curr_note_frame_len,
            ) in curr_note_tuples:
                frames = []
                for i in range(curr_note_frame_len):
                    frame = [
                        animate_ellipsis_blur,
                        {
                            "track": track,
                            "points": nodes[current_note].e_points,
                            "frame_number": i,
                            "animation_len": curr_note_frame_len,
                            "velocity": curr_note_velocity,
                        },
                    ]

                    frames.append(frame)
                FRAMES.add_frames_to_layer(
                    f"l1-{track}-{current_note}", curr_frame, frames
                )

            # Animate the Chord Lines
            if len(curr_note_tuples) > 1:
                pairs = []
                for idx in range(len(curr_note_tuples) - 1):
                    a = curr_note_tuples[idx][0]
                    frame_len = curr_note_tuples[idx][2]
                    b = curr_note_tuples[idx + 1][0]
                    pairs.append(
                        (
                            a,
                            b,
                            frame_len,
                        )
                    )

                pairs = sorted(pairs, key=lambda x: x[0])
                pairs.append(
                    (
                        curr_note_tuples[-1][0],
                        curr_note_tuples[-1][2],
                        curr_note_tuples[0][0],
                    )
                )

                for a, b, frame_len in pairs:
                    frames = []
                    for i in range(frame_len):
                        if a == b:
                            continue

                        if b not in edges[a]:
                            continue

                        frames.append(
                            [
                                draw_fading_bezier_curve,
                                {
                                    "track": track,
                                    "points": edges[a][b].b_points,
                                    "frame_number": i,
                                    "animation_len": frame_len,
                                },
                            ]
                        )
                    FRAMES.add_frames_to_layer(
                        f"l2-{track}-{a}-{b}-line", curr_frame, frames
                    )

            curr_notes = [curr_note_tuple[0] for curr_note_tuple in curr_note_tuples]

            # Animate the "next note" balls
            if prev_notes:
                animation_length_in_frames = curr_frame - prev_notes_frame
                drawn_to = set()
                source_usage = {note: 0 for note in prev_notes}

                # New Rule: Check if there are more destinations than sources to determine max usage
                max_usage = 2 if len(curr_notes) > len(prev_notes) else 1

                if animation_length_in_frames / theme.frame_rate <= 10:
                    for a in prev_notes:
                        for b in curr_notes:
                            if (
                                b in drawn_to
                                or (a == b and not theme.allow_self_notes(track))
                                or source_usage[a] >= max_usage
                                or b not in edges[a]
                            ):
                                continue

                            frames = []
                            for i in range(animation_length_in_frames):
                                frame = [
                                    animate_bezier_point,
                                    {
                                        "track": track,
                                        "points": edges[a][b].b_points,
                                        "frame_number": i,
                                        "animation_length_in_frames": animation_length_in_frames,
                                    },
                                ]

                                frames.append(frame)
                            FRAMES.add_frames_to_layer(
                                f"l3-{track}-{a}-{b}-balls", prev_notes_frame, frames
                            )
                            drawn_to.add(b)
                            source_usage[a] += 1

            prev_notes = curr_notes
            prev_notes_frame = curr_frame

    num_frames = len(FRAMES)
    if theme.debug_max_frames:
        num_frames = theme.debug_max_frames

    writer_context = initialize_video_writer(theme.frame_rate)
    frames_written = 0
    click.echo("\nDrawing frames, writing videos...")
    with writer_context as (writer, video_file_path):
        for current_frame in range(num_frames):
            usage = size(psutil.Process().memory_info().rss)
            click.echo(
                f"\rProcessed {current_frame} of {num_frames}... (memory usage={usage})",
                nl=False,
            )

            # Create a new image for the base
            frame_image = base_image.copy()

            # Flatten the layers for the current frame
            for layer, layer_images in sorted(FRAMES.items()):
                frame = layer_images[current_frame]
                if frame:
                    draw_function, args = frame
                    frame_image = draw_function(
                        base_image=frame_image,
                        theme=theme,
                        offsets=offsets,
                        **args,
                    )

            add_frame_to_video(writer, frame_image)
            frames_written += 1

    finalize_video_with_music(
        writer,
        video_file_path,
        output_path,
        midi_file_path,
        theme.frame_rate,
        soundfont_file,
        frames_written,
    )