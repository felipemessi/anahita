"""CombatService orchestrates encounter and participant management.

Covers both the REST CRUD that happens outside the live turn flow
(creating/listing encounters, starting one, adding/updating/removing
participants) and the live actions driven by `app.combat.ws_router` over
WebSocket (advance turn, damage/heal/condition, end encounter) — the two
share the same permission rules and read-model, so one service backs both.

Public methods return `EncounterRead`/`EncounterParticipantRead` (not raw
ORM rows) — mirrors `CharacterService`, since a participant's `effects` are
computed from its conditions on every read, never persisted (backlog Fase 2
história 3).
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.campaigns.domain import CampaignRole
from app.campaigns.models import CampaignMember
from app.catalog.domain import AbilityScore
from app.catalog.models import (
    ClassDefinition,
    Item,
    ItemProperty,
    Monster,
    MonsterAction,
    MonsterActionDamage,
    MonsterLegendaryAction,
    MonsterLegendaryActionDamage,
    MonsterProficiency,
    MonsterReaction,
    MonsterReactionDamage,
    Proficiency,
    SkillDefinition,
    Spell,
    SpellDamage,
    WeaponDetail,
)
from app.characters.domain import SKILL_ABILITY, Skill
from app.characters.models import (
    Character,
    CharacterAbilityScore,
    CharacterEquipment,
    CharacterSkill,
    CharacterSpell,
)
from app.combat.domain import (
    ActionType,
    ConditionType,
    EncounterStatus,
    ParticipantKindError,
    TurnAdvanceResult,
    TurnParticipant,
    validate_participant_kind,
)
from app.combat.domain import advance_turn as compute_next_turn
from app.combat.models import (
    CombatLog,
    Encounter,
    EncounterCondition,
    EncounterParticipant,
)
from app.combat.schemas import (
    CombatLogRead,
    DeclareActionResultRead,
    EncounterConditionRead,
    EncounterCreate,
    EncounterParticipantCreate,
    EncounterParticipantRead,
    EncounterParticipantUpdate,
    EncounterRead,
    MechanicalEffectRead,
    WSDeclareActionPayload,
    WSTriggerReactionPayload,
    WSUseLegendaryActionPayload,
)
from app.sessions.models import Session
from app.world.models import NPC
from engine.abilities import calculate_modifier, calculate_skill_bonus
from engine.conditions import get_condition_effects
from engine.dice import roll, roll_d20
from engine.types import Condition as EngineCondition
from engine.types import ConditionType as EngineConditionType

#: Skills whose contest resolves a grapple/shove (PHB: attacker's Athletics
#: vs. the target's choice of Athletics/Acrobatics) — see `declare_action`.
_GRAPPLE_ATTACKER_SKILLS = (Skill.athletics,)
_GRAPPLE_DEFENSE_SKILLS = (Skill.athletics, Skill.acrobatics)

_ENCOUNTER_LOAD_OPTIONS = (
    selectinload(Encounter.participants).selectinload(EncounterParticipant.conditions),
)


def participant_to_read(
    participant: EncounterParticipant, *, concentration_dc: int | None = None
) -> EncounterParticipantRead:
    """Build a participant's read schema, resolving its conditions' effects.

    `engine.conditions.get_condition_effects` has no notion of exhaustion
    *level* beyond what `engine.types.Condition.level` carries; the DB
    doesn't track a severity for conditions (PRD §7.6 has no such column),
    so exhaustion is always resolved at level 1 here.
    """
    engine_conditions = [
        EngineCondition(condition_type=EngineConditionType(c.condition.value))
        for c in participant.conditions
    ]
    effects = [
        MechanicalEffectRead(
            effect_type=e.effect_type, value=e.value, target=e.target
        )
        for e in get_condition_effects(engine_conditions)
    ]
    return EncounterParticipantRead(
        id=participant.id,
        encounter_id=participant.encounter_id,
        character_id=participant.character_id,
        npc_id=participant.npc_id,
        monster_id=participant.monster_id,
        name=participant.name,
        initiative=participant.initiative,
        hit_point_max=participant.hit_point_max,
        hit_point_current=participant.hit_point_current,
        temporary_hit_points=participant.temporary_hit_points,
        armor_class=participant.armor_class,
        turn_order=participant.turn_order,
        is_active=participant.is_active,
        conditions=[
            EncounterConditionRead.model_validate(c) for c in participant.conditions
        ],
        effects=effects,
        concentration_dc=concentration_dc,
        legendary_actions_used=participant.legendary_actions_used,
        reactions_used=participant.reactions_used,
    )


def encounter_to_read(encounter: Encounter) -> EncounterRead:
    """Build an encounter's read schema, with each participant's effects resolved."""
    return EncounterRead(
        id=encounter.id,
        session_id=encounter.session_id,
        name=encounter.name,
        status=encounter.status,
        current_round=encounter.current_round,
        current_turn_order=encounter.current_turn_order,
        created_at=encounter.created_at,
        participants=[participant_to_read(p) for p in encounter.participants],
    )


class CombatService:
    """Orchestrates encounter creation, participant management, and reads."""

    async def create_encounter(
        self,
        session_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: EncounterCreate,
        db: AsyncSession,
    ) -> EncounterRead:
        """Create an encounter for a session; only the campaign's DM may do this."""
        session = await self._require_dm_for_session(session_id, requester_id, db)

        encounter = Encounter(session_id=session.id, name=data.name)
        db.add(encounter)
        await db.commit()
        return encounter_to_read(await self._reload_encounter(encounter.id, db))

    async def start_encounter(
        self, encounter_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> EncounterRead:
        """Transition an encounter from `preparing` to `active`. DM only.

        Also auto-adds every campaign PC not already a participant, without
        an initiative — monsters/NPCs are still added manually. Nobody can
        advance turns until every active participant has rolled (see
        `advance_turn`).
        """
        encounter = await self._load_encounter_or_404(encounter_id, db)
        session = await self._require_dm_for_session(
            encounter.session_id, requester_id, db
        )

        if encounter.status != EncounterStatus.preparing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only a preparing encounter can be started",
            )
        await self._add_missing_campaign_pcs(encounter, session.campaign_id, db)
        encounter.status = EncounterStatus.active
        encounter.current_round = 1
        await db.commit()
        return encounter_to_read(await self._reload_encounter(encounter.id, db))

    async def _add_missing_campaign_pcs(
        self, encounter: Encounter, campaign_id: uuid.UUID, db: AsyncSession
    ) -> None:
        """Add every campaign PC not already a participant, initiative unset."""
        existing_character_ids = {
            p.character_id for p in encounter.participants if p.character_id is not None
        }
        result = await db.execute(
            select(Character)
            .join(CampaignMember, CampaignMember.id == Character.campaign_member_id)
            .where(CampaignMember.campaign_id == campaign_id)
        )
        next_turn_order = (
            max((p.turn_order for p in encounter.participants), default=-1) + 1
        )
        for character in result.scalars().all():
            if character.id in existing_character_ids:
                continue
            db.add(
                EncounterParticipant(
                    encounter_id=encounter.id,
                    character_id=character.id,
                    name=character.name,
                    initiative=None,
                    hit_point_max=character.hit_point_max,
                    hit_point_current=character.hit_point_current,
                    armor_class=character.armor_class,
                    turn_order=next_turn_order,
                )
            )
            next_turn_order += 1

    async def list_encounters(
        self, session_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> list[EncounterRead]:
        """List a session's encounters. Viewable by any campaign member."""
        session = await self._require_session(session_id, db)
        await self._require_membership(session.campaign_id, requester_id, db)

        result = await db.execute(
            select(Encounter)
            .where(Encounter.session_id == session_id)
            .options(*_ENCOUNTER_LOAD_OPTIONS)
            .order_by(Encounter.created_at)
        )
        return [encounter_to_read(e) for e in result.scalars().all()]

    async def get_encounter(
        self, encounter_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> EncounterRead:
        """Get an encounter's detail. Viewable by any campaign member."""
        encounter, _member = await self.get_encounter_membership(
            encounter_id, requester_id, db
        )
        return encounter_to_read(encounter)

    async def get_encounter_membership(
        self, encounter_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> tuple[Encounter, CampaignMember]:
        """Load an encounter (ORM row) plus the requester's campaign membership.

        Reused by the WebSocket handler to authenticate a connection and
        learn the requester's role (DM vs. player) in one call. Returns the
        raw ORM `Encounter` (not `EncounterRead`) — callers that need the
        read schema should use `get_encounter` instead.
        """
        encounter = await self._load_encounter_or_404(encounter_id, db)
        session = await self._require_session(encounter.session_id, db)
        member = await self._require_membership(session.campaign_id, requester_id, db)
        return encounter, member

    async def add_participant(
        self,
        encounter_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: EncounterParticipantCreate,
        db: AsyncSession,
    ) -> EncounterRead:
        """Add a participant (PC, NPC, or manual entry) to an encounter. DM only."""
        encounter = await self._load_encounter_or_404(encounter_id, db)
        await self._require_dm_for_session(encounter.session_id, requester_id, db)

        try:
            validate_participant_kind(
                character_id=data.character_id,
                npc_id=data.npc_id,
                monster_id=data.monster_id,
            )
        except ParticipantKindError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
            ) from exc

        hit_point_current = (
            data.hit_point_current
            if data.hit_point_current is not None
            else data.hit_point_max
        )
        participant = EncounterParticipant(
            encounter_id=encounter.id,
            character_id=data.character_id,
            npc_id=data.npc_id,
            monster_id=data.monster_id,
            name=data.name,
            initiative=data.initiative,
            hit_point_max=data.hit_point_max,
            hit_point_current=hit_point_current,
            armor_class=data.armor_class,
            turn_order=data.turn_order,
        )
        db.add(participant)
        await db.flush()
        self._log(
            db,
            encounter,
            actor_id=participant.id,
            description=f"{participant.name} joined the encounter",
        )
        await db.commit()
        return encounter_to_read(await self._reload_encounter(encounter.id, db))

    async def update_participant(
        self,
        encounter_id: uuid.UUID,
        participant_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: EncounterParticipantUpdate,
        db: AsyncSession,
    ) -> EncounterRead:
        """Update a participant's fields outside the live turn flow. DM only."""
        encounter = await self._load_encounter_or_404(encounter_id, db)
        await self._require_dm_for_session(encounter.session_id, requester_id, db)
        participant = self._find_participant_or_404(encounter, participant_id)

        if data.hit_point_current is not None:
            if data.hit_point_current > participant.hit_point_max:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="hit_point_current cannot exceed hit_point_max",
                )
            self._log_hp_change(
                db, encounter, participant, data.hit_point_current
            )
            participant.hit_point_current = data.hit_point_current
        if data.temporary_hit_points is not None:
            participant.temporary_hit_points = data.temporary_hit_points
        if data.armor_class is not None:
            participant.armor_class = data.armor_class
        if data.initiative is not None:
            participant.initiative = data.initiative
        if data.turn_order is not None:
            participant.turn_order = data.turn_order
        if data.is_active is not None:
            participant.is_active = data.is_active

        await db.commit()
        return encounter_to_read(await self._reload_encounter(encounter.id, db))

    async def remove_participant(
        self,
        encounter_id: uuid.UUID,
        participant_id: uuid.UUID,
        requester_id: uuid.UUID,
        db: AsyncSession,
    ) -> EncounterRead:
        """Remove a participant from an encounter. DM only."""
        encounter = await self._load_encounter_or_404(encounter_id, db)
        await self._require_dm_for_session(encounter.session_id, requester_id, db)
        participant = self._find_participant_or_404(encounter, participant_id)

        self._log(
            db,
            encounter,
            actor_id=participant.id,
            description=f"{participant.name} left the encounter",
        )
        await db.delete(participant)
        await db.commit()
        return encounter_to_read(await self._reload_encounter(encounter.id, db))

    async def advance_turn(
        self, encounter_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> tuple[EncounterRead, TurnAdvanceResult]:
        """Advance to the next active participant's turn (live, WS-driven). DM only.

        Rejected while any active participant hasn't rolled initiative yet
        (see `roll_initiative`) — 422, not blocked silently.
        """
        encounter = await self._load_encounter_or_404(encounter_id, db)
        await self._require_dm_for_session(encounter.session_id, requester_id, db)

        missing_initiative = [
            p for p in encounter.participants if p.is_active and p.initiative is None
        ]
        if missing_initiative:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    "All participants must roll initiative before turns can "
                    "advance"
                ),
            )

        turn_participants = [
            TurnParticipant(id=p.id, turn_order=p.turn_order, is_active=p.is_active)
            for p in encounter.participants
        ]
        result = compute_next_turn(
            turn_participants,
            current_round=encounter.current_round,
            current_turn_order=encounter.current_turn_order,
        )
        encounter.current_round = result.round
        encounter.current_turn_order = result.turn_order
        if result.participant_id is not None:
            next_up = next(
                p for p in encounter.participants if p.id == result.participant_id
            )
            # Legendary actions/reactions spend resets at the start of the
            # participant's own turn (Fase 7) — harmless no-op for a PC.
            next_up.legendary_actions_used = 0
            next_up.reactions_used = 0
            self._log(
                db,
                encounter,
                actor_id=next_up.id,
                description=f"Round {result.round}: {next_up.name}'s turn",
            )
        await db.commit()
        reloaded = await self._reload_encounter(encounter.id, db)
        return encounter_to_read(reloaded), result

    async def end_encounter(
        self, encounter_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> EncounterRead:
        """End an encounter (live, WS-driven): sets it to `completed`. DM only."""
        encounter = await self._load_encounter_or_404(encounter_id, db)
        await self._require_dm_for_session(encounter.session_id, requester_id, db)

        encounter.status = EncounterStatus.completed
        self._log(db, encounter, description="Encounter ended")
        await db.commit()
        return encounter_to_read(await self._reload_encounter(encounter.id, db))

    async def live_update_participant(
        self,
        encounter_id: uuid.UUID,
        participant_id: uuid.UUID,
        requester_id: uuid.UUID,
        *,
        hit_point_current: int | None,
        temporary_hit_points: int | None,
        armor_class: int | None,
        add_condition: ConditionType | None,
        remove_condition: ConditionType | None,
        db: AsyncSession,
    ) -> EncounterParticipantRead:
        """Apply damage/heal/AC/condition changes to a participant (WS-driven). DM only.

        Returns just the updated participant (not the whole encounter) — the
        WS handler broadcasts a `participant_updated` event scoped to it.
        """
        encounter = await self._load_encounter_or_404(encounter_id, db)
        await self._require_dm_for_session(encounter.session_id, requester_id, db)
        participant = self._find_participant_or_404(encounter, participant_id)

        concentration_dc: int | None = None
        if hit_point_current is not None:
            if hit_point_current > participant.hit_point_max:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="hit_point_current cannot exceed hit_point_max",
                )
            damage = participant.hit_point_current - hit_point_current
            concentration_dc = await self._concentration_dc(participant, damage, db)
            self._log_hp_change(db, encounter, participant, hit_point_current)
            participant.hit_point_current = hit_point_current
        if temporary_hit_points is not None:
            participant.temporary_hit_points = temporary_hit_points
        if armor_class is not None:
            participant.armor_class = armor_class

        if add_condition is not None:
            already_has = any(
                c.condition == add_condition for c in participant.conditions
            )
            if not already_has:
                db.add(
                    EncounterCondition(
                        participant_id=participant.id,
                        condition=add_condition,
                        applied_at_round=encounter.current_round,
                    )
                )
                self._log(
                    db,
                    encounter,
                    target_id=participant.id,
                    description=(
                        f"{participant.name} gained condition: {add_condition}"
                    ),
                )
        if remove_condition is not None:
            for condition in list(participant.conditions):
                if condition.condition == remove_condition:
                    await db.delete(condition)
                    self._log(
                        db,
                        encounter,
                        target_id=participant.id,
                        description=(
                            f"{participant.name} lost condition: "
                            f"{remove_condition}"
                        ),
                    )

        await db.commit()
        result = await db.execute(
            select(EncounterParticipant)
            .where(EncounterParticipant.id == participant.id)
            .options(selectinload(EncounterParticipant.conditions))
            .execution_options(populate_existing=True)
        )
        return participant_to_read(
            result.scalar_one(), concentration_dc=concentration_dc
        )

    async def roll_initiative(
        self,
        encounter_id: uuid.UUID,
        participant_id: uuid.UUID,
        requester_id: uuid.UUID,
        initiative: int | None,
        db: AsyncSession,
    ) -> EncounterParticipantRead:
        """Set a participant's initiative (live, WS-driven).

        Unlike other WS commands this isn't DM-only: a player may roll for
        their own character's participant; the DM may roll for any
        participant (their own characters, NPCs, monsters).

        `initiative=None` rolls `1d20 + DEX modifier` server-side via
        `engine/dice.py` (Character or catalog-linked Monster participant
        only — a purely manual participant has no ability scores to roll
        from and must supply `initiative` explicitly, 422 otherwise).
        Supplied, it's used as-is and logged as a manual roll (backlog Fase
        6 história 6).
        """
        encounter = await self._load_encounter_or_404(encounter_id, db)
        session = await self._require_session(encounter.session_id, db)
        member = await self._require_membership(session.campaign_id, requester_id, db)
        participant = self._find_participant_or_404(encounter, participant_id)

        if member.role != CampaignRole.dm:
            owns = await self._participant_owned_by(participant, requester_id, db)
            if not owns:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only roll initiative for your own character",
                )

        if initiative is not None:
            rolled_value = initiative
            log_suffix = " (manual)"
            rolled_by_system = False
        else:
            dex_mod = await self._participant_dex_modifier(participant, db)
            if dex_mod is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=(
                        "This participant has no ability scores to roll "
                        "initiative from — supply `initiative` manually"
                    ),
                )
            rolled_value = roll_d20(bonus=dex_mod).total
            log_suffix = ""
            rolled_by_system = True

        participant.initiative = rolled_value
        self._log(
            db,
            encounter,
            actor_id=participant.id,
            description=(
                f"{participant.name} rolled initiative: {rolled_value}{log_suffix}"
            ),
            rolled_by_system=rolled_by_system,
        )
        await db.commit()
        result = await db.execute(
            select(EncounterParticipant)
            .where(EncounterParticipant.id == participant.id)
            .options(selectinload(EncounterParticipant.conditions))
            .execution_options(populate_existing=True)
        )
        return participant_to_read(result.scalar_one())

    async def _participant_dex_modifier(
        self, participant: EncounterParticipant, db: AsyncSession
    ) -> int | None:
        """Return a Character/Monster participant's DEX modifier, else None."""
        if participant.character_id is not None:
            result = await db.execute(
                select(CharacterAbilityScore).where(
                    CharacterAbilityScore.character_id == participant.character_id,
                    CharacterAbilityScore.ability == AbilityScore.dex,
                )
            )
            score = result.scalar_one_or_none()
            if score is None:
                return None
            return calculate_modifier(
                score.base_score + score.asi_bonus + score.misc_bonus
            )
        if participant.monster_id is not None:
            monster_result = await db.execute(
                select(Monster).where(Monster.id == participant.monster_id)
            )
            monster = monster_result.scalar_one_or_none()
            if monster is None:
                return None
            return calculate_modifier(monster.dexterity)
        return None

    async def declare_action(
        self,
        encounter_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: WSDeclareActionPayload,
        db: AsyncSession,
    ) -> DeclareActionResultRead:
        """Declare and resolve a combat action (live, WS-driven).

        `attack_weapon`/`attack_spell`: attack roll (`1d20 + bonus`, or
        `manual_attack_roll`) vs. the target's `armor_class`; on hit, rolls
        (or takes `manual_damage_roll` for) the weapon/spell's damage.
        `grapple`/`shove`: an opposed check (attacker's Athletics vs. the
        best of the target's Athletics/Acrobatics — PHB lets the target
        choose which; this always uses whichever is higher rather than
        prompting live, a documented simplification) resolved server-side;
        applies `grappled` on a successful grapple (repositioning for a
        shove isn't tracked — no position/map model in this app yet).
        Every other `action_type` (dash, dodge, disengage, help, hide,
        ready, search, ...) has nothing to roll — just logged as taken,
        for the turn-by-turn record (frontend's `action-picker.tsx`).

        Unlike the DM-only WS commands, only the attacker's own
        player (or the DM) may declare for it — mirrors `roll_initiative`.
        """
        encounter = await self._load_encounter_or_404(encounter_id, db)
        session = await self._require_session(encounter.session_id, db)
        member = await self._require_membership(session.campaign_id, requester_id, db)
        attacker = self._find_participant_or_404(encounter, data.participant_id)
        target = self._find_participant_or_404(encounter, data.target_id)

        if member.role != CampaignRole.dm:
            owns = await self._participant_owned_by(attacker, requester_id, db)
            if not owns:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only declare actions for your own character",
                )

        if data.action_type in (ActionType.attack_weapon, ActionType.attack_spell):
            result = await self._resolve_attack(encounter, attacker, target, data, db)
        elif data.action_type in (ActionType.grapple, ActionType.shove):
            result = await self._resolve_contest(encounter, attacker, target, data, db)
        else:
            result = self._resolve_flavor_action(encounter, attacker, data, db)

        await db.commit()
        return result

    def _resolve_flavor_action(
        self,
        encounter: Encounter,
        attacker: EncounterParticipant,
        data: WSDeclareActionPayload,
        db: AsyncSession,
    ) -> DeclareActionResultRead:
        """Log an action with nothing to roll (dash, dodge, help, search, ...)."""
        description = f"{attacker.name} takes the {data.action_type.value} action"
        self._log(
            db,
            encounter,
            actor_id=attacker.id,
            action_type=data.action_type,
            description=description,
        )
        return DeclareActionResultRead(
            actor_id=attacker.id,
            target_id=data.target_id,
            action_type=data.action_type,
            description=description,
        )

    async def _resolve_attack(
        self,
        encounter: Encounter,
        attacker: EncounterParticipant,
        target: EncounterParticipant,
        data: WSDeclareActionPayload,
        db: AsyncSession,
    ) -> DeclareActionResultRead:
        """Resolve `attack_weapon`/`attack_spell`: to-hit roll, then damage."""
        source = await self._resolve_attack_source(attacker, data, db)
        return await self._resolve_and_apply_attack(
            encounter,
            attacker,
            target,
            source,
            action_type=data.action_type,
            manual_attack_roll=data.manual_attack_roll,
            manual_damage_roll=data.manual_damage_roll,
            db=db,
        )

    async def _resolve_and_apply_attack(
        self,
        encounter: Encounter,
        attacker: EncounterParticipant,
        target: EncounterParticipant,
        source: tuple[int, str | None, str | None, str],
        *,
        action_type: ActionType,
        manual_attack_roll: int | None,
        manual_damage_roll: int | None,
        db: AsyncSession,
    ) -> DeclareActionResultRead:
        """Roll to-hit and damage against `target`, logging and applying it.

        Shared core for `declare_action`'s `attack_weapon`/`attack_spell`
        and (Fase 7) a monster's legendary action / reaction — every caller
        first resolves its own `(attack_bonus, damage_expression,
        damage_type, source_desc)` tuple, then hands it here.
        """
        attack_bonus, damage_expression, damage_type, source_desc = source

        if manual_attack_roll is not None:
            attack_roll = manual_attack_roll
        else:
            attack_roll = roll_d20(bonus=attack_bonus).total

        hit = attack_roll >= target.armor_class
        description = (
            f"{attacker.name} attacks {target.name} with {source_desc}: "
            f"{attack_roll} vs AC {target.armor_class} — "
            f"{'hit' if hit else 'miss'}"
        )
        damage_rolled: int | None = None
        concentration_dc: int | None = None
        if hit:
            if manual_damage_roll is not None:
                damage_rolled = manual_damage_roll
            elif damage_expression is not None:
                damage_rolled = roll(damage_expression).total
            else:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=(
                        "No damage expression could be resolved for this "
                        "attack — supply manual_damage_expression or "
                        "manual_damage_roll"
                    ),
                )
            new_hp = max(0, target.hit_point_current - damage_rolled)
            self._log_hp_change(db, encounter, target, new_hp)
            target.hit_point_current = new_hp
            concentration_dc = await self._concentration_dc(
                target, damage_rolled, db
            )
            description += (
                f", dealing {damage_rolled} {damage_type or ''} damage".rstrip()
            )

        self._log(
            db,
            encounter,
            actor_id=attacker.id,
            target_id=target.id,
            action_type=action_type,
            description=description,
            damage_dealt=damage_rolled if hit else None,
            damage_type=damage_type if hit else None,
            rolled_by_system=(
                manual_attack_roll is None and manual_damage_roll is None
            ),
        )
        return DeclareActionResultRead(
            actor_id=attacker.id,
            target_id=target.id,
            action_type=action_type,
            attack_roll=attack_roll,
            attack_bonus=attack_bonus,
            hit=hit,
            damage_rolled=damage_rolled,
            damage_type=damage_type if hit else None,
            description=description,
            concentration_dc=concentration_dc,
        )

    async def _resolve_attack_source(
        self,
        attacker: EncounterParticipant,
        data: WSDeclareActionPayload,
        db: AsyncSession,
    ) -> tuple[int, str | None, str | None, str]:
        """Resolve `(attack_bonus, damage_expression, damage_type, source_name)`.

        `damage_expression` is `None` only when the source genuinely has no
        damage to roll (e.g. a non-damaging spell) — the caller must then
        supply `manual_damage_expression`/`manual_damage_roll` to hit with
        an effect but no auto damage.
        """
        if (
            data.action_type == ActionType.attack_weapon
            and attacker.character_id is not None
        ):
            if data.weapon_equipment_id is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="weapon_equipment_id is required to attack with a weapon",
                )
            return await self._resolve_character_weapon_attack(
                attacker.character_id, data.weapon_equipment_id, db
            )
        if (
            data.action_type == ActionType.attack_spell
            and attacker.character_id is not None
        ):
            if data.spell_entry_id is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="spell_entry_id is required to attack with a spell",
                )
            return await self._resolve_character_spell_attack(
                attacker.character_id, data.spell_entry_id, data.cast_at_level, db
            )
        if attacker.monster_id is not None:
            if data.monster_action_id is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="monster_action_id is required for a monster's attack",
                )
            return await self._resolve_monster_attack(
                attacker.monster_id, data.monster_action_id, db
            )
        if data.manual_attack_bonus is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    "This participant has no stat block to resolve an attack "
                    "from — supply manual_attack_bonus (and "
                    "manual_damage_expression/manual_damage_roll)"
                ),
            )
        return (
            data.manual_attack_bonus,
            data.manual_damage_expression,
            None,
            attacker.name,
        )

    async def _resolve_character_weapon_attack(
        self, character_id: uuid.UUID, equipment_id: uuid.UUID, db: AsyncSession
    ) -> tuple[int, str, str, str]:
        """Resolve a Character's equipped weapon into attack bonus + damage.

        Ability used: DEX for ranged or finesse weapons, STR otherwise — for
        finesse specifically the PHB lets the player pick either; this
        always picks DEX (the common choice in play), a documented
        simplification. Proficiency is assumed with any weapon a character
        has equipped — this app doesn't model per-category weapon
        proficiency on `Character`, another documented simplification.
        """
        result = await db.execute(
            select(CharacterEquipment).where(
                CharacterEquipment.id == equipment_id,
                CharacterEquipment.character_id == character_id,
            )
        )
        equipment = result.scalar_one_or_none()
        if equipment is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Equipment entry not found on the attacker's character",
            )
        item_result = await db.execute(
            select(Item)
            .where(Item.id == equipment.item_id)
            .options(
                selectinload(Item.weapon_detail).selectinload(WeaponDetail.damage_type),
                selectinload(Item.properties).selectinload(
                    ItemProperty.weapon_property
                ),
            )
        )
        item = item_result.scalar_one_or_none()
        if item is None or item.weapon_detail is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Selected equipment is not a weapon",
            )

        has_finesse = any(
            p.weapon_property.index == "finesse" for p in item.properties
        )
        ability = (
            AbilityScore.dex
            if item.weapon_detail.weapon_range == "Ranged" or has_finesse
            else AbilityScore.str
        )
        ability_mod = await self._character_ability_modifier(character_id, ability, db)
        proficiency_bonus = await self._character_proficiency_bonus(character_id, db)
        attack_bonus = ability_mod + proficiency_bonus
        sign = "+" if ability_mod >= 0 else ""
        damage_expression = f"{item.weapon_detail.damage_dice}{sign}{ability_mod}"
        return (
            attack_bonus,
            damage_expression,
            item.weapon_detail.damage_type.index or "",
            item.index or "weapon",
        )

    async def _resolve_character_spell_attack(
        self,
        character_id: uuid.UUID,
        spell_entry_id: uuid.UUID,
        cast_at_level: int | None,
        db: AsyncSession,
    ) -> tuple[int, str | None, str | None, str]:
        """Resolve a Character's known spell into attack bonus + damage.

        Attack bonus: the casting class's spellcasting-ability modifier +
        proficiency bonus, matched by `CharacterSpell.source_class` against
        the character's classes (same lookup `CharacterService` uses).
        Damage: looked up from catalog `SpellDamage` at `cast_at_level`
        (slot-scaled) or the character's class level (cantrip/character-
        level-scaled); `None` if the spell has no damage entry at all (e.g.
        a pure debuff/utility spell) — the caller must then supply a manual
        damage expression to log an effect without rolling one here.
        """
        entry_result = await db.execute(
            select(CharacterSpell).where(
                CharacterSpell.id == spell_entry_id,
                CharacterSpell.character_id == character_id,
            )
        )
        entry = entry_result.scalar_one_or_none()
        if entry is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Spell entry not found on the attacker's character",
            )
        spell_result = await db.execute(
            select(Spell)
            .where(Spell.id == entry.spell_id)
            .options(selectinload(Spell.damages).selectinload(SpellDamage.damage_type))
        )
        spell = spell_result.scalar_one_or_none()
        if spell is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Spell not found"
            )

        character_result = await db.execute(
            select(Character)
            .where(Character.id == character_id)
            .options(selectinload(Character.classes))
        )
        character = character_result.scalar_one()
        ability_mod = 0
        caster_level = character.level
        if entry.source_class is not None:
            class_result = await db.execute(
                select(ClassDefinition).where(
                    ClassDefinition.index == entry.source_class
                )
            )
            class_def = class_result.scalar_one_or_none()
            class_entry = next(
                (
                    c
                    for c in character.classes
                    if class_def is not None
                    and c.class_definition_id == class_def.id
                ),
                None,
            )
            if class_def is not None and class_entry is not None:
                caster_level = class_entry.level
                if class_def.spellcasting_ability is not None:
                    ability_mod = await self._character_ability_modifier(
                        character_id, AbilityScore(class_def.spellcasting_ability), db
                    )
        proficiency_bonus = await self._character_proficiency_bonus(character_id, db)
        attack_bonus = ability_mod + proficiency_bonus

        target_level = cast_at_level or spell.level
        damage_row = next(
            (
                d
                for d in spell.damages
                if (d.scaling_type == "slot_level" and d.scaling_key == target_level)
                or (
                    d.scaling_type == "character_level"
                    and d.scaling_key
                    == max(
                        (k for k in (1, 5, 11, 17) if k <= caster_level), default=1
                    )
                )
            ),
            None,
        )
        if damage_row is None:
            return attack_bonus, None, None, spell.index or "spell"
        return (
            attack_bonus,
            damage_row.dice_expression,
            damage_row.damage_type.index or "",
            spell.index or "spell",
        )

    async def _resolve_monster_attack(
        self, monster_id: uuid.UUID, monster_action_id: uuid.UUID, db: AsyncSession
    ) -> tuple[int, str | None, str | None, str]:
        """Resolve a catalog Monster's action into attack bonus + damage.

        `attack_bonus` is read straight from `MonsterAction.attack_bonus`
        (already the SRD's precomputed number). Multiple `MonsterActionDamage`
        rows (e.g. a bite that also deals poison) are summed into one dice
        expression, logged under the first row's damage type — mixed-type
        damage isn't split out per type, a documented simplification.
        """
        result = await db.execute(
            select(MonsterAction)
            .where(
                MonsterAction.id == monster_action_id,
                MonsterAction.monster_id == monster_id,
            )
            .options(
                selectinload(MonsterAction.damages).selectinload(
                    MonsterActionDamage.damage_type
                )
            )
        )
        action = result.scalar_one_or_none()
        if action is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Action not found on the attacker's monster stat block",
            )
        if action.attack_bonus is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    "This monster action has no attack roll "
                    "(e.g. a save-based effect)"
                ),
            )
        if not action.damages:
            return action.attack_bonus, None, None, action.name
        damage_expression = "+".join(d.damage_dice for d in action.damages)
        return (
            action.attack_bonus,
            damage_expression,
            action.damages[0].damage_type.index or "",
            action.name,
        )

    #: Every SRD monster with legendary actions gets 3 per round — the
    #: catalog doesn't carry a per-monster override (a documented
    #: simplification, see `WSUseLegendaryActionPayload`).
    _LEGENDARY_ACTIONS_PER_ROUND = 3

    async def _resolve_stat_block_monster_id(
        self, participant: EncounterParticipant, db: AsyncSession
    ) -> uuid.UUID | None:
        """The catalog `Monster` id backing a participant, if any.

        Direct for a `monster_id` participant; for an `npc_id` one, looked
        up via `NPC.stat_block_id` (Fase 7) — `None` for a purely manual
        participant or an NPC with no stat block.
        """
        if participant.monster_id is not None:
            return participant.monster_id
        if participant.npc_id is not None:
            result = await db.execute(
                select(NPC).where(NPC.id == participant.npc_id)
            )
            npc = result.scalar_one_or_none()
            return npc.stat_block_id if npc is not None else None
        return None

    async def use_legendary_action(
        self,
        encounter_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: WSUseLegendaryActionPayload,
        db: AsyncSession,
    ) -> DeclareActionResultRead:
        """Resolve a monster's legendary action against a target (Fase 7). DM only.

        Rejected on the acting participant's own turn, and once its
        `_LEGENDARY_ACTIONS_PER_ROUND` budget for the round is spent (reset
        at the start of its own turn by `advance_turn`).
        """
        encounter = await self._load_encounter_or_404(encounter_id, db)
        await self._require_dm_for_session(encounter.session_id, requester_id, db)
        attacker = self._find_participant_or_404(encounter, data.participant_id)
        target = self._find_participant_or_404(encounter, data.target_id)

        monster_id = await self._resolve_stat_block_monster_id(attacker, db)
        if monster_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="This participant has no monster stat block",
            )
        if attacker.turn_order == encounter.current_turn_order:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Legendary actions can't be used on the monster's own turn",
            )
        if attacker.legendary_actions_used >= self._LEGENDARY_ACTIONS_PER_ROUND:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="No legendary actions remaining this round",
            )

        result = await db.execute(
            select(MonsterLegendaryAction)
            .where(
                MonsterLegendaryAction.id == data.legendary_action_id,
                MonsterLegendaryAction.monster_id == monster_id,
            )
            .options(
                selectinload(MonsterLegendaryAction.damages).selectinload(
                    MonsterLegendaryActionDamage.damage_type
                )
            )
        )
        action = result.scalar_one_or_none()
        if action is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Legendary action not found on the attacker's stat block",
            )
        if action.attack_bonus is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="This legendary action has no attack roll",
            )
        damage_expression = (
            "+".join(d.damage_dice for d in action.damages)
            if action.damages
            else None
        )
        damage_type = action.damages[0].damage_type.index if action.damages else None
        source = (action.attack_bonus, damage_expression, damage_type, action.name)

        attacker.legendary_actions_used += 1
        outcome = await self._resolve_and_apply_attack(
            encounter,
            attacker,
            target,
            source,
            action_type=ActionType.legendary_action,
            manual_attack_roll=data.manual_attack_roll,
            manual_damage_roll=data.manual_damage_roll,
            db=db,
        )
        await db.commit()
        return outcome

    async def trigger_reaction(
        self,
        encounter_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: WSTriggerReactionPayload,
        db: AsyncSession,
    ) -> DeclareActionResultRead:
        """Resolve a monster's reaction against a target (Fase 7). DM only.

        Once per round (reset at the start of the reacting monster's own
        turn by `advance_turn`) — unlike a legendary action, usable on
        anyone's turn including its own (PHB rule).
        """
        encounter = await self._load_encounter_or_404(encounter_id, db)
        await self._require_dm_for_session(encounter.session_id, requester_id, db)
        attacker = self._find_participant_or_404(encounter, data.participant_id)
        target = self._find_participant_or_404(encounter, data.target_id)

        monster_id = await self._resolve_stat_block_monster_id(attacker, db)
        if monster_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="This participant has no monster stat block",
            )
        if attacker.reactions_used >= 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="No reaction remaining this round",
            )

        result = await db.execute(
            select(MonsterReaction)
            .where(
                MonsterReaction.id == data.reaction_id,
                MonsterReaction.monster_id == monster_id,
            )
            .options(
                selectinload(MonsterReaction.damages).selectinload(
                    MonsterReactionDamage.damage_type
                )
            )
        )
        reaction = result.scalar_one_or_none()
        if reaction is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Reaction not found on the attacker's stat block",
            )
        if reaction.attack_bonus is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="This reaction has no attack roll",
            )
        damage_expression = (
            "+".join(d.damage_dice for d in reaction.damages)
            if reaction.damages
            else None
        )
        damage_type = (
            reaction.damages[0].damage_type.index if reaction.damages else None
        )
        source = (reaction.attack_bonus, damage_expression, damage_type, reaction.name)

        attacker.reactions_used += 1
        outcome = await self._resolve_and_apply_attack(
            encounter,
            attacker,
            target,
            source,
            action_type=ActionType.reaction,
            manual_attack_roll=data.manual_attack_roll,
            manual_damage_roll=data.manual_damage_roll,
            db=db,
        )
        await db.commit()
        return outcome

    async def _character_ability_modifier(
        self, character_id: uuid.UUID, ability: AbilityScore, db: AsyncSession
    ) -> int:
        result = await db.execute(
            select(CharacterAbilityScore).where(
                CharacterAbilityScore.character_id == character_id,
                CharacterAbilityScore.ability == ability,
            )
        )
        score = result.scalar_one_or_none()
        if score is None:
            return 0
        return calculate_modifier(score.base_score + score.asi_bonus + score.misc_bonus)

    async def _character_proficiency_bonus(
        self, character_id: uuid.UUID, db: AsyncSession
    ) -> int:
        result = await db.execute(
            select(Character).where(Character.id == character_id)
        )
        character = result.scalar_one_or_none()
        return character.proficiency_bonus if character is not None else 0

    async def _resolve_contest(
        self,
        encounter: Encounter,
        attacker: EncounterParticipant,
        target: EncounterParticipant,
        data: WSDeclareActionPayload,
        db: AsyncSession,
    ) -> DeclareActionResultRead:
        """Resolve `grapple`/`shove` as attacker's Athletics vs. defense.

        The target's contest uses the best of Athletics/Acrobatics — see
        `declare_action`'s docstring for the "always picks the target's
        best" simplification.
        """
        attacker_bonus = await self._resolve_check_bonus(
            attacker, _GRAPPLE_ATTACKER_SKILLS, data.manual_athletics_bonus, db
        )
        target_bonus = await self._resolve_check_bonus(
            target, _GRAPPLE_DEFENSE_SKILLS, data.manual_target_bonus, db
        )

        attacker_roll = (
            data.manual_attack_roll
            if data.manual_attack_roll is not None
            else roll_d20(bonus=attacker_bonus).total
        )
        target_roll = (
            data.manual_target_roll
            if data.manual_target_roll is not None
            else roll_d20(bonus=target_bonus).total
        )
        succeeded = attacker_roll >= target_roll

        verb = "grapples" if data.action_type == ActionType.grapple else "shoves"
        description = (
            f"{attacker.name} {verb} {target.name}: {attacker_roll} vs "
            f"{target_roll} — {'success' if succeeded else 'fail'}"
        )
        condition_applied: str | None = None
        if succeeded and data.action_type == ActionType.grapple:
            already_grappled = any(
                c.condition == ConditionType.grappled for c in target.conditions
            )
            if not already_grappled:
                db.add(
                    EncounterCondition(
                        participant_id=target.id,
                        condition=ConditionType.grappled,
                        applied_at_round=encounter.current_round,
                    )
                )
                condition_applied = ConditionType.grappled.value

        self._log(
            db,
            encounter,
            actor_id=attacker.id,
            target_id=target.id,
            action_type=data.action_type,
            description=description,
            rolled_by_system=(
                data.manual_attack_roll is None and data.manual_target_roll is None
            ),
        )
        return DeclareActionResultRead(
            actor_id=attacker.id,
            target_id=target.id,
            action_type=data.action_type,
            attacker_check=attacker_roll,
            target_check=target_roll,
            hit=succeeded,
            condition_applied=condition_applied,
            description=description,
        )

    async def _resolve_check_bonus(
        self,
        participant: EncounterParticipant,
        skills: tuple[Skill, ...],
        manual_bonus: int | None,
        db: AsyncSession,
    ) -> int:
        """Resolve the best of `skills`' bonus for a participant.

        Character: `engine.abilities.calculate_skill_bonus` per skill,
        best wins. Monster: best of `MonsterProficiency` (if proficient in
        one of `skills`) or the governing ability's modifier otherwise.
        Manual participant: `manual_bonus` is required (422 without it).
        """
        if participant.character_id is not None:
            return await self._character_best_skill_bonus(
                participant.character_id, skills, db
            )
        if participant.monster_id is not None:
            return await self._monster_best_skill_bonus(
                participant.monster_id, skills, db
            )
        if manual_bonus is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    f"{participant.name} has no stat block to resolve a check "
                    "from — supply a manual bonus"
                ),
            )
        return manual_bonus

    async def _character_best_skill_bonus(
        self, character_id: uuid.UUID, skills: tuple[Skill, ...], db: AsyncSession
    ) -> int:
        skills_result = await db.execute(
            select(CharacterSkill).where(
                CharacterSkill.character_id == character_id,
                CharacterSkill.skill.in_(skills),
            )
        )
        char_skills = skills_result.scalars().all()
        scores_result = await db.execute(
            select(CharacterAbilityScore).where(
                CharacterAbilityScore.character_id == character_id
            )
        )
        scores_by_ability = {s.ability: s for s in scores_result.scalars().all()}
        proficiency_bonus = await self._character_proficiency_bonus(character_id, db)

        bonuses = []
        for skill_row in char_skills:
            score = scores_by_ability.get(SKILL_ABILITY[skill_row.skill])
            if score is None:
                continue
            mod = calculate_modifier(
                score.base_score + score.asi_bonus + score.misc_bonus
            )
            bonuses.append(
                calculate_skill_bonus(
                    mod, skill_row.proficient, skill_row.expertise, proficiency_bonus
                )
            )
        return max(bonuses) if bonuses else 0

    async def _monster_best_skill_bonus(
        self, monster_id: uuid.UUID, skills: tuple[Skill, ...], db: AsyncSession
    ) -> int:
        monster_result = await db.execute(
            select(Monster).where(Monster.id == monster_id)
        )
        monster = monster_result.scalar_one_or_none()
        if monster is None:
            return 0

        prof_result = await db.execute(
            select(SkillDefinition.index, MonsterProficiency.value)
            .join(Proficiency, Proficiency.id == MonsterProficiency.proficiency_id)
            .join(SkillDefinition, SkillDefinition.id == Proficiency.skill_id)
            .where(
                MonsterProficiency.monster_id == monster_id,
                SkillDefinition.index.in_([s.value for s in skills]),
            )
        )
        prof_by_skill = {index: value for index, value in prof_result.all()}

        ability_by_skill = {
            Skill.athletics.value: monster.strength,
            Skill.acrobatics.value: monster.dexterity,
        }
        bonuses = []
        for skill in skills:
            if skill.value in prof_by_skill:
                bonuses.append(prof_by_skill[skill.value])
            elif skill.value in ability_by_skill:
                bonuses.append(calculate_modifier(ability_by_skill[skill.value]))
        return max(bonuses) if bonuses else 0

    async def _participant_owned_by(
        self,
        participant: EncounterParticipant,
        requester_id: uuid.UUID,
        db: AsyncSession,
    ) -> bool:
        """Whether `requester_id` owns the campaign membership behind `participant`."""
        if participant.character_id is None:
            return False
        result = await db.execute(
            select(Character).where(Character.id == participant.character_id)
        )
        character = result.scalar_one_or_none()
        if character is None:
            return False
        member_result = await db.execute(
            select(CampaignMember).where(
                CampaignMember.id == character.campaign_member_id
            )
        )
        member = member_result.scalar_one_or_none()
        return member is not None and member.user_id == requester_id

    async def get_log(
        self, encounter_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> list[CombatLogRead]:
        """List an encounter's combat log, in chronological order. Any member."""
        encounter, _member = await self.get_encounter_membership(
            encounter_id, requester_id, db
        )
        result = await db.execute(
            select(CombatLog)
            .where(CombatLog.encounter_id == encounter.id)
            .order_by(CombatLog.created_at)
        )
        return [CombatLogRead.model_validate(log) for log in result.scalars().all()]

    def _log(
        self,
        db: AsyncSession,
        encounter: Encounter,
        *,
        description: str,
        actor_id: uuid.UUID | None = None,
        target_id: uuid.UUID | None = None,
        action_type: ActionType = ActionType.other,
        damage_dealt: int | None = None,
        damage_type: str | None = None,
        rolled_by_system: bool = True,
    ) -> None:
        """Record one CombatLog entry at the encounter's current round/turn."""
        db.add(
            CombatLog(
                encounter_id=encounter.id,
                round=encounter.current_round,
                turn_order=encounter.current_turn_order,
                actor_id=actor_id,
                action_type=action_type,
                description=description,
                damage_dealt=damage_dealt,
                damage_type=damage_type,
                target_id=target_id,
                rolled_by_system=rolled_by_system,
            )
        )

    def _log_hp_change(
        self,
        db: AsyncSession,
        encounter: Encounter,
        participant: EncounterParticipant,
        new_hit_point_current: int,
    ) -> None:
        """Log a damage or heal entry from an HP change, skipping no-ops."""
        delta = new_hit_point_current - participant.hit_point_current
        if delta == 0:
            return
        if delta < 0:
            description = f"{participant.name} took {-delta} damage"
            damage_dealt = -delta
        else:
            description = f"{participant.name} healed {delta} HP"
            damage_dealt = None
        self._log(
            db,
            encounter,
            target_id=participant.id,
            description=description,
            damage_dealt=damage_dealt,
        )

    async def _concentration_dc(
        self,
        participant: EncounterParticipant,
        damage: int,
        db: AsyncSession,
    ) -> int | None:
        """DC for the target's concentration check, if damage broke it (Fase 7).

        `max(10, damage // 2)`, PHB rule — only computed for a Character
        participant currently concentrating on a spell; the client resolves
        the actual CON saving throw (backlog Fase 6's manual/auto roll flow
        already covers that).
        """
        if damage <= 0 or participant.character_id is None:
            return None
        result = await db.execute(
            select(Character).where(Character.id == participant.character_id)
        )
        character = result.scalar_one_or_none()
        if character is None or character.concentrating_spell_id is None:
            return None
        return max(10, damage // 2)

    def _find_participant_or_404(
        self, encounter: Encounter, participant_id: uuid.UUID
    ) -> EncounterParticipant:
        for participant in encounter.participants:
            if participant.id == participant_id:
                return participant
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found"
        )

    async def _reload_encounter(
        self, encounter_id: uuid.UUID, db: AsyncSession
    ) -> Encounter:
        """Reload an encounter with fresh relationships (see characters' equivalent)."""
        result = await db.execute(
            select(Encounter)
            .where(Encounter.id == encounter_id)
            .options(*_ENCOUNTER_LOAD_OPTIONS)
            .execution_options(populate_existing=True)
        )
        return result.scalar_one()

    async def _load_encounter_or_404(
        self, encounter_id: uuid.UUID, db: AsyncSession
    ) -> Encounter:
        result = await db.execute(
            select(Encounter)
            .where(Encounter.id == encounter_id)
            .options(*_ENCOUNTER_LOAD_OPTIONS)
        )
        encounter = result.scalar_one_or_none()
        if encounter is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found"
            )
        return encounter

    async def _require_session(
        self, session_id: uuid.UUID, db: AsyncSession
    ) -> Session:
        result = await db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
            )
        return session

    async def _require_membership(
        self, campaign_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> CampaignMember:
        result = await db.execute(
            select(CampaignMember).where(
                CampaignMember.campaign_id == campaign_id,
                CampaignMember.user_id == requester_id,
            )
        )
        member = result.scalar_one_or_none()
        if member is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this campaign",
            )
        return member

    async def _require_dm_for_session(
        self, session_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> Session:
        """Fetch `session_id`, ensuring `requester_id` is its campaign's DM."""
        session = await self._require_session(session_id, db)
        member = await self._require_membership(session.campaign_id, requester_id, db)
        if member.role != CampaignRole.dm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the campaign's DM can manage encounters",
            )
        return session
