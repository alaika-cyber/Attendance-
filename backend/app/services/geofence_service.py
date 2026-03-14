from math import asin, cos, radians, sin, sqrt


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371000
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return radius * c


def is_within_geofence(
    current_lat: float,
    current_lon: float,
    center_lat: float,
    center_lon: float,
    radius_meters: float,
) -> bool:
    return (
        haversine_distance_meters(current_lat, current_lon, center_lat, center_lon)
        <= radius_meters
    )
