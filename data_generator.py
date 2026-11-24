"""Генерация демонстрационного потока спутниковых снимков."""
from datetime import datetime, timedelta
import random


def generate_dataset(count=30, seed=42):
    """Возвращает список снимков в едином формате проекта.

    true_fire — только тестовая метка для расчёта метрик.
    Её нельзя использовать в detector.py или prioritizer.py.
    """
    random.seed(seed)
    start = datetime(2026, 11, 24, 9, 0)
    images = []

    fire_indices = {5, 17, 23}
    for number in range(count):
        is_test_fire = number in fire_indices
        cloudiness = random.randint(0, 85)
        probability = round(random.uniform(0.02, 0.35), 2)
        confidence = round(random.uniform(0.55, 0.98), 2)

        if is_test_fire:
            probability = round(random.uniform(0.78, 0.98), 2)
            confidence = round(random.uniform(0.75, 0.97), 2)
            cloudiness = random.randint(0, 35)

        captured = start + timedelta(minutes=number * 4)
        image_id = f"IMG_{number + 1:03d}"

        images.append({
            "image_id": image_id,
            "timestamp": captured.strftime("%Y-%m-%d %H:%M:%S"),
            "latitude": round(52.0 + random.uniform(-3, 3), 5),
            "longitude": round(35.0 + random.uniform(-5, 5), 5),
            "area_id": f"AREA_{number % 8 + 1:02d}",
            "fire_probability": probability,
            "confidence": confidence,
            "cloudiness": cloudiness,
            "size_mb": round(random.uniform(1.0, 5.0), 2),
            "preview_size_mb": 0.30,
            "alert_size_mb": 0.01,
            "energy_cost": round(random.uniform(1.0, 4.0), 2),
            "image_path": f"data/images/{image_id}.jpg",
            "priority": 0,
            "transmission_status": "pending",
            "true_fire": is_test_fire
        })
    return images


if __name__ == "__main__":
    import csv
    rows = generate_dataset()
    with open("data/satellite_data.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Создано снимков: {len(rows)}")
