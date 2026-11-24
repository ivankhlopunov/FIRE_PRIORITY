
from prioritizer import rank_images
from simulator import run_transmission


def calculate_metrics(results, images):
    """Рассчитывает показатели качества передачи снимков."""

    important_events = 0
    delivered_events = 0
    missed_events = 0

    true_fire_ids = set()
    delivered_alert_ids = set()

    for image in images:
        if image.get("true_fire", False):
            important_events += 1
            true_fire_ids.add(image["image_id"])

    for result in results["transmitted"]:
        if (
            result["type"] == "alert"
            and result["status"] == "transmitted"
        ):
            delivered_alert_ids.add(result["image_id"])

    for image_id in true_fire_ids:
        if image_id in delivered_alert_ids:
            delivered_events += 1
        else:
            missed_events += 1

    false_alerts = 0

    for image_id in delivered_alert_ids:
        if image_id not in true_fire_ids:
            false_alerts += 1

    if important_events > 0:
        recall = delivered_events / important_events * 100
    else:
        recall = 0

    if len(delivered_alert_ids) > 0:
        precision = (
            delivered_events / len(delivered_alert_ids) * 100
        )
    else:
        precision = 0

    return {
        "important_events": important_events,
        "delivered_events": delivered_events,
        "missed_events": missed_events,
        "false_alerts": false_alerts,
        "recall": round(recall, 2),
        "precision": round(precision, 2),
        "used_volume": results["used_volume"],
        "transfer_limit": results["transfer_limit"],
        "used_energy": results["used_energy"],
        "remaining_energy": results["remaining_energy"],
        "time_used": results["time_used"],
        "remaining_minutes": results["remaining_minutes"]
    }


def compare_algorithms(images, satellite, minutes_to_contact=None):
    """Сравнивает FIFO и FIRE PRIORITY в одинаковых условиях."""

    fifo_images = [image.copy() for image in images]

    if minutes_to_contact is None:
        minutes_to_contact = satellite.get(
            "minutes_to_contact", 30
        )

    priority_images = rank_images(
        [image.copy() for image in images],
        minutes_to_contact
    )

    satellite_settings = satellite.copy()
    satellite_settings["minutes_to_contact"] = minutes_to_contact

    fifo_result = run_transmission(
        fifo_images,
        satellite_settings.copy()
    )

    priority_result = run_transmission(
        priority_images,
        satellite_settings.copy()
    )

    fifo_metrics = calculate_metrics(
        fifo_result,
        fifo_images
    )

    priority_metrics = calculate_metrics(
        priority_result,
        priority_images
    )

    return {
        "FIFO": fifo_metrics,
        "FIRE PRIORITY": priority_metrics
    }
