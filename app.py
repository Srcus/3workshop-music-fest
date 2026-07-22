"""
三车间音乐节 - 群友社交破冰站 后端
Python Flask + JSON 文件存储
"""
import json
import os
import time
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="static", static_url_path="")

# WSGI 兼容：PythonAnywhere 需要 application 变量
application = app

# 确保 data 目录存在（WSGI 模式下 __main__ 不执行）
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# CORS - 允许前端跨域访问
@app.after_request
def add_cors_headers(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET,POST,DELETE,OPTIONS"
    return resp


@app.route("/api/health")
def health():
    return {"ok": True, "time": now_ts()}

PROFILES_FILE = os.path.join(DATA_DIR, "profiles.json")
TRIBES_FILE = os.path.join(DATA_DIR, "tribes.json")
HANGOUTS_FILE = os.path.join(DATA_DIR, "hangouts.json")
SONGS_FILE = os.path.join(DATA_DIR, "songs.json")


def read_json(filepath, default=None):
    if default is None:
        default = []
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return default


def write_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def now_ts():
    return datetime.now().strftime("%m-%d %H:%M")


# ==================== 群友名片墙 ====================

@app.route("/api/profiles", methods=["GET"])
def get_profiles():
    profiles = read_json(PROFILES_FILE)
    profiles.sort(key=lambda p: p["id"], reverse=True)
    return jsonify(profiles)


@app.route("/api/profiles", methods=["POST"])
def create_profile():
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    city = (data.get("city") or "").strip()
    bio = (data.get("bio") or "").strip()
    bands = data.get("bands") or []
    vibe = data.get("vibe") or ""
    looking = (data.get("looking") or "").strip()
    contact = (data.get("contact") or "").strip()

    if not name:
        return jsonify({"error": "至少写个名字吧"}), 400
    if len(bio) > 60:
        return jsonify({"error": "一句话介绍别超过60字"}), 400

    profiles = read_json(PROFILES_FILE)
    profile = {
        "id": int(time.time() * 1000),
        "name": name,
        "city": city,
        "bio": bio,
        "bands": bands,
        "vibe": vibe,
        "looking": looking,
        "contact": contact,
        "time": now_ts()
    }
    profiles.append(profile)
    write_json(PROFILES_FILE, profiles)
    return jsonify(profile), 201


@app.route("/api/profiles/<int:profile_id>", methods=["DELETE"])
def delete_profile(profile_id):
    profiles = read_json(PROFILES_FILE)
    profiles = [p for p in profiles if p["id"] != profile_id]
    write_json(PROFILES_FILE, profiles)
    return jsonify({"ok": True})


# ==================== 乐队阵营 ====================

# 所有乐队列表
ALL_BANDS = {
    "day1": ["崔健", "二手玫瑰", "万能青年旅店", "痛仰", "梅卡德尔",
             "黑豹乐队", "九宝", "椿乐队", "石岩", "虎啸春"],
    "day2": ["罗大佑", "老狼", "逃跑计划", "棱镜", "夏日入侵企画",
             "叶世荣", "康姆士", "刘忻&遗忘俱乐部", "岛屿心情", "丑橘出逃"]
}


@app.route("/api/tribes", methods=["GET"])
def get_tribes():
    tribes = read_json(TRIBES_FILE)
    # 计算每个阵营的人数
    result = {}
    for day_key, bands in ALL_BANDS.items():
        for band in bands:
            members = [t["name"] for t in tribes if t["band"] == band]
            result[band] = {"day": day_key, "members": members, "count": len(members)}
    return jsonify(result)


@app.route("/api/tribes/join", methods=["POST"])
def join_tribe():
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    band = (data.get("band") or "").strip()

    if not name or not band:
        return jsonify({"error": "名字和乐队不能为空"}), 400

    # 验证乐队名
    all_names = []
    for bands in ALL_BANDS.values():
        all_names.extend(bands)
    if band not in all_names:
        return jsonify({"error": "这个乐队不在阵容里"}), 400

    tribes = read_json(TRIBES_FILE)
    # 同一人名同一乐队不能重复加入
    for t in tribes:
        if t["name"].strip() == name and t["band"].strip() == band:
            return jsonify({"error": "你已经在这个阵营里了"}), 409

    entry = {"id": int(time.time() * 1000), "name": name, "band": band, "time": now_ts()}
    tribes.append(entry)
    write_json(TRIBES_FILE, tribes)
    return jsonify(entry), 201


@app.route("/api/tribes/leave", methods=["POST"])
def leave_tribe():
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    band = (data.get("band") or "").strip()

    tribes = read_json(TRIBES_FILE)
    tribes = [t for t in tribes if not (t["name"].strip() == name and t["band"].strip() == band)]
    write_json(TRIBES_FILE, tribes)
    return jsonify({"ok": True})


# ==================== 约酒组局 ====================

HANGOUT_TYPES = ["约酒", "约饭", "约前排蹦迪", "约拍照", "约拼车", "其他"]


@app.route("/api/hangouts", methods=["GET"])
def get_hangouts():
    hangouts = read_json(HANGOUTS_FILE)
    hangouts.sort(key=lambda h: h["id"], reverse=True)
    return jsonify(hangouts)


@app.route("/api/hangouts", methods=["POST"])
def create_hangout():
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    htype = data.get("type", "约酒")
    detail = (data.get("detail") or "").strip()
    when_where = (data.get("when") or "").strip()
    contact = (data.get("contact") or "").strip()

    if not name or not detail:
        return jsonify({"error": "信息不完整"}), 400

    hangouts = read_json(HANGOUTS_FILE)
    h = {
        "id": int(time.time() * 1000),
        "name": name,
        "type": htype,
        "detail": detail,
        "when": when_where,
        "contact": contact,
        "time": now_ts()
    }
    hangouts.insert(0, h)
    if len(hangouts) > 100:
        hangouts = hangouts[:100]
    write_json(HANGOUTS_FILE, hangouts)
    return jsonify(h), 201


# ==================== 歌单许愿池（保留） ====================

@app.route("/api/songs", methods=["GET"])
def get_songs():
    songs = read_json(SONGS_FILE)
    songs.sort(key=lambda s: s["votes"], reverse=True)
    return jsonify(songs)


@app.route("/api/songs", methods=["POST"])
def post_song():
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    title = (data.get("title") or "").strip()
    artist = (data.get("artist") or "").strip()
    if not title or not name:
        return jsonify({"error": "歌名和昵称不能为空"}), 400
    songs = read_json(SONGS_FILE)
    for s in songs:
        if s["title"].strip() == title:
            return jsonify({"error": "已经在池子里了"}), 409
    song = {
        "id": int(time.time() * 1000),
        "title": title,
        "artist": artist,
        "by": name,
        "votes": 0,
        "voters": [],
        "time": now_ts()
    }
    songs.append(song)
    write_json(SONGS_FILE, songs)
    return jsonify(song), 201


@app.route("/api/songs/<int:song_id>/vote", methods=["POST"])
def vote_song(song_id):
    data = request.get_json(force=True)
    voter = (data.get("voter") or "").strip()
    if not voter:
        return jsonify({"error": "需要一个名字"}), 400
    songs = read_json(SONGS_FILE)
    for s in songs:
        if s["id"] == song_id:
            s.setdefault("voters", [])
            if voter in s["voters"]:
                return jsonify({"error": "投过了"}), 409
            s["votes"] = s.get("votes", 0) + 1
            s["voters"].append(voter)
            write_json(SONGS_FILE, songs)
            return jsonify(s)
    return jsonify({"error": "没找到"}), 404


# ==================== 首页 ====================

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
