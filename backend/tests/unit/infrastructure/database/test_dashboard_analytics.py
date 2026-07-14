import pytest

from boutique.infrastructure.database.dashboard_query_service import _build_log_normal_fit


@pytest.mark.unit
def test_log_normal_fit_includes_parametric_and_kde_density_curves() -> None:
    fit = _build_log_normal_fit(values=[20.0, 35.0, 60.0, 95.0, 180.0])

    assert fit.sample_size == 5
    assert fit.mu is not None
    assert fit.sigma is not None
    assert fit.log_likelihood is not None
    assert fit.aic is not None
    assert fit.bic is not None
    assert len(fit.density_points) == 41
    assert len(fit.kde_points) == 41
    assert len(fit.qq_points) == 5
    assert all(point.density >= 0 for point in fit.kde_points)


@pytest.mark.unit
def test_log_normal_fit_reports_insufficient_data_without_fake_statistics() -> None:
    fit = _build_log_normal_fit(values=[50.0])

    assert fit.sample_size == 1
    assert fit.mu is None
    assert fit.kde_points == []
