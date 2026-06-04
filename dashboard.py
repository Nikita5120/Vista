import streamlit as st
import requests
import pandas as pd

st.set_page_config(
    page_title="Store Intelligence Dashboard",
    layout="wide"
)

st.title("🛒 Purplle Store Intelligence")

STORE_ID = "STORE_001"

metrics = requests.get(
    f"http://127.0.0.1:8000/metrics/{STORE_ID}"
).json()

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "👥 Visitors",
    metrics["unique_visitors"]
)

c2.metric(
    "💰 Conversion %",
    f"{metrics['conversion_rate']}%"
)

c3.metric(
    "🧾 Queue Depth",
    metrics["queue_depth"]
)

c4.metric(
    "🛍 Transactions",
    metrics["total_transactions"]
)

st.divider()

st.subheader("Store Performance")
zone_data = requests.get(
    f"http://127.0.0.1:8000/metrics/zones/{STORE_ID}"
).json()

if len(zone_data) > 0:

    zone_df = pd.DataFrame(
        zone_data
    )

    st.subheader(
        "🔥 Most Visited Zones"
    )

    st.bar_chart(
        zone_df.set_index(
            "zone"
        )
    )
st.success(
    f"""
    Store Summary

    • Total Visitors: {metrics['unique_visitors']}
    • Conversion Rate: {metrics['conversion_rate']}%
    • Queue Depth: {metrics['queue_depth']}
    • Transactions: {metrics['total_transactions']}
    """
)


st.subheader(
    "Key Insights"
)

insights = []

if metrics["conversion_rate"] > 10:
    insights.append(
        "Healthy visitor conversion observed."
    )

if metrics["queue_depth"] == 0:
    insights.append(
        "No active queue congestion detected."
    )

if metrics["unique_visitors"] > 10:
    insights.append(
        "Good visitor traffic captured."
    )

for item in insights:
    st.write(
        f"✅ {item}"
    )

st.subheader(
    "📋 Recent Events"
)

events = requests.get(
    f"http://127.0.0.1:8000/metrics/events/{STORE_ID}"
).json()

if len(events) > 0:

    events_df = pd.DataFrame(
        events
    )

    st.dataframe(
        events_df,
        use_container_width=True
    )

summary = pd.DataFrame(
    {
        "Metric": [
            "Visitors",
            "Conversion Rate",
            "Queue Depth",
            "Transactions",
            "Basket Value"
        ],
        "Value": [
            metrics["unique_visitors"],
            metrics["conversion_rate"],
            metrics["queue_depth"],
            metrics["total_transactions"],
            metrics["avg_basket_value"]
        ]
    }
)

st.dataframe(
    summary,
    use_container_width=True
)

st.divider()

st.subheader("📍 Zone Analytics")

zone_data = requests.get(
    f"http://127.0.0.1:8000/metrics/zones/{STORE_ID}"
).json()

st.write(zone_data)  # temporary debug

if len(zone_data) > 0:

    zone_df = pd.DataFrame(zone_data)

    st.bar_chart(
        zone_df.set_index("zone")
    )

st.subheader("📍 Most Visited Zones")

zone_data = requests.get(
    f"http://127.0.0.1:8000/metrics/zones/{STORE_ID}"
).json()

if zone_data:

    zone_df = pd.DataFrame(zone_data)

    st.dataframe(
        zone_df,
        use_container_width=True
    )

    st.bar_chart(
        zone_df.set_index("zone")
    )

st.divider()

st.subheader("API Response")

st.json(metrics)