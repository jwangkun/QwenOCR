import io
import base64
from PIL import Image

def encode_image_to_base64(image):
    """
    将PIL图像对象转换为base64编码
    """
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")