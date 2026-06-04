from __future__ import annotations

import csv
import os

from datetime import datetime

from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Index,
    text,
)

from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
    Session,
)

from dotenv import load_dotenv

load_dotenv()

# ==========================================================
# DATABASE CONFIG
# ==========================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///store.db"
)

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()

# ==========================================================
# EVENTS TABLE
# ==========================================================


class EventRecord(Base):

    __tablename__ = "events"

    event_id = Column(
        String,
        primary_key=True,
    )

    store_id = Column(
        String,
        nullable=False,
        index=True,
    )

    camera_id = Column(
        String,
        nullable=False,
    )

    visitor_id = Column(
        String,
        nullable=False,
        index=True,
    )

    event_type = Column(
        String,
        nullable=False,
        index=True,
    )

    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    zone_id = Column(
        String,
        nullable=True,
    )

    dwell_ms = Column(
        Integer,
        default=0,
    )

    is_staff = Column(
        Boolean,
        default=False,
    )

    confidence = Column(
        Float,
        nullable=False,
    )

    queue_depth = Column(
        Integer,
        nullable=True,
    )

    session_seq = Column(
        Integer,
        default=0,
    )

    ingested_at = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
    )


# ==========================================================
# POS TABLE
# ==========================================================


class POSTransaction(Base):

    __tablename__ = "pos_transactions"

    transaction_id = Column(
        String,
        primary_key=True,
    )

    store_id = Column(
        String,
        nullable=False,
        index=True,
    )

    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    basket_value_inr = Column(
        Float,
        nullable=False,
    )


# ==========================================================
# EXTRA INDEXES
# ==========================================================

Index(
    "idx_store_event_time",
    EventRecord.store_id,
    EventRecord.timestamp,
)

Index(
    "idx_store_visitor",
    EventRecord.store_id,
    EventRecord.visitor_id,
)

# ==========================================================
# DB INITIALIZATION
# ==========================================================


def init_db() -> None:
    """
    Creates all tables.
    Safe to call multiple times.
    """

    Base.metadata.create_all(bind=engine)


# ==========================================================
# FASTAPI DEPENDENCY
# ==========================================================


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ==========================================================
# POS CSV LOADER
# ==========================================================


def load_pos_csv(filepath: str) -> int:
    """
    Loads POS transactions into database.

    Returns:
        Number of inserted rows.
    """

    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"POS file not found: {filepath}"
        )

    db: Session = SessionLocal()

    inserted = 0

    try:

        with open(
            filepath,
            newline="",
            encoding="utf-8",
        ) as fp:

            reader = csv.DictReader(fp)

            for row in reader:

                txn_id = row.get(
                    "transaction_id"
                )

                if not txn_id:
                    continue

                existing = db.get(
                    POSTransaction,
                    txn_id,
                )

                if existing:
                    continue

                txn = POSTransaction(
                    transaction_id=txn_id,
                    store_id=row["store_id"],
                    timestamp=datetime.fromisoformat(
                        row["timestamp"]
                    ),
                    basket_value_inr=float(
                        row["basket_value_inr"]
                    ),
                )

                db.add(txn)

                inserted += 1

        db.commit()

        return inserted

    except (
        ValueError,
        KeyError,
        OSError,
    ) as exc:

        db.rollback()

        raise RuntimeError(
            f"Failed loading POS CSV: {exc}"
        ) from exc

    finally:
        db.close()