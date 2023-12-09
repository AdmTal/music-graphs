import click
import psutil
from graphviz import Graph
from hurry.filesize import size

from src.animation_stuff import AnimationFrames
from src.cache_stuff import (
    cleanup_cache_dir,
    get_cache_dir,
)
from src.graph_stuff import (
    animate_bezier_point,
    animate_ellipsis_blur,
    draw_fading_bezier_curve,
    parse_graph,
    get_node_positions,
)
from src.midi_stuff import (
    get_note_start_times_in_frames,
    TRACK_NOTE_DELIMITER,
)
from src.theme_stuff import Theme
from src.video_stuff import (
    add_frame_to_video,
    finalize_video_with_music,
    initialize_video_writer,
)


def midi_note_to_pitch_class(midi_note):
    _, note = midi_note.split(TRACK_NOTE_DELIMITER)
    midi_note = int(note)
    note_names = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
    return note_names[(midi_note - 1) % 12]


def overlapping_pairs(lst):
    return list(zip(lst, lst[1:])) + [(lst[-2], lst[-1])] if len(lst) > 1 else []


def create_graphviz_default_sort(theme, track_events_frames):
    """Create a Graphviz without a specified order"""
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
        if theme.skip_track(track):
            continue
        notes = [
            [note_tuple[0] for note_tuple in list_of_note_tuples]
            for frame_num, list_of_note_tuples in note_tuples.items()
        ]
        # Create Nodes
        for note in notes:
            n = note[0]
            song_graph.node(n, label=midi_note_to_pitch_class(n))

        # Create Edges
        melody_pairs = overlapping_pairs(notes)
        for a_notes, b_notes in melody_pairs:
            for a in a_notes:
                for b in b_notes:
                    song_graph.node(b, label=midi_note_to_pitch_class(b))
                    song_graph.edge(a, b)

    return song_graph


def filter_and_order_custom(reference_list, input_list):
    # Extract the numbers from the input strings and convert them to integers
    input_numbers = [int(item.split(TRACK_NOTE_DELIMITER)[1]) for item in input_list]

    # Create a mapping of number to original string for reconstruction later
    number_to_string = dict(zip(input_numbers, input_list))

    # Filter and order the input list based on the reference list
    ordered_list = [
        number_to_string[item] for item in reference_list if item in number_to_string
    ]

    return ordered_list


def create_graphviz_sorted(theme, track_events_frames):
    """
    This function implements a hack to force Graphviz node ordering.
    Step 1: Create a bare-bones CIRCO graph with nodes added in order
    Step 2: Save that graph to a file, and extract its node positions
    Step 3: Generate the final NEATO graph, using hard coded node positions
    """
    if theme.graphviz_engine.lower() != "circo":
        click.echo(
            "ERROR: Node sorting only works when graphviz engine is circo", err=True
        )
        cleanup_cache_dir(get_cache_dir())
        exit(1)
    song_graph = Graph(
        "G",
        engine=theme.graphviz_engine,
        format="plain",
        strict=True,
        node_attr=theme.graphviz_node_attrs,
        graph_attr=theme.graphviz_graph_attrs,
        edge_attr=theme.graphviz_edge_attrs,
    )

    all_notes = {}

    for track, note_tuples in track_events_frames.items():
        if theme.skip_track(track):
            continue
        notes = [
            [note_tuple[0] for note_tuple in list_of_note_tuples]
            for frame_num, list_of_note_tuples in note_tuples.items()
        ]

        for note in notes:
            all_notes[note[0]] = True

    # Create Nodes - In order
    prev_note = None
    all_notes = list(all_notes.keys())
    if theme.nodes_sorted:
        if isinstance(theme.nodes_sorted, bool):
            all_notes = sorted(
                all_notes, key=lambda i: int(i.split(TRACK_NOTE_DELIMITER)[1])
            )
        else:
            all_notes = filter_and_order_custom(theme.nodes_sorted, all_notes)
    for n in all_notes + [all_notes[0]]:  # tack on the first to make a circle
        song_graph.node(n, label=midi_note_to_pitch_class(n))
        if prev_note:
            song_graph.edge(n, prev_note)
        prev_note = n

    node_positions = get_node_positions(song_graph)

    song_graph = Graph(
        "G",
        engine="neato",
        format="xdot",
        strict=True,
        node_attr=theme.graphviz_node_attrs,
        graph_attr=theme.graphviz_graph_attrs,
        edge_attr=theme.graphviz_edge_attrs,
    )

    for track, note_tuples in track_events_frames.items():
        if theme.skip_track(track):
            continue
        notes = [
            [note_tuple[0] for note_tuple in list_of_note_tuples]
            for frame_num, list_of_note_tuples in note_tuples.items()
        ]
        # Create Nodes
        for note in notes:
            n = note[0]
            song_graph.node(
                n,
                label=midi_note_to_pitch_class(n),
                _attributes={"pos": node_positions[n]},
            )

        # Create Edges
        melody_pairs = overlapping_pairs(notes)
        for a_notes, b_notes in melody_pairs:
            for a in a_notes:
                for b in b_notes:
                    song_graph.node(b, label=midi_note_to_pitch_class(b))
                    song_graph.edge(a, b)

    return song_graph


def create_graphviz(theme, track_events_frames):
    if theme.nodes_sorted:
        return create_graphviz_sorted(theme, track_events_frames)

    return create_graphviz_default_sort(theme, track_events_frames)


def generate_music_graph(
    midi_file_path,
    default_theme_file_path,
    theme_file_path,
    output_path,
    soundfont_file,
):
    theme = Theme(theme_file_path, default_theme_file_path)
    track_events_frames = get_note_start_times_in_frames(
        midi_file_path,
        theme.frame_rate,
        squash_tracks=theme.squash_tracks,
        group_notes_by_track=theme.group_notes_by_track,
    )

    song_graph = create_graphviz(theme, track_events_frames)

    base_image, nodes, edges, offsets = parse_graph(song_graph, theme)

    if theme.debug_show_base_image:
        base_image.show()
        cleanup_cache_dir(get_cache_dir())
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
                    f"l2-{track}-{current_note}", curr_frame, frames
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
                        curr_note_tuples[0][0],
                        curr_note_tuples[-1][2],
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
                        f"l1-{track}-{a}-{b}-line", curr_frame, frames
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
