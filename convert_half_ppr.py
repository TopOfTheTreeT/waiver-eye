import csv
from collections import defaultdict

# Read the Half PPR CSV
half_ppr_file = r'c:\_Projects\waiver-eye\example-data\Half PPR 2026 Draft Rankings (08_29_2026) - Half PPR Cheat Sheet (08_29).csv'
output_file = r'c:\_Projects\waiver-eye\example-data\Half_PPR_Converted.csv'

# Store all players by position
players_by_position = defaultdict(list)
seen_players = set()

with open(half_ppr_file, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    
    # Skip header
    next(reader)
    
    # Process data rows
    for row in reader:
        # Skip empty lines and note lines
        if not row or not any(row):
            continue
        
        # QB section: columns 0-2 (Rank, Name, Tier)
        if len(row) > 2 and row[0] and row[1]:
            try:
                qb_rank = int(row[0])
                qb_name = row[1].strip()
                qb_tier = row[2].strip() if len(row) > 2 else ""
                if qb_name and qb_name not in seen_players:
                    seen_players.add(qb_name)
                    players_by_position['QB'].append((qb_rank, qb_name, qb_tier))
            except:
                pass
        
        try:
            # RB section 1: columns 4-6 (Rank, Name, Tier)
            if len(row) > 6 and row[4] and row[5]:
                rb_rank = int(row[4])
                rb_name = row[5].strip()
                rb_tier = row[6].strip() if len(row) > 6 else ""
                if rb_name and rb_name not in seen_players:
                    seen_players.add(rb_name)
                    players_by_position['RB'].append((rb_rank, rb_name, rb_tier))
        except:
            pass
        
        try:
            # RB section 2: columns 8-10 (Rank, Name, Tier)
            if len(row) > 10 and row[8] and row[9]:
                rb_rank = int(row[8])
                rb_name = row[9].strip()
                rb_tier = row[10].strip() if len(row) > 10 else ""
                if rb_name and rb_name not in seen_players:
                    seen_players.add(rb_name)
                    players_by_position['RB'].append((rb_rank, rb_name, rb_tier))
        except:
            pass
        
        try:
            # WR section 1: columns 12-14 (Rank, Name, Tier)
            if len(row) > 14 and row[12] and row[13]:
                wr_rank = int(row[12])
                wr_name = row[13].strip()
                wr_tier = row[14].strip() if len(row) > 14 else ""
                if wr_name and wr_name not in seen_players:
                    seen_players.add(wr_name)
                    players_by_position['WR'].append((wr_rank, wr_name, wr_tier))
        except:
            pass
        
        try:
            # WR section 2: columns 16-18 (Rank, Name, Tier)
            if len(row) > 18 and row[16] and row[17]:
                wr_rank = int(row[16])
                wr_name = row[17].strip()
                wr_tier = row[18].strip() if len(row) > 18 else ""
                if wr_name and wr_name not in seen_players:
                    seen_players.add(wr_name)
                    players_by_position['WR'].append((wr_rank, wr_name, wr_tier))
        except:
            pass
        
        try:
            # WR section 3: columns 20-22 (Rank, Name, Tier)
            if len(row) > 22 and row[20] and row[21]:
                wr_rank = int(row[20])
                wr_name = row[21].strip()
                wr_tier = row[22].strip() if len(row) > 22 else ""
                if wr_name and wr_name not in seen_players:
                    seen_players.add(wr_name)
                    players_by_position['WR'].append((wr_rank, wr_name, wr_tier))
        except:
            pass
        
        try:
            # TE section: columns 24-26 (Rank, Name, Tier)
            if len(row) > 26 and row[24] and row[25]:
                te_rank = int(row[24])
                te_name = row[25].strip()
                te_tier = row[26].strip() if len(row) > 26 else ""
                if te_name and te_name not in seen_players:
                    seen_players.add(te_name)
                    players_by_position['TE'].append((te_rank, te_name, te_tier))
        except:
            pass
        
        try:
            # Team Defense: columns 48-50 (Rank, Name, Tier)
            if len(row) > 50 and row[48] and row[49]:
                dst_rank = int(row[48])
                dst_name = row[49].strip()
                dst_tier = row[50].strip() if len(row) > 50 else ""
                if dst_name and dst_name not in seen_players:
                    seen_players.add(dst_name)
                    players_by_position['DST'].append((dst_rank, dst_name, dst_tier))
        except:
            pass
        
        try:
            # Kicker: columns 52-54 (Rank, Name, Tier)
            if len(row) > 54 and row[52] and row[53]:
                k_rank = int(row[52])
                k_name = row[53].strip()
                k_tier = row[54].strip() if len(row) > 54 else ""
                if k_name and k_name not in seen_players:
                    seen_players.add(k_name)
                    players_by_position['K'].append((k_rank, k_name, k_tier))
        except:
            pass

# Now create the final player list with sequential position ranks
players = []

for position in ['QB', 'RB', 'WR', 'TE', 'DST', 'K']:
    # Sort by overall rank
    pos_players = sorted(players_by_position[position], key=lambda x: x[0])
    
    # Assign sequential position ranks
    for pos_rank, (overall_rank, player_name, tier) in enumerate(pos_players, 1):
        players.append({
            'RK': overall_rank,
            'PLAYER NAME': player_name,
            'TEAM': '',
            'POS': f'{position}{pos_rank}',
            'TIERS': tier
        })

# Sort all players by overall rank
players.sort(key=lambda x: x['RK'])

# Write to output CSV
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['RK', 'TIERS', 'PLAYER NAME', 'TEAM', 'POS'])
    writer.writeheader()
    writer.writerows(players)

print(f"Converted {len(players)} players")
print(f"Output written to: {output_file}")
print(f"\nPosition breakdown:")
for position in ['QB', 'RB', 'WR', 'TE', 'DST', 'K']:
    print(f"{position}: {len(players_by_position[position])}")
