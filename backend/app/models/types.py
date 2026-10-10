from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator
from shapely.geometry.base import BaseGeometry


class SafeGeometry(TypeDecorator):
    """
    Geometry TypeDecorator that stores geometries as WKT (Well-Known Text) in standard Text columns.
    Accepts WKT strings or Shapely geometry objects and serializes them to WKT text.
    Keeps all spatial logic in Python (via Shapely) with no PostGIS or PostgreSQL-only features.
    """
    impl = Text
    cache_ok = True

    def __init__(self, geometry_type: str = "GEOMETRY", srid: int = 4326, spatial_index: bool = False):
        self.geometry_type = geometry_type.upper()
        self.srid = srid
        self.spatial_index = spatial_index
        super().__init__()

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(Text()) if dialect is not None else Text()

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, BaseGeometry):
            return value.wkt
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return str(value)
