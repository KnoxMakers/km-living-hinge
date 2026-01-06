# Functions that return segments to draw each shape based on height/width
# Configs that are highly opinionated to calculate some parameters

def line_shape(height, width):
    return [
        [(0, 0), (0, height)]
    ]


def fishbone_shape(height, width):
    mid_x = width / 2
    return [
        [(0, 0), (mid_x, height), (width, 0)]
    ]


def cross_shape(height, width):
    dx = width * 0.1
    mid_y = height / 2
    left_inner = width * 0.25 + dx
    right_inner = width * 0.75 - dx

    return [
        [(0, 0), (left_inner, mid_y), (0, height)],
        [(left_inner, mid_y), (right_inner, mid_y)],
        [(width, 0), (right_inner, mid_y), (width, height)],
    ]


def bezier_shape(height, width, anchor_tip=0.2, anchor_center=0.3):
    return [
        ('C', [
            (0, 0),
            (width * anchor_tip, 0),
            (width * (0.5 - anchor_center), height),
            (width * 0.5, height)
        ]),
        ('C', [
            (width * 0.5, height),
            (width * (0.5 + anchor_center), height),
            (width * (1 - anchor_tip), 0),
            (width, 0)
        ]),
    ]


def wave_shape(height, width, param_a=0.0, param_b=0.0):
    mid_y = height / 2

    return [
        ('L', [(0, 0), (width * 0.25, 0)]),
        ('Q', [(width * 0.25, 0), (width * (0.5 + param_a), height * param_b), (width * 0.5, mid_y)]),
        ('Q', [(width * 0.5, mid_y), (width * (0.5 - param_a), height * (1 - param_b)), (width * 0.75, height)]),
        ('L', [(width * 0.75, height), (width, height)]),
    ]


def fabric_shape(height, width):
    line1 = [
        (width * 0.25, height * 0.25),
        (width * 0.0, height * 0.25),
        (width * 0.0, height * 0.0),
        (width * 0.5, height * 0.0),
        (width * 0.5, height * 1.0),
        (width * 1.0, height * 1.0),
        (width * 1.0, height * 0.75),
        (width * 0.75, height * 0.75),
    ]

    line2 = [
        (width * 0.75, height * 0.25),
        (width * 0.75, height * 0.0),
        (width * 1.0, height * 0.0),
        (width * 1.0, height * 0.5),
        (width * 0.0, height * 0.5),
        (width * 0.0, height * 1.0),
        (width * 0.25, height * 1.0),
        (width * 0.25, height * 0.75),
    ]

    return [line1, line2]


def line_config(height, width, x_spacing, y_spacing, bbox):
    _, _, _, bbox_height = bbox
    height = height * bbox_height
    y_offset = (height + y_spacing) / 2
    return (height, 0, x_spacing, y_spacing, y_offset)


def fishbone_config(height, width, x_spacing, y_spacing, bbox):
    y_offset = (height + y_spacing) / 2
    return (height, width, x_spacing, y_spacing, y_offset)


def cross_config(height, width, x_spacing, y_spacing, bbox):
    x_spacing = -0.4 * width
    y_spacing = height
    y_offset = height
    return (height, width, x_spacing, y_spacing, y_offset)


def bezier_config(height, width, x_spacing, y_spacing, bbox):
    y_offset = (height + y_spacing) / 2
    return (height, width, x_spacing, y_spacing, y_offset)


def wave_config(height, width, x_spacing, y_spacing, bbox):
    x_spacing = -0.2 * width
    y_spacing = 0
    y_offset = 0.5 * height
    return (height, width, x_spacing, y_spacing, y_offset)


def fabric_config(height, width, x_spacing, y_spacing, bbox):
    x_spacing = -0.375 * width
    y_spacing = 0.25 * height
    y_offset = 0.625 * height
    return (height, width, x_spacing, y_spacing, y_offset)


SHAPES = {
    'line': line_shape,
    'fishbone': fishbone_shape,
    'cross': cross_shape,
    'bezier': bezier_shape,
    'wave': wave_shape,
    'fabric': fabric_shape,
}

CONFIGS = {
    'line': line_config,
    'fishbone': fishbone_config,
    'cross': cross_config,
    'bezier': bezier_config,
    'wave': wave_config,
    'fabric': fabric_config,
}


def get_shape(shape_type):
    return SHAPES.get(shape_type, line_shape)


def get_config(shape_type):
    return CONFIGS.get(shape_type, line_config)
