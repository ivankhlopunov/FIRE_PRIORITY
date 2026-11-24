
import os
from datetime import datetime

import streamlit as st
import pandas as pd

from data_generator import generate_dataset
from detector import analyze_image
from prioritizer import rank_images
from simulator import run_transmission
from metrics import compare_algorithms


# ==================================================
# НАСТРОЙКА
# ==================================================

st.set_page_config(
    page_title="FIRE PRIORITY",
    page_icon="🛰️",
    layout="wide"
)

st.title("🛰️ FIRE PRIORITY")
st.caption(
    "Интеллектуальная система раннего оповещения "
    "о возможных природных пожарах"
)


# ==================================================
# ГЕНЕРАЦИЯ АВАРИЙНОГО СЦЕНАРИЯ
# ==================================================

def generate_emergency_scenario():
    """Создаёт поток снимков для аварийной симуляции."""

    images = generate_dataset(count=60, seed=77)

    fire_indices = [8, 19, 31, 44, 53]

    for number, image in enumerate(images):
        image["size_mb"] = round(
            3.0 + (number % 5) * 0.7, 2
        )

        image["alert_size_mb"] = 0.01
        image["preview_size_mb"] = 0.30
        image["energy_cost"] = 2.0 + (number % 4)

        # Тестовая метка используется только для метрик.
        image["true_fire"] = number in fire_indices

        if number in fire_indices:
            image["fire_probability"] = 0.95
            image["confidence"] = 0.92
            image["cloudiness"] = 5

    return images


# ==================================================
# ПОДГОТОВКА ДАННЫХ
# ==================================================

if "images" not in st.session_state:
    st.session_state.images = generate_dataset()

if "scenario_name" not in st.session_state:
    st.session_state.scenario_name = "Обычный сценарий"

if "simulation" not in st.session_state:
    st.session_state.simulation = None


images = [
    image.copy()
    for image in st.session_state.images
]

latest_time = max(
    datetime.strptime(
        image["timestamp"],
        "%Y-%m-%d %H:%M:%S"
    )
    for image in images
)

area_counts = {}

for image in images:
    captured = datetime.strptime(
        image["timestamp"],
        "%Y-%m-%d %H:%M:%S"
    )

    image["age_minutes"] = (
        latest_time - captured
    ).total_seconds() / 60

    area = image["area_id"]

    image["repeat_count"] = area_counts.get(area, 0)
    area_counts[area] = area_counts.get(area, 0) + 1

    image["analysis_source"] = "Демонстрационные данные"
    image["analysis_status"] = "success"

    path = image.get("image_path", "")

    if path and os.path.exists(path):
        detection = analyze_image(path)

        image["analysis_status"] = detection["status"]

        if detection["status"] == "success":
            image["fire_probability"] = detection["fire_probability"]
            image["confidence"] = detection["confidence"]
            image["cloudiness"] = detection["cloudiness"]
            image["analysis_source"] = "Анализ изображения"
        else:
            image["confidence"] = 0
            image["analysis_source"] = "Ошибка анализа"


# ==================================================
# БОКОВАЯ ПАНЕЛЬ
# ==================================================

st.sidebar.header("🛰️ Управление спутником")

transfer_percent = st.sidebar.slider(
    "Доступная доля канала, %",
    1, 30, 10
)

energy = st.sidebar.slider(
    "Запас энергии",
    1, 200, 5
)

minutes_to_contact = st.sidebar.slider(
    "Время до завершения сеанса связи, мин",
    1, 60, 30
)

st.sidebar.divider()

mode = st.sidebar.radio(
    "Режим диспетчера",
    ["Обычный режим", "🚨 Аварийный режим"]
)

if st.sidebar.button("🔄 Обычный поток"):
    st.session_state.images = generate_dataset()
    st.session_state.scenario_name = "Обычный сценарий"
    st.session_state.simulation = None
    st.rerun()

if st.sidebar.button(
    "🚨 Смоделировать аварию",
    type="primary",
    use_container_width=True
):
    st.session_state.images = generate_emergency_scenario()
    st.session_state.scenario_name = "Аварийный сценарий"
    st.session_state.simulation = None
    st.rerun()


# ==================================================
# РАСЧЁТ ПРИОРИТЕТОВ
# ==================================================

ranked_images = rank_images(
    images,
    minutes_to_contact
)

if mode == "🚨 Аварийный режим":
    for image in ranked_images:
        image["emergency_score"] = round(
            image["fire_probability"]
            * image["confidence"]
            * (1 - image["cloudiness"] / 100),
            4
        )

    ranked_images.sort(
        key=lambda x: (
            x["emergency_score"],
            x["priority"]
        ),
        reverse=True
    )

    for image in ranked_images:
        image["dispatcher_reason"] = (
            "Аварийный приоритет. "
            f"Оценка опасности: {image['emergency_score']:.2f}"
        )
else:
    for image in ranked_images:
        image["dispatcher_reason"] = image["priority_reason"]


# ==================================================
# ЗАГОЛОВОК ДИСПЕТЧЕРА
# ==================================================

st.subheader("🧠 SMART SATELLITE DISPATCHER")

st.caption(
    f"Активный сценарий: {st.session_state.scenario_name}"
)

if mode == "🚨 Аварийный режим":
    st.error(
        "АВАРИЙНЫЙ РЕЖИМ: повышенный приоритет "
        "событий с признаками возможного пожара."
    )
else:
    st.success(
        "Обычный режим: диспетчер использует "
        "стандартный алгоритм приоритизации."
    )

st.info(
    "Тестовые метки пожаров используются только для оценки "
    "качества алгоритма. Они не участвуют в принятии решений."
)


# ==================================================
# ОБЩАЯ СТАТИСТИКА
# ==================================================

total_volume = sum(
    image["size_mb"] for image in images
)

transfer_limit = (
    total_volume * transfer_percent / 100
)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Получено снимков", len(images))
col2.metric("Объём данных", f"{total_volume:.2f} МБ")
col3.metric("Лимит передачи", f"{transfer_limit:.2f} МБ")
col4.metric("Запас энергии", energy)


# ==================================================
# ВКЛАДКИ
# ==================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "🛰️ Мониторинг",
    "🚨 Оповещения",
    "📡 Передача",
    "📊 Аналитика"
])


# ==================================================
# МОНИТОРИНГ
# ==================================================

with tab1:
    st.subheader("Поток спутниковых снимков")

    df = pd.DataFrame(images)

    st.dataframe(
        df[
            [
                "image_id",
                "timestamp",
                "latitude",
                "longitude",
                "area_id",
                "fire_probability",
                "confidence",
                "cloudiness",
                "size_mb",
                "analysis_source"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Состояние анализа")

    errors = sum(
        image["analysis_status"] == "error"
        for image in images
    )

    low_confidence = sum(
        image["confidence"] < 0.5
        for image in images
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Проанализировано", len(images) - errors)
    col2.metric("Низкая уверенность", low_confidence)
    col3.metric("Ошибки анализа", errors)


# ==================================================
# ОПОВЕЩЕНИЯ
# ==================================================

with tab2:
    st.subheader("Возможные события")

    alerts = [
        image for image in ranked_images
        if image["fire_probability"] >= 0.6
    ]

    review_items = [
        image for image in ranked_images
        if (
            image["analysis_status"] == "error"
            or image["confidence"] < 0.5
        )
    ]

    st.metric(
        "Событий с высокой вероятностью",
        len(alerts)
    )

    if alerts:
        for image in alerts:
            with st.expander(
                f"🔥 {image['image_id']} — "
                f"{image['fire_probability'] * 100:.1f}%"
            ):
                st.write(
                    f"Координаты: "
                    f"{image['latitude']}, {image['longitude']}"
                )

                st.write(
                    f"Уверенность: {image['confidence']:.2f}"
                )

                st.write(
                    f"Облачность: {image['cloudiness']}%"
                )

                st.write(
                    f"Причина приоритета: "
                    f"{image['dispatcher_reason']}"
                )

                st.warning(
                    "Возможный пожар. "
                    "Требуется проверка наземной службой."
                )
    else:
        st.success(
            "Событий с высокой вероятностью не обнаружено."
        )

    st.divider()

    st.subheader("Очередь ручной проверки")

    st.caption(
        "Снимки с ошибками анализа или низкой уверенностью "
        "не исключаются из системы."
    )

    st.metric("Требуют проверки", len(review_items))

    if review_items:
        review_df = pd.DataFrame([
            {
                "Снимок": image["image_id"],
                "Статус анализа": image["analysis_status"],
                "Уверенность": image["confidence"],
                "Вероятность": image["fire_probability"],
                "Причина": (
                    "Ошибка анализа"
                    if image["analysis_status"] == "error"
                    else "Низкая уверенность"
                )
            }
            for image in review_items
        ])

        st.dataframe(
            review_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("Снимков, требующих ручной проверки, нет.")


# ==================================================
# ПЕРЕДАЧА
# ==================================================

with tab3:
    st.subheader("Управление передачей данных")

    st.write(
        "Последовательность передачи: "
        "**Alert → Preview → Full**."
    )

    satellite = {
        "transfer_percent": transfer_percent,
        "energy": energy,
        "minutes_to_contact": minutes_to_contact
    }

    if st.button(
        "🚀 Запустить передачу",
        type="primary",
        use_container_width=True
    ):
        st.session_state.simulation = run_transmission(
            ranked_images,
            satellite
        )

    if st.session_state.simulation is not None:
        result = st.session_state.simulation

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Передано",
            f"{result['used_volume']:.2f} МБ"
        )

        col2.metric(
            "Лимит",
            f"{result['transfer_limit']:.2f} МБ"
        )

        col3.metric(
            "Использовано энергии",
            f"{result['used_energy']:.2f}"
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Остаток энергии",
            f"{result['remaining_energy']:.2f}"
        )

        col2.metric(
            "Затрачено времени",
            f"{result['time_used']:.3f} мин"
        )

        col3.metric(
            "Осталось времени",
            f"{result['remaining_minutes']:.3f} мин"
        )

        transmission_df = pd.DataFrame(
            result["transmitted"]
        )

        st.subheader("Результаты передачи")

        st.dataframe(
            transmission_df,
            use_container_width=True,
            hide_index=True
        )

        transmitted_count = sum(
            item["status"] == "transmitted"
            for item in result["transmitted"]
        )

        not_transmitted_count = sum(
            item["status"] == "not_transmitted"
            for item in result["transmitted"]
        )

        col1, col2 = st.columns(2)

        col1.metric("Успешно передано", transmitted_count)
        col2.metric("Не передано", not_transmitted_count)


# ==================================================
# АНАЛИТИКА
# ==================================================

with tab4:
    st.subheader("Сравнение FIFO и FIRE PRIORITY")

    satellite = {
        "transfer_percent": transfer_percent,
        "energy": energy,
        "minutes_to_contact": minutes_to_contact
    }

    comparison = compare_algorithms(
        images,
        satellite,
        minutes_to_contact
    )

    comparison_df = pd.DataFrame(comparison).T

    st.dataframe(
        comparison_df,
        use_container_width=True
    )

    st.subheader("Доставка важных событий")

    chart_data = pd.DataFrame({
        "Алгоритм": ["FIFO", "FIRE PRIORITY"],
        "Доставлено": [
            comparison["FIFO"]["delivered_events"],
            comparison["FIRE PRIORITY"]["delivered_events"]
        ],
        "Пропущено": [
            comparison["FIFO"]["missed_events"],
            comparison["FIRE PRIORITY"]["missed_events"]
        ]
    })

    st.bar_chart(
        chart_data.set_index("Алгоритм")
    )

    st.subheader("Качество обнаружения")

    quality_data = pd.DataFrame({
        "Алгоритм": ["FIFO", "FIRE PRIORITY"],
        "Recall": [
            comparison["FIFO"]["recall"],
            comparison["FIRE PRIORITY"]["recall"]
        ],
        "Precision": [
            comparison["FIFO"]["precision"],
            comparison["FIRE PRIORITY"]["precision"]
        ]
    })

    st.bar_chart(
        quality_data.set_index("Алгоритм")
    )

    st.subheader("Использование канала")

    volume_data = pd.DataFrame({
        "Алгоритм": ["FIFO", "FIRE PRIORITY"],
        "Объём": [
            comparison["FIFO"]["used_volume"],
            comparison["FIRE PRIORITY"]["used_volume"]
        ]
    })

    st.bar_chart(
        volume_data.set_index("Алгоритм")
    )

    st.subheader("Расход энергии")

    energy_data = pd.DataFrame({
        "Алгоритм": ["FIFO", "FIRE PRIORITY"],
        "Энергия": [
            comparison["FIFO"]["used_energy"],
            comparison["FIRE PRIORITY"]["used_energy"]
        ]
    })

    st.bar_chart(
        energy_data.set_index("Алгоритм")
    )

    if st.session_state.scenario_name == "Аварийный сценарий":
        st.success(
            "Аварийный сценарий активен. "
            "Алгоритмы сравниваются при одинаковых "
            "ограничениях канала, энергии и времени."
        )


# ==================================================
# ЗАВЕРШЕНИЕ
# ==================================================

st.divider()

st.caption(
    "FIRE PRIORITY | SMART SATELLITE DISPATCHER"
)

st.caption(
    "Демонстрационная модель. Анализ изображений основан "
    "на эвристиках и не заменяет профессиональную проверку."
)
