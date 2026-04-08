"""Team models shim.

Defines `TeamMembership` used by endpoints to query team memberships.
This is a minimal model sufficient for query-time imports and tests.
"""

import uuid
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class TeamMembership(Base):
    __tablename__ = "team_memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    team_id = Column(UUID(as_uuid=True), nullable=False)
