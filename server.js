/**
 * 三车间音乐节 - 群友社交破冰站 后端 (Node.js)
 * Express + JSON 文件存储
 */
const express = require("express");
const fs = require("fs");
const path = require("path");

const app = express();
app.use(express.json());

// 静态文件
app.use(express.static(path.join(__dirname, "static")));

// CORS
app.use((req, res, next) => {
  res.header("Access-Control-Allow-Origin", "*");
  res.header("Access-Control-Allow-Headers", "Content-Type");
  res.header("Access-Control-Allow-Methods", "GET,POST,DELETE,OPTIONS");
  if (req.method === "OPTIONS") return res.sendStatus(200);
  next();
});

// ==================== 存储 ====================
const DATA_DIR = path.join(__dirname, "data");
if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });

const FILES = {
  profiles: path.join(DATA_DIR, "profiles.json"),
  tribes: path.join(DATA_DIR, "tribes.json"),
  hangouts: path.join(DATA_DIR, "hangouts.json"),
  songs: path.join(DATA_DIR, "songs.json")
};

function readJson(file, def) {
  if (def === undefined) def = [];
  try {
    if (!fs.existsSync(file)) return def;
    return JSON.parse(fs.readFileSync(file, "utf-8"));
  } catch (e) {
    return def;
  }
}

function writeJson(file, data) {
  fs.writeFileSync(file, JSON.stringify(data, null, 2), "utf-8");
}

function nowTs() {
  const d = new Date();
  const p = n => String(n).padStart(2, "0");
  return (d.getMonth() + 1) + "-" + p(d.getDate()) + " " + p(d.getHours()) + ":" + p(d.getMinutes());
}

function nowId() {
  return Date.now();
}

const ALL_BANDS = {
  day1: ["崔健", "二手玫瑰", "万能青年旅店", "痛仰", "梅卡德尔", "黑豹乐队", "九宝", "椿乐队", "石岩", "虎啸春"],
  day2: ["罗大佑", "老狼", "逃跑计划", "棱镜", "夏日入侵企画", "叶世荣", "康姆士", "刘忻&遗忘俱乐部", "岛屿心情", "丑橘出逃"]
};

// ==================== 健康检查 ====================
app.get("/api/health", (req, res) => {
  res.json({ ok: true, time: nowTs() });
});

// ==================== 群友名片墙 ====================
app.get("/api/profiles", (req, res) => {
  let profiles = readJson(FILES.profiles);
  profiles.sort((a, b) => b.id - a.id);
  res.json(profiles);
});

app.post("/api/profiles", (req, res) => {
  const d = req.body || {};
  const name = (d.name || "").trim();
  const city = (d.city || "").trim();
  const bio = (d.bio || "").trim();
  const bands = d.bands || [];
  const vibe = d.vibe || "";
  const looking = (d.looking || "").trim();
  const contact = (d.contact || "").trim();

  if (!name) return res.status(400).json({ error: "至少写个名字吧" });
  if (bio.length > 60) return res.status(400).json({ error: "一句话介绍别超过60字" });

  const profiles = readJson(FILES.profiles);
  const profile = { id: nowId(), name, city, bio, bands, vibe, looking, contact, time: nowTs() };
  profiles.push(profile);
  writeJson(FILES.profiles, profiles);
  res.status(201).json(profile);
});

app.delete("/api/profiles/:id", (req, res) => {
  const id = parseInt(req.params.id);
  let profiles = readJson(FILES.profiles);
  profiles = profiles.filter(p => p.id !== id);
  writeJson(FILES.profiles, profiles);
  res.json({ ok: true });
});

// ==================== 乐队阵营 ====================
app.get("/api/tribes", (req, res) => {
  const tribes = readJson(FILES.tribes);
  const result = {};
  for (const [dayKey, bands] of Object.entries(ALL_BANDS)) {
    for (const band of bands) {
      const members = tribes.filter(t => t.band === band).map(t => t.name);
      result[band] = { day: dayKey, members, count: members.length };
    }
  }
  res.json(result);
});

app.post("/api/tribes/join", (req, res) => {
  const d = req.body || {};
  const name = (d.name || "").trim();
  const band = (d.band || "").trim();

  if (!name || !band) return res.status(400).json({ error: "名字和乐队不能为空" });

  const allNames = [...ALL_BANDS.day1, ...ALL_BANDS.day2];
  if (!allNames.includes(band)) return res.status(400).json({ error: "这个乐队不在阵容里" });

  const tribes = readJson(FILES.tribes);
  for (const t of tribes) {
    if (t.name.trim() === name && t.band.trim() === band) {
      return res.status(409).json({ error: "你已经在这个阵营里了" });
    }
  }

  const entry = { id: nowId(), name, band, time: nowTs() };
  tribes.push(entry);
  writeJson(FILES.tribes, tribes);
  res.status(201).json(entry);
});

app.post("/api/tribes/leave", (req, res) => {
  const d = req.body || {};
  const name = (d.name || "").trim();
  const band = (d.band || "").trim();

  let tribes = readJson(FILES.tribes);
  tribes = tribes.filter(t => !(t.name.trim() === name && t.band.trim() === band));
  writeJson(FILES.tribes, tribes);
  res.json({ ok: true });
});

// ==================== 约酒组局 ====================
app.get("/api/hangouts", (req, res) => {
  let hangouts = readJson(FILES.hangouts);
  hangouts.sort((a, b) => b.id - a.id);
  res.json(hangouts);
});

app.post("/api/hangouts", (req, res) => {
  const d = req.body || {};
  const name = (d.name || "").trim();
  const type = d.type || "约酒";
  const detail = (d.detail || "").trim();
  const when = (d.when || "").trim();
  const contact = (d.contact || "").trim();

  if (!name || !detail) return res.status(400).json({ error: "信息不完整" });

  const hangouts = readJson(FILES.hangouts);
  const h = { id: nowId(), name, type, detail, when, contact, time: nowTs() };
  hangouts.unshift(h);
  if (hangouts.length > 100) hangouts.length = 100;
  writeJson(FILES.hangouts, hangouts);
  res.status(201).json(h);
});

// ==================== 歌单许愿池 ====================
app.get("/api/songs", (req, res) => {
  let songs = readJson(FILES.songs);
  songs.sort((a, b) => b.votes - a.votes);
  res.json(songs);
});

app.post("/api/songs", (req, res) => {
  const d = req.body || {};
  const name = (d.name || "").trim();
  const title = (d.title || "").trim();
  const artist = (d.artist || "").trim();

  if (!title || !name) return res.status(400).json({ error: "歌名和昵称不能为空" });

  const songs = readJson(FILES.songs);
  for (const s of songs) {
    if (s.title.trim() === title) return res.status(409).json({ error: "已经在池子里了" });
  }

  const song = { id: nowId(), title, artist, by: name, votes: 0, voters: [], time: nowTs() };
  songs.push(song);
  writeJson(FILES.songs, songs);
  res.status(201).json(song);
});

app.post("/api/songs/:id/vote", (req, res) => {
  const id = parseInt(req.params.id);
  const voter = ((req.body || {}).voter || "").trim();
  if (!voter) return res.status(400).json({ error: "需要一个名字" });

  const songs = readJson(FILES.songs);
  for (const s of songs) {
    if (s.id === id) {
      if (!s.voters) s.voters = [];
      if (s.voters.includes(voter)) return res.status(409).json({ error: "投过了" });
      s.votes = (s.votes || 0) + 1;
      s.voters.push(voter);
      writeJson(FILES.songs, songs);
      return res.json(s);
    }
  }
  res.status(404).json({ error: "没找到" });
});

// ==================== 首页 ====================
app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "static", "index.html"));
});

// ==================== 启动 ====================
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log("三车间音乐节破冰站 running on port " + PORT);
});
