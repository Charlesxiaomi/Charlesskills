#!/usr/bin/env python3
"""解密微信 4.x 聊天图片（V2 格式的 .dat），只读，不改微信的任何文件。

用法：
  python3 -I wx_images.py --acc 1 --chat "48409737039@chatroom" --start 2026-11-01 [--end 2026-11-12] [--out DIR]

--chat 传会话的 username（wechat-cli history 的 JSON 输出里的 "username" 字段：
群是 xxx@chatroom，个人是 wxid 或微信号），不是显示名。

输出：每张图一行「文件时间<TAB>解密后的路径」，按时间排序。文件时间是图片落到本机的时间，
和消息时间通常差几秒到十几分钟；同一会话里两边的先后顺序一致，按顺序和时间去对消息。

密钥：AES 密钥 = md5(uin + wxid) 的前 16 个字符，异或密钥 = uin & 0xff。
uin 从微信的 kvcomm 文件名里取候选，用一张图验证后缓存到配置目录的 image_key.json。
"""
import argparse
import datetime as dt
import hashlib
import json
import multiprocessing
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile

from Crypto.Cipher import AES

ACCOUNTS = {
    "1": ("com.tencent.xinWeChat", "~/.wechat-cli-acc1"),
    "2": ("com.tencent.xinWeChat2", "~/.wechat-cli-acc2"),
}
V2 = b"\x07\x08V2\x08\x07"
MAGIC = {b"\xff\xd8\xff": "jpg", b"\x89PN": "png", b"GIF": "gif", b"wxg": "wxgf", b"RIF": "webp"}


def aes_len(aes_size):
    return (aes_size // 16 + 1) * 16  # PKCS7：整块时也多补一块


def find_key(container, cfg_dir, wxid, sample):
    cache = os.path.join(cfg_dir, "image_key.json")
    if os.path.exists(cache):
        return json.load(open(cache))
    kv = os.path.expanduser(f"~/Library/Containers/{container}/Data/Documents/app_data/net/kvcomm")
    uins = []
    for name in sorted(os.listdir(kv)):
        for tok in re.findall(r"\d{5,10}", name):
            if tok not in uins:
                uins.append(tok)
    blk = open(sample, "rb").read()[15:31]
    for uin in uins:
        aes = hashlib.md5((uin + wxid).encode()).hexdigest()[:16]
        head = AES.new(aes.encode(), AES.MODE_ECB).decrypt(blk)[:3]
        if head in MAGIC:
            key = {"uin": uin, "aes": aes, "xor": int(uin) & 0xFF}
            with open(cache, "w") as f:
                json.dump(key, f)
            os.chmod(cache, 0o600)
            return key
    # kvcomm 里没有（文件名里 uin 为 0）：从 JPEG 结尾 FFD9 反推 uin 低 8 位，穷举其余 24 位
    data = open(sample, "rb").read()
    xor = data[-1] ^ 0xD9
    if data[-2] ^ xor != 0xFF:
        sys.exit("样本图不是 JPEG，没法反推 uin。换一个带 JPEG 缩略图的会话再试。")
    print("本机没存 uin，正在穷举（约一两分钟，只需一次）…", file=sys.stderr)
    n = os.cpu_count() or 4
    step = (1 << 24) // n + 1
    jobs = [(wxid, blk, xor, lo, min(lo + step, 1 << 24)) for lo in range(0, 1 << 24, step)]
    with multiprocessing.Pool(n) as pool:
        for uin in pool.imap_unordered(_brute, jobs):
            if uin:
                pool.terminate()
                aes = hashlib.md5((uin + wxid).encode()).hexdigest()[:16]
                key = {"uin": uin, "aes": aes, "xor": xor}
                with open(cache, "w") as f:
                    json.dump(key, f)
                os.chmod(cache, 0o600)
                return key
    sys.exit("穷举完也没找到 uin，密钥推导方式可能随微信版本变了。")


def _brute(job):
    wxid, blk, xor, lo, hi = job
    w = wxid.encode()
    for hi24 in range(lo, hi):
        uin = str((hi24 << 8) | xor).encode()
        k = hashlib.md5(uin + w).hexdigest()[:16].encode()
        if AES.new(k, AES.MODE_ECB).decrypt(blk)[:3] == b"\xff\xd8\xff":
            return uin.decode()
    return None


def decrypt(path, key):
    data = open(path, "rb").read()
    if data[:6] != V2:
        return None
    aes_size, xor_size = struct.unpack("<II", data[6:14])
    n = aes_len(aes_size)
    head = AES.new(key["aes"].encode(), AES.MODE_ECB).decrypt(data[15:15 + n])[:aes_size]
    body = data[15 + n:]
    if xor_size:
        raw, tail = body[:-xor_size], bytes(b ^ key["xor"] for b in body[-xor_size:])
    else:
        raw, tail = body, b""
    return head + raw + tail


def wxgf_to_jpg(plain, base):
    """wxgf 是微信包了一层头的 HEVC 画面，从第一个 NAL 起交给 ffmpeg 取第一帧。"""
    i = plain.find(b"\x00\x00\x00\x01")
    if i < 0 or not shutil.which("ffmpeg"):
        return None
    dst = base + ".jpg"
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-f", "hevc", "-i", "pipe:0", "-frames:v", "1", "-q:v", "2", dst],
        input=plain[i:], capture_output=True,
    )
    return dst if r.returncode == 0 and os.path.exists(dst) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--acc", choices=["1", "2"], required=True)
    ap.add_argument("--chat", required=True, help="会话 username，如 48409737039@chatroom")
    ap.add_argument("--start", required=True, help="YYYY-MM-DD")
    ap.add_argument("--end", help="YYYY-MM-DD（含当天），默认到现在")
    ap.add_argument("--out", help="输出目录，默认系统临时目录下的 wx_images/")
    ap.add_argument("--thumb", action="store_true", help="只要缩略图（快，够看大意）")
    a = ap.parse_args()

    container, cfg_dir = ACCOUNTS[a.acc]
    cfg_dir = os.path.expanduser(cfg_dir)
    db_dir = json.load(open(os.path.join(cfg_dir, "config.json")))["db_dir"]
    acc_root = os.path.dirname(db_dir.rstrip("/"))
    wxid = re.sub(r"_[0-9a-f]{4}$", "", os.path.basename(acc_root))
    chat_md5 = hashlib.md5(a.chat.encode()).hexdigest()
    attach = os.path.join(acc_root, "msg", "attach", chat_md5)
    if not os.path.isdir(attach):
        sys.exit(f"这个会话没有图片目录：{attach}\n确认 --chat 传的是 username 而不是显示名。")

    start = dt.datetime.strptime(a.start, "%Y-%m-%d")
    end = dt.datetime.strptime(a.end, "%Y-%m-%d") + dt.timedelta(days=1) if a.end else dt.datetime.now()
    out = a.out or os.path.join(tempfile.gettempdir(), "wx_images", chat_md5)
    os.makedirs(out, exist_ok=True)

    # 每张图有 _t（缩略）、无后缀（标准）、_h（高清）三种，取最好的那份；时间取最早那份
    groups = {}
    for month in sorted(os.listdir(attach)):
        img = os.path.join(attach, month, "Img")
        if not os.path.isdir(img):
            continue
        for name in os.listdir(img):
            m = re.fullmatch(r"([0-9a-f]{32})(_t|_h)?\.dat", name)
            if m:
                groups.setdefault(m.group(1), {})[m.group(2) or ""] = os.path.join(img, name)

    rows, key = [], None
    for stem, files in groups.items():
        when = dt.datetime.fromtimestamp(min(os.path.getmtime(p) for p in files.values()))
        if not (start <= when < end):
            continue
        order = ["_t"] if a.thumb else ["_h", "", "_t"]
        src = next((files[k] for k in order if k in files), None)
        if not src:
            continue
        if key is None:
            key = find_key(container, cfg_dir, wxid, src)
        plain = decrypt(src, key)
        if plain is None:
            rows.append((when, f"{src}（不是 V2 格式，跳过）"))
            continue
        ext = MAGIC.get(plain[:3], "bin")
        base = os.path.join(out, f"{when:%Y%m%d-%H%M%S}_{stem[:8]}")
        note = ""
        if ext == "wxgf":
            dst = wxgf_to_jpg(plain, base)
            if dst is None:  # 转不了就退回缩略图
                thumb = decrypt(files["_t"], key) if "_t" in files else None
                if thumb and thumb[:3] in MAGIC and MAGIC[thumb[:3]] != "wxgf":
                    plain, ext, note = thumb, MAGIC[thumb[:3]], "（wxgf 转码失败，这是缩略图）"
                else:
                    note = "（wxgf 转码失败，需要 ffmpeg）"
        else:
            dst = None
        if dst is None:
            dst = f"{base}.{ext}"
            with open(dst, "wb") as f:
                f.write(plain)
        rows.append((when, dst + note))

    for when, path in sorted(rows):
        print(f"{when:%Y-%m-%d %H:%M:%S}\t{path}")
    if not rows:
        print("这个时间段内没有图片文件。", file=sys.stderr)


if __name__ == "__main__":
    main()
