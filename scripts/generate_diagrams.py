#!/usr/bin/env python3
"""Generate high-contrast, professional, responsive SVG architecture diagrams
for the VoxFlow Case Study.

Features:
- Self-contained dark-mode card styling (#0B132B / #0F172A)
- 100% visible across GitHub Dark and Light themes
- High-contrast typography (system fonts, bold labels, readable subtext)
- Proportional viewBox (960px width, matching GitHub document columns)
- Distinct enterprise color palette (Sky Blue, Emerald, Indigo, Amber, Rose)
"""

from pathlib import Path

DIAGRAMS_DIR = Path(__file__).resolve().parents[1] / "diagrams"

def make_card(w, h, title, subtitle):
    return f"""<svg width="100%" height="100%" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="headerGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#0284C7" />
      <stop offset="50%" stop-color="#6366F1" />
      <stop offset="100%" stop-color="#10B981" />
    </linearGradient>
    <linearGradient id="cardGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#1E293B" />
      <stop offset="100%" stop-color="#0F172A" />
    </linearGradient>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="115%">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000000" flood-opacity="0.35" />
    </filter>
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
  <rect x="2" y="2" width="{w - 4}" height="{h - 4}" rx="14" fill="#0B132B" stroke="#334155" stroke-width="2" />
  <rect x="2" y="2" width="{w - 4}" height="6" rx="3" fill="url(#headerGrad)" />

  <!-- Header Section -->
  <g transform="translate(30, 36)">
    <circle cx="12" cy="12" r="12" fill="#0284C7" />
    <path d="M 7 12 L 11 16 L 17 8" stroke="#FFFFFF" stroke-width="2.5" fill="none" stroke-linecap="round" />
    <text x="34" y="14" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="17" font-weight="700" fill="#F8FAFC">{title}</text>
    <text x="34" y="32" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="12" font-weight="500" fill="#94A3B8">{subtitle}</text>
  </g>
"""

def node_box(x, y, w, h, title, subtitle, stroke="#38BDF8", fill="#1E293B", badge=""):
    badge_markup = ""
    if badge:
        badge_markup = f"""
    <rect x="{x + w - 75}" y="{y + 8}" width="65" height="18" rx="9" fill="{stroke}" fill-opacity="0.2" stroke="{stroke}" stroke-width="1" />
    <text x="{x + w - 42.5}" y="{y + 20}" font-family="system-ui, sans-serif" font-size="9" font-weight="700" fill="{stroke}" text-anchor="middle">{badge}</text>"""

    return f"""
  <!-- Node: {title} -->
  <g filter="url(#shadow)">
    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1.8" />
    {badge_markup}
    <text x="{x + 16}" y="{y + 24}" font-family="system-ui, sans-serif" font-size="13.5" font-weight="700" fill="#F8FAFC">{title}</text>
    <text x="{x + 16}" y="{y + 44}" font-family="system-ui, sans-serif" font-size="11" font-weight="500" fill="#94A3B8">{subtitle}</text>
  </g>"""

def group_box(x, y, w, h, title, stroke="#334155", fill="#0F172A", title_color="#38BDF8"):
    return f"""
  <!-- Group: {title} -->
  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="1.2" stroke-dasharray="4,4" />
  <text x="{x + 16}" y="{y + 20}" font-family="system-ui, sans-serif" font-size="11.5" font-weight="700" fill="{title_color}" letter-spacing="0.5">{title.upper()}</text>
"""

def connection(x1, y1, x2, y2, label="", color="#38BDF8", marker="url(#arrow)", dash=""):
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    label_markup = ""
    if label:
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        label_w = len(label) * 6.5 + 16
        label_markup = f"""
    <rect x="{mid_x - label_w/2}" y="{mid_y - 10}" width="{label_w}" height="20" rx="6" fill="#0B132B" stroke="{color}" stroke-width="1" />
    <text x="{mid_x}" y="{mid_y + 3.5}" font-family="system-ui, sans-serif" font-size="10" font-weight="600" fill="#F8FAFC" text-anchor="middle">{label}</text>"""

    return f"""
  <path d="M {x1} {y1} L {x2} {y2}" stroke="{color}" stroke-width="1.8"{dash_attr} fill="none" marker-end="{marker}" />
  {label_markup}"""

def curve_connection(d, label="", mid_x=0, mid_y=0, color="#38BDF8", marker="url(#arrow)", dash=""):
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    label_markup = ""
    if label and mid_x and mid_y:
        label_w = len(label) * 6.5 + 16
        label_markup = f"""
    <rect x="{mid_x - label_w/2}" y="{mid_y - 10}" width="{label_w}" height="20" rx="6" fill="#0B132B" stroke="{color}" stroke-width="1" />
    <text x="{mid_x}" y="{mid_y + 3.5}" font-family="system-ui, sans-serif" font-size="10" font-weight="600" fill="#F8FAFC" text-anchor="middle">{label}</text>"""

    return f"""
  <path d="{d}" stroke="{color}" stroke-width="1.8"{dash_attr} fill="none" marker-end="{marker}" />
  {label_markup}"""

# -------------------------------------------------------------
# 1. 01-voice-pipeline.svg
# -------------------------------------------------------------
def build_svg_01():
    svg = make_card(960, 520, "VoxFlow Voice Pipeline Architecture", "Inbound PSTN via Amazon Connect & Browser Audio Simulator Paths (London eu-west-2)")
    
    # Groups
    svg += group_box(30, 80, 260, 410, "1. Inbound Telephony Layer", stroke="#0284C7", title_color="#38BDF8")
    svg += group_box(310, 80, 310, 410, "2. Security & Agent Gateway", stroke="#6366F1", title_color="#818CF8")
    svg += group_box(640, 80, 290, 410, "3. Intelligence & Persistence", stroke="#10B981", title_color="#34D399")

    # Column 1: Telephony
    svg += node_box(50, 115, 220, 60, "PSTN Caller (UK)", "Supplier / driver on UK DID", stroke="#38BDF8", badge="PSTN")
    svg += node_box(50, 215, 220, 65, "Amazon Connect", "Contact flow · en-GB · eu-west-2", stroke="#0284C7", badge="AWS")
    svg += node_box(50, 315, 220, 60, "Amazon Lex V2", "en-GB Speech Recognition (STT)", stroke="#0EA5E9", badge="STT")
    svg += node_box(50, 415, 220, 60, "Browser Simulator", "PCM 16 kHz Web Audio client", stroke="#64748B", badge="TEST")

    # Column 2: Security & Agent Gateway
    svg += node_box(330, 115, 270, 70, "AWS Lambda Bridge", "HMAC-SHA256 signature + timestamp", stroke="#F59E0B", badge="AUTH")
    svg += node_box(330, 220, 270, 70, "Replay Ledger & Route Gate", "Redis SET NX EX 300s · Exact DID match", stroke="#818CF8", badge="GUARD")
    svg += node_box(330, 325, 270, 70, "FastAPI Voice Engine", "AgentRunner · Session state machine", stroke="#6366F1", badge="CORE")
    svg += node_box(330, 420, 270, 55, "Spoken Grounding Guard", "Refuses unbacked status claims", stroke="#10B981", badge="SAFETY")

    # Column 3: Intelligence & Persistence
    svg += node_box(660, 115, 250, 65, "Groq Cloud LLM / STT", "gpt-oss-20b · Whisper-large-v3", stroke="#A855F7", badge="AI")
    svg += node_box(660, 215, 250, 65, "Tenant PostgreSQL", "Calls, logs, PBKDF2 PINs, orders", stroke="#10B981", badge="DB")
    svg += node_box(660, 315, 250, 65, "Google Sheets Worker", "Idempotent writeback mirror", stroke="#14B8A6", badge="SYNC")
    svg += node_box(660, 415, 250, 65, "Amazon Polly / Edge TTS", "Neural en-GB voice synthesis", stroke="#F43F5E", badge="TTS")

    # Connections
    svg += connection(160, 175, 160, 215, "Inbound", color="#38BDF8")
    svg += connection(160, 280, 160, 315, "Capture", color="#0EA5E9")
    svg += curve_connection("M 270 345 C 300 345, 300 150, 330 150", "Transcript", 300, 230, color="#38BDF8")
    svg += connection(465, 185, 465, 220, "Signed Turn", color="#F59E0B")
    svg += connection(465, 290, 465, 325, "Verified", color="#818CF8")
    svg += connection(465, 395, 465, 420, "Filter", color="#10B981")
    svg += connection(600, 345, 660, 150, "Prompt / STT", color="#A855F7")
    svg += connection(600, 360, 660, 250, "Tool Query", color="#10B981")
    svg += connection(785, 280, 785, 315, "Mirror", color="#14B8A6")
    svg += curve_connection("M 465 475 C 465 500, 785 500, 785 480", "Allow-listed text", 625, 500, color="#10B981")
    svg += curve_connection("M 660 445 C 290 470, 280 260, 270 250", "Spoken Audio", 290, 300, color="#F43F5E")
    svg += connection(160, 215, 160, 175, "Speech to Caller", color="#F43F5E")

    svg += "</svg>"
    return svg

# -------------------------------------------------------------
# 2. 02-state-machine.svg
# -------------------------------------------------------------
def build_svg_02():
    svg = make_card(960, 560, "VoxFlow Voice Call State Machine", "Multi-Factor Identity, Deterministic Routing, Confirmation Gates & Safe Escalation")
    
    # 5 Main Steps Across
    svg += node_box(40, 100, 160, 80, "1. Inbound Call", "DID Routing\nRecording notice", stroke="#38BDF8", badge="INIT")
    svg += node_box(240, 100, 180, 80, "2. Identity Verification", "Account + 1 factor\nMax 2 attempts", stroke="#0284C7", badge="2FA")
    svg += node_box(460, 100, 180, 80, "3. Intent Detection", "Slot & reference extraction\nBounded tool intent", stroke="#818CF8", badge="ROUTER")
    svg += node_box(680, 100, 240, 80, "4. Policy & Security Gate", "Read: Authorized\nWrite: Confirmation / PIN", stroke="#F59E0B", badge="GATE")

    # Lower Tier: Tool Execution, Grounding, Escalation, Closure
    svg += node_box(40, 260, 240, 80, "High-Impact PIN Gate", "4-8 digit caller PIN\nPBKDF2-HMAC-SHA256", stroke="#F59E0B", badge="PIN")
    svg += node_box(320, 260, 260, 80, "Explicit Confirmation Gate", "Yes/No bound to exact args hash\nIdempotency deduplication", stroke="#10B981", badge="WRITE")
    svg += node_box(620, 260, 300, 80, "5. Tool Execution & Validation", "Execute scoped tool\nStrict result schema check", stroke="#10B981", badge="EXEC")

    svg += node_box(40, 420, 280, 90, "6A. Grounded Spoken Output", "Speak allow-listed tool facts only\nAnti-hallucination lexical filter", stroke="#10B981", badge="SUCCESS")
    svg += node_box(360, 420, 280, 90, "6B. Graceful Escalation", "Fixed escalation script\nNever invent status or ETAs", stroke="#F43F5E", badge="ESCALATE")
    svg += node_box(680, 420, 240, 90, "7. Call Closure & Ledger", "Callback ticket in Postgres\nStructured call summary to Sheet", stroke="#64748B", badge="LOG")

    # Connections
    svg += connection(200, 140, 240, 140, "Turn 1", color="#38BDF8")
    svg += connection(420, 140, 460, 140, "Verified", color="#0284C7")
    svg += connection(640, 140, 680, 140, "Matched", color="#818CF8")

    # Routing from Policy Gate
    svg += curve_connection("M 780 180 C 780 220, 780 220, 780 260", "Read Tool", 780, 220, color="#10B981")
    svg += curve_connection("M 720 180 C 720 220, 450 220, 450 260", "Write Tool", 580, 220, color="#34D399")
    svg += curve_connection("M 700 180 C 700 210, 160 210, 160 260", "High Impact (PO)", 350, 210, color="#F59E0B")

    # PIN to Confirmation
    svg += connection(280, 300, 320, 300, "PIN OK", color="#10B981")
    svg += connection(580, 300, 620, 300, "Confirmed", color="#10B981")

    # Tool outcomes
    svg += curve_connection("M 700 340 C 700 380, 180 380, 180 420", "Schema Valid", 440, 380, color="#10B981")
    svg += connection(770, 340, 500, 420, "Timeout / Error", color="#F43F5E", marker="url(#arrowRose)")

    # Escalation trigger from 2FA
    svg += curve_connection("M 330 180 C 330 230, 20 230, 20 465 L 360 465", "2 Mismatches", 150, 240, color="#F43F5E", marker="url(#arrowRose)", dash="4,4")

    # Final to Closure
    svg += connection(320, 465, 680, 465, "Resolved", color="#10B981")
    svg += connection(640, 465, 680, 465, "Callback Raised", color="#F43F5E")

    svg += "</svg>"
    return svg

# -------------------------------------------------------------
# 3. 03-tool-approval-boundary.svg
# -------------------------------------------------------------
def build_svg_03():
    svg = make_card(960, 540, "VoxFlow Tool Authorization & Approval Boundary", "Zero-Trust Execution: Schema Validation, Identity Scoping, Confirmation & Idempotency")
    
    # Left Input
    svg += node_box(40, 120, 220, 70, "1. Caller Speech", "Untrusted spoken audio\nTranscript extraction", stroke="#38BDF8", badge="INPUT")
    svg += node_box(40, 230, 220, 70, "2. Schema Validator", "Deterministic intent + args\nReject unexpected keys", stroke="#0284C7", badge="VALIDATE")
    svg += node_box(40, 340, 220, 70, "3. Identity Scoping", "Check session factor binding\nExact supplier_id match", stroke="#818CF8", badge="AUTH")

    # Center: Tool Tiers
    svg += group_box(300, 100, 340, 390, "Tool Classification & Approval Gates", stroke="#6366F1", title_color="#818CF8")
    svg += node_box(320, 130, 300, 65, "Tier 1: Read-Only Tools", "check_stock · get_order_status\nRequires verified session identity", stroke="#10B981", badge="READ")
    svg += node_box(320, 215, 300, 75, "Tier 2: Reversible Writes", "book_delivery_slot · update_status\nRequires explicit yes + arg hash match", stroke="#38BDF8", badge="CONFIRM")
    svg += node_box(320, 310, 300, 80, "Tier 3: High-Impact Writes", "create_po · update_critical_record\nRequires PBKDF2 PIN + Confirmation", stroke="#F59E0B", badge="PIN+CONFIRM")
    svg += node_box(320, 410, 300, 60, "Tier 4: Prohibited Actions", "issue_refund · arbitrary shell/code\nHard-blocked; never executed", stroke="#F43F5E", badge="BLOCKED")

    # Right: Idempotency & Grounded Execution
    svg += node_box(680, 150, 240, 75, "4. Idempotency Check", "Deduplicate repeated requests\nReturn cached result on hit", stroke="#F59E0B", badge="IDEMPOTENT")
    svg += node_box(680, 260, 240, 75, "5. Scoped DB Execution", "Explicit tenant_id filter\nAtomic transaction commit", stroke="#10B981", badge="EXEC")
    svg += node_box(680, 370, 240, 85, "6. Spoken Fact Grounding", "Validate result payload schema\nSpeak allow-listed fields only", stroke="#10B981", badge="GROUNDED")

    # Connections
    svg += connection(150, 190, 150, 230, "Turn", color="#38BDF8")
    svg += connection(150, 300, 150, 340, "Valid", color="#0284C7")
    svg += curve_connection("M 260 375 C 290 375, 290 160, 320 160", "Read", 290, 240, color="#10B981")
    svg += curve_connection("M 260 375 C 290 375, 290 250, 320 250", "Write", 290, 310, color="#38BDF8")
    svg += connection(260, 375, 320, 350, "Critical", color="#F59E0B")
    svg += curve_connection("M 260 375 C 290 375, 290 440, 320 440", "Forbidden", 290, 420, color="#F43F5E", marker="url(#arrowRose)")

    svg += curve_connection("M 620 160 C 650 160, 650 280, 680 280", "Direct Read", 650, 210, color="#10B981")
    svg += connection(620, 250, 680, 185, "Key Check", color="#F59E0B")
    svg += connection(620, 350, 680, 185, "Key Check", color="#F59E0B")
    svg += connection(800, 225, 800, 260, "New Key", color="#10B981")
    svg += connection(800, 335, 800, 370, "Valid Data", color="#10B981")

    svg += "</svg>"
    return svg

# -------------------------------------------------------------
# 4. 04-failure-escalation.svg
# -------------------------------------------------------------
def build_svg_04():
    svg = make_card(960, 480, "VoxFlow Failure Modes & Escalation Architecture", "Fail-Closed Safety: Turn Deadlines, Tool Timeouts, Schema Rejections & Callback Queuing")
    
    # Left Input
    svg += node_box(40, 120, 220, 75, "Caller Turn Inbound", "Transcript received from bridge\nTurn timer starts (0 ms)", stroke="#38BDF8", badge="TURN")
    svg += node_box(40, 250, 220, 80, "Turn Deadline Guard", "Strict 6.0s hard deadline\nFail closed if delayed", stroke="#F59E0B", badge="SLA 6.0s")
    svg += node_box(40, 380, 220, 70, "Tool Dispatch", "Execute query or mutation\nMonitor runtime health", stroke="#818CF8", badge="RUNNER")

    # Center Failure Types
    svg += group_box(300, 95, 340, 365, "Failure Mode Classifiers", stroke="#F43F5E", title_color="#F87171")
    svg += node_box(320, 125, 300, 65, "Tool Timeout / Network Failure", "No record received within turn window", stroke="#F87171", badge="TIMEOUT")
    svg += node_box(320, 205, 300, 65, "Malformed / Missing Record", "Result missing required fact schema fields", stroke="#F87171", badge="SCHEMA")
    svg += node_box(320, 285, 300, 65, "Adversarial Injection Detected", "Instruction text in speech or sheet data", stroke="#F59E0B", badge="INJECTION")
    svg += node_box(320, 365, 300, 75, "Authentication / PIN Lockout", "2 failed factor attempts or 2 wrong PINs", stroke="#F43F5E", badge="LOCKOUT")

    # Right Escalation Outcomes
    svg += node_box(680, 140, 240, 90, "Fixed Escalation Script", "\"I can't confirm that from live records right now. I've raised it with our ops team.\"", stroke="#F87171", badge="HONEST SCRIPT")
    svg += node_box(680, 260, 240, 80, "Human Callback Ticket", "Enqueue callback ticket in Postgres\nInclude call summary & reason", stroke="#F59E0B", badge="TICKET")
    svg += node_box(680, 370, 240, 75, "Graceful Call Closure", "Safe termination of voice turn\nZero hallucinated status spoken", stroke="#10B981", badge="SAFE EXIT")

    # Connections
    svg += connection(150, 195, 150, 250, "Turn Active", color="#38BDF8")
    svg += connection(150, 330, 150, 380, "< 6.0s", color="#10B981")
    svg += curve_connection("M 260 280 C 470 280, 470 185, 680 185", "> 6.0s SLA Exceeded", 470, 240, color="#F43F5E", marker="url(#arrowRose)")

    svg += connection(260, 415, 320, 160, "Timeout", color="#F87171", marker="url(#arrowRose)")
    svg += connection(260, 415, 320, 240, "Invalid", color="#F87171", marker="url(#arrowRose)")
    svg += connection(260, 415, 320, 320, "Flagged", color="#F59E0B", marker="url(#arrowAmber)")
    svg += connection(260, 415, 320, 400, "Exceeded", color="#F87171", marker="url(#arrowRose)")

    svg += connection(620, 160, 680, 175, "Speak Script", color="#F87171", marker="url(#arrowRose)")
    svg += connection(620, 240, 680, 175, "Speak Script", color="#F87171", marker="url(#arrowRose)")
    svg += connection(620, 320, 680, 175, "Neutralize", color="#F59E0B", marker="url(#arrowAmber)")
    svg += connection(620, 400, 680, 175, "Lockout", color="#F87171", marker="url(#arrowRose)")

    svg += connection(800, 230, 800, 260, "Log Event", color="#F59E0B")
    svg += connection(800, 340, 800, 370, "Finalize", color="#10B981")

    svg += "</svg>"
    return svg

# -------------------------------------------------------------
# 5. 05-data-lifecycle.svg
# -------------------------------------------------------------
def build_svg_05():
    svg = make_card(960, 500, "VoxFlow Multi-Tenant Data Lifecycle & Storage", "In-Flight Audio Processing, Structured Postgres Persistence & Async Sheet Mirroring")
    
    # 4 Groups Across
    svg += group_box(30, 90, 205, 390, "1. Audio Ingress", stroke="#0284C7", title_color="#38BDF8")
    svg += group_box(250, 90, 220, 390, "2. Cloud Services", stroke="#818CF8", title_color="#818CF8")
    svg += group_box(485, 90, 235, 390, "3. Core Persistence", stroke="#10B981", title_color="#34D399")
    svg += group_box(735, 90, 195, 390, "4. Mirror & Purge", stroke="#F59E0B", title_color="#FBBF24")

    # Column 1
    svg += node_box(45, 130, 175, 75, "PSTN Stream", "Amazon Connect\neu-west-2 Ingress", stroke="#38BDF8", badge="PSTN")
    svg += node_box(45, 240, 175, 80, "Ephemeral Buffer", "Turn audio buffer\nIn-memory only", stroke="#0EA5E9", badge="MEMORY")
    svg += node_box(45, 360, 175, 80, "Browser PCM", "16 kHz Web Audio\nSimulator test input", stroke="#64748B", badge="TEST")

    # Column 2
    svg += node_box(265, 130, 190, 75, "Amazon Lex V2", "Speech-to-Text en-GB\nContact flow bridge", stroke="#818CF8", badge="STT")
    svg += node_box(265, 240, 190, 80, "Groq LLM Engine", "FastAPI AgentRunner\ngpt-oss-20b reasoning", stroke="#A855F7", badge="LLM")
    svg += node_box(265, 360, 190, 80, "Amazon Polly", "Neural en-GB TTS\nAudio playback", stroke="#F43F5E", badge="TTS")

    # Column 3
    svg += node_box(500, 130, 205, 80, "Postgres: calls", "Call sessions, DID,\nlatencies, outcomes", stroke="#10B981", badge="DB")
    svg += node_box(500, 240, 205, 80, "Postgres: audit", "Tool execution audit,\nconfirmations, args hash", stroke="#10B981", badge="AUDIT")
    svg += node_box(500, 360, 205, 80, "Postgres: escalations", "Priority queue,\ncallback ticket summaries", stroke="#F59E0B", badge="QUEUE")

    # Column 4
    svg += node_box(750, 140, 165, 80, "Google Sheets", "Per-tenant mirror\nAsync worker sync", stroke="#14B8A6", badge="SHEETS")
    svg += node_box(750, 260, 165, 80, "Telemetry Log", "Sanitized metrics\nNo PII or audio", stroke="#6366F1", badge="METRICS")
    svg += node_box(750, 370, 165, 80, "Retention Purge", "Scheduled turn purge\nGDPR data cleanup", stroke="#F87171", badge="PURGE")

    # Connections
    svg += connection(220, 165, 265, 165, "Audio", color="#38BDF8")
    svg += connection(360, 205, 360, 240, "Transcript", color="#818CF8")
    svg += connection(360, 320, 360, 360, "Speech Text", color="#A855F7")

    svg += connection(455, 270, 500, 170, "Log Turn", color="#10B981")
    svg += connection(455, 280, 500, 280, "Audit Event", color="#10B981")
    svg += connection(455, 290, 500, 390, "Escalate", color="#F59E0B")

    svg += connection(705, 170, 750, 175, "Mirror", color="#14B8A6")
    svg += connection(705, 280, 750, 295, "Export", color="#6366F1")
    svg += connection(705, 400, 750, 405, "Purge", color="#F87171")

    svg += "</svg>"
    return svg

# -------------------------------------------------------------
# 6. 06-trust-boundaries.svg
# -------------------------------------------------------------
def build_svg_06():
    svg = make_card(960, 540, "VoxFlow Multi-Tenant Trust & Isolation Boundaries", "Exact-DID Inbound Routing, HMAC Signed Bridge & Zero Cross-Tenant Data Leakage")
    
    # Ingress / Edge Layer
    svg += group_box(30, 85, 900, 100, "Untrusted Public Internet & Ingress Edge Layer", stroke="#0284C7", title_color="#38BDF8")
    svg += node_box(50, 110, 240, 60, "Inbound PSTN Caller", "Calls Depot UK DID (+44 20...)", stroke="#38BDF8", badge="PSTN")
    svg += node_box(350, 110, 260, 60, "AWS Lambda Bridge", "HMAC-SHA256 turn authentication", stroke="#F59E0B", badge="HMAC")
    svg += node_box(670, 110, 240, 60, "Exact-DID Route Gate", "Strict tenant_id resolution\nFail-close if unmatched", stroke="#10B981", badge="GATE")

    # Center Isolation
    svg += connection(290, 140, 350, 140, "Voice Call", color="#38BDF8")
    svg += connection(610, 140, 670, 140, "Signed Turn", color="#F59E0B")

    # Tenant A Boundary (Left)
    svg += group_box(30, 210, 430, 305, "Tenant A Isolation Boundary (Apex Depot)", stroke="#10B981", title_color="#34D399")
    svg += node_box(50, 245, 390, 65, "Session A (tenant_id = 'apex-depot')", "Scoped caller identity & PIN binding", stroke="#10B981", badge="SESSION A")
    svg += node_box(50, 330, 390, 75, "Scoped Tool Execution A", "Queries: WHERE tenant_id = 'apex-depot'\nInventory, orders, slots strictly isolated", stroke="#10B981", badge="TOOLS A")
    svg += node_box(50, 425, 390, 65, "Tenant A Mirror (Google Sheets A)", "Dedicated tenant spreadsheet writeback", stroke="#14B8A6", badge="SHEETS A")

    # Tenant B Boundary (Right)
    svg += group_box(500, 210, 430, 305, "Tenant B Isolation Boundary (Beacon Depot)", stroke="#818CF8", title_color="#818CF8")
    svg += node_box(520, 245, 390, 65, "Session B (tenant_id = 'beacon-depot')", "Scoped caller identity & PIN binding", stroke="#818CF8", badge="SESSION B")
    svg += node_box(520, 330, 390, 75, "Scoped Tool Execution B", "Queries: WHERE tenant_id = 'beacon-depot'\nInventory, orders, slots strictly isolated", stroke="#818CF8", badge="TOOLS B")
    svg += node_box(520, 425, 390, 65, "Tenant B Mirror (Google Sheets B)", "Dedicated tenant spreadsheet writeback", stroke="#818CF8", badge="SHEETS B")

    # Router to Tenants
    svg += curve_connection("M 730 170 C 730 220, 245 220, 245 245", "Route to DID A", 450, 205, color="#10B981")
    svg += curve_connection("M 850 170 C 850 220, 715 220, 715 245", "Route to DID B", 790, 205, color="#818CF8")

    # Internal Tenant Flows
    svg += connection(245, 310, 245, 330, "Execute", color="#10B981")
    svg += connection(245, 405, 245, 425, "Mirror", color="#14B8A6")

    svg += connection(715, 310, 715, 330, "Execute", color="#818CF8")
    svg += connection(715, 405, 715, 425, "Mirror", color="#818CF8")

    # Isolation Firewall Line
    svg += """
  <line x1="480" y1="210" x2="480" y2="515" stroke="#F43F5E" stroke-width="2" stroke-dasharray="6,4" />
  <rect x="420" y="345" width="120" height="24" rx="12" fill="#0B132B" stroke="#F43F5E" stroke-width="1.5" />
  <text x="480" y="361" font-family="system-ui, sans-serif" font-size="10" font-weight="700" fill="#F87171" text-anchor="middle">NO CROSS-LEAK</text>
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
        print(f"Generated {filename} ({len(content)} bytes)")

if __name__ == "__main__":
    main()
