#!/usr/bin/env python3
"""Generate high-contrast, professional, responsive SVG architecture diagrams
for the VoxFlow Case Study.

Guarantees:
- 100% Valid XML with html.escape for all text/attributes
- GitHub Camo safe: no feDropShadow or unsupported filter primitives
- Multi-line text support via <tspan> elements
- Fixed, elegant aspect ratio and compact vertical footprint
- Self-contained dark-mode card canvas (#0B132B / #0F172A)
- High-contrast typography (system fonts, bold labels, readable subtext)
"""

import html
import xml.etree.ElementTree as ET
from pathlib import Path

DIAGRAMS_DIR = Path(__file__).resolve().parents[1] / "diagrams"

def esc(text: str) -> str:
    return html.escape(str(text))

def make_card(w, h, title, subtitle):
    t_safe = esc(title)
    s_safe = esc(subtitle)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
  <defs>
    <linearGradient id="headerGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#0284C7" />
      <stop offset="50%" stop-color="#6366F1" />
      <stop offset="100%" stop-color="#10B981" />
    </linearGradient>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 9 5 L 0 9 z" fill="#38BDF8" />
    </marker>
    <marker id="arrowGreen" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 9 5 L 0 9 z" fill="#34D399" />
    </marker>
    <marker id="arrowAmber" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 9 5 L 0 9 z" fill="#FBBF24" />
    </marker>
    <marker id="arrowRose" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 9 5 L 0 9 z" fill="#F87171" />
    </marker>
  </defs>

  <!-- Container Canvas -->
  <rect x="2" y="2" width="{w - 4}" height="{h - 4}" rx="12" fill="#0B132B" stroke="#334155" stroke-width="2" />
  <rect x="2" y="2" width="{w - 4}" height="5" rx="2" fill="url(#headerGrad)" />

  <!-- Header Section -->
  <g transform="translate(24, 30)">
    <circle cx="10" cy="10" r="10" fill="#0284C7" />
    <path d="M 6 10 L 9 13 L 14 7" stroke="#FFFFFF" stroke-width="2" fill="none" stroke-linecap="round" />
    <text x="28" y="14" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="15" font-weight="700" fill="#F8FAFC">{t_safe}</text>
    <text x="28" y="28" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="11" font-weight="500" fill="#94A3B8">{s_safe}</text>
  </g>
"""

def node_box(x, y, w, h, title, subtitle, stroke="#38BDF8", fill="#1E293B", badge=""):
    t_safe = esc(title)
    lines = [esc(line.strip()) for line in subtitle.split("\n") if line.strip()]
    
    badge_markup = ""
    if badge:
        b_safe = esc(badge)
        badge_w = max(55, len(badge) * 7 + 14)
        badge_markup = f"""
    <rect x="{x + w - badge_w - 10}" y="{y + 7}" width="{badge_w}" height="16" rx="8" fill="{stroke}" fill-opacity="0.2" stroke="{stroke}" stroke-width="1" />
    <text x="{x + w - badge_w/2 - 10}" y="{y + 18.5}" font-family="system-ui, sans-serif" font-size="8.5" font-weight="700" fill="{stroke}" text-anchor="middle">{b_safe}</text>"""

    title_y = y + 19 if h <= 55 else y + 22
    start_y = y + 35 if h <= 55 else y + 40
    line_dy = "12" if h <= 55 else "14"

    tspans = ""
    for i, line in enumerate(lines):
        dy = "0" if i == 0 else line_dy
        tspans += f'<tspan x="{x + 14}" dy="{dy}">{line}</tspan>'

    return f"""
  <!-- Node: {t_safe} -->
  <g>
    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1.6" />
    {badge_markup}
    <text x="{x + 14}" y="{title_y}" font-family="system-ui, sans-serif" font-size="12.5" font-weight="700" fill="#F8FAFC">{t_safe}</text>
    <text x="{x + 14}" y="{start_y}" font-family="system-ui, sans-serif" font-size="10.5" font-weight="500" fill="#94A3B8">{tspans}</text>
  </g>"""

def group_box(x, y, w, h, title, stroke="#334155", fill="#0F172A", title_color="#38BDF8"):
    t_safe = esc(title.upper())
    return f"""
  <!-- Group: {t_safe} -->
  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1.2" stroke-dasharray="3,3" />
  <text x="{x + 14}" y="{y + 18}" font-family="system-ui, sans-serif" font-size="10.5" font-weight="700" fill="{title_color}" letter-spacing="0.5">{t_safe}</text>
"""

def connection(x1, y1, x2, y2, label="", color="#38BDF8", marker="url(#arrow)", dash=""):
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    label_markup = ""
    if label:
        l_safe = esc(label)
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        label_w = len(label) * 6 + 14
        label_markup = f"""
    <rect x="{mid_x - label_w/2}" y="{mid_y - 9}" width="{label_w}" height="18" rx="5" fill="#0B132B" stroke="{color}" stroke-width="0.9" />
    <text x="{mid_x}" y="{mid_y + 3}" font-family="system-ui, sans-serif" font-size="9" font-weight="600" fill="#F8FAFC" text-anchor="middle">{l_safe}</text>"""

    return f"""
  <path d="M {x1} {y1} L {x2} {y2}" stroke="{color}" stroke-width="1.6"{dash_attr} fill="none" marker-end="{marker}" />
  {label_markup}"""

def curve_connection(d, label="", mid_x=0, mid_y=0, color="#38BDF8", marker="url(#arrow)", dash=""):
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    label_markup = ""
    if label and mid_x and mid_y:
        l_safe = esc(label)
        label_w = len(label) * 6 + 14
        label_markup = f"""
    <rect x="{mid_x - label_w/2}" y="{mid_y - 9}" width="{label_w}" height="18" rx="5" fill="#0B132B" stroke="{color}" stroke-width="0.9" />
    <text x="{mid_x}" y="{mid_y + 3}" font-family="system-ui, sans-serif" font-size="9" font-weight="600" fill="#F8FAFC" text-anchor="middle">{l_safe}</text>"""

    return f"""
  <path d="{d}" stroke="{color}" stroke-width="1.6"{dash_attr} fill="none" marker-end="{marker}" />
  {label_markup}"""

# -------------------------------------------------------------
# 1. 01-voice-pipeline.svg (Compact 960x440)
# -------------------------------------------------------------
def build_svg_01():
    svg = make_card(960, 440, "VoxFlow Voice Pipeline Architecture", "Inbound PSTN via Amazon Connect & Browser Audio Simulator Paths (London eu-west-2)")
    
    svg += group_box(24, 68, 270, 350, "1. Inbound Telephony Layer", stroke="#0284C7", title_color="#38BDF8")
    svg += group_box(310, 68, 310, 350, "2. Security & Agent Gateway", stroke="#6366F1", title_color="#818CF8")
    svg += group_box(636, 68, 300, 350, "3. Intelligence & Persistence", stroke="#10B981", title_color="#34D399")

    # Column 1: Telephony
    svg += node_box(38, 98, 242, 58, "PSTN Caller (UK)", "Supplier / driver on UK DID", stroke="#38BDF8", badge="PSTN")
    svg += node_box(38, 178, 242, 60, "Amazon Connect", "Contact flow · en-GB · eu-west-2", stroke="#0284C7", badge="AWS")
    svg += node_box(38, 260, 242, 58, "Amazon Lex V2", "en-GB Speech Capture (STT)", stroke="#0EA5E9", badge="STT")
    svg += node_box(38, 340, 242, 58, "Browser Simulator", "PCM 16 kHz Web Audio client", stroke="#64748B", badge="TEST")

    # Column 2: Security & Agent Gateway
    svg += node_box(326, 98, 278, 62, "AWS Lambda Bridge", "HMAC-SHA256 signature + timestamp", stroke="#F59E0B", badge="AUTH")
    svg += node_box(326, 180, 278, 62, "Replay Ledger & Route Gate", "Redis SET NX EX 300s · Exact DID match", stroke="#818CF8", badge="GUARD")
    svg += node_box(326, 262, 278, 62, "FastAPI Voice Engine", "AgentRunner · Session state machine", stroke="#6366F1", badge="CORE")
    svg += node_box(326, 344, 278, 54, "Spoken Grounding Guard", "Refuses unbacked status claims", stroke="#10B981", badge="SAFETY")

    # Column 3: Intelligence & Persistence
    svg += node_box(652, 98, 268, 60, "Groq Cloud LLM / STT", "gpt-oss-20b · Whisper-large-v3", stroke="#A855F7", badge="AI")
    svg += node_box(652, 178, 268, 60, "Tenant PostgreSQL", "Calls, logs, PBKDF2 PINs, orders", stroke="#10B981", badge="DB")
    svg += node_box(652, 260, 268, 60, "Google Sheets Worker", "Idempotent writeback mirror", stroke="#14B8A6", badge="SYNC")
    svg += node_box(652, 340, 268, 60, "Amazon Polly / Edge TTS", "Neural en-GB voice synthesis", stroke="#F43F5E", badge="TTS")

    # Connections
    svg += connection(159, 156, 159, 178, "Inbound", color="#38BDF8")
    svg += connection(159, 238, 159, 260, "Capture", color="#0EA5E9")
    svg += curve_connection("M 280 289 C 305 289, 305 129, 326 129", "Transcript", 305, 205, color="#38BDF8")
    svg += connection(465, 160, 465, 180, "Signed Turn", color="#F59E0B")
    svg += connection(465, 242, 465, 262, "Verified", color="#818CF8")
    svg += connection(465, 324, 465, 344, "Filter", color="#10B981")
    svg += connection(604, 280, 652, 128, "Prompt / STT", color="#A855F7")
    svg += connection(604, 295, 652, 208, "Tool Query", color="#10B981")
    svg += connection(786, 238, 786, 260, "Mirror", color="#14B8A6")
    svg += curve_connection("M 465 398 C 465 425, 786 425, 786 400", "Allow-listed text", 625, 425, color="#10B981")
    svg += curve_connection("M 652 370 C 290 410, 285 220, 280 208", "Spoken Audio", 295, 265, color="#F43F5E")

    svg += "</svg>"
    return svg

# -------------------------------------------------------------
# 2. 02-state-machine.svg (Compact 960x420)
# -------------------------------------------------------------
def build_svg_02():
    svg = make_card(960, 420, "VoxFlow Voice Call State Machine", "Multi-Factor Identity, Deterministic Routing, Confirmation Gates & Safe Escalation")
    
    # 4 Steps Top Row
    svg += node_box(30, 80, 205, 74, "1. Inbound Call", "DID exact routing\nRecording disclosure", stroke="#38BDF8", badge="INIT")
    svg += node_box(265, 80, 205, 74, "2. Caller 2FA Identity", "Account + 1 factor\nMax 2 attempts limit", stroke="#0284C7", badge="2FA")
    svg += node_box(500, 80, 205, 74, "3. Intent Routing", "Slot & reference parse\nBounded tool surface", stroke="#818CF8", badge="ROUTER")
    svg += node_box(735, 80, 195, 74, "4. Policy Gate", "Read: Authorized\nWrite: Gate required", stroke="#F59E0B", badge="GATE")

    # Middle Row: Gating & Execution
    svg += node_box(30, 205, 215, 74, "High-Impact PIN Gate", "4-8 digit caller PIN\nPBKDF2-HMAC-SHA256", stroke="#F59E0B", badge="PIN")
    svg += node_box(275, 205, 225, 74, "Confirmation Gate", "Explicit verbal yes\nBound to args hash", stroke="#10B981", badge="CONFIRM")
    svg += node_box(530, 205, 225, 74, "Tool Execution", "Scoped tenant query\nStrict result check", stroke="#10B981", badge="EXEC")
    svg += node_box(785, 205, 145, 74, "Idempotency", "Deduplicate key\nReplay on match", stroke="#F59E0B", badge="IDEM")

    # Bottom Row: Outcomes
    svg += node_box(30, 325, 270, 72, "Grounded Spoken Output", "Speak allow-listed fields only\nAnti-hallucination lexical filter", stroke="#10B981", badge="SUCCESS")
    svg += node_box(330, 325, 270, 72, "Safe Call Closure", "Zero-lost-turn state committed\nSummary written to tenant sheet", stroke="#0284C7", badge="EXIT")
    svg += node_box(630, 325, 300, 72, "Deterministic Escalation", "Fixed escalation script played\nStructured callback ticket enqueued", stroke="#F43F5E", badge="ESCALATE")

    # Connections
    svg += connection(235, 117, 265, 117, "Turn 1", color="#38BDF8")
    svg += connection(470, 117, 500, 117, "Verified", color="#0284C7")
    svg += connection(705, 117, 735, 117, "Parsed", color="#818CF8")

    svg += curve_connection("M 832 154 C 832 185, 642 185, 642 205", "Read", 737, 185, color="#10B981")
    svg += curve_connection("M 800 154 C 800 185, 387 185, 387 205", "Write", 580, 185, color="#34D399")
    svg += curve_connection("M 760 154 C 760 185, 137 185, 137 205", "High-Impact (PO)", 350, 185, color="#F59E0B")

    svg += connection(245, 242, 275, 242, "PIN OK", color="#10B981")
    svg += connection(500, 242, 530, 242, "Confirmed", color="#10B981")
    svg += connection(755, 242, 785, 242, "Check", color="#F59E0B")

    svg += curve_connection("M 642 279 C 642 305, 165 305, 165 325", "Schema Valid", 400, 305, color="#10B981")
    svg += connection(300, 361, 330, 361, "Speak", color="#10B981")
    svg += curve_connection("M 642 279 C 642 305, 780 305, 780 325", "Timeout / Error", 711, 305, color="#F43F5E", marker="url(#arrowRose)")
    svg += connection(630, 361, 600, 361, "Log & End", color="#F59E0B", marker="url(#arrowAmber)")

    svg += "</svg>"
    return svg

# -------------------------------------------------------------
# 3. 03-tool-approval-boundary.svg (Compact 960x420)
# -------------------------------------------------------------
def build_svg_03():
    svg = make_card(960, 420, "VoxFlow Tool Authorization & Approval Boundary", "Zero-Trust Execution: Schema Validation, Identity Scoping, Confirmation & Idempotency")
    
    # Left Input (3 steps)
    svg += node_box(30, 80, 215, 66, "1. Caller Speech", "Untrusted spoken audio\nTranscript extraction", stroke="#38BDF8", badge="INPUT")
    svg += node_box(30, 175, 215, 66, "2. Schema Validator", "Deterministic intent + args\nReject unexpected keys", stroke="#0284C7", badge="VALIDATE")
    svg += node_box(30, 270, 215, 66, "3. Identity Scoping", "Check session factor binding\nExact supplier_id match", stroke="#818CF8", badge="AUTH")

    # Center: Tool Tiers
    svg += group_box(275, 70, 360, 335, "Tool Classification & Approval Gates", stroke="#6366F1", title_color="#818CF8")
    svg += node_box(290, 95, 330, 58, "Tier 1: Read-Only Tools", "check_stock · get_order_status", stroke="#10B981", badge="READ")
    svg += node_box(290, 168, 330, 68, "Tier 2: Reversible Writes", "book_delivery_slot · update_status\nRequires explicit yes + arg hash match", stroke="#38BDF8", badge="CONFIRM")
    svg += node_box(290, 250, 330, 72, "Tier 3: High-Impact Writes", "create_po · update_critical_record\nRequires PBKDF2 PIN + Confirmation", stroke="#F59E0B", badge="PIN+CONFIRM")
    svg += node_box(290, 334, 330, 56, "Tier 4: Prohibited Actions", "issue_refund · arbitrary commands", stroke="#F43F5E", badge="BLOCKED")

    # Right: Idempotency & Grounded Execution
    svg += node_box(665, 95, 265, 68, "4. Idempotency Check", "Deduplicate repeated requests\nReturn cached result on hit", stroke="#F59E0B", badge="IDEMPOTENT")
    svg += node_box(665, 195, 265, 68, "5. Scoped DB Execution", "Explicit tenant_id filter\nAtomic transaction commit", stroke="#10B981", badge="EXEC")
    svg += node_box(665, 295, 265, 78, "6. Spoken Fact Grounding", "Validate result payload schema\nSpeak allow-listed fields only", stroke="#10B981", badge="GROUNDED")

    # Connections
    svg += connection(137, 146, 137, 175, "Turn", color="#38BDF8")
    svg += connection(137, 241, 137, 270, "Valid", color="#0284C7")
    svg += curve_connection("M 245 303 C 265 303, 265 124, 290 124", "Read", 265, 210, color="#10B981")
    svg += curve_connection("M 245 303 C 265 303, 265 202, 290 202", "Write", 265, 252, color="#38BDF8")
    svg += connection(245, 303, 290, 286, "Critical", color="#F59E0B")
    svg += curve_connection("M 245 303 C 265 303, 265 362, 290 362", "Forbidden", 265, 332, color="#F43F5E", marker="url(#arrowRose)")

    svg += curve_connection("M 620 124 C 642 124, 642 229, 665 229", "Direct Read", 642, 176, color="#10B981")
    svg += connection(620, 202, 665, 129, "Key Check", color="#F59E0B")
    svg += connection(620, 286, 665, 129, "Key Check", color="#F59E0B")
    svg += connection(797, 163, 797, 195, "New Key", color="#10B981")
    svg += connection(797, 263, 797, 295, "Valid Data", color="#10B981")

    svg += "</svg>"
    return svg

# -------------------------------------------------------------
# 4. 04-failure-escalation.svg (Compact 960x390)
# -------------------------------------------------------------
def build_svg_04():
    svg = make_card(960, 390, "VoxFlow Failure Modes & Escalation Architecture", "Fail-Closed Safety: Turn Deadlines, Tool Timeouts, Schema Rejections & Callback Queuing")
    
    # Left Input
    svg += node_box(30, 80, 215, 68, "Caller Turn Inbound", "Transcript received from bridge\nTurn timer starts (0 ms)", stroke="#38BDF8", badge="TURN")
    svg += node_box(30, 175, 215, 72, "Turn Deadline Guard", "Strict 6.0s hard deadline\nFail closed if delayed", stroke="#F59E0B", badge="SLA 6.0s")
    svg += node_box(30, 275, 215, 68, "Tool Dispatch", "Execute query or mutation\nMonitor runtime health", stroke="#818CF8", badge="RUNNER")

    # Center Failure Types
    svg += group_box(275, 70, 345, 300, "Failure Mode Classifiers", stroke="#F43F5E", title_color="#F87171")
    svg += node_box(290, 95, 315, 54, "Tool Timeout / Network Failure", "No record received within window", stroke="#F87171", badge="TIMEOUT")
    svg += node_box(290, 162, 315, 54, "Malformed / Missing Record", "Result missing required fact fields", stroke="#F87171", badge="SCHEMA")
    svg += node_box(290, 228, 315, 54, "Prompt Injection Detected", "Instruction text in speech / sheet", stroke="#F59E0B", badge="INJECTION")
    svg += node_box(290, 295, 315, 60, "Authentication Lockout", "2 failed factors or 2 wrong PINs", stroke="#F43F5E", badge="LOCKOUT")

    # Right Escalation Outcomes
    svg += node_box(650, 95, 280, 78, "Fixed Escalation Script", "\"I can't confirm that from live records right now. I've raised it with our ops team.\"", stroke="#F87171", badge="HONEST SCRIPT")
    svg += node_box(650, 195, 280, 68, "Human Callback Ticket", "Enqueue callback ticket in Postgres\nInclude call summary & reason", stroke="#F59E0B", badge="TICKET")
    svg += node_box(650, 285, 280, 68, "Graceful Call Closure", "Safe termination of voice turn\nZero hallucinated status spoken", stroke="#10B981", badge="SAFE EXIT")

    # Connections
    svg += connection(137, 148, 137, 175, "Active", color="#38BDF8")
    svg += connection(137, 247, 137, 275, "< 6.0s", color="#10B981")
    svg += curve_connection("M 245 211 C 450 211, 450 134, 650 134", "> 6.0s SLA Exceeded", 450, 172, color="#F43F5E", marker="url(#arrowRose)")

    svg += connection(245, 309, 290, 122, "Timeout", color="#F87171", marker="url(#arrowRose)")
    svg += connection(245, 309, 290, 189, "Invalid", color="#F87171", marker="url(#arrowRose)")
    svg += connection(245, 309, 290, 255, "Flagged", color="#F59E0B", marker="url(#arrowAmber)")
    svg += connection(245, 309, 290, 325, "Exceeded", color="#F87171", marker="url(#arrowRose)")

    svg += connection(605, 122, 650, 134, "Script", color="#F87171", marker="url(#arrowRose)")
    svg += connection(790, 173, 790, 195, "Log Event", color="#F59E0B")
    svg += connection(790, 263, 790, 285, "Finalize", color="#10B981")

    svg += "</svg>"
    return svg

# -------------------------------------------------------------
# 5. 05-data-lifecycle.svg (Compact 960x390)
# -------------------------------------------------------------
def build_svg_05():
    svg = make_card(960, 390, "VoxFlow Multi-Tenant Data Lifecycle & Storage", "In-Flight Audio Processing, Structured Postgres Persistence & Async Sheet Mirroring")
    
    svg += group_box(24, 70, 215, 300, "1. Audio Ingress", stroke="#0284C7", title_color="#38BDF8")
    svg += group_box(255, 70, 220, 300, "2. Cloud Services", stroke="#818CF8", title_color="#818CF8")
    svg += group_box(490, 70, 225, 300, "3. Core Persistence", stroke="#10B981", title_color="#34D399")
    svg += group_box(730, 70, 205, 300, "4. Mirror & Purge", stroke="#F59E0B", title_color="#FBBF24")

    # Column 1
    svg += node_box(38, 100, 185, 68, "PSTN Stream", "Amazon Connect\neu-west-2 Ingress", stroke="#38BDF8", badge="PSTN")
    svg += node_box(38, 190, 185, 68, "Ephemeral Buffer", "Turn audio buffer\nIn-memory only", stroke="#0EA5E9", badge="MEMORY")
    svg += node_box(38, 280, 185, 68, "Browser PCM", "16 kHz Web Audio\nSimulator test input", stroke="#64748B", badge="TEST")

    # Column 2
    svg += node_box(270, 100, 190, 68, "Amazon Lex V2", "Speech-to-Text en-GB\nContact flow bridge", stroke="#818CF8", badge="STT")
    svg += node_box(270, 190, 190, 68, "Groq LLM Engine", "FastAPI AgentRunner\ngpt-oss-20b reasoning", stroke="#A855F7", badge="LLM")
    svg += node_box(270, 280, 190, 68, "Amazon Polly", "Neural en-GB TTS\nAudio playback", stroke="#F43F5E", badge="TTS")

    # Column 3
    svg += node_box(505, 100, 195, 68, "Postgres: calls", "Call sessions, DID,\nlatencies, outcomes", stroke="#10B981", badge="DB")
    svg += node_box(505, 190, 195, 68, "Postgres: audit", "Tool execution audit,\nconfirmations, args hash", stroke="#10B981", badge="AUDIT")
    svg += node_box(505, 280, 195, 68, "Postgres: escalations", "Priority queue,\ncallback ticket data", stroke="#F59E0B", badge="QUEUE")

    # Column 4
    svg += node_box(745, 100, 175, 68, "Google Sheets", "Per-tenant mirror\nAsync worker sync", stroke="#14B8A6", badge="SHEETS")
    svg += node_box(745, 190, 175, 68, "Telemetry Log", "Sanitized metrics\nNo PII or audio", stroke="#6366F1", badge="METRICS")
    svg += node_box(745, 280, 175, 68, "Retention Purge", "Scheduled turn purge\nGDPR data cleanup", stroke="#F87171", badge="PURGE")

    # Connections
    svg += connection(223, 134, 270, 134, "Audio", color="#38BDF8")
    svg += connection(365, 168, 365, 190, "Text", color="#818CF8")
    svg += connection(365, 258, 365, 280, "Reply", color="#A855F7")

    svg += connection(460, 215, 505, 134, "Log Turn", color="#10B981")
    svg += connection(460, 224, 505, 224, "Audit", color="#10B981")
    svg += connection(460, 233, 505, 314, "Escalate", color="#F59E0B")

    svg += connection(700, 134, 745, 134, "Mirror", color="#14B8A6")
    svg += connection(700, 224, 745, 224, "Export", color="#6366F1")
    svg += connection(700, 314, 745, 314, "Purge", color="#F87171")

    svg += "</svg>"
    return svg

# -------------------------------------------------------------
# 6. 06-trust-boundaries.svg (Compact 960x420)
# -------------------------------------------------------------
def build_svg_06():
    svg = make_card(960, 420, "VoxFlow Multi-Tenant Trust & Isolation Boundaries", "Exact-DID Inbound Routing, HMAC Signed Bridge & Zero Cross-Tenant Data Leakage")
    
    # Ingress / Edge Layer
    svg += group_box(24, 68, 912, 78, "Untrusted Public Internet & Ingress Edge Layer", stroke="#0284C7", title_color="#38BDF8")
    svg += node_box(38, 88, 260, 48, "Inbound PSTN Caller", "Calls Depot UK DID (+44 20...)", stroke="#38BDF8", badge="PSTN")
    svg += node_box(348, 88, 270, 48, "AWS Lambda Bridge", "HMAC-SHA256 turn authentication", stroke="#F59E0B", badge="HMAC")
    svg += node_box(668, 88, 250, 48, "Exact-DID Route Gate", "Strict tenant_id resolution", stroke="#10B981", badge="GATE")

    # Connections top
    svg += connection(298, 112, 348, 112, "Voice Call", color="#38BDF8")
    svg += connection(618, 112, 668, 112, "Signed Turn", color="#F59E0B")

    # Tenant A Boundary (Left)
    svg += group_box(24, 168, 435, 235, "Tenant A Boundary (Apex Depot)", stroke="#10B981", title_color="#34D399")
    svg += node_box(38, 196, 405, 54, "Session A (tenant_id = 'apex-depot')", "Scoped caller identity & PIN binding", stroke="#10B981", badge="SESSION A")
    svg += node_box(38, 266, 405, 62, "Scoped Tool Execution A", "Queries: WHERE tenant_id = 'apex-depot'\nInventory, orders, slots strictly isolated", stroke="#10B981", badge="TOOLS A")
    svg += node_box(38, 342, 405, 50, "Tenant A Mirror (Google Sheets A)", "Dedicated spreadsheet writeback", stroke="#14B8A6", badge="SHEETS A")

    # Tenant B Boundary (Right)
    svg += group_box(501, 168, 435, 235, "Tenant B Boundary (Beacon Depot)", stroke="#818CF8", title_color="#818CF8")
    svg += node_box(515, 196, 405, 54, "Session B (tenant_id = 'beacon-depot')", "Scoped caller identity & PIN binding", stroke="#818CF8", badge="SESSION B")
    svg += node_box(515, 266, 405, 62, "Scoped Tool Execution B", "Queries: WHERE tenant_id = 'beacon-depot'\nInventory, orders, slots strictly isolated", stroke="#818CF8", badge="TOOLS B")
    svg += node_box(515, 342, 405, 50, "Tenant B Mirror (Google Sheets B)", "Dedicated spreadsheet writeback", stroke="#818CF8", badge="SHEETS B")

    # Router to Tenants
    svg += curve_connection("M 725 136 C 725 170, 240 170, 240 196", "Route to DID A", 450, 166, color="#10B981")
    svg += curve_connection("M 860 136 C 860 170, 717 170, 717 196", "Route to DID B", 790, 166, color="#818CF8")

    # Internal Tenant Flows
    svg += connection(240, 250, 240, 266, "Execute", color="#10B981")
    svg += connection(240, 328, 240, 342, "Mirror", color="#14B8A6")

    svg += connection(717, 250, 717, 266, "Execute", color="#818CF8")
    svg += connection(717, 328, 717, 342, "Mirror", color="#818CF8")

    # Isolation Firewall Line
    svg += """
  <line x1="480" y1="168" x2="480" y2="403" stroke="#F43F5E" stroke-width="2" stroke-dasharray="5,3" />
  <rect x="425" y="275" width="110" height="22" rx="11" fill="#0B132B" stroke="#F43F5E" stroke-width="1.2" />
  <text x="480" y="289.5" font-family="system-ui, sans-serif" font-size="9" font-weight="700" fill="#F87171" text-anchor="middle">NO CROSS-LEAK</text>
"""

    svg += "</svg>"
    return svg

def main():
    generators = [
        ("01-voice-pipeline.svg", build_svg_01),
        ("02-state-machine.svg", build_svg_02),
        ("03-tool-approval-boundary.svg", build_svg_03),
        ("04-failure-escalation.svg", build_svg_04),
        ("05-data-lifecycle.svg", build_svg_05),
        ("06-trust-boundaries.svg", build_svg_06),
    ]
    for filename, func in generators:
        path = DIAGRAMS_DIR / filename
        content = func()
        path.write_text(content, encoding="utf-8")
        
        # Verify XML validity immediately!
        try:
            ET.fromstring(content)
            print(f"Generated {filename} ({len(content)} bytes) -> XML VALID")
        except Exception as e:
            print(f"Generated {filename} -> XML ERROR: {e}")
            raise

if __name__ == "__main__":
    main()
