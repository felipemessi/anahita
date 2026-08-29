"""Integration tests for catalog homebrew-creation HTTP endpoints."""

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


async def _register_and_login(client: AsyncClient, email: str) -> str:
    await client.post(
        "/auth/register",
        json={"email": email, "username": email.split("@")[0], "password": "pass1234"},
    )
    login_resp = await client.post(
        "/auth/login", json={"email": email, "password": "pass1234"}
    )
    token: str = login_resp.json()["access_token"]
    return token


async def _make_campaign(client: AsyncClient, dm_token: str, name: str) -> str:
    resp = await client.post(
        "/campaigns",
        json={"name": name},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    campaign_id: str = resp.json()["id"]
    return campaign_id


async def test_create_race_requires_dm(client: AsyncClient) -> None:
    """A non-DM member is rejected with 403 when creating homebrew."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_id = await _make_campaign(client, dm_token, "Waterdeep")

    invite_resp = await client.post(
        f"/campaigns/{campaign_id}/invites",
        json={"role": "player"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    invite_code = invite_resp.json()["invite_code"]
    player_token = await _register_and_login(client, "player@example.com")
    await client.post(
        "/campaigns/invites/redeem",
        json={"invite_code": invite_code},
        headers={"Authorization": f"Bearer {player_token}"},
    )

    resp = await client.post(
        "/catalog/races",
        json={"campaign_id": campaign_id, "name": "Homebrew Elf"},
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert resp.status_code == 403


async def test_create_race_over_http(client: AsyncClient) -> None:
    """The DM can create a homebrew race scoped to their campaign."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_id = await _make_campaign(client, dm_token, "Waterdeep")

    resp = await client.post(
        "/catalog/races",
        json={
            "campaign_id": campaign_id,
            "name": "Duskling",
            "description": "A twilight-touched folk.",
            "speed": 25,
        },
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Duskling"
    assert body["speed"] == 25
    assert body["is_custom"] is True


async def test_created_homebrew_visible_only_in_own_campaign(
    client: AsyncClient,
) -> None:
    """`GET /catalog/races?campaign_id=` scopes homebrew to that campaign only."""
    dm_a_token = await _register_and_login(client, "dm-a@example.com")
    campaign_a = await _make_campaign(client, dm_a_token, "Campaign A")
    dm_b_token = await _register_and_login(client, "dm-b@example.com")
    campaign_b = await _make_campaign(client, dm_b_token, "Campaign B")

    await client.post(
        "/catalog/races",
        json={"campaign_id": campaign_a, "name": "Campaign A Homebrew"},
        headers={"Authorization": f"Bearer {dm_a_token}"},
    )

    resp = await client.get(
        "/catalog/races",
        params={"campaign_id": campaign_b, "include_custom": True},
    )
    names = [r["name"] for r in resp.json()]
    assert "Campaign A Homebrew" not in names

    own_resp = await client.get(
        "/catalog/races",
        params={"campaign_id": campaign_a, "include_custom": True},
    )
    own_names = [r["name"] for r in own_resp.json()]
    assert "Campaign A Homebrew" in own_names


async def test_create_spell_rejects_unknown_school(client: AsyncClient) -> None:
    """Creating a homebrew spell with an unknown magic school is rejected."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_id = await _make_campaign(client, dm_token, "Waterdeep")

    resp = await client.post(
        "/catalog/spells",
        json={
            "campaign_id": campaign_id,
            "name": "Bogus Bolt",
            "level": 1,
            "school": "not-a-real-school",
        },
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert resp.status_code == 422


async def test_create_spell_and_monster_over_http(client: AsyncClient) -> None:
    """The DM can create a homebrew spell and monster scoped to their campaign."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_id = await _make_campaign(client, dm_token, "Waterdeep")

    spell_resp = await client.post(
        "/catalog/spells",
        json={
            "campaign_id": campaign_id,
            "name": "Homebrew Bolt",
            "level": 1,
            "school": "evocation",
        },
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert spell_resp.status_code == 201
    assert spell_resp.json()["school"] == "evocation"

    monster_resp = await client.post(
        "/catalog/monsters",
        json={
            "campaign_id": campaign_id,
            "name": "Swamp Horror",
            "size": "large",
            "creature_type": "monstrosity",
            "hit_points": 45,
            "challenge_rating": 3,
        },
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert monster_resp.status_code == 201
    assert monster_resp.json()["hit_points"] == 45


async def test_create_item_over_http(client: AsyncClient) -> None:
    """The DM can create a homebrew item scoped to their campaign."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_id = await _make_campaign(client, dm_token, "Waterdeep")

    resp = await client.post(
        "/catalog/items",
        json={
            "campaign_id": campaign_id,
            "name": "Rusty Dagger",
            "item_type": "weapon",
        },
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["item_type"] == "weapon"


async def test_create_magic_item_over_http(client: AsyncClient) -> None:
    """The DM can create a homebrew magic item scoped to their campaign."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_id = await _make_campaign(client, dm_token, "Waterdeep")

    resp = await client.post(
        "/catalog/magic-items",
        json={
            "campaign_id": campaign_id,
            "name": "Ring of Whispers",
            "rarity": "uncommon",
        },
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Ring of Whispers"
    assert body["is_custom"] is True


async def test_create_background_over_http(client: AsyncClient) -> None:
    """The DM can create a homebrew background scoped to their campaign."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_id = await _make_campaign(client, dm_token, "Waterdeep")

    resp = await client.post(
        "/catalog/backgrounds",
        json={"campaign_id": campaign_id, "name": "Shipwreck Survivor"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Shipwreck Survivor"


async def test_create_feat_over_http(client: AsyncClient) -> None:
    """The DM can create a homebrew feat scoped to their campaign."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_id = await _make_campaign(client, dm_token, "Waterdeep")

    resp = await client.post(
        "/catalog/feats",
        json={"campaign_id": campaign_id, "name": "Storm Born"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Storm Born"


async def test_create_rule_over_http(client: AsyncClient) -> None:
    """The DM can create a homebrew rule scoped to their campaign."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_id = await _make_campaign(client, dm_token, "Waterdeep")

    resp = await client.post(
        "/catalog/rules",
        json={
            "campaign_id": campaign_id,
            "name": "House Rule: Flanking",
            "desc": "Flanking grants advantage.",
        },
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "House Rule: Flanking"


async def test_rule_homebrew_visible_only_in_own_campaign(client: AsyncClient) -> None:
    """`GET /catalog/rules?campaign_id=` scopes homebrew to that campaign only."""
    dm_a_token = await _register_and_login(client, "dm-a@example.com")
    campaign_a = await _make_campaign(client, dm_a_token, "Campaign A")
    dm_b_token = await _register_and_login(client, "dm-b@example.com")
    campaign_b = await _make_campaign(client, dm_b_token, "Campaign B")

    await client.post(
        "/catalog/rules",
        json={"campaign_id": campaign_a, "name": "Campaign A House Rule"},
        headers={"Authorization": f"Bearer {dm_a_token}"},
    )

    other_resp = await client.get("/catalog/rules", params={"campaign_id": campaign_b})
    names = [r["name"] for r in other_resp.json()]
    assert "Campaign A House Rule" not in names

    own_resp = await client.get("/catalog/rules", params={"campaign_id": campaign_a})
    own_names = [r["name"] for r in own_resp.json()]
    assert "Campaign A House Rule" in own_names


async def test_create_monster_rejects_invalid_size(client: AsyncClient) -> None:
    """An unknown `size` value is rejected with a clean 422, not a 500.

    Regression test: `MonsterCreate.size` used to be a bare `str`, while
    `Monster.size` is a native DB enum (`CreatureSize`). A value outside the
    enum (e.g. a size the DM mistyped, or a translated label like "Grande")
    passed Pydantic validation, got written to the row, and only blew up
    with an unhandled `LookupError` -> 500 when the row was read back to
    build the response — see Fase 9 backlog story on homebrew creation.
    """
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_id = await _make_campaign(client, dm_token, "Waterdeep")

    resp = await client.post(
        "/catalog/monsters",
        json={
            "campaign_id": campaign_id,
            "name": "Swamp Horror",
            "size": "Grande",
            "creature_type": "monstrosity",
            "hit_points": 45,
            "challenge_rating": 3,
        },
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert resp.status_code == 422


async def test_create_magic_item_requires_dm(client: AsyncClient) -> None:
    """A non-DM member is rejected with 403 when creating homebrew magic items."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_id = await _make_campaign(client, dm_token, "Waterdeep")

    invite_resp = await client.post(
        f"/campaigns/{campaign_id}/invites",
        json={"role": "player"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    invite_code = invite_resp.json()["invite_code"]
    player_token = await _register_and_login(client, "player@example.com")
    await client.post(
        "/campaigns/invites/redeem",
        json={"invite_code": invite_code},
        headers={"Authorization": f"Bearer {player_token}"},
    )

    resp = await client.post(
        "/catalog/magic-items",
        json={"campaign_id": campaign_id, "name": "Stolen Ring"},
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert resp.status_code == 403


# --- Homebrew deletion (backlog Fase 11) -------------------------------------

#: (URL path segment, minimal create payload beyond `campaign_id`) for each
#: of the 9 homebrew categories — reused by the parametrized delete tests
#: below so every category exercises the same policy.
_CATEGORIES: list[tuple[str, dict[str, object]]] = [
    ("races", {"name": "Duskling"}),
    ("classes", {"name": "Duelist", "hit_die": 8, "primary_ability": "dex"}),
    ("spells", {"name": "Homebrew Bolt", "level": 1, "school": "evocation"}),
    ("items", {"name": "Rusty Dagger", "item_type": "weapon"}),
    ("magic-items", {"name": "Ring of Whispers"}),
    ("backgrounds", {"name": "Shipwreck Survivor"}),
    ("feats", {"name": "Storm Born"}),
    (
        "monsters",
        {
            "name": "Swamp Horror",
            "size": "large",
            "creature_type": "monstrosity",
            "hit_points": 45,
            "challenge_rating": 3,
        },
    ),
    ("rules", {"name": "House Rule: Flanking", "desc": "Advantage."}),
]


@pytest.mark.parametrize("path, payload", _CATEGORIES)
async def test_delete_own_campaign_homebrew_succeeds(
    client: AsyncClient, path: str, payload: dict[str, object]
) -> None:
    """The DM can delete homebrew they created in their own campaign."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_id = await _make_campaign(client, dm_token, "Waterdeep")

    create_resp = await client.post(
        f"/catalog/{path}",
        json={"campaign_id": campaign_id, **payload},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert create_resp.status_code == 201
    entity_id = create_resp.json()["id"]

    delete_resp = await client.delete(
        f"/catalog/{path}/{entity_id}",
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert delete_resp.status_code == 204

    get_resp = await client.get(f"/catalog/{path}/{entity_id}")
    assert get_resp.status_code == 404


@pytest.mark.parametrize("path, payload", _CATEGORIES)
async def test_delete_srd_content_is_rejected(
    client: AsyncClient, path: str, payload: dict[str, object]
) -> None:
    """Deleting SRD content (campaign_id IS NULL) is rejected, never deleted."""
    dm_token = await _register_and_login(client, "dm@example.com")
    await _make_campaign(client, dm_token, "Waterdeep")

    list_resp = await client.get(f"/catalog/{path}", params={"include_custom": False})
    srd_entries = list_resp.json()
    assert srd_entries, f"expected seeded SRD {path}"
    srd_id = srd_entries[0]["id"]

    delete_resp = await client.delete(
        f"/catalog/{path}/{srd_id}",
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert delete_resp.status_code == 403

    get_resp = await client.get(f"/catalog/{path}/{srd_id}")
    assert get_resp.status_code == 200


@pytest.mark.parametrize("path, payload", _CATEGORIES)
async def test_delete_other_campaign_homebrew_is_rejected(
    client: AsyncClient, path: str, payload: dict[str, object]
) -> None:
    """Deleting homebrew from a campaign the requester isn't in returns 404.

    Not 403 — a DM of Campaign A must never learn whether homebrew content
    exists in Campaign B, which they have no access to at all.
    """
    dm_a_token = await _register_and_login(client, "dm-a@example.com")
    campaign_a = await _make_campaign(client, dm_a_token, "Campaign A")
    dm_b_token = await _register_and_login(client, "dm-b@example.com")
    await _make_campaign(client, dm_b_token, "Campaign B")

    create_resp = await client.post(
        f"/catalog/{path}",
        json={"campaign_id": campaign_a, **payload},
        headers={"Authorization": f"Bearer {dm_a_token}"},
    )
    assert create_resp.status_code == 201
    entity_id = create_resp.json()["id"]

    delete_resp = await client.delete(
        f"/catalog/{path}/{entity_id}",
        headers={"Authorization": f"Bearer {dm_b_token}"},
    )
    assert delete_resp.status_code == 404

    get_resp = await client.get(f"/catalog/{path}/{entity_id}")
    assert get_resp.status_code == 200


async def test_delete_homebrew_requires_dm(client: AsyncClient) -> None:
    """A non-DM member of the owning campaign is rejected with 403, not 404."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_id = await _make_campaign(client, dm_token, "Waterdeep")

    create_resp = await client.post(
        "/catalog/races",
        json={"campaign_id": campaign_id, "name": "Duskling"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    race_id = create_resp.json()["id"]

    invite_resp = await client.post(
        f"/campaigns/{campaign_id}/invites",
        json={"role": "player"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    invite_code = invite_resp.json()["invite_code"]
    player_token = await _register_and_login(client, "player@example.com")
    await client.post(
        "/campaigns/invites/redeem",
        json={"invite_code": invite_code},
        headers={"Authorization": f"Bearer {player_token}"},
    )

    resp = await client.delete(
        f"/catalog/races/{race_id}",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert resp.status_code == 403

    # 403 (not 404) because the player *is* a member of this campaign — the
    # 404-instead-of-403 leak protection only kicks in for a non-member (see
    # `test_delete_other_campaign_homebrew_is_rejected` above).
    get_resp = await client.get(f"/catalog/races/{race_id}")
    assert get_resp.status_code == 200


# The 409-on-existing-reference policy (block deletion when a character
# still uses the homebrew entity) is exercised directly against the service
# layer in `tests/catalog/test_service.py` — building a referencing row (a
# `Character`, `CharacterClass`, `CharacterSpell`, etc.) doesn't need the
# full character-creation HTTP flow, and every one of the 6 categories with
# a cross-domain reference (races, classes, spells, items, magic items,
# monsters) is covered there.


# --- Race depth: attach ability bonuses / traits / subraces (Fase 11) -------


async def test_attach_ability_bonus_to_homebrew_race(client: AsyncClient) -> None:
    """The DM can attach an ability bonus to their own homebrew race."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_id = await _make_campaign(client, dm_token, "Waterdeep")
    create_resp = await client.post(
        "/catalog/races",
        json={"campaign_id": campaign_id, "name": "Duskling"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    race_id = create_resp.json()["id"]

    resp = await client.post(
        f"/catalog/races/{race_id}/ability-bonuses",
        json={"ability": "wis", "bonus": 2},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["ability"] == "wis"
    assert resp.json()["bonus"] == 2

    race_resp = await client.get(f"/catalog/races/{race_id}")
    ability_bonuses = race_resp.json()["ability_bonuses"]
    assert any(ab["ability"] == "wis" and ab["bonus"] == 2 for ab in ability_bonuses)


async def test_attach_trait_to_homebrew_race(client: AsyncClient) -> None:
    """The DM can attach a trait to their own homebrew race."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_id = await _make_campaign(client, dm_token, "Waterdeep")
    create_resp = await client.post(
        "/catalog/races",
        json={"campaign_id": campaign_id, "name": "Duskling"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    race_id = create_resp.json()["id"]

    resp = await client.post(
        f"/catalog/races/{race_id}/traits",
        json={
            "trait_name": "Twilight Resilience",
            "description": "Resistance to necrotic damage.",
            "mechanical_effect": "resistance:necrotic",
        },
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["trait_name"] == "Twilight Resilience"

    race_resp = await client.get(f"/catalog/races/{race_id}")
    names = [t["trait_name"] for t in race_resp.json()["traits"]]
    assert "Twilight Resilience" in names


async def test_attach_subrace_to_homebrew_race(client: AsyncClient) -> None:
    """The DM can attach a subrace, with nested traits/bonuses, in one request."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_id = await _make_campaign(client, dm_token, "Waterdeep")
    create_resp = await client.post(
        "/catalog/races",
        json={"campaign_id": campaign_id, "name": "Duskling"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    race_id = create_resp.json()["id"]

    resp = await client.post(
        f"/catalog/races/{race_id}/subraces",
        json={
            "name": "Deep Duskling",
            "description": "A subrace adapted to the Underdark.",
            "ability_bonuses": [{"ability": "con", "bonus": 1}],
            "traits": [
                {
                    "trait_name": "Sunlight Sensitivity",
                    "description": "Disadvantage on attacks in direct sunlight.",
                }
            ],
        },
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Deep Duskling"
    assert body["ability_bonuses"][0]["ability"] == "con"
    assert body["traits"][0]["trait_name"] == "Sunlight Sensitivity"

    race_resp = await client.get(f"/catalog/races/{race_id}")
    subrace_names = [s["name"] for s in race_resp.json()["subraces"]]
    assert "Deep Duskling" in subrace_names


@pytest.mark.parametrize(
    "sub_path, payload",
    [
        ("ability-bonuses", {"ability": "wis", "bonus": 1}),
        ("traits", {"trait_name": "Some Trait"}),
        ("subraces", {"name": "Some Subrace"}),
    ],
)
async def test_attach_to_srd_race_is_rejected(
    client: AsyncClient, sub_path: str, payload: dict[str, object]
) -> None:
    """Attaching to an SRD race (campaign_id IS NULL) is rejected, not written."""
    dm_token = await _register_and_login(client, "dm@example.com")
    await _make_campaign(client, dm_token, "Waterdeep")

    list_resp = await client.get(
        "/catalog/races", params={"include_custom": False}
    )
    srd_race_id = list_resp.json()[0]["id"]

    resp = await client.post(
        f"/catalog/races/{srd_race_id}/{sub_path}",
        json=payload,
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.parametrize(
    "sub_path, payload",
    [
        ("ability-bonuses", {"ability": "wis", "bonus": 1}),
        ("traits", {"trait_name": "Some Trait"}),
        ("subraces", {"name": "Some Subrace"}),
    ],
)
async def test_attach_to_other_campaign_homebrew_race_is_rejected(
    client: AsyncClient, sub_path: str, payload: dict[str, object]
) -> None:
    """Attaching to another campaign's homebrew race returns 404, not 403.

    Same leak-protection policy as delete: a DM of Campaign A must never
    learn whether homebrew content exists in Campaign B.
    """
    dm_a_token = await _register_and_login(client, "dm-a@example.com")
    campaign_a = await _make_campaign(client, dm_a_token, "Campaign A")
    dm_b_token = await _register_and_login(client, "dm-b@example.com")
    await _make_campaign(client, dm_b_token, "Campaign B")

    create_resp = await client.post(
        "/catalog/races",
        json={"campaign_id": campaign_a, "name": "Duskling"},
        headers={"Authorization": f"Bearer {dm_a_token}"},
    )
    race_id = create_resp.json()["id"]

    resp = await client.post(
        f"/catalog/races/{race_id}/{sub_path}",
        json=payload,
        headers={"Authorization": f"Bearer {dm_b_token}"},
    )
    assert resp.status_code == 404


async def test_attach_ability_bonus_requires_dm(client: AsyncClient) -> None:
    """A non-DM member of the owning campaign is rejected with 403, not 404."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_id = await _make_campaign(client, dm_token, "Waterdeep")
    create_resp = await client.post(
        "/catalog/races",
        json={"campaign_id": campaign_id, "name": "Duskling"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    race_id = create_resp.json()["id"]

    invite_resp = await client.post(
        f"/campaigns/{campaign_id}/invites",
        json={"role": "player"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    invite_code = invite_resp.json()["invite_code"]
    player_token = await _register_and_login(client, "player@example.com")
    await client.post(
        "/campaigns/invites/redeem",
        json={"invite_code": invite_code},
        headers={"Authorization": f"Bearer {player_token}"},
    )

    resp = await client.post(
        f"/catalog/races/{race_id}/ability-bonuses",
        json={"ability": "wis", "bonus": 1},
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert resp.status_code == 403


async def test_create_race_rejects_unknown_language_id(client: AsyncClient) -> None:
    """RaceCreate rejects an unknown `language_ids` entry with 422."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_id = await _make_campaign(client, dm_token, "Waterdeep")

    resp = await client.post(
        "/catalog/races",
        json={
            "campaign_id": campaign_id,
            "name": "Duskling",
            "language_ids": ["00000000-0000-0000-0000-000000000000"],
        },
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert resp.status_code == 422
