"""Puerto del repositorio del negocio."""
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.modules.business.domain.entities import BusinessProfile, Invitation, Location, Member


class BusinessProfileRepository(Protocol):
    async def get(self, business_id: UUID) -> BusinessProfile: ...

    async def update(self, business_id: UUID, changes: dict) -> BusinessProfile: ...

    async def list_locations(self, business_id: UUID) -> list[Location]: ...

    async def get_location(self, business_id: UUID, location_id: UUID) -> Location | None: ...

    async def save_location(self, business_id: UUID, location_id: UUID | None, data: dict) -> Location:
        """Crea (location_id None) o reemplaza una sede. Si es principal, desmarca las demás."""
        ...

    async def delete_location(self, business_id: UUID, location_id: UUID) -> None: ...

    async def list_members(self, business_id: UUID) -> list[Member]: ...

    async def get_member(self, business_id: UUID, user_id: UUID) -> Member | None: ...

    async def find_user_id(self, email: str) -> UUID | None: ...

    async def add_member(self, business_id: UUID, user_id: UUID, role: str) -> None: ...

    async def set_role(self, business_id: UUID, user_id: UUID, role: str) -> None: ...

    async def remove_member(self, business_id: UUID, user_id: UUID) -> None: ...

    async def add_invitation(
        self,
        *,
        business_id: UUID,
        email: str,
        role: str,
        invited_by: UUID,
        token_hash: str,
        code_hash: str,
        expires_at: datetime,
    ) -> Invitation:
        """Anula antes la invitación vigente al mismo correo: reinvitar manda enlace y código nuevos."""
        ...

    async def list_invitations(self, business_id: UUID) -> list[Invitation]:
        """Vigentes y sin vencer."""
        ...

    async def revoke_invitation(self, business_id: UUID, invitation_id: UUID) -> bool: ...

    async def find_invitation(self, token_hash: str) -> Invitation | None:
        """Vigente (sin aceptar ni anular); puede estar vencida."""
        ...

    async def count_invitation_attempt(self, invitation_id: UUID) -> None: ...

    async def accept_invitation(self, invitation_id: UUID) -> None: ...
