<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive } from "vue";
import { Eye, EyeOff } from "lucide-vue-next";
import Papa from "papaparse";

type Ranking = {
  rank: number;
  name: string;
  pos: string;
  posRank: number;
  posRankStr: string;
  team: string;
  bye: string;
  tier: string;
  normName: string;
  sleeperId?: string;
};
type DepthEntry = { order: number; name: string; normName: string };
type Player = { name: string; team: string; pos: string };

const teams = [
  "ARI",
  "ATL",
  "BAL",
  "BUF",
  "CAR",
  "CHI",
  "CIN",
  "CLE",
  "DAL",
  "DEN",
  "DET",
  "GB",
  "HOU",
  "IND",
  "JAX",
  "KC",
  "LAC",
  "LAR",
  "LV",
  "MIA",
  "MIN",
  "NE",
  "NO",
  "NYG",
  "NYJ",
  "PHI",
  "PIT",
  "SEA",
  "SF",
  "TB",
  "TEN",
  "WAS",
];
const slots = [
  { label: "QB1", pos: "QB", order: 1 },
  { label: "RB1", pos: "RB", order: 1 },
  { label: "RB2", pos: "RB", order: 2 },
  { label: "WR1", pos: "WR", order: 1 },
  { label: "WR2", pos: "WR", order: 2 },
  { label: "WR3", pos: "WR", order: 3 },
  { label: "TE1", pos: "TE", order: 1 },
];
const tabs = ["ALL", "QB", "RB", "WR", "TE"];
const state = reactive({
  leagueId: "",
  draftId: "",
  username: "",
  posFilter: "ALL",
  search: "",
  teamSearch: "",
  hideDrafted: false,
  sortKey: "rank",
  sortDir: 1,
  selectedTeam: "",
  selectedPlayerKey: "",
  statusKind: "",
  statusText: "not connected",
  modalOpen: false,
  settingsOpen: false,
  rankings: [] as Ranking[],
  depthCharts: {} as Record<string, Record<string, DepthEntry[]>>,
  power: {} as Record<string, number>,
  defense: {} as Record<string, number>,
  players: {} as Record<string, Player>,
  drafted: new Set<string>(),
  mine: new Set<string>(),
  myUserId: null as string | null,
  myRosterId: null as number | null,
});
const csv = reactive({ rankings: "", depth: "", power: "", defense: "" });
const importStatus = reactive({
  rankings: "",
  depth: "",
  power: "",
  defense: "",
});
let pollTimer: ReturnType<typeof setInterval> | undefined;

const normName = (value: string) =>
  value
    .toLowerCase()
    .replace(/\./g, "")
    .replace(/'/g, "")
    .replace(/\s+jr\b|\s+sr\b|\s+ii\b|\s+iii\b|\s+iv\b/g, "")
    .replace(/[^a-z\s]/g, "")
    .replace(/\s+/g, " ")
    .trim();
const findCol = (headers: string[], names: string[]) =>
  names
    .map(
      (name) =>
        headers.find((header) => header.toLowerCase().trim() === name) ||
        headers.find((header) => header.toLowerCase().includes(name)),
    )
    .find(Boolean);
const parseRows = (text: string) =>
  Papa.parse<Record<string, string>>(text.trim(), {
    header: true,
    skipEmptyLines: true,
  });
const parseRankings = (text: string): Ranking[] => {
  const parsed = parseRows(text);
  const headers = parsed.meta.fields || [];
  const nameCol = findCol(headers, ["player", "name", "player name"]);
  if (!nameCol) throw new Error("could not find a Player/Name column");
  const rankCol = findCol(headers, ["rank", "rk", "overall", "ecr"]);
  const posCol = findCol(headers, ["pos", "position"]);
  const teamCol = findCol(headers, ["team", "tm"]);
  const byeCol = findCol(headers, ["bye", "bye week"]);
  const tierCol = findCol(headers, ["tier"]);
  const rows = parsed.data
    .map((row, index) => {
      const name = (row[nameCol] || "").replace(/\(.*?\)/g, "").trim();
      const position = posCol
        ? (row[posCol] || "").toUpperCase().replace("DST", "DEF").trim()
        : "";
      const positionMatch = position.match(/^([A-Z]+)(\d+)?$/);
      return {
        rank: rankCol ? Number.parseInt(row[rankCol]) || index + 1 : index + 1,
        name,
        pos: positionMatch?.[1] || position,
        posRankStr: positionMatch?.[2] || "",
        posRank: positionMatch?.[2] ? Number.parseInt(positionMatch[2]) : 0,
        team: teamCol ? (row[teamCol] || "").toUpperCase().trim() : "",
        bye: byeCol ? row[byeCol] || "" : "",
        tier: tierCol ? row[tierCol] || "" : "",
        normName: normName(name),
      };
    })
    .filter((row) => row.name);
  if (!rows.length) throw new Error("no rows parsed");
  return rows;
};
const teamAbbreviations: Record<string, string> = {
  "Arizona Cardinals": "ARI",
  "Atlanta Falcons": "ATL",
  "Baltimore Ravens": "BAL",
  "Buffalo Bills": "BUF",
  "Carolina Panthers": "CAR",
  "Chicago Bears": "CHI",
  "Cincinnati Bengals": "CIN",
  "Cleveland Browns": "CLE",
  "Dallas Cowboys": "DAL",
  "Denver Broncos": "DEN",
  "Detroit Lions": "DET",
  "Green Bay Packers": "GB",
  "Houston Texans": "HOU",
  "Indianapolis Colts": "IND",
  "Jacksonville Jaguars": "JAX",
  "Kansas City Chiefs": "KC",
  "Las Vegas Raiders": "LV",
  "Los Angeles Chargers": "LAC",
  "Los Angeles Rams": "LAR",
  "Miami Dolphins": "MIA",
  "Minnesota Vikings": "MIN",
  "New England Patriots": "NE",
  "New Orleans Saints": "NO",
  "New York Giants": "NYG",
  "New York Jets": "NYJ",
  "Philadelphia Eagles": "PHI",
  "Pittsburgh Steelers": "PIT",
  "Seattle Seahawks": "SEA",
  "San Francisco 49ers": "SF",
  "Tampa Bay Buccaneers": "TB",
  "Tennessee Titans": "TEN",
  "Washington Commanders": "WAS",
};
const parseDepth = (text: string) => {
  const rows = Papa.parse<string[]>(text.trim(), {
    skipEmptyLines: false,
  }).data;
  const chart: Record<string, Record<string, DepthEntry[]>> = {};
  let team = "";
  let positions: string[] = [];
  rows.forEach((row) => {
    if (row.length === 1 && row[0].trim()) {
      team = teamAbbreviations[row[0].trim()] || row[0].trim().toUpperCase();
      chart[team] ||= {};
      positions = [];
      return;
    }
    if (row[0]?.trim() === "ECR" && row.length >= 8) {
      positions = [row[1], row[3], row[5], row[7]].map((position) =>
        position
          .replace(/\s+/g, "")
          .replace(/s$/, "")
          .toUpperCase()
          .replace("QUARTERBACK", "QB")
          .replace("RUNNINGBACK", "RB")
          .replace("WIDERECEIVER", "WR")
          .replace("TIGHTEND", "TE"),
      );
      return;
    }
    if (!team || positions.length !== 4) return;
    positions.forEach((position, index) => {
      const name = (row[index * 2 + 1] || "").trim();
      if (!name) return;
      (chart[team][position] ||= []).push({
        order: chart[team][position].length + 1,
        name,
        normName: normName(name),
      });
    });
  });
  if (!Object.keys(chart).length)
    throw new Error("no FantasyPros team sections found");
  return chart;
};
const parseTeamRanks = (text: string) => {
  const parsed = parseRows(text);
  const headers = parsed.meta.fields || [];
  const rankCol = findCol(headers, ["rank", "rk"]);
  const teamCol = findCol(headers, ["team", "tm"]);
  if (!rankCol || !teamCol) throw new Error("need Rank and Team columns");
  const result: Record<string, number> = {};
  parsed.data.forEach((row) => {
    const team = (row[teamCol] || "").toUpperCase().trim();
    const rank = Number.parseInt(row[rankCol]);
    if (team && rank) result[team] = rank;
  });
  if (!Object.keys(result).length) throw new Error("no rows parsed");
  return result;
};

const sample = {
  rankings: `Rank,Player,Pos,Team,Bye,Tier\n1,Ja'Marr Chase,WR,CIN,10,1\n2,Bijan Robinson,RB,ATL,5,1\n3,CeeDee Lamb,WR,DAL,10,1\n4,Saquon Barkley,RB,PHI,9,1\n5,Justin Jefferson,WR,MIN,6,1\n6,Jahmyr Gibbs,RB,DET,8,2\n7,Amon-Ra St. Brown,WR,DET,8,2\n8,Puka Nacua,WR,LAR,8,2\n9,Patrick Mahomes,QB,KC,10,2\n10,Christian McCaffrey,RB,SF,14,2\n11,Brian Thomas Jr.,WR,JAX,8,3\n12,Malik Nabers,WR,NYG,14,3\n13,Travis Kelce,TE,KC,10,3\n14,De'Von Achane,RB,MIA,12,3\n15,Josh Allen,QB,BUF,7,3\n16,Tee Higgins,WR,CIN,10,4\n17,Chase Brown,RB,CIN,10,4\n18,Tyler Allgeier,RB,ATL,5,5\n19,David Montgomery,RB,DET,8,4\n20,Zack Moss,RB,CIN,10,6`,
  depth: `Team,Position,Order,Player\nCIN,WR,1,Ja'Marr Chase\nCIN,WR,2,Tee Higgins\nCIN,RB,1,Chase Brown\nCIN,RB,2,Zack Moss\nCIN,QB,1,Joe Burrow\nCIN,TE,1,Mike Gesicki\nATL,RB,1,Bijan Robinson\nATL,RB,2,Tyler Allgeier\nATL,QB,1,Kirk Cousins\nATL,WR,1,Drake London\nATL,WR,2,Darnell Mooney\nATL,TE,1,Kyle Pitts\nDET,RB,1,Jahmyr Gibbs\nDET,RB,2,David Montgomery\nDET,QB,1,Jared Goff\nDET,WR,1,Amon-Ra St. Brown\nDET,WR,2,Jameson Williams\nDET,TE,1,Sam LaPorta\nKC,QB,1,Patrick Mahomes\nKC,TE,1,Travis Kelce\nKC,RB,1,Isiah Pacheco\nKC,WR,1,Rashee Rice`,
  power: `Rank,Team\n1,KC\n2,SF\n3,DET\n4,BAL\n5,PHI\n6,CIN\n7,DAL\n8,MIA\n9,ATL\n10,MIN`,
  defense: `Rank,Team\n1,BAL\n2,PIT\n3,SF\n4,CLE\n5,KC\n6,DAL\n7,MIA\n8,NYJ\n9,DET\n10,CIN`,
};
const rankIndex = computed(() =>
  Object.fromEntries(state.rankings.map((row) => [row.normName, row])),
);
const positionalMaxRanks = computed(() => {
  const maxByPos: Record<string, number> = { QB: 24, RB: 50, WR: 60, TE: 20 };
  // state.rankings.forEach((row) => {
  //   if (!row.pos || !row.posRank) return;
  //   maxByPos[row.pos] = Math.max(maxByPos[row.pos] || 0, row.posRank);
  // });
  return maxByPos;
});
const positionalColors: Record<string, number[]> = {
  QB: [224, 122, 95],
  RB: [129, 178, 154],
  WR: [242, 204, 143],
  TE: [156, 158, 222],
};
const standardPosMax = (pos: string) =>
  Math.max(1, positionalMaxRanks.value[pos] || 50);
const rankColor = (rank: number, pos = "") => {
  const maxRank = standardPosMax(pos);
  const ratio =
    maxRank <= 1
      ? 0
      : Math.min(1, Math.max(0, (rank - 1) / (maxRank - 1)));
  const start = positionalColors[pos] || [96, 180, 255];
  const end = [12, 22, 34];
  const r = Math.round(start[0] + (end[0] - start[0]) * ratio);
  const g = Math.round(start[1] + (end[1] - start[1]) * ratio);
  const b = Math.round(start[2] + (end[2] - start[2]) * ratio);
  return `rgb(${r}, ${g}, ${b})`;
};
const nameIndex = computed(() =>
  Object.fromEntries(
    Object.entries(state.players).map(([id, player]) => [
      normName(player.name),
      id,
    ]),
  ),
);
const activeSlots = computed(() =>
  slots,
);
const visibleTeams = computed(() =>
  teams.filter((team) => {
    const query = state.teamSearch.toLowerCase();
    if (!query) return true;
    return (
      team.toLowerCase().includes(query) ||
      Object.values(state.depthCharts[team] || {}).some((list) =>
        list.some((entry) => entry.name.toLowerCase().includes(query)),
      )
    );
  }),
);
const visibleRankings = computed(() =>
  state.rankings
    .filter(
      (row) =>
        (state.posFilter === "ALL" || row.pos === state.posFilter) &&
        (!state.search ||
          row.name.toLowerCase().includes(state.search.toLowerCase())),
    )
    .filter(
      (row) =>
        !state.hideDrafted ||
        statusFor(row.sleeperId || nameIndex.value[row.normName]) !== "gone" ||
        selectedKey(
          row.sleeperId || nameIndex.value[row.normName],
          row.normName,
        ) === state.selectedPlayerKey,
    )
    .sort((a, b) => {
      const av =
        state.sortKey === "rank"
          ? a.rank
          : String(a[state.sortKey as keyof Ranking] || "").toLowerCase();
      const bv =
        state.sortKey === "rank"
          ? b.rank
          : String(b[state.sortKey as keyof Ranking] || "").toLowerCase();
      return (av < bv ? -1 : av > bv ? 1 : 0) * state.sortDir;
    }),
);
const statusFor = (id?: string) =>
  id && state.mine.has(id)
    ? "mine"
    : id && state.drafted.has(id)
      ? "gone"
      : "avail";
const selectedKey = (id: string | undefined, name: string) => id || `n:${name}`;
const isTeamSelected = (team: string) => state.selectedTeam === team;
const selectTeam = (team: string) => {
  state.selectedTeam = state.selectedTeam === team ? "" : team;
};
const togglePlayerSelection = (id: string | undefined, name: string) => {
  const key = selectedKey(id, name);
  if (state.selectedPlayerKey === key) {
    state.selectedPlayerKey = "";
    return;
  }
  choosePlayer(id, name);
};
const isPositionStart = (index: number) => index === 0 || slots[index].pos !== slots[index - 1].pos;
const hasTierBreak = (index: number) => index > 0 && visibleRankings.value[index].tier !== visibleRankings.value[index - 1].tier;
const entryFor = (team: string, slot: { pos: string; order: number }) =>
  state.depthCharts[team]?.[slot.pos]?.find(
    (entry) => entry.order === slot.order,
  );
const setStatus = (kind: string, text: string) => {
  state.statusKind = kind;
  state.statusText = text;
};
const save = (key: string, value: unknown) =>
  localStorage.setItem(`draft-wizard-${key}`, JSON.stringify(value));
const load = <T,>(key: string, fallback: T) => {
  try {
    return (
      JSON.parse(localStorage.getItem(`draft-wizard-${key}`) || "null") ??
      fallback
    );
  } catch {
    return fallback;
  }
};
const handleSave = (type: keyof typeof csv) => {
  try {
    if (!csv[type].trim()) throw new Error("paste or upload CSV first");
    if (type === "rankings") state.rankings = parseRankings(csv[type]);
    if (type === "depth") state.depthCharts = parseDepth(csv[type]);
    if (type === "power") state.power = parseTeamRanks(csv[type]);
    if (type === "defense") state.defense = parseTeamRanks(csv[type]);
    save(`${type}-csv`, csv[type]);
    importStatus[type] = `saved`;
  } catch (error) {
    importStatus[type] =
      error instanceof Error ? error.message : "could not parse CSV";
  }
};
const loadSample = () => {
  Object.assign(csv, sample);
  (Object.keys(csv) as (keyof typeof csv)[]).forEach(handleSave);
};
const choosePlayer = (id: string | undefined, name: string) => {
  state.selectedPlayerKey = selectedKey(id, name);
  state.selectedTeam = "";
};
const resetDrafted = () => {
  state.drafted = new Set();
  state.mine = new Set();
  setStatus("", "drafted list reset");
};
const sortBy = (key: string) => {
  state.sortDir = state.sortKey === key ? state.sortDir * -1 : 1;
  state.sortKey = key;
};
const connect = async () => {
  save("settings", {
    leagueId: state.leagueId || "1386222812854767616",
    draftId: state.draftId || "1386222812875730944",
    username: state.username || "TopOfTheTreeT",
  });
  if (!state.leagueId && !state.draftId)
    return setStatus("", "enter a league or draft id");

  try {
    setStatus("", "connecting...");
    await fetchPlayers();
    await pollDraft();
    // pollTimer = setInterval(pollDraft, 5000);
  } catch (error) {
    setStatus("err", error instanceof Error ? error.message : "sync error");
  }
};
const fetchPlayers = async () => {
  const cached = load<{
    fetchedAt: number;
    players: Record<string, Player>;
  } | null>("players-cache", null);
  if (cached && Date.now() - cached.fetchedAt < 43200000)
    return Object.assign(state.players, cached.players);
  setStatus("", "downloading player list...");
  const response = await fetch("https://api.sleeper.app/v1/players/nfl");
  if (!response.ok) throw new Error("sleeper players fetch failed");
  const data = await response.json();
  const players: Record<string, Player> = {};
  Object.entries(data).forEach(([id, raw]) => {
    const player = raw as {
      position?: string;
      full_name?: string;
      first_name?: string;
      last_name?: string;
      team?: string;
    };
    if (["QB", "RB", "WR", "TE", "K", "DEF"].includes(player.position || ""))
      players[id] = {
        name:
          player.full_name ||
          `${player.first_name || ""} ${player.last_name || ""}`.trim() ||
          id,
        team: player.team || "FA",
        pos: player.position || "",
      };
  });
  Object.assign(state.players, players);
  save("players-cache", { fetchedAt: Date.now(), players });
};
const pollDraft = async () => {
  const draftId =
    state.draftId ||
    (state.leagueId
      ? (
          await (
            await fetch(
              `https://api.sleeper.app/v1/league/${state.leagueId}/drafts`,
            )
          ).json()
        )[0]?.draft_id
      : null);
  if (!draftId) return setStatus("", "enter a league or draft id");
  await resolveMyIdentity(draftId);
  const response = await fetch(
    `https://api.sleeper.app/v1/draft/${draftId}/picks`,
  );
  if (!response.ok) throw new Error("pick fetch failed");
  const picks = await response.json();
  state.drafted = new Set();
  state.mine = new Set();
  picks.forEach((pick: { player_id?: string; picked_by?: string; roster_id?: number }) => {
    if (!pick.player_id) return;
    const playerId = String(pick.player_id);
    state.drafted.add(playerId);
    if ((state.myUserId && pick.picked_by === state.myUserId) || (state.myRosterId && pick.roster_id === state.myRosterId)) state.mine.add(playerId);
  });
  setStatus(
    "live",
    `synced · ${picks.length} picks made · ${new Date().toLocaleTimeString()}`,
  );
};
const resolveMyIdentity = async (draftId: string) => {
  state.myUserId = null;
  state.myRosterId = null;
  if (!state.username) return;
  try {
    const userResponse = await fetch(`https://api.sleeper.app/v1/user/${encodeURIComponent(state.username)}`);
    if (!userResponse.ok) return;
    const user = await userResponse.json();
    state.myUserId = user.user_id;
    let leagueId = state.leagueId;
    if (!leagueId) {
      const draftResponse = await fetch(`https://api.sleeper.app/v1/draft/${draftId}`);
      if (draftResponse.ok) leagueId = (await draftResponse.json()).league_id;
    }
    if (!leagueId) return;
    const rosterResponse = await fetch(`https://api.sleeper.app/v1/league/${leagueId}/rosters`);
    if (rosterResponse.ok) {
      const roster = (await rosterResponse.json()).find((entry: { owner_id?: string; roster_id?: number }) => entry.owner_id === state.myUserId);
      state.myRosterId = roster?.roster_id || null;
    }
  } catch {
    state.myUserId = null;
    state.myRosterId = null;
  }
};
const fileLoaded = async (event: Event, type: keyof typeof csv) => {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (file) csv[type] = await file.text();
};
onMounted(() => {
  const settings = load("settings", {
    leagueId: "",
    draftId: "",
    username: "",
  });
  Object.assign(state, settings);
  (["rankings", "depth", "power", "defense"] as const).forEach((type) => {
    csv[type] = load(`${type}-csv`, "") as string;
    if (csv[type]) handleSave(type);
  });
  if (state.leagueId || state.draftId) connect();
});
onBeforeUnmount(() => {
  if (pollTimer) clearInterval(pollTimer);
});
</script>

<template>
  <div class="app-shell">
      <header>
        <div class="topbar">
          <div class="brand">
            <strong>DRAFT<span>WIZARD</span></strong>
          </div>
          <div class="sync-field">
            <i class="status-dot" :class="state.statusKind"></i
            ><span class="status-text">{{ state.statusText }}</span>
          </div>
          
          <div class="settings-actions">
            <button class="btn ghost" @click="resetDrafted">Reset</button>
            <button class="btn" @click="connect">Connect</button>
          </div>
            <button
              class="settings-button"
              aria-label="Open settings"
              title="Open settings"
              @click="state.settingsOpen = true"
            >
              ⚙
            </button>
          </div>
      </header>
    <main class="layout">
      <section class="main-col">
        <div class="grid-scroll">
          <table class="depth-table">
            <thead>
              <tr>
                <th class="team-h">TEAM</th>
                <th
                  v-for="slot in activeSlots"
                  :key="slot.label"
                  :class="{ inactive: state.posFilter !== 'ALL' && slot.pos !== state.posFilter, 'position-start': isPositionStart(activeSlots.indexOf(slot)) }"
                >
                  {{ slot.label }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!Object.keys(state.depthCharts).length">
                <td :colspan="activeSlots.length + 1">
                  <div class="empty-hint">
                    No depth chart data imported yet. Click
                    <strong>Import Data</strong> or load sample data.
                  </div>
                </td>
              </tr>
              <tr
                v-else
                v-for="team in visibleTeams"
                :key="team"
                :class="{
                  'team-row-selected': isTeamSelected(team),
                  'team-row-dimmed': !!state.selectedTeam && !isTeamSelected(team),
                }"
              >
                <td
                  class="team-cell"
                  :class="{ 'team-cell-selected': isTeamSelected(team) }"
                  @click="selectTeam(team)"
                >
                  {{ team }}
                </td>
                <td
                  v-for="slot in activeSlots"
                  :key="slot.label"
                  :class="{ inactive: state.posFilter !== 'ALL' && slot.pos !== state.posFilter, 'position-start': isPositionStart(activeSlots.indexOf(slot)) }"
                >
                  <span
                    v-if="entryFor(team, slot)"
                    class="slot-player"
                    :class="
                      [
                        statusFor(nameIndex[entryFor(team, slot)?.normName || '']),
                        {
                          selected: state.selectedPlayerKey === selectedKey(nameIndex[entryFor(team, slot)?.normName || ''], entryFor(team, slot)?.normName || ''),
                          'team-selected-card': !!state.selectedTeam && team === state.selectedTeam,
                          'team-dimmed-card': !!state.selectedTeam && team !== state.selectedTeam,
                        },
                      ]
                    "
                    @click="
                      togglePlayerSelection(
                        nameIndex[entryFor(team, slot)?.normName || ''],
                        entryFor(team, slot)?.normName || '',
                      )
                    "
                    ><span class="player-name">{{ entryFor(team, slot)?.name }}</span>
                    <b
                      v-if="rankIndex[entryFor(team, slot)?.normName || '']"
                      class="rank-badge"
                      :class="{
                        drafted: statusFor(nameIndex[entryFor(team, slot)?.normName || '']) === 'gone',
                      }"
                      :style="{
                        backgroundColor:
                          statusFor(nameIndex[entryFor(team, slot)?.normName || '']) === 'gone'
                            ? 'transparent'
                            : rankColor(
                                rankIndex[entryFor(team, slot)?.normName || ''].posRank,
                                rankIndex[entryFor(team, slot)?.normName || ''].pos,
                              ),
                      }"
                    >{{ rankIndex[entryFor(team, slot)?.normName || ''].posRankStr }}</b></span
                  ><span v-else class="slot-empty">–</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
      <aside class="side-col">
        <!-- <div class="side-badges">
          <div class="badge">
            <strong>{{ teamRanks.power || "–" }}</strong
            ><small>POWER</small><em>{{ state.selectedTeam || " " }}</em>
          </div>
          <div class="badge">
            <strong>{{ teamRanks.defense || "–" }}</strong
            ><small>DEFENSE</small><em>{{ state.selectedTeam || " " }}</em>
          </div>
        </div> -->
        <div class="side-filterbar">
          <div class="postabs">
            <button
              v-for="tab in tabs"
              :key="tab"
              class="postab"
              :class="{ active: state.posFilter === tab }"
              @click="state.posFilter = tab"
            >
              {{ tab }}
            </button>
            <input
              v-model="state.search"
              class="searchbox"
              placeholder="Search players..."
            />
            <button
              class="hide-drafted"
              :class="{ active: state.hideDrafted }"
              @click="state.hideDrafted = !state.hideDrafted"
              >"state.hideDrafted" ? <EyeOff/> : <Eye /></button>
          </div>
        </div>
        <div class="side-list-scroll">
          <table class="rank-table">
            <thead>
              <tr>
                <th
                  :class="{ sorted: state.sortKey === 'rank' }"
                  @click="sortBy('rank')"
                >
                  RK
                </th>
                <th
                  :class="{ sorted: state.sortKey === 'name' }"
                  @click="sortBy('name')"
                >
                  PLAYER
                </th>
                <th
                  :class="{ sorted: state.sortKey === 'pos' }"
                  @click="sortBy('pos')"
                >
                  POS
                </th>
                <th>BYE</th>
                <th>TEAM</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in visibleRankings"
                :key="row.normName"
                :class="{
                  'tier-break': hasTierBreak(visibleRankings.indexOf(row)),
                  'selected-row':
                    state.selectedPlayerKey ===
                    selectedKey(row.sleeperId || nameIndex[row.normName], row.normName),
                  'team-selected-row': !!state.selectedTeam && row.team === state.selectedTeam,
                  'mine-row':
                    statusFor(row.sleeperId || nameIndex[row.normName]) === 'mine',
                  'drafted-row':
                    statusFor(row.sleeperId || nameIndex[row.normName]) === 'gone',
                }"
                @click="
                  togglePlayerSelection(
                    row.sleeperId || nameIndex[row.normName],
                    row.normName,
                  )
                "
              >
                <td class="rank">{{ row.rank }}</td>
                <td class="name-cell">{{ row.name }}</td>
                <td>
                  <span class="pos-chip" :class="`pos-${row.pos}`">{{
                    row.pos + row.posRankStr
                  }}</span>
                </td>
                <td class="meta-cell">{{ row.bye || "–" }}</td>
                <td class="meta-cell">{{ row.team || "–" }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </aside>
    </main>
    <div
      v-if="state.settingsOpen"
      class="modal-backdrop"
      @click.self="state.settingsOpen = false"
    >
      <section class="modal settings-modal">
        <button class="close-x" @click="state.settingsOpen = false">×</button>
        <h2>Settings</h2>
        <div class="settings-form">
          <label class="settings-field"
            >League ID<input
              v-model="state.leagueId"
              placeholder="e.g. 987654321012345678" /></label
          ><label class="settings-field"
            >Draft ID (optional)<input
              v-model="state.draftId"
              placeholder="auto-detected" /></label
          ><label class="settings-field"
            >Your username<input
              v-model="state.username"
              class="username"
              placeholder="sleeper username" /></label
          >
        </div>
        <div class="settings-actions">
          <button class="btn ghost" @click="resetDrafted">Reset</button>
          <button class="btn" @click="connect">Connect</button>
        </div>

        <div class="import-divider">
          <h3>Import Data</h3>
          <p class="modal-sub">
            FantasyPros CSV exports are supported directly. Upload or paste your
            rankings and depth-chart exports below.
          </p>
        </div>
        <div
          v-for="type in ['rankings', 'depth', 'power', 'defense'] as const"
          :key="type"
          class="import-block"
        >
          <h3>
            {{
              type === "rankings"
                ? "PLAYER RANKINGS"
                : type === "depth"
                  ? "TEAM DEPTH CHARTS"
                  : type === "power"
                    ? "TEAM POWER RANKINGS"
                    : "DEFENSIVE RANKINGS"
            }}
          </h3>
          <p v-if="type === 'rankings'">
            FantasyPros rankings: RK, TIERS, PLAYER NAME, TEAM, POS, BYE WEEK.
          </p>
          <p v-else-if="type === 'depth'">
            FantasyPros depth charts use one team section with ECR/player
            columns for Quarterbacks, Running Backs, Wide Receivers, and Tight
            Ends.
          </p>
          <p v-else>Columns: Rank, Team.</p>
          <div class="import-row">
            <textarea
              v-model="csv[type]"
              class="csv-input"
              :placeholder="`Paste ${type} CSV here...`"
            ></textarea>
            <div class="import-actions">
              <label class="file-label"
                >Upload<input
                  type="file"
                  accept=".csv"
                  hidden
                  @change="fileLoaded($event, type)" /></label
              ><button class="btn ghost" @click="handleSave(type)">Save</button>
            </div>
          </div>
          <div
            class="import-status"
            :class="{
              ok: importStatus[type] === 'saved',
              bad: importStatus[type] && importStatus[type] !== 'saved',
            }"
          >
            {{ importStatus[type] }}
          </div>
        </div>
        <footer class="modal-footer">
          <button class="btn ghost" @click="loadSample">Load sample data</button
          ><button class="btn" @click="state.settingsOpen = false">Done</button>
        </footer>
      </section>
    </div>
  </div>
</template>
