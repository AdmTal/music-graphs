import operator
import yaml

DEFAULT_THEME_FILE = "assets/default_theme.yaml"


class AttributeDict(dict):
    """Helper class to allow for Dicts to have Dot Notation"""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if isinstance(value, dict):
                self.__dict__[key] = AttributeDict(**value)
            else:
                self.__dict__[key] = value
        super().__init__(**kwargs)

    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def get_path(self, path):
        try:
            return operator.attrgetter(path)(self)
        except KeyError:
            pass
        except AttributeError:
            pass
        return None


class Theme:
    def __init__(
            self,
            theme_file,
            defaults_file=DEFAULT_THEME_FILE,
    ):
        with open(theme_file, "r") as stream:
            self._theme = AttributeDict(**yaml.safe_load(stream))

        with open(defaults_file, "r") as stream:
            try:
                self._defaults = AttributeDict(**yaml.safe_load(stream))
            except:
                self._defaults = AttributeDict(**{})

    def _get_value(self, path, default_path=""):
        value = self._theme.get_path(path)
        if value is not None:
            return value
        if default_path:
            return self._defaults.get_path(default_path)

    @property
    def debug_show_base_image(self):
        path = "debug.show_base_image"
        return self._get_value(path, path)

    @property
    def debug_max_frames(self):
        path = "debug.max_frames"
        return self._get_value(path, path)

    @property
    def frame_rate(self):
        path = "frame_rate"
        return self._get_value(path, path)

    @property
    def graphviz_engine(self):
        path = "graphviz_engine"
        return self._get_value(path, path)

    @property
    def squash_tracks(self):
        path = "squash_tracks"
        return self._get_value(path, path)

    def skip_track(self, track):
        if track == "track_1":
            return True
        return self._get_value(
            f"tracks.{track}.skip",
            default_path=f"tracks.default.skip",
        )

    def allow_self_notes(self, track):
        return self._get_value(
            f"tracks.{track}.allow_self_notes",
            default_path=f"tracks.default.skip",
        )

    @property
    def graphviz_edge_attrs(self):
        path = "graphviz_edge_attrs"
        return self._get_value(path, path)

    @property
    def graphviz_node_attrs(self):
        path = "graphviz_node_attrs"
        return self._get_value(path, path)

    @property
    def graphviz_graph_attrs(self):
        path = "graphviz_graph_attrs"
        return self._get_value(path, path)

    @property
    def background_image(self):
        path = "background_image"
        return self._get_value(path, path)

    @property
    def font(self):
        path = "font"
        return self._get_value(path, path)

    @property
    def width(self):
        path = "width"
        return self._get_value(path, path)

    @property
    def height(self):
        path = "height"
        return self._get_value(path, path)

    @property
    def show_lines(self):
        path = "show_graph_lines"
        return self._get_value(path, path)

    @property
    def graph_line_width(self):
        path = "graph_line_width"
        return self._get_value(path, path)

    @property
    def font_size(self):
        path = "font_size"
        return self._get_value(path, path)

    @property
    def node_outline_color(self):
        path = "node.outline_color"
        return self._get_value(path, path)

    @property
    def node_fill_color(self):
        path = "node.fill_color"
        return self._get_value(path, path)

    @property
    def node_text_color(self):
        path = "node.text.color"
        return self._get_value(path, path)

    @property
    def node_text_outline_color(self):
        path = "node.text.stroke_color"
        return self._get_value(path, path)

    @property
    def node_text_stroke_width(self):
        path = "node.text.stroke_width"
        return self._get_value(path, path)

    @property
    def dpi(self):
        path = "dpi"
        return self._get_value(path, path)

    @property
    def text_location_offsets(self):
        path = "text_location_offsets"
        return self._get_value(path, path)

    @property
    def node_shadow_color(self):
        path = "node.shadow_color"
        return self._get_value(path, path)

    @property
    def node_shadow_size(self):
        path = "node.shadow_size"
        return self._get_value(path, path) / 100

    @property
    def tracks(self):
        return list(self._theme.tracks.keys())

    def note_num_frames(self, track):
        a = self._get_value(
            f"tracks.{track}.note.num_frames",
            default_path=f"tracks.default.note.num_frames",
        )
        return a

    def note_color(self, track):
        return self._get_value(
            f"tracks.{track}.note.color",
            default_path=f"tracks.default.note.color",
        )

    def note_stroke_width(self, track):
        return self._get_value(
            f"tracks.{track}.note.stroke_width",
            default_path=f"tracks.default.note.stroke_width",
        )

    def note_increase_size(self, track):
        return (
                self._get_value(
                    f"tracks.{track}.note.increase_size",
                    default_path=f"tracks.default.note.increase_size",
                )
                / 100
        )

    def chord_line_width(self, track):
        return self._get_value(
            f"tracks.{track}.chord_line.width",
            default_path=f"tracks.default.chord_line.width",
        )

    def chord_line_border_color(self, track):
        return self._get_value(
            f"tracks.{track}.chord_line.border_color",
            default_path=f"tracks.default.chord_line.border_color",
        )

    def chord_line_color(self, track):
        return self._get_value(
            f"tracks.{track}.chord_line.color",
            default_path=f"tracks.default.chord_line.color",
        )

    def ball_radius(self, track):
        return self._get_value(
            f"tracks.{track}.ball.radius",
            default_path=f"tracks.default.ball.radius",
        )

    def ball_g_blur_max(self, track):
        return self._get_value(
            f"tracks.{track}.ball.g_blur_max",
            default_path=f"tracks.default.ball.g_blur_max",
        )

    def ball_color(self, track):
        return self._get_value(
            f"tracks.{track}.ball.color",
            default_path=f"tracks.default.ball.color",
        )

    def ball_stroke_color(self, track):
        return self._get_value(
            f"tracks.{track}.ball.stroke_color",
            default_path=f"tracks.default.ball.stroke_color",
        )

    def ball_stroke_width(self, track):
        return self._get_value(
            f"tracks.{track}.ball.stroke_width",
            default_path=f"tracks.default.ball.stroke_width",
        )
