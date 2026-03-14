from app.services.geofence_service import is_within_geofence


def test_geofence_within_radius():
    assert is_within_geofence(12.9716, 77.5946, 12.9716, 77.5946, 100)


def test_geofence_outside_radius():
    assert not is_within_geofence(12.9816, 77.6046, 12.9716, 77.5946, 100)
