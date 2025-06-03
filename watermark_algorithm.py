# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

from PIL import Image, ImageDraw, ImageFont

from PIL import Image, ImageDraw, ImageFont

from PIL import Image, ImageDraw, ImageFont
import math


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
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    # Calculate text size before rotation
    bbox = temp_draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Create sufficiently large canvas for rotation
    diagonal = int(math.sqrt(text_width ** 2 + text_height ** 2))
    canvas_size = diagonal + 20  # Add padding
    text_cell = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    cell_draw = ImageDraw.Draw(text_cell)

    # Draw text centered on rotation canvas
    x = (canvas_size - text_width) // 2
    y = (canvas_size - text_height) // 2
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
    text_layer = create_text_layer(text, image_size=background.size, **kwargs)

    # Composite images
    result = Image.alpha_composite(background, text_layer)

    # Save in appropriate format
    if output_path.lower().endswith('.jpg'):
        result = result.convert("RGB")
    result.save(output_path)
    return True


def calculate_grid_spacing(
        background_path,
        text,
        font_size,
        rows,
        cols,
        angle=0,
        padding_ratio=0.1
):
    """
    Calculates optimal h_spacing and v_spacing for a rotated text grid on a background image.

    Args:
        background_path (str): Path to background image
        text (str): Text to be displayed in grid
        font_size (int): Fixed font size in points
        rows (int): Number of grid rows
        cols (int): Number of grid columns
        angle (float): Text rotation angle in degrees (default: 0)
        padding_ratio (float): Spacing ratio relative to text size (0.0-1.0)

    Returns:
        tuple: (h_spacing, v_spacing) in pixels
    """
    # Get background dimensions
    with Image.open(background_path) as bg:
        bg_width, bg_height = bg.size

    # Create temporary drawing context
    temp_img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
    draw = ImageDraw.Draw(temp_img)

    # Load font with fallback
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    # Get unrotated text dimensions
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Calculate rotated dimensions using trigonometry
    rad = math.radians(angle)
    rotated_width = abs(text_width * math.cos(rad)) + abs(text_height * math.sin(rad))
    rotated_height = abs(text_height * math.cos(rad)) + abs(text_width * math.sin(rad))

    # Calculate maximum available space per cell
    max_cell_width = bg_width / cols
    max_cell_height = bg_height / rows

    # Calculate base spacing (centered in each cell)
    h_spacing = max(0, int((max_cell_width - rotated_width) * padding_ratio))
    v_spacing = max(0, int((max_cell_height - rotated_height) * padding_ratio))

    # Ensure minimum spacing of 1 pixel
    h_spacing = max(1, h_spacing)
    v_spacing = max(1, v_spacing)

    return h_spacing, v_spacing

'''
if __name__ == "__main__":
    overlay_text_on_image(
        background_path="passport.jpg",
        output_path="output.png",
        text="WATERMARK",
        font_size=30,
        rows=3,
        cols=3,
        angle=30,
        text_color=(255, 100, 100, 228),
        h_spacing=5,
        v_spacing=10
    )
'''
def apply_watermark(file_path, watermark_text, output_path):
    FONTSIZE = 30
    ROWS = 10
    COLUMNS = 5
    ANGLE = 30

    # Calculate spacing automatically
    h_spacing, v_spacing = calculate_grid_spacing(
        background_path=file_path,
        text=watermark_text,
        font_size=FONTSIZE,
        rows=ROWS,
        cols=COLUMNS,
        angle=ANGLE,
        padding_ratio=0.2  # 20% padding around text
    )

    return overlay_text_on_image(
        background_path=file_path,
        output_path=output_path,
        text=watermark_text,
        font_size=FONTSIZE,
        rows=ROWS,
        cols=COLUMNS,
        angle=ANGLE,
        text_color=(255, 100, 100, 228),
        h_spacing=h_spacing,
        v_spacing=v_spacing
    )

