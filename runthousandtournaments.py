#!/usr/bin/env python3
"""
Run many tournaments and summarize placement frequencies
PLUS 3-2-1 point scoring.
"""
import sys
from collections import defaultdict
from tournament_runner import TournamentRunner, TournamentSettings, TournamentType

NUM_RUNS = 1000

def main():
    print("🃏 Poker Bot Tournament System (multi-run) 🤖")
    print("=" * 60)

    settings = TournamentSettings(
        tournament_type=TournamentType.FREEZE_OUT,
        starting_chips=1000,
        small_blind=10,
        big_blind=20,
        time_limit_per_action=10.0,
        blind_increase_interval=10,
        blind_increase_factor=1.5
    )

    placement_counts = defaultdict(lambda: defaultdict(int))
    total_points = defaultdict(int)   # ★ NEW ★

    runner = TournamentRunner(settings, players_directory="players", log_directory="logs")

    print(f"Running {NUM_RUNS} tournaments...")

    for i in range(NUM_RUNS):
        try:
            results = runner.run_tournament()
        except Exception as e:
            print(f"❌ Run {i+1}: Tournament failed with error: {e}")
            try:
                runner = TournamentRunner(settings, players_directory="players", log_directory="logs")
            except Exception as ee:
                print(f"   ⚠️ Failed to recreate TournamentRunner: {ee}")
                print("   Aborting remaining runs.")
                break
            continue

        standings = results.get('final_standings')
        if not standings:
            print(f"⚠️ Run {i+1}: No 'final_standings' in results, skipping.")
            continue

        # READ STANDINGS FORMAT
        ordered_players = []

        if isinstance(standings[0], (list, tuple)) and len(standings[0]) >= 3:
            # Format: (player_name, chips, position)
            for entry in standings:
                player = entry[0]
                position = entry[2]
                placement_counts[player][position] += 1
                ordered_players.append((player, position))
        else:
            # Fallback: standings is simply a list of player names in finishing order
            for pos, pname in enumerate(standings, start=1):
                placement_counts[pname][pos] += 1
                ordered_players.append((pname, pos))

        # ★★★ ADD 3-2-1 POINTS ★★★
        for player, pos in ordered_players:
            if pos == 1:
                total_points[player] += 3
            elif pos == 2:
                total_points[player] += 2
            elif pos == 3:
                total_points[player] += 1

        if (i + 1) % 50 == 0 or (i + 1) == NUM_RUNS:
            print(f"  → Completed {i+1} / {NUM_RUNS} runs")

    # SUMMARY
    print("\n🎉 Runs complete. Summary of placements:")
    print("=" * 60)

    players = sorted(placement_counts.keys())
    for player in players:
        counts = placement_counts[player]
        places_text = "  ".join(
            f"{pos}st:{counts.get(pos,0)}" if pos == 1 else
            f"{pos}nd:{counts.get(pos,0)}" if pos == 2 else
            f"{pos}rd:{counts.get(pos,0)}" if pos == 3 else
            f"{pos}th:{counts.get(pos,0)}"
            for pos in range(1, 5)
        )
        print(f"{player:20s} {places_text}")

    print("\n🏆 Total Points (3–2–1 System):")
    print("=" * 60)

    # Sort by points descending
    ranking = sorted(total_points.items(), key=lambda x: x[1], reverse=True)
    for player, pts in ranking:
        print(f"{player:20s} {pts} pts")

    print("\nDone.")

if __name__ == "__main__":
    main()