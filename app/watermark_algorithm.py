from PIL import Image, ImageDraw, ImageFont
import math
from logger_settings import logger

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
        logger.debug(f"Loading fonts from fonts/")
        font = ImageFont.truetype("fonts/Roboto-Regular.ttf", font_size)
    except IOError:
        logger.debug(f"Loading default fonts")
        font = ImageFont.load_default()

    # Calculate text dimensions
    logger.debug(f"Calculating text dimensions")
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
        logger.debug(f"creating rotated layer from work_size ({work_size[0]}, {work_size[1]}) to rotated _size ({diagonal}, {diagonal})")
        try:
            rotated_layer = Image.new("RGBA", rotated_size, (0, 0, 0, 0))
        except MemoryError as e:
            logger.error(f"Memory error: {e}")
            # Return a small fallback image
            rotated_layer = Image.new("RGBA", (100, 100), (0, 0, 0, 0))

        # Paste the original layer in the center
        logger.debug(f"pasting original layer in the center")
        paste_x = (rotated_size[0] - work_size[0]) // 2
        paste_y = (rotated_size[1] - work_size[1]) // 2
        rotated_layer.paste(text_layer, (paste_x, paste_y))

        # Rotate the entire layer
        logger.debug(f"rotating entire layer")
        rotated_layer = rotated_layer.rotate(
            angle,
            expand=False,
            resample=Image.BICUBIC,
            fillcolor=(0, 0, 0, 0)
        )

        # Crop back to original size
        crop_x = (rotated_size[0] - image_size[0]) // 2
        crop_y = (rotated_size[1] - image_size[1]) // 2
        logger.debug(f"cropping text layer")
        text_layer = rotated_layer.crop((
            crop_x,
            crop_y,
            crop_x + image_size[0],
            crop_y + image_size[1]
        ))

    return text_layer

def overlay_text_on_image(background_path, output_path, text, **kwargs):
    """Overlays text grid on background image"""
    # Open background and ensure RGBA
    logger.debug(f"loading background")
    background = Image.open(background_path).convert("RGBA")

    # Create text layer matching background size
    logger.debug(f"creating text layer")
    text_layer = create_text_layer3(text, image_size=background.size, **kwargs)

    # Composite images
    logger.debug(f"composing images")
    result = Image.alpha_composite(background, text_layer)

    # Save in appropriate format
    if output_path.lower().endswith('.jpg'):
        result = result.convert("RGB")
    logger.debug(f"saving example")
    result.save(output_path)
    logger.debug(f"saved to {output_path}")
    return True



def apply_watermark(file_path, watermark_text, output_path):
    logger.debug(f"running apply_watermark with arguments {file_path}, {watermark_text}, {output_path}")
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

