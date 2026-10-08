from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator
from geoalchemy2 import Geometry
from shapely.geometry.base import BaseGeometry


class SafeGeometry(TypeDecorator):
    """
    Geometry TypeDecorator that compiles to PostGIS Geometry on PostgreSQL
    and Text (storing WKT) on SQLite / non-PostGIS backends.
    Accepts WKT strings or Shapely geometry objects.
    """
    impl = Text
    cache_ok = True

    def __init__(self, geometry_type: str = "GEOMETRY", srid: int = 4326, spatial_index: bool = False):
        self.geometry_type = geometry_type.upper()
        self.srid = srid
        self.spatial_index = spatial_index
        super().__init__()

    def load_dialect_impl(self, dialect):
        if dialect is not None and dialect.name == "postgresql":
            return dialect.type_descriptor(
                Geometry(geometry_type=self.geometry_type, srid=self.srid, spatial_index=self.spatial_index)
            )
        return dialect.type_descriptor(Text()) if dialect is not None else Text()

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, BaseGeometry):
            value = value.wkt
        if dialect is not None and dialect.name == "postgresql":
            if isinstance(value, str) and not value.startswith("SRID="):
                return f"SRID={self.srid};{value}"
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return str(value)
