from app.analysis.classical import compute_rating_stats, extract_themes
from app.db.models import Review


def test_compute_rating_stats_handles_basic_metrics() -> None:
    reviews = [
        Review(dataset_id=1, body="Great battery", rating=5),
        Review(dataset_id=1, body="Poor strap", rating=2),
    ]
    stats = compute_rating_stats(reviews)
    assert stats.total_reviews == 2
    assert stats.rating_distribution["5"] == 1
    assert round(stats.average_rating, 1) == 3.5


def test_extract_themes_returns_top_terms() -> None:
    reviews = [
        Review(dataset_id=1, body="Battery life is amazing", rating=5, id=1),
        Review(dataset_id=1, body="Battery life could be better", rating=3, id=2),
        Review(dataset_id=1, body="Strap quality is bad", rating=2, id=3),
    ]
    themes = extract_themes(reviews, max_themes=2)
    assert themes
    assert any("Battery" in theme.name for theme in themes)
