# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

from PIL import Image, ImageDraw, ImageFont

from PIL import Image, ImageDraw, ImageFont

from PIL import Image, ImageDraw, ImageFont
import math


def create_text_layer3(text, font_size=50, text_color=(255, 255, 255, 128),
                      image_size=(800, 600), rows=1, cols=1,
                      h_spacing=100, v_spacing=100, angle=0):
    """
    Creates a transparent image with text items in a grid and rotates the entire layer.
    Maintains exact pixel spacing between elements with optional rotation.
    """
    work_size = (2 * image_size[0], 2 * image_size[1])
    # Create base transparent image
    text_layer = Image.new("RGBA", work_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)

    # Load font with fallback
    try:
        font = ImageFont.truetype("fonts/Roboto-Regular.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    # Calculate text dimensions
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Calculate total grid dimensions
    grid_width = cols * (text_width + h_spacing) - h_spacing
    grid_height = rows * (text_height + v_spacing) - v_spacing

    # Center the grid in the output image
    start_x = (work_size[0] - grid_width) // 2
    start_y = (work_size[1] - grid_height) // 2

    # Draw each text item in the grid
    for row in range(rows):
        for col in range(cols):
            x = start_x + col * (text_width + h_spacing)
            y = start_y + row * (text_height + v_spacing)
            draw.text((x, y), text, font=font, fill=text_color)

    # Rotate the entire text layer if angle is specified
    if angle != 0:
        # Create a new image large enough to hold the rotated layer
        diagonal = int(math.sqrt(work_size[0] ** 2 + work_size[1] ** 2))
        rotated_size = (diagonal, diagonal)
        rotated_layer = Image.new("RGBA", rotated_size, (0, 0, 0, 0))

        # Paste the original layer in the center
        paste_x = (rotated_size[0] - work_size[0]) // 2
        paste_y = (rotated_size[1] - work_size[1]) // 2
        rotated_layer.paste(text_layer, (paste_x, paste_y))

        # Rotate the entire layer
        rotated_layer = rotated_layer.rotate(
            angle,
            expand=False,
            resample=Image.BICUBIC,
            fillcolor=(0, 0, 0, 0)
        )

        # Crop back to original size
        crop_x = (rotated_size[0] - image_size[0]) // 2
        crop_y = (rotated_size[1] - image_size[1]) // 2
        text_layer = rotated_layer.crop((
            crop_x,
            crop_y,
            crop_x + image_size[0],
            crop_y + image_size[1]
        ))

    return text_layer
def create_text_layer2(text, font_size=50, text_color=(255, 255, 255, 128),
                     image_size=(800, 600), rows=1, cols=1,
                     h_spacing=100, v_spacing=100):
    """
    Creates a transparent image with text items in a grid.
    Maintains exact pixel spacing between elements without rotation or extra padding.
    """

    # Create base transparent image
    text_layer = Image.new("RGBA", image_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)

    # Load font with fallback
    try:
        font = ImageFont.truetype("fonts/Roboto-Regular.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    # Calculate text dimensions
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Calculate total grid dimensions
    grid_width = cols * (text_width + h_spacing) - h_spacing
    grid_height = rows * (text_height + v_spacing) - v_spacing

    # Center the grid in the output image
    start_x = (image_size[0] - grid_width) // 2
    start_y = (image_size[1] - grid_height) // 2

    # Draw each text item in the grid
    for row in range(rows):
        for col in range(cols):
            x = start_x + col * (text_width + h_spacing)
            y = start_y + row * (text_height + v_spacing)
            draw.text((x, y), text, font=font, fill=text_color)

    return text_layer

def create_text_layer(text, font_size=50, text_color=(255, 255, 255, 128),
                      image_size=(800, 600), rows=1, cols=1,
                      h_spacing=50, v_spacing=50, angle=0):
    """
    Creates a transparent image with properly rotated text items in a grid.
    Ensures no clipping of rotated text.
    """
    # Create base transparent image
    text_layer = Image.new("RGBA", image_size, (0, 0, 0, 0))
    temp_draw = ImageDraw.Draw(text_layer)

    # Load font with fallback
    try:
        font = ImageFont.truetype("fonts/Roboto-Regular.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    # Calculate text size before rotation
    bbox = temp_draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Create sufficiently large canvas for rotation
    diagonal = int(math.sqrt(text_width ** 2 + text_height ** 2))
    #canvas_size = diagonal + 0  # Add padding
    text_cell = Image.new("RGBA", (text_width, text_height), (0, 0, 0, 0))
    cell_draw = ImageDraw.Draw(text_cell)

    # Draw text centered on rotation canvas
    x = (text_width) / 2
    y = (text_height) / 2
    cell_draw.text((x, y), text, font=font, fill=text_color)

    # Rotate the text cell
    if angle != 0:
        text_cell = text_cell.rotate(angle, expand=False, resample=Image.BICUBIC, fillcolor=(0, 0, 0, 0))

    # Get actual size after rotation
    rotated_width, rotated_height = text_cell.size

    # Calculate grid positions with proper spacing
    cell_width = rotated_width + h_spacing
    cell_height = rotated_height + v_spacing

    # Center the grid in the output image
    grid_width = cols * cell_width - h_spacing
    grid_height = rows * cell_height - v_spacing
    start_x = (image_size[0] - grid_width) // 2
    start_y = (image_size[1] - grid_height) // 2

    # Draw each text cell in the grid
    for row in range(rows):
        for col in range(cols):
            x_pos = int(start_x + col * cell_width)
            y_pos = int(start_y + row * cell_height)
            text_layer.paste(text_cell, (x_pos, y_pos), text_cell)

    return text_layer



def overlay_text_on_image(background_path, output_path, text, **kwargs):
    """Overlays text grid on background image"""
    # Open background and ensure RGBA
    background = Image.open(background_path).convert("RGBA")

    # Create text layer matching background size
    text_layer = create_text_layer3(text, image_size=background.size, **kwargs)

    # Composite images
    result = Image.alpha_composite(background, text_layer)

    # Save in appropriate format
    if output_path.lower().endswith('.jpg'):
        result = result.convert("RGB")
    result.save(output_path)
    return True



def apply_watermark(file_path, watermark_text, output_path):
    FONTSIZE = 30
    ROWS = 50
    COLUMNS = 50
    ANGLE = 40


    return overlay_text_on_image(
        background_path=file_path,
        output_path=output_path,
        text=watermark_text,
        font_size=FONTSIZE,
        rows=ROWS,
        cols=COLUMNS,
        angle=ANGLE,
        text_color=(255, 100, 100, 228),
        h_spacing=20,
        v_spacing=60
    )

