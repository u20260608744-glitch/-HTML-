#!/usr/bin/env python3
"""Plan narrated video timing and verify exported MP4s using supplied tools.

Python's standard library is sufficient. FFprobe and FFmpeg are external tools;
their paths must be supplied and nothing is installed or downloaded. A successful
report checks timing and media structure, not project facts, visual completeness,
caption legibility, music rights, or correspondence between video and source HTML.
"""

import argparse
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from fractions import Fraction


class VideoToolsError(Exception):
    """An actionable input or external-tool failure."""


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_path(value, label, base=None):
    if not isinstance(value, str) or not value.strip():
        raise VideoToolsError(f"{label} must be a nonempty local file path")
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = (base or Path.cwd()) / path
    return path.resolve()


def require_file(path, label):
    if not path.is_file() or path.stat().st_size == 0:
        raise VideoToolsError(f"{label} is missing, empty, or not a file: {path}")


def finite_number(value, label, minimum=0, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise VideoToolsError(f"{label} must be a finite JSON number")
    try:
        number = float(value)
    except (OverflowError, ValueError):
        raise VideoToolsError(f"{label} must be finite") from None
    if not math.isfinite(number) or number < minimum or (positive and number <= 0):
        bound = "positive" if positive else f"at least {minimum}"
        raise VideoToolsError(f"{label} must be finite and {bound}")
    return Fraction(str(value))


def fraction_value(value, label):
    """Parse a finite positive ffprobe ratio without accepting NaN/Infinity."""
    try:
        result = Fraction(str(value).replace(":", "/"))
    except (ValueError, ZeroDivisionError, OverflowError):
        raise VideoToolsError(f"{label} is not a valid positive ratio: {value}") from None
    if result <= 0:
        raise VideoToolsError(f"{label} must be positive")
    return result


def aspect_argument(value):
    if not re.fullmatch(r"[1-9]\d*:[1-9]\d*", value):
        raise argparse.ArgumentTypeError("aspect must be a positive integer ratio N:D, such as 16:9, 9:16, 1:1, or 4:5")
    return value


def probe_number(value, label, positive=False):
    if value is None or value == "N/A":
        return None
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        raise VideoToolsError(f"{label} is not numeric") from None
    if not math.isfinite(result) or result < 0 or (positive and result <= 0):
        raise VideoToolsError(f"{label} must be finite and nonnegative")
    return result


def tool_path(value):
    candidate = Path(value).expanduser()
    if candidate.is_file():
        return str(candidate.resolve())
    resolved = shutil.which(value)
    if resolved:
        return str(Path(resolved).resolve())
    raise VideoToolsError(f"Tool not found: {value}. Supply an installed executable path.")


def run(command):
    try:
        return subprocess.run(command, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", check=False)
    except OSError as error:
        raise VideoToolsError(f"Could not run {command[0]}: {error}") from None


def probe(path, executable, report):
    command = [executable, "-v", "error", "-show_format", "-show_streams",
               "-of", "json", str(path)]
    result = run(command)
    report.setdefault("probeCommands", []).append(command)
    if result.returncode:
        raise VideoToolsError(f"FFprobe failed ({result.returncode}): {result.stderr[-2000:]}")
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise VideoToolsError("FFprobe did not return valid JSON") from None
    if not isinstance(data, dict) or not isinstance(data.get("streams"), list):
        raise VideoToolsError("FFprobe output has no stream list")
    return data


def stream_duration(stream):
    duration = probe_number(stream.get("duration"), "stream duration", positive=True)
    if duration is not None:
        return duration
    ticks = probe_number(stream.get("duration_ts"), "stream duration_ts", positive=True)
    if ticks is not None and stream.get("time_base"):
        return float(Fraction(str(ticks)) * fraction_value(stream["time_base"], "time base"))
    return None


def ceil_fraction(value):
    return -(-value.numerator // value.denominator)


def write_report(path, data, protected):
    path = Path(path).expanduser().resolve()
    if path in protected:
        raise VideoToolsError(f"Report must not overwrite an input or tool: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                         prefix=path.name + ".", suffix=".tmp",
                                         delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def plan(args, report, protected):
    report.update({"timing_only": True, "rendered": False,
                   "unverified": ["Full configuration-schema validation", "Project facts and source geometry",
                                  "Voice and music rights or provider availability", "Browser actions and visual coverage",
                                  "Video rendering, caption legibility, and video-to-source correspondence"]})
    config_path = file_path(args.config, "config")
    protected.add(config_path)
    require_file(config_path, "config")
    report["config"] = str(config_path)
    report["configSHA256"] = sha256(config_path)

    def reject_constant(value):
        raise VideoToolsError(f"Nonfinite JSON number is not allowed: {value}")

    try:
        config = json.loads(config_path.read_text(encoding="utf-8-sig"),
                            parse_constant=reject_constant)
    except (json.JSONDecodeError, UnicodeError) as error:
        raise VideoToolsError(f"Cannot read config JSON: {error}") from None
    if not isinstance(config, dict):
        raise VideoToolsError("Config must be a JSON object")
    source_inputs = [config.get("source_html")]
    if isinstance(config.get("source_assets"), list):
        source_inputs += [asset.get("path") for asset in config["source_assets"] if isinstance(asset, dict)]
    for value in source_inputs:
        if isinstance(value, str) and value.strip():
            protected.add(file_path(value, "source file", config_path.parent))
    scenes = config.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise VideoToolsError("scenes is empty or missing; prepare scene definitions and narration audio first")
    for scene in scenes:
        if isinstance(scene, dict) and isinstance(scene.get("narration_audio"), str):
            protected.add(file_path(scene["narration_audio"], "narration_audio", config_path.parent))
    fps = finite_number(config.get("fps", 25), "fps", positive=True)
    cap = finite_number(config.get("max_seconds", 300), "max_seconds", positive=True)
    target = config.get("target_seconds")
    target = finite_number(target, "target_seconds", positive=True) if target is not None else None
    if target is not None and target > cap:
        raise VideoToolsError("target_seconds must not exceed the hard max_seconds limit")
    capture = config.get("capture")
    if capture is not None:
        if not isinstance(capture, dict):
            raise VideoToolsError("capture must be an object when provided")
        if "motion_speed" in capture and finite_number(capture["motion_speed"], "capture.motion_speed", positive=True) != 1:
            raise VideoToolsError("capture.motion_speed must be 1; do not accelerate captured motion")

    def file_identity(value, expected, label):
        path = file_path(value, label, config_path.parent)
        protected.add(path)
        require_file(path, label)
        actual = sha256(path)
        if expected is not None:
            if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
                raise VideoToolsError(f"{label} SHA256 must contain exactly 64 hexadecimal characters")
            if actual != expected.lower():
                raise VideoToolsError(f"{label} SHA256 does not match the supplied value: {path}")
        return {"path": str(path), "sha256": actual, "expectedSHA256": expected,
                "matchRequested": expected is not None, "fileIdentityOnly": True}

    source = config.get("source_html")
    source_hash = config.get("source_html_sha256")
    if source is None and source_hash is not None:
        raise VideoToolsError("source_html_sha256 requires source_html")
    if source is not None:
        report["source"] = file_identity(source, source_hash, "source HTML")
    assets = config.get("source_assets", [])
    if not isinstance(assets, list):
        raise VideoToolsError("source_assets must be an array when provided")
    if assets:
        report["sourceAssets"] = []
        for index, asset in enumerate(assets, 1):
            if not isinstance(asset, dict):
                raise VideoToolsError(f"Source asset {index} must be an object")
            report["sourceAssets"].append(file_identity(asset.get("path"), asset.get("sha256"), f"Source asset {index}"))
    executable = tool_path(args.ffprobe)
    protected.add(Path(executable))
    report["parameters"] = {"ffprobe": executable, "fps": float(fps),
                            "fpsRational": str(fps), "maxSeconds": float(cap),
                            "targetSeconds": float(target) if target is not None else None}
    seen = set()
    prepared = []
    for index, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict):
            raise VideoToolsError(f"Scene {index} must be an object")
        identity = scene.get("id")
        if not isinstance(identity, str) or not identity.strip():
            raise VideoToolsError(f"Scene {index} requires a nonempty id")
        if identity in seen:
            raise VideoToolsError(f"Duplicate scene id: {identity}")
        seen.add(identity)
        title = scene.get("title", identity)
        if not isinstance(title, str):
            raise VideoToolsError(f"Scene {identity}: title must be text")
        audio = file_path(scene.get("narration_audio"), f"Scene {identity} narration_audio", config_path.parent)
        require_file(audio, f"Scene {identity} narration audio")
        lead = finite_number(scene.get("lead_seconds", 0), f"Scene {identity} lead_seconds")
        tail = finite_number(scene.get("tail_seconds", 0), f"Scene {identity} tail_seconds")
        minimum = finite_number(scene.get("min_visual_seconds", 0), f"Scene {identity} min_visual_seconds")
        prepared.append((identity, title, audio, lead, tail, minimum))
    timeline = []
    frame = 0
    for identity, title, audio, lead, tail, minimum in prepared:
        headers = probe(audio, executable, report)
        audio_streams = [s for s in headers["streams"] if s.get("codec_type") == "audio"]
        if not audio_streams:
            raise VideoToolsError(f"Scene {identity}: narration file has no audio stream")
        durations = [stream_duration(s) for s in audio_streams]
        container_duration = probe_number(headers.get("format", {}).get("duration"), "audio container duration", positive=True)
        candidates = [v for v in durations + [container_duration] if v is not None]
        if not candidates:
            raise VideoToolsError(f"Scene {identity}: FFprobe could not establish the actual audio duration")
        audio_duration = Fraction(str(max(candidates)))
        seconds_required = max(lead + audio_duration + tail, minimum)
        frames = ceil_fraction(seconds_required * fps)
        start = Fraction(frame, 1) / fps
        end = Fraction(frame + frames, 1) / fps
        timeline.append({"id": identity, "title": title,
                         "narrationAudio": str(audio), "narrationAudioSHA256": sha256(audio),
                         "audioDurationSeconds": float(audio_duration),
                         "leadSeconds": float(lead), "tailSeconds": float(tail),
                         "minVisualSeconds": float(minimum), "frames": frames,
                         "startFrame": frame, "endFrame": frame + frames,
                         "startSeconds": float(start), "endSeconds": float(end),
                         "durationSeconds": float(Fraction(frames, 1) / fps),
                         "audioStartSeconds": float(start + lead),
                         "audioEndSeconds": float(start + lead + audio_duration)})
        frame += frames
    duration = Fraction(frame, 1) / fps
    report.update({"scenes": timeline, "totalFrames": frame, "durationSeconds": float(duration),
                   "hardLimitSeconds": float(cap), "targetIsBudgetHintOnly": True,
                   "targetExceeded": target is not None and duration > target,
                   "targetExceedsHardLimit": target is not None and target > cap,
                   "noSpeechSpeedChange": True,
                   "timingPolicy": "Each scene is ceil(max(actual audio + lead + tail, minimum visual duration) * fps) frames. Audio offsets remain in seconds; no narration speed change.",
                   "scope": "Timing plan and optional supplied source-file identities only; no full config-schema validation, scene rendering, editing, semantic checks, or publication."})
    if duration > cap:
        raise VideoToolsError(f"Planned duration {float(duration):.6f}s exceeds hard max_seconds {float(cap):.6f}s; shorten the script or explicitly revise the budget, not playback speed")
    report["pass"] = True


def mp4_atoms(path):
    atoms = []
    total = path.stat().st_size
    with path.open("rb") as stream:
        while stream.tell() < total:
            offset = stream.tell()
            header = stream.read(8)
            if len(header) != 8:
                raise VideoToolsError("Incomplete MP4 atom header")
            size, kind = struct.unpack(">I4s", header)
            header_size = 8
            if size == 1:
                extra = stream.read(8)
                if len(extra) != 8:
                    raise VideoToolsError("Incomplete extended MP4 atom")
                size = struct.unpack(">Q", extra)[0]
                header_size = 16
            elif size == 0:
                size = total - offset
            if size < header_size or offset + size > total:
                raise VideoToolsError("MP4 atom exceeds its file boundary")
            atoms.append({"type": kind.decode("ascii", errors="replace"), "offset": offset, "bytes": size})
            stream.seek(offset + size)
    return atoms


TIMESTAMP = re.compile(r"^(\d{2,}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2,}):(\d{2}):(\d{2})[,.](\d{3})(?:\s+.*)?$")


def srt_times(path, limit):
    text = path.read_text(encoding="utf-8-sig").strip()
    if not text:
        raise VideoToolsError("Subtitle file is empty")
    cues = []
    previous_end = 0
    for block in re.split(r"\r?\n\s*\r?\n", text):
        lines = block.splitlines()
        if lines and lines[0].strip().isdigit():
            lines = lines[1:]
        match = TIMESTAMP.fullmatch(lines[0].strip()) if lines else None
        if not match or len(lines) < 2 or not "\n".join(lines[1:]).strip():
            raise VideoToolsError(f"Malformed or empty SRT cue {len(cues) + 1}")
        values = [int(v) for v in match.groups()]
        if any(values[i] >= 60 for i in (1, 2, 5, 6)):
            raise VideoToolsError(f"Invalid SRT minutes/seconds in cue {len(cues) + 1}")
        start = ((values[0] * 60 + values[1]) * 60 + values[2]) * 1000 + values[3]
        end = ((values[4] * 60 + values[5]) * 60 + values[6]) * 1000 + values[7]
        if start < previous_end or end <= start:
            raise VideoToolsError(f"SRT cue {len(cues) + 1} overlaps or reverses timing")
        if Fraction(end, 1000) > Fraction(str(limit)):
            raise VideoToolsError(f"SRT cue {len(cues) + 1} ends beyond the video or duration cap")
        cues.append({"startSeconds": start / 1000, "endSeconds": end / 1000})
        previous_end = end
    return {"cueCount": len(cues), "maximumEndSeconds": previous_end / 1000,
            "monotonicNonoverlapping": True, "withinVideoAndCap": True,
            "legibilityChecked": False}


def verify(args, report, protected):
    video = file_path(args.video, "video")
    protected.add(video)
    require_file(video, "video")
    cap = finite_number(args.max_seconds, "max-seconds", positive=True)
    expected_aspect = fraction_value(args.aspect, "aspect")
    ffprobe = tool_path(args.ffprobe)
    ffmpeg = tool_path(args.ffmpeg)
    protected.update((Path(ffprobe), Path(ffmpeg)))
    report.update({"video": str(video), "videoSHA256": sha256(video), "bytes": video.stat().st_size,
                   "parameters": {"ffprobe": ffprobe, "ffmpeg": ffmpeg,
                                  "maxSeconds": float(cap), "aspect": args.aspect,
                                  "sourceHTML": args.source_html,
                                  "expectedSourceSHA256": args.expected_source_sha256,
                                  "subtitles": args.subtitles}, "checks": {}, "failures": [],
                   "scope": "Media encoding, timing, complete AV decoding, optional SRT timing and source-file hash only. Content semantics, caption legibility, model fidelity, audio quality, rights, and video-to-HTML correspondence are not automatically verified."})

    def check(name, passed, evidence=None):
        report["checks"][name] = bool(passed)
        if not passed:
            report["failures"].append({"check": name, "evidence": evidence})

    if args.expected_source_sha256 and not args.source_html:
        raise VideoToolsError("--expected-source-sha256 requires --source-html")
    if args.source_html:
        source = file_path(args.source_html, "source HTML")
        protected.add(source)
        require_file(source, "source HTML")
        actual_hash = sha256(source)
        expected = args.expected_source_sha256
        if expected and not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
            raise VideoToolsError("Expected source SHA256 must contain exactly 64 hexadecimal characters")
        report["source"] = {"path": str(source), "sha256": actual_hash,
                            "expectedSHA256": expected, "matchRequested": bool(expected)}
        if expected:
            check("sourceSHA256Matches", actual_hash == expected.lower(), actual_hash)
    headers = probe(video, ffprobe, report)
    report["headers"] = headers
    format_data = headers.get("format", {})
    duration = probe_number(format_data.get("duration"), "container duration", positive=True)
    check("containerMP4", video.suffix.lower() == ".mp4" and "mp4" in format_data.get("format_name", "").split(","))
    check("containerDurationWithinCap", duration is not None and duration <= float(cap), duration)
    streams = [s for s in headers["streams"] if s.get("codec_type") in ("video", "audio")]
    videos = [s for s in streams if s["codec_type"] == "video"]
    audios = [s for s in streams if s["codec_type"] == "audio"]
    check("hasVideoAndAudio", bool(videos and audios), {"videoCount": len(videos), "audioCount": len(audios)})
    stream_rows = []
    for stream in streams:
        identity = f"stream{stream.get('index', len(stream_rows))}"
        seconds = stream_duration(stream)
        check(identity + "DurationWithinCap", seconds is not None and seconds <= float(cap), seconds)
        start_raw = stream.get("start_time")
        try:
            start = float(start_raw) if start_raw not in (None, "N/A") else 0
        except (TypeError, ValueError, OverflowError):
            raise VideoToolsError(f"{identity} has an invalid start_time") from None
        if not math.isfinite(start):
            raise VideoToolsError(f"{identity} has a nonfinite start_time")
        check(identity + "EndWithinCap", seconds is not None and max(0, start) + seconds <= float(cap), {"start": start, "duration": seconds})
        row = {"index": stream.get("index"), "type": stream["codec_type"],
               "codec": stream.get("codec_name"), "durationSeconds": seconds, "startSeconds": start}
        if stream["codec_type"] == "video":
            check(identity + "H264", stream.get("codec_name") == "h264", stream.get("codec_name"))
            check(identity + "YUV420P", stream.get("pix_fmt") == "yuv420p", stream.get("pix_fmt"))
            sar = fraction_value(stream.get("sample_aspect_ratio", "0:1"), identity + " SAR")
            check(identity + "SquarePixels", sar == 1, str(sar))
            width, height = stream.get("width", 0), stream.get("height", 0)
            check(identity + "AspectMatches", width > 0 and height > 0 and Fraction(width, height) == expected_aspect, [width, height])
            fps = fraction_value(stream.get("avg_frame_rate", "0/1"), identity + " frame rate")
            row.update({"width": width, "height": height, "fps": float(fps), "fpsRational": str(fps),
                        "sampleAspectRatio": str(sar), "declaredFrames": stream.get("nb_frames")})
        else:
            check(identity + "AAC", stream.get("codec_name") == "aac", stream.get("codec_name"))
            row.update({"sampleRate": stream.get("sample_rate"), "channels": stream.get("channels")})
        stream_rows.append(row)
    report["streams"] = stream_rows
    atoms = mp4_atoms(video)
    report["mp4Atoms"] = atoms
    first_moov = next((a["offset"] for a in atoms if a["type"] == "moov"), None)
    first_mdat = next((a["offset"] for a in atoms if a["type"] == "mdat"), None)
    check("mp4FileTypeAtom", any(a["type"] == "ftyp" for a in atoms))
    check("faststartMoovBeforeMdat", first_moov is not None and first_mdat is not None and first_moov < first_mdat)
    if args.subtitles:
        subtitles = file_path(args.subtitles, "subtitles")
        protected.add(subtitles)
        require_file(subtitles, "subtitles")
        primary_duration = stream_duration(videos[0]) if videos else None
        bounds = [float(cap)] + [v for v in (duration, primary_duration) if v is not None]
        report["subtitles"] = {"path": str(subtitles), "sha256": sha256(subtitles),
                               **srt_times(subtitles, min(bounds))}
        check("subtitleTimingValid", True)
    command = [ffmpeg, "-hide_banner", "-v", "error", "-nostdin", "-xerror",
               "-i", str(video), "-map", "0:v?", "-map", "0:a?", "-vsync", "0",
               "-progress", "pipe:1", "-nostats", "-f", "null", os.devnull]
    report["decodeCommand"] = command
    decoded = run(command)
    progress = {}
    for line in decoded.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            progress[key.strip()] = value.strip()
    report["decode"] = {"returnCode": decoded.returncode, "stderr": decoded.stderr,
                        "finalProgress": progress, "allAVStreamsMapped": True}
    check("fullDecodeWithoutError", decoded.returncode == 0 and not decoded.stderr.strip()
          and progress.get("progress") == "end", decoded.stderr[-2000:])
    actual_frames = int(progress.get("frame", "0"))
    check("decodedPrimaryVideoHasFrames", actual_frames > 0, actual_frames)
    if videos:
        primary = videos[0]
        fps = fraction_value(primary.get("avg_frame_rate", "0/1"), "primary frame rate")
        primary_duration = stream_duration(primary)
        estimate = primary_duration * float(fps) if primary_duration is not None else None
        check("decodedPrimaryFrameCountReasonable", estimate is not None
              and abs(actual_frames - estimate) <= max(2, float(fps) * 0.1),
              {"decoded": actual_frames, "durationTimesFPS": estimate})
        declared = primary.get("nb_frames")
        if declared not in (None, "N/A"):
            check("decodedPrimaryFramesMatchDeclared", int(declared) == actual_frames,
                  {"decoded": actual_frames, "declared": declared})
    if progress.get("out_time_us"):
        decoded_end = int(progress["out_time_us"]) / 1000000
        report["decode"]["endSeconds"] = decoded_end
        check("decodedAVTimelineWithinCap", decoded_end <= float(cap), decoded_end)
    check("videoUnchangedDuringVerification", sha256(video) == report["videoSHA256"])
    if args.source_html:
        check("sourceUnchangedDuringVerification", sha256(source) == actual_hash)
    report["pass"] = not report["failures"]


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    planned = commands.add_parser("plan", help="Plan scene timing from real narration files; never speed speech up")
    planned.add_argument("--config", required=True)
    planned.add_argument("--ffprobe", required=True)
    planned.add_argument("--output", required=True)
    verified = commands.add_parser("verify", help="Verify media structure and timing, not semantic content or caption legibility")
    verified.add_argument("--video", required=True)
    verified.add_argument("--ffprobe", required=True)
    verified.add_argument("--ffmpeg", required=True)
    verified.add_argument("--max-seconds", type=float, default=300)
    verified.add_argument("--aspect", type=aspect_argument, required=True,
                          help="Positive integer width:height ratio, including 16:9, 9:16, 1:1, and 4:5")
    verified.add_argument("--report", required=True)
    verified.add_argument("--source-html")
    verified.add_argument("--expected-source-sha256")
    verified.add_argument("--subtitles")
    return result


def main():
    args = parser().parse_args()
    output = Path(args.output if args.command == "plan" else args.report).expanduser().resolve()
    protected = {file_path(getattr(args, key), key) for key in
                 ("config", "video", "source_html", "subtitles", "ffprobe", "ffmpeg")
                 if getattr(args, key, None)}
    report = {"pass": False, "command": args.command,
              "checkedAtUTC": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "argv": sys.argv[1:], "report": str(output)}
    try:
        if args.command == "plan":
            plan(args, report, protected)
        else:
            verify(args, report, protected)
    except (VideoToolsError, OSError, ValueError, TypeError, KeyError, OverflowError) as error:
        report["pass"] = False
        report["error"] = str(error)
    try:
        write_report(output, report, protected)
    except (VideoToolsError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"pass": report["pass"], "command": args.command,
                      "report": str(output), "error": report.get("error")}, ensure_ascii=True))
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
