
from PIL import Image
import os


def analyze_image(image_path):
    """
    Демонстрационный анализ спутникового снимка.
    Оценивает признаки огня и облачности по цветам пикселей.
    """

    if not os.path.exists(image_path):
        return {
            "fire_probability": 0.0,
            "confidence": 0.0,
            "cloudiness": 0,
            "status": "error",
            "message": "Изображение не найдено"
        }

    try:
        image = Image.open(image_path).convert("RGB")
        image.thumbnail((200, 200))

        pixels = list(image.getdata())
        total = len(pixels)

        fire_pixels = 0
        cloud_pixels = 0

        for r, g, b in pixels:
            if r > 180 and g > 60 and g < 160 and b < 100:
                fire_pixels += 1

            if r > 190 and g > 190 and b > 190:
                cloud_pixels += 1

        fire_ratio = fire_pixels / total
        cloud_ratio = cloud_pixels / total

        probability = min(fire_ratio * 8, 1.0)
        confidence = min(total / 10000, 1.0)

        return {
            "fire_probability": round(probability, 3),
            "confidence": round(confidence, 3),
            "cloudiness": round(cloud_ratio * 100),
            "status": "success",
            "message": "Анализ завершён"
        }

    except Exception as error:
        return {
            "fire_probability": 0.0,
            "confidence": 0.0,
            "cloudiness": 0,
            "status": "error",
            "message": str(error)
        }
