"""Video composition tool — vendored minimal copy (burn_subtitles only).

This is a trimmed copy of OpenMontage's tools/video/video_compose.py,
keeping only the `burn_subtitles` operation this render pipeline uses.
The `_burn_subtitles` and `_build_subtitle_style` implementations are
copied verbatim from upstream; the Remotion / HyperFrames / compose /
overlay / encode paths are omitted (this pipeline uses plain FFmpeg
assembly in scripts/build_video.sh instead).
Upstream: https://github.com/openmontage/openmontage (AGPL-3.0).
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ToolResult,
    ToolStability,
    ToolTier,
)


class VideoCompose(BaseTool):
    name = "video_compose"
    version = "0.1.0"
    tier = ToolTier.CORE
    capability = "video_post"
    provider = "ffmpeg"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC

    dependencies = ["cmd:ffmpeg"]
    install_instructions = "Install FFmpeg: https://ffmpeg.org/download.html"
    agent_skills = ["remotion-best-practices", "remotion", "ffmpeg"]

    capabilities = [
        "compose_cuts",
        "burn_subtitles",
        "overlay_assets",
        "encode_profile",
        "remotion_render",
    ]

    input_schema = {
        "type": "object",
        "required": ["operation"],
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["burn_subtitles"],
                "description": "burn_subtitles: burn subtitle file into existing video.",
            },
            "input_path": {"type": "string"},
            "subtitle_path": {"type": "string"},
            "output_path": {"type": "string"},
            "subtitle_style": {"type": "object"},
            "codec": {"type": "string"},
            "crf": {"type": "integer"},
        },
    }

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        operation = inputs["operation"]
        start = time.time()

        try:
            if operation == "burn_subtitles":
                result = self._burn_subtitles(inputs)
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown operation: {operation} "
                    "(this vendored copy implements burn_subtitles only)",
                )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

        result.duration_seconds = round(time.time() - start, 2)
        return result

    def _burn_subtitles(self, inputs: dict[str, Any]) -> ToolResult:
        """Burn subtitle file into video."""
        input_path = Path(inputs["input_path"])
        subtitle_path = Path(inputs["subtitle_path"])
        output_path = Path(inputs.get("output_path", str(input_path.with_stem(f"{input_path.stem}_subtitled"))))

        if not input_path.exists():
            return ToolResult(success=False, error=f"Input not found: {input_path}")
        if not subtitle_path.exists():
            return ToolResult(success=False, error=f"Subtitle file not found: {subtitle_path}")

        style = inputs.get("subtitle_style", {})
        ass_style = self._build_subtitle_style(style)
        sub_escaped = str(subtitle_path.resolve()).replace("\\", "/").replace(":", "\\:")
        codec = inputs.get("codec", "libx264")
        crf = inputs.get("crf", 23)

        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-vf", f"subtitles='{sub_escaped}':force_style='{ass_style}'",
            "-c:v", codec, "-crf", str(crf),
            "-c:a", "copy",
            str(output_path),
        ]

        self.run_command(cmd)

        return ToolResult(
            success=True,
            data={
                "operation": "burn_subtitles",
                "output": str(output_path),
            },
            artifacts=[str(output_path)],
        )

    @staticmethod
    def _build_subtitle_style(style: dict) -> str:
        """Build ASS force_style string from style dict."""

        def _safe(val: Any) -> str:
            # Every value below ends up inside -vf "...force_style='...'". Drop the
            # characters that let a value close the quoted literal or start a new filter.
            return "".join(c for c in str(val) if c not in "'\\:,;[]=")

        parts = []
        parts.append(f"FontName={_safe(style.get('font', 'Inter'))}")
        parts.append(f"FontSize={_safe(style.get('font_size', 28))}")
        parts.append(f"Bold={1 if style.get('bold', True) else 0}")
        if style.get("primary_color"):
            parts.append(f"PrimaryColour={_safe(style['primary_color'])}")
        if style.get("outline_color"):
            parts.append(f"OutlineColour={_safe(style['outline_color'])}")
        if style.get("back_color"):
            parts.append(f"BackColour={_safe(style['back_color'])}")
        border_style = style.get("border_style", 1)
        parts.append(f"BorderStyle={_safe(border_style)}")
        parts.append(f"Outline={_safe(style.get('outline_width', 2))}")
        parts.append(f"Shadow={_safe(style.get('shadow', 0))}")
        parts.append(f"MarginV={_safe(style.get('margin_v', 40))}")
        parts.append(f"Alignment={_safe(style.get('alignment', 2))}")
        return ",".join(parts)
