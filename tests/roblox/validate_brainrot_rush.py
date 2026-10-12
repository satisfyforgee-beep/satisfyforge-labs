#!/usr/bin/env python3
"""Static safety contract for the Brainrot Rush v0.3 source pair.

This intentionally does not simulate Roblox. It protects the repository from
accidentally deleting important persistence, authority, economy, event, or HUD
mechanics before the required Studio/device release gate is completed.
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SERVER_PATH = ROOT / "src" / "roblox" / "BrainrotRush.server.lua"
CLIENT_PATH = ROOT / "src" / "roblox" / "BrainrotRush.client.lua"


def require(source: str, tokens: list[str], label: str) -> None:
    missing = [token for token in tokens if token not in source]
    assert not missing, f"{label} is missing required markers: {missing}"


def extract_number(source: str, name: str) -> float:
    match = re.search(rf"local\s+{re.escape(name)}\s*=\s*([0-9]+(?:\.[0-9]+)?)", source)
    assert match, f"missing numeric constant {name}"
    return float(match.group(1))


def validate_server(server: str) -> None:
    require(
        server,
        [
            'game:GetService("DataStoreService")',
            'DataStoreService:GetDataStore(DATASTORE_NAME)',
            'store:GetAsync("u_" .. player.UserId)',
            'store:SetAsync("u_" .. player.UserId, payload)',
            "Players.PlayerRemoving:Connect",
            "game:BindToClose",
            "task.wait(SAVE_INTERVAL)",
        ],
        "persistence contract",
    )
    require(
        server,
        [
            'local claimed = false',
            'if claimed then return end',
            'claimed = true',
            'stats.Brainrot.Value += payout',
            'stats.Collected.Value += 1',
        ],
        "server-authoritative collection contract",
    )
    require(
        server,
        [
            'local function upgradePrice(level)',
            'if currency.Value >= cost then',
            'if stats.Level.Value >= 20 and stats.Brainrot.Value >= 2500 then',
            'stats.Rebirths.Value += 1',
        ],
        "progression contract",
    )
    require(
        server,
        [
            'local function registerCombo(player)',
            'math.min(MAX_COMBO, combo + 1)',
            'local eventMultiplier = snackquakeActive and 2 or 1',
            'announce:FireAllClients("SNACKQUAKE!',
        ],
        "combo and Snackquake contract",
    )

    save_interval = extract_number(server, "SAVE_INTERVAL")
    combo_window = extract_number(server, "COMBO_WINDOW")
    max_combo = extract_number(server, "MAX_COMBO")
    snackquake_every = extract_number(server, "SNACKQUAKE_EVERY")
    snackquake_duration = extract_number(server, "SNACKQUAKE_DURATION")

    assert 30 <= save_interval <= 300, "autosave interval is outside the reviewed range"
    assert 1 <= combo_window <= 15, "combo window is outside the reviewed range"
    assert 2 <= max_combo <= 10, "combo cap is outside the reviewed range"
    assert snackquake_every > snackquake_duration > 0, "Snackquake timing is invalid"

    weights = [int(value) for value in re.findall(r"weight\s*=\s*(\d+)", server)]
    rewards = [int(value) for value in re.findall(r"reward\s*=\s*(\d+)", server)]
    assert weights and sum(weights) == 100, f"rarity weights must total 100, got {weights}"
    assert len(weights) == len(rewards) == 4, "expected four rarity tiers"
    assert all(value > 0 for value in rewards), "rarity rewards must be positive"

    claim_at = server.index("claimed = true")
    payout_at = server.index("stats.Brainrot.Value += payout")
    assert claim_at < payout_at, "orb must be claimed before currency is awarded"


def validate_client(client: str) -> None:
    require(
        client,
        [
            'gui.Name = "BrainrotRushHUD"',
            'gui.ResetOnSpawn = false',
            'grid.CellSize = UDim2.new(0.2, -4, 1, -10)',
            '{"Brainrot", "Level", "Collected", "Rebirths", "Combo"}',
            'player:GetAttributeChangedSignal("Combo")',
            'player:GetAttributeChangedSignal("Snackquake")',
            "announce.OnClientEvent:Connect",
        ],
        "responsive HUD contract",
    )

    forbidden = [
        'game:GetService("DataStoreService")',
        "FireServer(",
        "InvokeServer(",
        "stats.Brainrot.Value +=",
        "stats.Collected.Value +=",
    ]
    found = [token for token in forbidden if token in client]
    assert not found, f"client must not own rewards or persistence: {found}"


def main() -> None:
    server = SERVER_PATH.read_text(encoding="utf-8")
    client = CLIENT_PATH.read_text(encoding="utf-8")
    validate_server(server)
    validate_client(client)
    print("Brainrot Rush source contract: PASS")
    print("Scope: static source checks only; Roblox Studio/device testing is still required.")


if __name__ == "__main__":
    main()
