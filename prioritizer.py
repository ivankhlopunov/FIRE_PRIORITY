
def calculate_priority(image, minutes_to_contact=30):
    """Рассчитывает приоритет снимка для передачи."""

    probability = image.get("fire_probability", 0)
    confidence = image.get("confidence", 0)
    cloudiness = image.get("cloudiness", 0)
    size = image.get("size_mb", 1)
    age = image.get("age_minutes", 0)
    repeat = image.get("repeat_count", 0)

    priority = 0
    reasons = []

    # Вероятность события и уверенность анализа
    if confidence >= 0.5:
        priority += probability * confidence * 70

        if probability >= 0.6:
            reasons.append("Высокая вероятность пожара")

    else:
        priority += 5
        reasons.append("Низкая уверенность: требуется проверка")

    # Облачность
    priority += (100 - cloudiness) * 0.1

    if cloudiness > 70:
        reasons.append("Высокая облачность")

    # Давность наблюдения
    priority += max(0, 20 - age * 0.2)

    if age < 10:
        reasons.append("Свежий снимок")

    # Повторные наблюдения
    if repeat == 0:
        priority += 10
        reasons.append("Новое наблюдение территории")
    else:
        priority -= min(repeat * 2, 10)

    # Размер файла
    priority -= size * 0.5

    # Срочность следующего сеанса связи
    if minutes_to_contact <= 10:
        priority += 15
        reasons.append("Скоро завершится сеанс связи")
    elif minutes_to_contact <= 30:
        priority += 8
        reasons.append("Ограниченное время до связи")

    return {
        "priority": round(max(0, priority), 2),
        "reason": ", ".join(reasons) if reasons else "Обычный приоритет"
    }


def rank_images(images, minutes_to_contact=30):
    """Сортирует снимки по рассчитанному приоритету."""

    ranked = []

    for image in images:
        result = calculate_priority(
            image,
            minutes_to_contact
        )

        item = image.copy()
        item["priority"] = result["priority"]
        item["priority_reason"] = result["reason"]

        ranked.append(item)

    ranked.sort(
        key=lambda x: x["priority"],
        reverse=True
    )

    return ranked
