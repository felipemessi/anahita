"""Integration tests for the characters HTTP endpoints."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.auth.models  # noqa: F401 — registers models with Base
import app.campaigns.models  # noqa: F401 — registers models with Base
import app.catalog.models  # noqa: F401 — registers models with Base
import app.characters.models  # noqa: F401 — registers models with Base
from app.catalog.seeds.seed import seed_catalog
from app.database import Base, get_db
from app.main import app as fastapi_app

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    """Provide an httpx client wired to the FastAPI app, seeded catalog, isolated DB."""
    engine = create_async_engine(_TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _override_get_db() -> AsyncGenerator[AsyncSession]:
        async with factory() as session:
            yield session

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    try:
        async with factory() as seed_session:
            await seed_catalog(seed_session)
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="https://test") as ac:
            yield ac
    finally:
        fastapi_app.dependency_overrides.pop(get_db, None)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


async def _register_and_login(
    client: AsyncClient, email: str = "player@example.com"
) -> str:
    await client.post(
        "/auth/register",
        json={"email": email, "username": email.split("@")[0], "password": "pass1234"},
    )
    login_resp = await client.post(
        "/auth/login", json={"email": email, "password": "pass1234"}
    )
    token: str = login_resp.json()["access_token"]
    return token


_STANDARD_ARRAY = [
    {"ability": "str", "base_score": 15},
    {"ability": "dex", "base_score": 14},
    {"ability": "con", "base_score": 13},
    {"ability": "int", "base_score": 12},
    {"ability": "wis", "base_score": 10},
    {"ability": "cha", "base_score": 8},
]


async def test_create_character_over_http(client: AsyncClient) -> None:
    """A logged-in player can create a character sheet for their own membership."""
    token = await _register_and_login(client)
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Waterdeep"},
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_id = campaign_resp.json()["id"]

    membership_resp = await client.get(
        f"/campaigns/{campaign_id}/members/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert membership_resp.status_code == 200
    campaign_member_id = membership_resp.json()["id"]

    catalog_resp = await client.get("/catalog/races", params={"search": "Human"})
    human_race_id = catalog_resp.json()[0]["id"]
    classes_resp = await client.get("/catalog/classes", params={"search": "Fighter"})
    fighter_class_id = classes_resp.json()[0]["id"]

    resp = await client.post(
        "/characters",
        json={
            "campaign_member_id": campaign_member_id,
            "name": "Aldric",
            "race_id": human_race_id,
            "ability_scores": _STANDARD_ARRAY,
            "classes": [{"class_definition_id": fighter_class_id}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Aldric"
    assert body["campaign_member_id"] == campaign_member_id
    assert len(body["ability_scores"]) == 6
    assert len(body["classes"]) == 1
    assert body["hit_point_max"] == 11
    assert len(body["skills"]) == 18
    dex_modifier = next(
        s["modifier"] for s in body["ability_scores"] if s["ability"] == "dex"
    )
    assert dex_modifier == 2

    character_id = body["id"]
    get_resp = await client.get(
        f"/characters/{character_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == character_id


async def test_get_character_forbidden_for_other_player(client: AsyncClient) -> None:
    """A different player cannot fetch someone else's character sheet."""
    token = await _register_and_login(client, "owner@example.com")
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Baldur's Gate"},
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_id = campaign_resp.json()["id"]
    membership_resp = await client.get(
        f"/campaigns/{campaign_id}/members/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_member_id = membership_resp.json()["id"]

    races_resp = await client.get("/catalog/races", params={"search": "Human"})
    human_race_id = races_resp.json()[0]["id"]
    classes_resp = await client.get("/catalog/classes", params={"search": "Fighter"})
    fighter_class_id = classes_resp.json()[0]["id"]

    create_resp = await client.post(
        "/characters",
        json={
            "campaign_member_id": campaign_member_id,
            "name": "Aldric",
            "race_id": human_race_id,
            "ability_scores": _STANDARD_ARRAY,
            "classes": [{"class_definition_id": fighter_class_id}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    character_id = create_resp.json()["id"]

    outsider_token = await _register_and_login(client, "outsider@example.com")
    resp = await client.get(
        f"/characters/{character_id}",
        headers={"Authorization": f"Bearer {outsider_token}"},
    )
    assert resp.status_code == 403


async def test_multiclass_over_http(client: AsyncClient) -> None:
    """A player can add a second class to their character over HTTP."""
    token = await _register_and_login(client)
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Waterdeep"},
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_id = campaign_resp.json()["id"]
    membership_resp = await client.get(
        f"/campaigns/{campaign_id}/members/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_member_id = membership_resp.json()["id"]

    races_resp = await client.get("/catalog/races", params={"search": "Human"})
    human_race_id = races_resp.json()[0]["id"]
    fighter_resp = await client.get("/catalog/classes", params={"search": "Fighter"})
    fighter_class_id = fighter_resp.json()[0]["id"]
    wizard_resp = await client.get("/catalog/classes", params={"search": "Wizard"})
    wizard_class_id = wizard_resp.json()[0]["id"]

    create_resp = await client.post(
        "/characters",
        json={
            "campaign_member_id": campaign_member_id,
            "name": "Aldric",
            "race_id": human_race_id,
            "ability_scores": [
                {"ability": "str", "base_score": 15},
                {"ability": "dex", "base_score": 14},
                {"ability": "con", "base_score": 13},
                {"ability": "int", "base_score": 13},
                {"ability": "wis", "base_score": 10},
                {"ability": "cha", "base_score": 8},
            ],
            "classes": [{"class_definition_id": fighter_class_id}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    character_id = create_resp.json()["id"]

    resp = await client.post(
        f"/characters/{character_id}/classes",
        json={"class_definition_id": wizard_class_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["classes"]) == 2
    assert body["level"] == 2


async def test_list_characters_by_campaign_over_http(client: AsyncClient) -> None:
    """GET /characters?campaign_id= lists every character in the campaign."""
    token = await _register_and_login(client)
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Waterdeep"},
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_id = campaign_resp.json()["id"]
    membership_resp = await client.get(
        f"/campaigns/{campaign_id}/members/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_member_id = membership_resp.json()["id"]

    races_resp = await client.get("/catalog/races", params={"search": "Human"})
    human_race_id = races_resp.json()[0]["id"]
    fighter_resp = await client.get("/catalog/classes", params={"search": "Fighter"})
    fighter_class_id = fighter_resp.json()[0]["id"]

    await client.post(
        "/characters",
        json={
            "campaign_member_id": campaign_member_id,
            "name": "Aldric",
            "race_id": human_race_id,
            "ability_scores": _STANDARD_ARRAY,
            "classes": [{"class_definition_id": fighter_class_id}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = await client.get(
        "/characters",
        params={"campaign_id": campaign_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    names = [c["name"] for c in resp.json()]
    assert names == ["Aldric"]


async def test_list_characters_forbidden_for_non_member(client: AsyncClient) -> None:
    """A non-member cannot list a campaign's characters."""
    token = await _register_and_login(client, "dm@example.com")
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Waterdeep"},
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_id = campaign_resp.json()["id"]

    outsider_token = await _register_and_login(client, "outsider@example.com")
    resp = await client.get(
        "/characters",
        params={"campaign_id": campaign_id},
        headers={"Authorization": f"Bearer {outsider_token}"},
    )
    assert resp.status_code == 403


async def test_update_character_hp_over_http(client: AsyncClient) -> None:
    """A player can update their own character's current HP inline."""
    token = await _register_and_login(client)
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Waterdeep"},
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_id = campaign_resp.json()["id"]
    membership_resp = await client.get(
        f"/campaigns/{campaign_id}/members/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_member_id = membership_resp.json()["id"]

    races_resp = await client.get("/catalog/races", params={"search": "Human"})
    human_race_id = races_resp.json()[0]["id"]
    fighter_resp = await client.get("/catalog/classes", params={"search": "Fighter"})
    fighter_class_id = fighter_resp.json()[0]["id"]

    create_resp = await client.post(
        "/characters",
        json={
            "campaign_member_id": campaign_member_id,
            "name": "Aldric",
            "race_id": human_race_id,
            "ability_scores": _STANDARD_ARRAY,
            "classes": [{"class_definition_id": fighter_class_id}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    character_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/characters/{character_id}",
        json={"hit_point_current": 3},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["hit_point_current"] == 3


async def test_update_character_hp_rejects_exceeding_max(client: AsyncClient) -> None:
    """Setting hit_point_current above hit_point_max is rejected."""
    token = await _register_and_login(client)
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Waterdeep"},
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_id = campaign_resp.json()["id"]
    membership_resp = await client.get(
        f"/campaigns/{campaign_id}/members/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_member_id = membership_resp.json()["id"]

    races_resp = await client.get("/catalog/races", params={"search": "Human"})
    human_race_id = races_resp.json()[0]["id"]
    fighter_resp = await client.get("/catalog/classes", params={"search": "Fighter"})
    fighter_class_id = fighter_resp.json()[0]["id"]

    create_resp = await client.post(
        "/characters",
        json={
            "campaign_member_id": campaign_member_id,
            "name": "Aldric",
            "race_id": human_race_id,
            "ability_scores": _STANDARD_ARRAY,
            "classes": [{"class_definition_id": fighter_class_id}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    character_id = create_resp.json()["id"]
    hit_point_max = create_resp.json()["hit_point_max"]

    resp = await client.patch(
        f"/characters/{character_id}",
        json={"hit_point_current": hit_point_max + 100},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


async def test_update_character_forbidden_for_other_player(client: AsyncClient) -> None:
    """A different player cannot update someone else's character."""
    token = await _register_and_login(client, "owner@example.com")
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Waterdeep"},
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_id = campaign_resp.json()["id"]
    membership_resp = await client.get(
        f"/campaigns/{campaign_id}/members/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_member_id = membership_resp.json()["id"]

    races_resp = await client.get("/catalog/races", params={"search": "Human"})
    human_race_id = races_resp.json()[0]["id"]
    fighter_resp = await client.get("/catalog/classes", params={"search": "Fighter"})
    fighter_class_id = fighter_resp.json()[0]["id"]

    create_resp = await client.post(
        "/characters",
        json={
            "campaign_member_id": campaign_member_id,
            "name": "Aldric",
            "race_id": human_race_id,
            "ability_scores": _STANDARD_ARRAY,
            "classes": [{"class_definition_id": fighter_class_id}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    character_id = create_resp.json()["id"]

    outsider_token = await _register_and_login(client, "outsider@example.com")
    resp = await client.patch(
        f"/characters/{character_id}",
        json={"hit_point_current": 1},
        headers={"Authorization": f"Bearer {outsider_token}"},
    )
    assert resp.status_code == 403


async def test_update_character_identity_and_ability_score_over_http(
    client: AsyncClient,
) -> None:
    """A player can edit name/alignment/background and an ability score."""
    token = await _register_and_login(client)
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Waterdeep"},
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_id = campaign_resp.json()["id"]
    membership_resp = await client.get(
        f"/campaigns/{campaign_id}/members/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_member_id = membership_resp.json()["id"]

    races_resp = await client.get("/catalog/races", params={"search": "Human"})
    human_race_id = races_resp.json()[0]["id"]
    fighter_resp = await client.get("/catalog/classes", params={"search": "Fighter"})
    fighter_class_id = fighter_resp.json()[0]["id"]

    create_resp = await client.post(
        "/characters",
        json={
            "campaign_member_id": campaign_member_id,
            "name": "Aldric",
            "race_id": human_race_id,
            "ability_scores": _STANDARD_ARRAY,
            "classes": [{"class_definition_id": fighter_class_id}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    character_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/characters/{character_id}",
        json={
            "name": "Aldric the Bold",
            "alignment": "Lawful Good",
            "background": "Soldier",
            "ability_scores": [{"ability": "str", "base_score": 18}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Aldric the Bold"
    assert body["alignment"] == "Lawful Good"
    assert body["background"] == "Soldier"
    str_score = next(s for s in body["ability_scores"] if s["ability"] == "str")
    assert str_score["base_score"] == 18
    assert str_score["modifier"] == 4


async def test_add_spell_over_http(client: AsyncClient) -> None:
    """A player can add a known spell to their own character."""
    token = await _register_and_login(client)
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Waterdeep"},
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_id = campaign_resp.json()["id"]
    membership_resp = await client.get(
        f"/campaigns/{campaign_id}/members/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_member_id = membership_resp.json()["id"]

    races_resp = await client.get("/catalog/races", params={"search": "Human"})
    human_race_id = races_resp.json()[0]["id"]
    wizard_resp = await client.get("/catalog/classes", params={"search": "Wizard"})
    wizard_class_id = wizard_resp.json()[0]["id"]
    spell_resp = await client.get("/catalog/spells", params={"search": "Fireball"})
    fireball_id = spell_resp.json()[0]["id"]

    create_resp = await client.post(
        "/characters",
        json={
            "campaign_member_id": campaign_member_id,
            "name": "Aldric",
            "race_id": human_race_id,
            "ability_scores": _STANDARD_ARRAY,
            "classes": [{"class_definition_id": wizard_class_id}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    character_id = create_resp.json()["id"]

    resp = await client.post(
        f"/characters/{character_id}/spells",
        json={"spell_id": fireball_id, "prepared": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    spells = resp.json()["spells"]
    assert len(spells) == 1
    assert spells[0]["spell_id"] == fireball_id
    assert spells[0]["prepared"] is True


async def test_add_equipment_over_http(client: AsyncClient) -> None:
    """A player can add an item to their own character's inventory."""
    token = await _register_and_login(client)
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Waterdeep"},
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_id = campaign_resp.json()["id"]
    membership_resp = await client.get(
        f"/campaigns/{campaign_id}/members/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_member_id = membership_resp.json()["id"]

    races_resp = await client.get("/catalog/races", params={"search": "Human"})
    human_race_id = races_resp.json()[0]["id"]
    fighter_resp = await client.get("/catalog/classes", params={"search": "Fighter"})
    fighter_class_id = fighter_resp.json()[0]["id"]
    items_resp = await client.get("/catalog/items", params={"search": "Longsword"})
    longsword_id = items_resp.json()[0]["id"]

    create_resp = await client.post(
        "/characters",
        json={
            "campaign_member_id": campaign_member_id,
            "name": "Aldric",
            "race_id": human_race_id,
            "ability_scores": _STANDARD_ARRAY,
            "classes": [{"class_definition_id": fighter_class_id}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    character_id = create_resp.json()["id"]

    resp = await client.post(
        f"/characters/{character_id}/equipment",
        json={"item_id": longsword_id, "equipped": True, "quantity": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    equipment = resp.json()["equipment"]
    assert len(equipment) == 1
    assert equipment[0]["item_id"] == longsword_id
    assert equipment[0]["equipped"] is True


async def test_get_weapon_attack_profile_over_http(client: AsyncClient) -> None:
    """A player can resolve their equipped weapon into an attack profile."""
    token = await _register_and_login(client)
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Waterdeep"},
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_id = campaign_resp.json()["id"]
    membership_resp = await client.get(
        f"/campaigns/{campaign_id}/members/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_member_id = membership_resp.json()["id"]

    races_resp = await client.get("/catalog/races", params={"search": "Human"})
    human_race_id = races_resp.json()[0]["id"]
    fighter_resp = await client.get("/catalog/classes", params={"search": "Fighter"})
    fighter_class_id = fighter_resp.json()[0]["id"]
    items_resp = await client.get("/catalog/items", params={"search": "Longsword"})
    longsword_id = items_resp.json()[0]["id"]

    create_resp = await client.post(
        "/characters",
        json={
            "campaign_member_id": campaign_member_id,
            "name": "Aldric",
            "race_id": human_race_id,
            "ability_scores": _STANDARD_ARRAY,
            "classes": [{"class_definition_id": fighter_class_id}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    character_id = create_resp.json()["id"]

    equip_resp = await client.post(
        f"/characters/{character_id}/equipment",
        json={"item_id": longsword_id, "equipped": True, "quantity": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    equipment_id = equip_resp.json()["equipment"][0]["id"]

    resp = await client.get(
        f"/characters/{character_id}/equipment/{equipment_id}/attack-profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    # STR 15 -> +2 mod; Fighter is proficient with martial weapons
    # (Longsword) -> level 1 proficiency bonus +2.
    assert body["attack_bonus"] == 4
    assert body["damage_bonus"] == 2
    assert body["proficient"] is True


async def test_get_spell_attack_profile_over_http(client: AsyncClient) -> None:
    """A player can resolve a known spell into an attack/save + damage profile."""
    token = await _register_and_login(client)
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Waterdeep"},
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_id = campaign_resp.json()["id"]
    membership_resp = await client.get(
        f"/campaigns/{campaign_id}/members/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_member_id = membership_resp.json()["id"]

    races_resp = await client.get("/catalog/races", params={"search": "Human"})
    human_race_id = races_resp.json()[0]["id"]
    wizard_resp = await client.get("/catalog/classes", params={"search": "Wizard"})
    wizard_class_id = wizard_resp.json()[0]["id"]
    spell_resp = await client.get("/catalog/spells", params={"search": "Fireball"})
    fireball_id = spell_resp.json()[0]["id"]

    create_resp = await client.post(
        "/characters",
        json={
            "campaign_member_id": campaign_member_id,
            "name": "Aldric",
            "race_id": human_race_id,
            "ability_scores": _STANDARD_ARRAY,
            "classes": [{"class_definition_id": wizard_class_id}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    character_id = create_resp.json()["id"]

    add_resp = await client.post(
        f"/characters/{character_id}/spells",
        json={"spell_id": fireball_id, "source_class": "wizard"},
        headers={"Authorization": f"Bearer {token}"},
    )
    spell_entry_id = add_resp.json()["spells"][0]["id"]

    resp = await client.get(
        f"/characters/{character_id}/spells/{spell_entry_id}/attack-profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["action_type"] == "saving_throw"
    assert body["save_dc"] is not None
    assert body["save_ability"] == "dex"
    assert body["damage_dice"]


async def test_add_feature_over_http(client: AsyncClient) -> None:
    """A player can record a class feature on their own character."""
    token = await _register_and_login(client)
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Waterdeep"},
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_id = campaign_resp.json()["id"]
    membership_resp = await client.get(
        f"/campaigns/{campaign_id}/members/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_member_id = membership_resp.json()["id"]

    races_resp = await client.get("/catalog/races", params={"search": "Human"})
    human_race_id = races_resp.json()[0]["id"]
    fighter_resp = await client.get("/catalog/classes", params={"search": "Fighter"})
    fighter_class_id = fighter_resp.json()[0]["id"]

    create_resp = await client.post(
        "/characters",
        json={
            "campaign_member_id": campaign_member_id,
            "name": "Aldric",
            "race_id": human_race_id,
            "ability_scores": _STANDARD_ARRAY,
            "classes": [{"class_definition_id": fighter_class_id}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    character_id = create_resp.json()["id"]

    resp = await client.post(
        f"/characters/{character_id}/features",
        json={
            "source_type": "class",
            "source_name": "Fighter",
            "feature_name": "Second Wind",
            "level_acquired": 1,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    features = resp.json()["features"]
    assert len(features) == 1
    assert features[0]["feature_name"] == "Second Wind"


async def test_add_spell_forbidden_for_other_player(client: AsyncClient) -> None:
    """A different player cannot add a spell to someone else's character."""
    token = await _register_and_login(client, "owner@example.com")
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Waterdeep"},
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_id = campaign_resp.json()["id"]
    membership_resp = await client.get(
        f"/campaigns/{campaign_id}/members/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_member_id = membership_resp.json()["id"]

    races_resp = await client.get("/catalog/races", params={"search": "Human"})
    human_race_id = races_resp.json()[0]["id"]
    wizard_resp = await client.get("/catalog/classes", params={"search": "Wizard"})
    wizard_class_id = wizard_resp.json()[0]["id"]
    spell_resp = await client.get("/catalog/spells", params={"search": "Fireball"})
    fireball_id = spell_resp.json()[0]["id"]

    create_resp = await client.post(
        "/characters",
        json={
            "campaign_member_id": campaign_member_id,
            "name": "Aldric",
            "race_id": human_race_id,
            "ability_scores": _STANDARD_ARRAY,
            "classes": [{"class_definition_id": wizard_class_id}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    character_id = create_resp.json()["id"]

    outsider_token = await _register_and_login(client, "outsider@example.com")
    resp = await client.post(
        f"/characters/{character_id}/spells",
        json={"spell_id": fireball_id},
        headers={"Authorization": f"Bearer {outsider_token}"},
    )
    assert resp.status_code == 403


async def test_list_characters_summary_for_other_player_over_http(
    client: AsyncClient,
) -> None:
    """Listing a campaign's characters over HTTP hides other players' full sheets."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Shared Table"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    campaign_id = campaign_resp.json()["id"]

    races_resp = await client.get("/catalog/races", params={"search": "Human"})
    human_race_id = races_resp.json()[0]["id"]
    fighter_resp = await client.get("/catalog/classes", params={"search": "Fighter"})
    fighter_class_id = fighter_resp.json()[0]["id"]

    async def _join_and_create(email: str, name: str) -> str:
        invite_resp = await client.post(
            f"/campaigns/{campaign_id}/invites",
            json={"role": "player"},
            headers={"Authorization": f"Bearer {dm_token}"},
        )
        invite_code = invite_resp.json()["invite_code"]
        token = await _register_and_login(client, email)
        await client.post(
            "/campaigns/invites/redeem",
            json={"invite_code": invite_code},
            headers={"Authorization": f"Bearer {token}"},
        )
        member_resp = await client.get(
            f"/campaigns/{campaign_id}/members/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        member_id = member_resp.json()["id"]
        await client.post(
            "/characters",
            json={
                "campaign_member_id": member_id,
                "name": name,
                "race_id": human_race_id,
                "ability_scores": _STANDARD_ARRAY,
                "classes": [{"class_definition_id": fighter_class_id}],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        return token

    player_a_token = await _join_and_create("a@example.com", "Aldric")
    await _join_and_create("b@example.com", "Brenna")

    list_resp = await client.get(
        "/characters",
        params={"campaign_id": campaign_id},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert list_resp.status_code == 200
    by_name = {c["name"]: c for c in list_resp.json()}
    assert "hit_point_max" in by_name["Aldric"]
    assert "hit_point_max" not in by_name["Brenna"]
    assert "ability_scores" not in by_name["Brenna"]
    assert by_name["Brenna"]["level"] == 1
