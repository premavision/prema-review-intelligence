from __future__ import annotations

import os
from typing import Any

import httpx
import pandas as pd
import streamlit as st

API_BASE_URL = os.getenv("REVIEW_API_BASE_URL", "http://localhost:8000")


@st.cache_data(ttl=60)
def fetch_datasets() -> list[dict[str, Any]]:
    response = httpx.get(f"{API_BASE_URL}/datasets", timeout=20)
    response.raise_for_status()
    return response.json()["datasets"]


@st.cache_data(ttl=120)
def fetch_summary(dataset_id: int, force: bool = False) -> dict[str, Any] | None:
    params = {"force": str(force).lower()} if force else None
    response = httpx.get(
        f"{API_BASE_URL}/datasets/{dataset_id}/summary", params=params, timeout=30
    )
    response.raise_for_status()
    data = response.json()
    return data.get("analysis")


def upload_dataset(name: str, file) -> dict[str, Any]:
    files = {"file": (file.name, file.getvalue())}
    data = {"name": name, "source": "import"}
    response = httpx.post(f"{API_BASE_URL}/datasets", data=data, files=files, timeout=60)
    response.raise_for_status()
    return response.json()


def layout_sidebar() -> tuple[int | None, bool]:
    st.sidebar.header("Datasets")
    datasets = fetch_datasets()
    names = {dataset["name"]: dataset["id"] for dataset in datasets}
    selected_name = st.sidebar.selectbox("Select dataset", options=list(names.keys()) or ["No datasets yet"])
    selected_id = names.get(selected_name)
    force_refresh = st.sidebar.toggle("Force re-run analysis", value=False)
    if st.sidebar.button("Refresh list"):
        fetch_datasets.clear()
    return selected_id, force_refresh


def render_summary(dataset_id: int, force_refresh: bool) -> None:
    summary = fetch_summary(dataset_id, force_refresh)
    if not summary:
        st.info("No analysis available yet. Upload reviews or run analysis via API.")
        return

    stats = summary["stats"]
    st.metric("Average rating", stats["average_rating"])
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total reviews", stats["total_reviews"])
    with col2:
        promoters = round(stats["positive_share"] * 100, 1)
        detractors = round(stats["negative_share"] * 100, 1)
        st.metric("Promoters vs Detractors", f"{promoters}% / {detractors}%")

    distribution = pd.DataFrame(
        {"rating": list(stats["rating_distribution"].keys()), "count": list(stats["rating_distribution"].values())}
    )
    st.bar_chart(distribution.set_index("rating"))

    st.subheader("Narrative summary")
    st.write(summary["summary_text"])

    st.subheader("Themes")
    for theme in summary.get("themes", []):
        with st.expander(f"{theme['name']} ({theme['sentiment']}) — {theme['importance']*100:.1f}% of reviews"):
            st.write(theme.get("summary") or "Representative reviews:")
            for review in theme.get("representative_reviews", []):
                st.markdown(f"*{review['rating']}⭐ — {review.get('title') or 'Review'}*")
                st.write(review["body_excerpt"])


def upload_section() -> None:
    st.sidebar.subheader("Upload new dataset")
    name = st.sidebar.text_input("Dataset name", placeholder="Fall launch set")
    file = st.sidebar.file_uploader("CSV or JSON", type=["csv", "json"])
    if st.sidebar.button("Upload") and file and name:
        with st.spinner("Uploading dataset..."):
            upload_dataset(name, file)
            fetch_datasets.clear()
        st.sidebar.success("Dataset uploaded")


def main() -> None:
    st.set_page_config(page_title="Review Intelligence Dashboard", layout="wide")
    st.title("Prema Review Intelligence")
    dataset_id, force_refresh = layout_sidebar()
    upload_section()
    if dataset_id:
        render_summary(dataset_id, force_refresh)
    else:
        st.info("Select or upload a dataset to see insights.")


if __name__ == "__main__":
    main()

