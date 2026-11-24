
def run_transmission(images, satellite):
    """Симуляция передачи данных со спутника на Землю."""

    # Общий объём исходных снимков
    total_volume = sum(image.get("size_mb", 0) for image in images)

    # Ограничение на передачу данных
    transfer_percent = satellite.get("transfer_percent", 10)
    transfer_limit = total_volume * transfer_percent / 100

    # Доступная энергия
    energy_limit = satellite.get("energy", 100)

    # Продолжительность сеанса связи
    contact_window = satellite.get("contact_window_minutes", 30)

    # Скорость передачи в МБ за минуту
    transfer_speed = satellite.get("transfer_speed", 5)

    used_volume = 0
    used_energy = 0
    time_used = 0

    results = []

    # Типы данных и доля энергии на их передачу
    variants = [
        ("alert", "alert_size_mb", 0.05),
        ("preview", "preview_size_mb", 0.25),
        ("full", "size_mb", 1.0)
    ]

    # Сначала уведомления, затем превью, затем оригиналы
    for data_type, size_field, energy_factor in variants:
        for image in images:

            size = image.get(size_field, 0)

            if size <= 0:
                continue

            # Энергия зависит от снимка и типа передачи
            energy_cost = image.get("energy_cost", 1) * energy_factor

            # Время передачи снимка
            transmission_time = size / transfer_speed

            # Проверяем ограничения
            if used_volume + size > transfer_limit:
                status = "not_transmitted"
                reason = "Недостаточно свободного объёма"

            elif used_energy + energy_cost > energy_limit:
                status = "not_transmitted"
                reason = "Недостаточно энергии"

            elif time_used + transmission_time > contact_window:
                status = "not_transmitted"
                reason = "Недостаточно времени сеанса"

            else:
                status = "transmitted"
                reason = "Передача выполнена"

                used_volume += size
                used_energy += energy_cost
                time_used += transmission_time

            results.append({
                "image_id": image["image_id"],
                "type": data_type,
                "size_mb": size,
                "energy_cost": round(energy_cost, 3),
                "time_minutes": round(transmission_time, 3),
                "status": status,
                "reason": reason
            })

    return {
        "transmitted": results,
        "used_volume": round(used_volume, 3),
        "transfer_limit": round(transfer_limit, 3),
        "used_energy": round(used_energy, 3),
        "remaining_energy": round(energy_limit - used_energy, 3),
        "time_used": round(time_used, 3),
        "remaining_minutes": round(contact_window - time_used, 3)
    }
