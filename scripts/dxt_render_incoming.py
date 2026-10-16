#!/usr/bin/env python3
"""Convert incoming DXT SVGs to immutable PNG assets. No external paid API."""
import hashlib, json, re
from pathlib import Path
import cairosvg

ROOT=Path(__file__).resolve().parents[1]
INCOMING=ROOT/"incoming"
PAT=re.compile(r"^DXT_NEWS_(20\d{6})_(\d{4})(?:_[A-Za-z0-9_-]{1,50})?\.svg$")
MAX_BYTES=2_000_000
def main():
    if not INCOMING.exists(): return
    for src in sorted(INCOMING.glob("*.svg")):
        m=PAT.fullmatch(src.name)
        if not m: continue
        raw=src.read_bytes()
        if len(raw)>MAX_BYTES: raise ValueError(f"SVG too large: {src.name}")
        low=raw.lower()
        if any(x in low for x in [b"<!doctype",b"<!entity",b"<script",b"foreignobject",b"javascript:",b"<image",b"<use",b"href=",b"xlink:href"]):
            raise ValueError(f"Disallowed SVG construct: {src.name}")
        if not re.search(rb"<svg\b",raw): raise ValueError("Missing SVG root")
        png=cairosvg.svg2png(bytestring=raw,output_width=1080,output_height=1350)
        if not png.startswith(b"\x89PNG\r\n\x1a\n"): raise ValueError("Not PNG")
        digest=hashlib.sha256(png).hexdigest()
        yyyy,mm=m.group(1)[:4],m.group(1)[4:6]
        target=ROOT/"images"/yyyy/mm/(src.stem+"_"+digest[:16]+".png")
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists(): target.write_bytes(png)
        manifest=ROOT/"manifests"/(src.stem+".json")
        manifest.parent.mkdir(parents=True,exist_ok=True)
        data={"source_svg":str(src.relative_to(ROOT)),"image_path":str(target.relative_to(ROOT)),"image_sha256":digest,"width":1080,"height":1350,"status":"RENDERED_NOT_APPROVED"}
        manifest.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(f"Rendered {src.name} -> {target.relative_to(ROOT)}")
if __name__=="__main__": main()
