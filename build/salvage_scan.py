"""Salvage text from a cut (truncated) scanned PDF by decoding its page images directly.

#559 / #398. A file cut at 64,000 bytes, 1 MiB or 5 MiB cannot be opened as a PDF, but
the image streams that survive can. salvage.py (16 Nov) handled text streams and JPEG
(DCTDecode) only. Most of the scans it left unreadable are mixed-raster: a small JPEG
background plus a 1-bit text mask, and the mask is where the words are. This decodes
the three mask and scan formats it missed, then OCRs each with build/ocr (Apple Vision):

  CCITTFaxDecode, K -1 (Group 4)  wrapped in a one-strip TIFF; ImageIO decodes a cut
                                  G4 stream down to the last whole row.
  JBIG2Decode                     wrapped with its JBIG2Globals in a one-page PDF and
                                  rendered by build/render_pdf (Quartz decodes JBIG2).
  JPXDecode (JPEG 2000)           codestream trimmed to its last whole tile-part and
                                  closed with EOC; OpenJPEG and ImageIO both refuse it
                                  otherwise ("Stream too short").

Images under 300 x 300 pixels (seals, signature strips) are skipped.

    python3 build/salvage_scan.py CUT.pdf [...]       # one JSON line per file

Build the renderer once per Mac:  swiftc -O build/render_pdf.swift -o build/render_pdf

The output is text for the OCR store (engine salvage:g4-ocr / jbig2-ocr / jpx-ocr). It
does not judge whether the text is a usable letter; that is the reader's job under QA.
"""
import json
import os
import re
import struct
import subprocess
import sys
import tempfile
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
OCR = os.path.join(HERE, "ocr")
RENDER = os.path.join(HERE, "render_pdf")
IMAGE = re.compile(rb"<<((?:(?!<<).){0,600}?)/(CCITTFaxDecode|JBIG2Decode|JPXDecode)(.{0,400}?)stream\r?\n", re.S)
MIN_AREA = 300 * 300


def num(dic, key):
    m = re.search(rb"/" + key + rb"\s+(-?\d+)", dic)
    return int(m.group(1)) if m else None


def stream_at(b, start, dic):
    """The stream's bytes, up to endstream or to the cut."""
    end = b.find(b"endstream", start)
    data = b[start:end] if end > 0 else b[start:]
    if b"FlateDecode" in dic:
        try:
            data = zlib.decompressobj().decompress(data)
        except zlib.error:
            return b""
    return data


def g4_tiff(w, h, data, black_is_1):
    tags = [(256, 4, w), (257, 4, h), (258, 3, 1), (259, 3, 4), (262, 3, 1 if black_is_1 else 0),
            (273, 4, 0), (277, 3, 1), (278, 4, h), (279, 4, len(data)), (293, 4, 0)]
    head = 8 + 2 + len(tags) * 12 + 4
    out = b"II*\x00" + struct.pack("<IH", 8, len(tags))
    for tag, typ, val in tags:
        val = head if tag == 273 else val
        out += struct.pack("<HHI", tag, typ, 1) + (struct.pack("<HH", val, 0) if typ == 3 else struct.pack("<I", val))
    return out + struct.pack("<I", 0) + data


def jbig2_pdf(w, h, data, globals_, decode):
    dp = b"/DecodeParms<</JBIG2Globals 6 0 R>>" if globals_ is not None else b""
    content = b"q %d 0 0 %d 0 0 cm /Im0 Do Q" % (w, h)
    objs = [b"<</Type/Catalog/Pages 2 0 R>>",
            b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
            b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 %d %d]/Resources<</XObject<</Im0 5 0 R>>>>/Contents 4 0 R>>" % (w, h),
            b"<</Length %d>>stream\n%s\nendstream" % (len(content), content),
            b"<</Type/XObject/Subtype/Image/Width %d/Height %d/ImageMask true%s/Filter/JBIG2Decode%s/Length %d>>stream\n"
            % (w, h, decode, dp, len(data)) + data + b"\nendstream"]
    if globals_ is not None:
        objs.append(b"<</Length %d>>stream\n" % len(globals_) + globals_ + b"\nendstream")
    out, offs = b"%PDF-1.5\n", []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1) + b"".join(b"%010d 00000 n \n" % o for o in offs)
    return out + b"trailer<</Size %d/Root 1 0 R>>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)


def jbig2_globals(b, ref):
    m = re.search(rb"(?<!\d)%d 0 obj\s*(<<.*?>>)\s*stream\r?\n" % ref, b, re.S)
    if not m:
        return None
    return b[m.end():m.end() + num(m.group(1), rb"Length")]


def jpx_trim(data):
    """Raw codestream cut back to its last whole tile-part, closed with EOC."""
    i = data.find(b"jp2c")
    cs = data[i + 4:] if i >= 0 else data
    p = cs.find(b"\xff\x90")
    last = p
    while p != -1 and p + 10 <= len(cs):
        psot = struct.unpack(">I", cs[p + 6:p + 10])[0]
        if psot == 0 or p + psot > len(cs):
            break
        p += psot
        last = p
        if cs[p:p + 2] != b"\xff\x90":
            break
    return cs[:last] + b"\xff\xd9" if last and last > 0 else None


def ocr(paths):
    out = subprocess.run([OCR, *paths], capture_output=True, text=True).stdout
    return [json.loads(l) for l in out.splitlines() if l.startswith("{")]


def salvage(path):
    b = open(path, "rb").read()
    found = []
    with tempfile.TemporaryDirectory() as td:
        for i, m in enumerate(IMAGE.finditer(b)):
            dic, kind = m.group(0), m.group(2).decode()
            w, h = num(dic, rb"Width") or num(dic, rb"Columns"), num(dic, rb"Height") or 0
            if not w or w * h < MIN_AREA:
                continue
            data = stream_at(b, m.end(), dic)
            if not data:
                continue
            f = os.path.join(td, "%d" % i)
            if kind == "CCITTFaxDecode":
                if num(dic, rb"K") != -1:
                    continue
                f += ".tif"
                open(f, "wb").write(g4_tiff(w, h, data, b"/BlackIs1 true" in dic))
            elif kind == "JBIG2Decode":
                ref = re.search(rb"/JBIG2Globals (\d+) 0 R", dic)
                dec = re.search(rb"/Decode\s*\[[^\]]*\]", dic)
                pdf = f + ".pdf"
                open(pdf, "wb").write(jbig2_pdf(w, h, data, jbig2_globals(b, int(ref.group(1))) if ref else None,
                                                dec.group(0) if dec else b""))
                f += ".png"
                if subprocess.run([RENDER, pdf, f, "1.5"], capture_output=True).returncode:
                    continue
            else:
                cs = jpx_trim(data)
                if not cs:
                    continue
                f += ".j2k"
                open(f, "wb").write(cs)
            r = ocr([f])
            text = r[0].get("text", "") if r else ""
            found.append({"index": i, "kind": kind, "width": w, "height": h, "chars": len(text), "text": text})
    method = {"CCITTFaxDecode": "g4-ocr", "JBIG2Decode": "jbig2-ocr", "JPXDecode": "jpx-ocr"}
    used = [x for x in found if x["chars"] >= 20]
    return {"file": path, "engine": "salvage:" + method[used[0]["kind"]] if used else None,
            "images": len(used), "text": "\n".join(x["text"] for x in used)}


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(json.dumps(salvage(p)), flush=True)
