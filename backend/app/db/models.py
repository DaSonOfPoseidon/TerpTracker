from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.db.base import Base

class Extraction(Base):
    __tablename__ = "extractions"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False, index=True)
    fetched_html_hash = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    source_used = Column(String, nullable=True)  # 'page' | 'coa' | 'api'
    status = Column(String, default='pending')  # 'pending' | 'completed' | 'failed'
    evidence = Column(JSON, nullable=True)  # Store detection evidence
    error_message = Column(Text, nullable=True)

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    strain_normalized = Column(String, nullable=False, index=True)
    terp_vector = Column(JSON, nullable=False)  # {myrcene: 0.8, limonene: 0.5, ...}
    totals = Column(JSON, nullable=True)  # {total_terps: 2.1, thc: 23.4, thca: 25.0, ...}
    category = Column(String, nullable=False)  # BLUE|YELLOW|PURPLE|GREEN|ORANGE|RED
    provenance = Column(JSON, nullable=True)  # Source metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    extraction_id = Column(Integer, nullable=True)  # Link to extraction if applicable

class TerpeneDef(Base):
    __tablename__ = "terpene_defs"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False, index=True)  # 'myrcene', 'limonene', etc
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    effects = Column(JSON, nullable=True)  # Array of effect strings
    aroma = Column(String, nullable=True)
    also_found_in = Column(JSON, nullable=True)  # Array of other sources

class Cache(Base):
    __tablename__ = "cache"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
