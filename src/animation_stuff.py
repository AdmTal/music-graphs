class AnimationFrames:
    """
    Helper object to organize layered frames in order to produce an animation.
    self._data is a Dict.  The Keys are "layer_ids", and the values are Lists of "images".
    They are not really images, they are instead closures that can be executed to create an image.
    """

    def __init__(self):
        self._data = {}

    def __len__(self):
        if not len(self._data):
            return 0
        first_layer = list(self._data.keys())[0]
        return len(self._data[first_layer])

    def items(self):
        return self._data.items()

    def _ensure_layer_length(self, length):
        for layer_id in self._data:
            self._data[layer_id].extend([None] * (length - len(self._data[layer_id])))

    def add_frames_to_layer(self, layer_id, frame_index, images):
        # Find the new length, which is the longer of the current max length or the new frame_index + number of images
        new_length = max(
            frame_index + len(images),
            max((len(frames) for frames in self._data.values()), default=0),
        )

        # Extend all layers to the new length
        self._ensure_layer_length(new_length)

        # Add new layer if it doesn't exist
        if layer_id not in self._data:
            self._data[layer_id] = [None] * new_length

        # Set images at the correct frame index
        for i, image in enumerate(images):
            self._data[layer_id][frame_index + i] = image

    def __str__(self):
        return str(self._data)
