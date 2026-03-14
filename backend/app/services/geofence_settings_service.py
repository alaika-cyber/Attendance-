from datetime import datetime

from sqlalchemy.orm import Session

from app.models import CampusGeofence


def get_geofence(db: Session) -> CampusGeofence | None:
    return db.query(CampusGeofence).order_by(CampusGeofence.id.desc()).first()


def upsert_geofence(db: Session, latitude: float, longitude: float, radius_meters: float) -> CampusGeofence:
    geofence = get_geofence(db)
    if not geofence:
        geofence = CampusGeofence(
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
            updated_at=datetime.utcnow(),
        )
        db.add(geofence)
    else:
        geofence.latitude = latitude
        geofence.longitude = longitude
        geofence.radius_meters = radius_meters
        geofence.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(geofence)
    return geofence
