from fastapi import FastAPI, UploadFile, File, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import io
import re
from typing import Any, Dict, List, Optional, Tuple
import os
import httpx
from datetime import datetime
from pydantic import BaseModel, Field

app = FastAPI(title="Local Invoice PDF Extractor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

INDEX_HTML = """
<!doctype html>
<html lang="pt">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Extrator de Faturas PDF</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #070b14;
      --bg-soft: #0b1020;
      --panel: rgba(12, 18, 34, 0.78);
      --panel-strong: rgba(15, 22, 40, 0.94);
      --panel-alt: rgba(255, 255, 255, 0.03);
      --line: rgba(148, 163, 184, 0.15);
      --line-strong: rgba(148, 163, 184, 0.26);
      --text: #eef2ff;
      --muted: #9aa8cb;
      --muted-2: #7281a7;
      --accent: #7c9cff;
      --accent-2: #9b87f5;
      --ok: #55e6a5;
      --warn: #ffcf70;
      --danger: #ff7a90;
      --shadow: 0 24px 80px rgba(0, 0, 0, 0.45);
      --radius: 24px;
      --radius-sm: 16px;
    }

    * { box-sizing: border-box; }

    html { scroll-behavior: smooth; }

    body {
      margin: 0;
      font-family: Inter, Arial, sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(124, 156, 255, 0.18), transparent 28%),
        radial-gradient(circle at 85% 12%, rgba(155, 135, 245, 0.15), transparent 22%),
        radial-gradient(circle at 50% 120%, rgba(85, 230, 165, 0.08), transparent 30%),
        linear-gradient(180deg, #090d18 0%, #070b14 48%, #05070e 100%);
      min-height: 100vh;
    }

    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image:
        linear-gradient(rgba(255,255,255,.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.03) 1px, transparent 1px);
      background-size: 40px 40px;
      mask-image: linear-gradient(180deg, rgba(0,0,0,.25), transparent 85%);
      opacity: .18;
    }

    .wrap {
      position: relative;
      z-index: 1;
      max-width: 1480px;
      margin: 0 auto;
      padding: 32px 24px 56px;
    }

    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 14px 18px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: rgba(8, 12, 24, 0.62);
      backdrop-filter: blur(16px);
      box-shadow: 0 10px 40px rgba(0,0,0,.25);
      margin-bottom: 26px;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 14px;
      min-width: 0;
    }

    .brand-mark {
      width: 42px;
      height: 42px;
      border-radius: 14px;
      display: grid;
      place-items: center;
      background: linear-gradient(135deg, rgba(124,156,255,.95), rgba(155,135,245,.95));
      box-shadow: inset 0 1px 0 rgba(255,255,255,.35), 0 10px 30px rgba(124,156,255,.28);
      font-weight: 800;
      letter-spacing: -.04em;
    }

    .brand-copy { min-width: 0; }
    .brand-eyebrow {
      margin: 0 0 4px;
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .14em;
    }
    .brand-title {
      margin: 0;
      font-size: 15px;
      font-weight: 700;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .topbar-status {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 10px 14px;
      border-radius: 999px;
      background: rgba(255,255,255,.04);
      border: 1px solid rgba(255,255,255,.06);
      color: var(--muted);
      font-size: 13px;
      white-space: nowrap;
    }

    .status-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--ok);
      box-shadow: 0 0 0 4px rgba(85,230,165,.12);
    }

    .hero {
      display: grid;
      grid-template-columns: minmax(0, 1.25fr) minmax(320px, .75fr);
      gap: 20px;
      align-items: stretch;
      margin-bottom: 22px;
    }

    .hero-panel,
    .hero-side,
    .toolbar,
    .card {
      position: relative;
      overflow: hidden;
      border: 1px solid var(--line);
      background: var(--panel);
      backdrop-filter: blur(18px);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
    }

    .hero-panel {
      padding: 34px;
      min-height: 330px;
    }

    .hero-panel::before,
    .hero-side::before,
    .toolbar::before,
    .card::before {
      content: "";
      position: absolute;
      inset: 0;
      background: linear-gradient(180deg, rgba(255,255,255,.06), transparent 28%);
      pointer-events: none;
    }

    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 8px 12px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 600;
      letter-spacing: .08em;
      text-transform: uppercase;
      color: #d9e2ff;
      border: 1px solid rgba(124,156,255,.22);
      background: rgba(124,156,255,.08);
    }

    .eyebrow::before {
      content: "";
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: linear-gradient(135deg, var(--accent), var(--accent-2));
      box-shadow: 0 0 0 5px rgba(124,156,255,.08);
    }

    .hero h1 {
      margin: 18px 0 12px;
      font-size: clamp(34px, 5vw, 58px);
      line-height: 1.02;
      letter-spacing: -0.06em;
      max-width: 11ch;
      background: linear-gradient(180deg, #ffffff 0%, #d9e4ff 38%, #8ea8ff 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .hero p {
      margin: 0;
      max-width: 62ch;
      color: var(--muted);
      font-size: 16px;
      line-height: 1.7;
    }

    .hero-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 26px;
    }

    .hero-note {
      margin-top: 22px;
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 12px 14px;
      border-radius: 16px;
      background: rgba(255,255,255,.04);
      border: 1px solid rgba(255,255,255,.06);
      color: var(--muted);
      font-size: 13px;
    }

    .hero-side {
      padding: 24px;
      display: grid;
      gap: 14px;
      align-content: start;
    }

    .side-label {
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .12em;
    }

    .stats {
      display: grid;
      gap: 12px;
    }

    .stat {
      display: grid;
      gap: 6px;
      padding: 16px 18px;
      border-radius: 18px;
      background: rgba(255,255,255,.03);
      border: 1px solid rgba(255,255,255,.06);
    }

    .stat .k {
      color: var(--muted-2);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .08em;
    }

    .stat .v {
      font-size: 28px;
      font-weight: 750;
      letter-spacing: -.04em;
    }

    .stat .hint {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
    }
    .editable {
    width: 100%;
    background: #0d1429;
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 10px;
    color: var(--text);
    font-size: 16px;
    font-weight: 600;
    outline: none;
    transition: .15s;
    }

    .editable:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 2px rgba(122,162,255,.2);
    }

    mark {
    background: rgba(123,240,177,.3);
    color: #7bf0b1;
    padding: 2px 4px;
    border-radius: 4px;
    }

    .toolbar {
      padding: 24px;
      margin-bottom: 22px;
    }

    .toolbar-grid {
      display: grid;
      grid-template-columns: minmax(0, 1.15fr) minmax(320px, .85fr);
      gap: 18px;
      align-items: stretch;
    }

    input[type=file] {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
  z-index: 4;
}

    .dropzone {
      position: relative;
      isolation: isolate;
      overflow: hidden;
      min-height: 248px;
      border-radius: 26px;
      border: 1px solid rgba(124,156,255,.22);
      background:
        radial-gradient(circle at 50% 0%, rgba(124,156,255,.18), transparent 42%),
        linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.02));
      display: grid;
      place-items: center;
      padding: 30px 24px;
      text-align: center;
      cursor: pointer;
      user-select: none;
      transition: transform .22s ease, border-color .22s ease, box-shadow .22s ease, background .22s ease;
      box-shadow: inset 0 1px 0 rgba(255,255,255,.05), 0 20px 60px rgba(3,8,20,.28);
    }

    .dropzone::before,
    .dropzone::after {
      content: "";
      position: absolute;
      inset: auto;
      pointer-events: none;
      transition: opacity .22s ease, transform .22s ease;
    }

    .dropzone::before {
      width: 320px;
      height: 320px;
      top: -180px;
      left: 50%;
      transform: translateX(-50%);
      background: radial-gradient(circle, rgba(124,156,255,.28), transparent 68%);
      filter: blur(10px);
      opacity: .9;
    }

    .dropzone::after {
      inset: 1px;
      border-radius: 25px;
      border: 1px solid rgba(255,255,255,.05);
    }

    .dropzone:hover {
      transform: translateY(-2px);
      border-color: rgba(124,156,255,.44);
      box-shadow: 0 28px 70px rgba(5,10,22,.34), 0 0 0 1px rgba(124,156,255,.12) inset;
    }

    .dropzone.dragover {
      transform: translateY(-4px) scale(1.012);
      border-color: rgba(85,230,165,.78);
      background:
        radial-gradient(circle at 50% 0%, rgba(85,230,165,.17), transparent 42%),
        linear-gradient(180deg, rgba(255,255,255,.07), rgba(255,255,255,.025));
      box-shadow: 0 32px 90px rgba(50,190,135,.14), 0 0 0 1px rgba(85,230,165,.15) inset;
    }

    .dropzone.dragover::before {
      transform: translateX(-50%) scale(1.08);
      opacity: 1;
    }

    .dropzone .inner {
      position: relative;
      z-index: 2;
      display: grid;
      gap: 14px;
      max-width: 440px;
      justify-items: center;
      pointer-events: none;
    }

    .upload-orb {
      position: relative;
      width: 88px;
      height: 88px;
      border-radius: 28px;
      display: grid;
      place-items: center;
      background: linear-gradient(135deg, rgba(124,156,255,.22), rgba(155,135,245,.16));
      border: 1px solid rgba(124,156,255,.26);
      box-shadow: inset 0 1px 0 rgba(255,255,255,.08), 0 18px 35px rgba(36,52,104,.22);
    }

    .upload-orb::before,
    .upload-orb::after {
      content: "";
      position: absolute;
      inset: -14px;
      border-radius: 34px;
      border: 1px solid rgba(124,156,255,.12);
      animation: pulseRing 2.8s ease-out infinite;
      pointer-events: none;
    }

    .upload-orb::after {
      inset: -26px;
      animation-delay: 1.1s;
      opacity: .55;
    }

    .upload-icon {
      width: 54px;
      height: 54px;
      display: grid;
      place-items: center;
      border-radius: 18px;
      background: rgba(7,12,26,.34);
      border: 1px solid rgba(255,255,255,.08);
      box-shadow: inset 0 1px 0 rgba(255,255,255,.06);
      font-size: 24px;
      font-weight: 700;
      line-height: 1;
    }

    .dropzone-beams {
      position: absolute;
      inset: 0;
      pointer-events: none;
      overflow: hidden;
      z-index: 1;
    }

    .dropzone-beams span {
      position: absolute;
      width: 140px;
      height: 1px;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,.22), transparent);
      opacity: .45;
      animation: beamFloat 8s linear infinite;
    }

    .dropzone-beams span:nth-child(1) { top: 26%; left: -8%; animation-delay: 0s; }
    .dropzone-beams span:nth-child(2) { top: 52%; right: -10%; animation-delay: 1.6s; }
    .dropzone-beams span:nth-child(3) { bottom: 24%; left: 12%; animation-delay: 3.2s; }

    .dropzone-actions {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 4px;
    }

    .dropzone-cta {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
      border-radius: 999px;
      background: rgba(255,255,255,.06);
      border: 1px solid rgba(255,255,255,.08);
      color: var(--text);
      font-size: 13px;
      font-weight: 650;
      box-shadow: inset 0 1px 0 rgba(255,255,255,.06);
    }

    .dropzone-tip {
      color: var(--muted);
      font-size: 12px;
      letter-spacing: .02em;
    }

    @keyframes pulseRing {
      0% { transform: scale(.9); opacity: .0; }
      28% { opacity: .42; }
      100% { transform: scale(1.18); opacity: 0; }
    }

    @keyframes beamFloat {
      0% { transform: translateX(0) scaleX(.9); opacity: 0; }
      15% { opacity: .45; }
      50% { transform: translateX(38px) scaleX(1.05); opacity: .55; }
      100% { transform: translateX(76px) scaleX(.92); opacity: 0; }
    }

    .dropzone .title {
      font-size: 24px;
      font-weight: 760;
      letter-spacing: -.04em;
    }

    .dropzone .subtitle {
      color: var(--muted);
      font-size: 14px;
      line-height: 1.7;
    }

    .dropzone .filename {
      min-height: 20px;
      color: #dfffee;
      font-size: 14px;
      font-weight: 650;
      word-break: break-word;
    }

    .upload-panel {
      display: grid;
      gap: 14px;
    }

    .stack-card {
      padding: 18px;
      border-radius: 20px;
      background: rgba(255,255,255,.03);
      border: 1px solid rgba(255,255,255,.06);
    }

    .stack-card h3 {
      margin: 0 0 8px;
      font-size: 15px;
      letter-spacing: -.02em;
    }

    .stack-card p {
      margin: 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.65;
    }

    .chip-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
    }

    .chip {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 11px;
      border-radius: 999px;
      border: 1px solid rgba(255,255,255,.08);
      background: rgba(255,255,255,.04);
      color: #dce5ff;
      font-size: 12px;
      font-weight: 600;
    }

    .chip::before {
      content: "";
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: linear-gradient(135deg, var(--accent), var(--accent-2));
    }

    .actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 16px;
    }

    .btn {
      appearance: none;
      border: 0;
      border-radius: 14px;
      padding: 12px 16px;
      font-weight: 700;
      font-size: 14px;
      color: white;
      background: linear-gradient(135deg, #7c9cff, #6d83ff 45%, #8d79ff 100%);
      box-shadow: 0 10px 28px rgba(124,156,255,.26), inset 0 1px 0 rgba(255,255,255,.22);
      cursor: pointer;
      transition: transform .16s ease, box-shadow .16s ease, opacity .16s ease;
    }

    .btn:hover { transform: translateY(-1px); }

    .btn.secondary {
      color: var(--text);
      background: rgba(255,255,255,.04);
      border: 1px solid rgba(255,255,255,.08);
      box-shadow: none;
    }

    .btn:disabled {
      opacity: .45;
      cursor: not-allowed;
      transform: none;
    }

    .status {
      margin-top: 16px;
      min-height: 22px;
      color: var(--muted);
      font-size: 14px;
    }

    .status-card {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 11px 14px;
      border-radius: 14px;
      background: rgba(255,255,255,.04);
      border: 1px solid rgba(255,255,255,.06);
    }

    .spinner {
      display: inline-block;
      width: 16px;
      height: 16px;
      border: 2px solid rgba(255,255,255,.18);
      border-top-color: white;
      border-radius: 50%;
      animation: spin .8s linear infinite;
    }

    @keyframes spin { to { transform: rotate(360deg); } }

    .dashboard-grid {
      display: grid;
      grid-template-columns: minmax(390px, 460px) minmax(0, 1fr);
      gap: 20px;
    }

    .card {
      padding: 22px;
      min-height: 220px;
      transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
    }

    .card:hover {
      transform: translateY(-3px);
      border-color: var(--line-strong);
      box-shadow: 0 34px 100px rgba(0,0,0,.42);
    }

    .card-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 16px;
    }

    .card h2 {
      margin: 0;
      font-size: 20px;
      letter-spacing: -.04em;
    }

    .card-subtitle {
      margin-top: 6px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.6;
    }

    .section-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 10px;
      border-radius: 999px;
      border: 1px solid rgba(255,255,255,.08);
      background: rgba(255,255,255,.03);
      color: var(--muted);
      font-size: 12px;
      font-weight: 600;
      white-space: nowrap;
    }

    .fields {
      display: grid;
      gap: 12px;
    }

    .field {
      padding: 16px;
      border-radius: 18px;
      background: linear-gradient(180deg, rgba(255,255,255,.05), rgba(255,255,255,.025));
      border: 1px solid rgba(255,255,255,.06);
      box-shadow: inset 0 1px 0 rgba(255,255,255,.04);
    }

    .field-top {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      margin-bottom: 10px;
    }

    .field .label {
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: .12em;
    }

    .field .value {
      font-size: 19px;
      line-height: 1.45;
      font-weight: 750;
      letter-spacing: -.03em;
      word-break: break-word;
    }

    .field-footer {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      margin-top: 12px;
    }

    .confidence {
      color: var(--muted);
      font-size: 12px;
    }

    .confidence-bar {
      position: relative;
      width: 120px;
      height: 8px;
      border-radius: 999px;
      overflow: hidden;
      background: rgba(255,255,255,.08);
      border: 1px solid rgba(255,255,255,.05);
    }

    .confidence-bar > span {
      display: block;
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, #ff9d7a 0%, #ffd670 42%, #55e6a5 100%);
    }

    .pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(85,230,165,.12);
      color: #9cf2c8;
      border: 1px solid rgba(85,230,165,.18);
      font-size: 12px;
      font-weight: 700;
    }

    .pill.warn {
      background: rgba(255,207,112,.11);
      color: #ffd98b;
      border-color: rgba(255,207,112,.18);
    }

    .items-shell {
      overflow: hidden;
      border-radius: 18px;
      border: 1px solid rgba(255,255,255,.06);
      background: rgba(255,255,255,.025);
      margin-top: 18px;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }

    thead th {
      position: sticky;
      top: 0;
      z-index: 1;
      background: rgba(11,16,32,.96);
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: .08em;
      font-size: 11px;
    }

    th, td {
      text-align: left;
      padding: 12px 14px;
      border-bottom: 1px solid rgba(255,255,255,.05);
      vertical-align: top;
    }

    tbody tr:hover {
      background: rgba(124,156,255,.05);
    }

    .meta {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }

    .mini {
      padding: 14px 14px 13px;
      border-radius: 18px;
      background: rgba(255,255,255,.03);
      border: 1px solid rgba(255,255,255,.06);
      min-width: 0;
    }

    .mini .k {
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: .12em;
      margin-bottom: 8px;
    }

    .mini .v {
      font-size: 18px;
      font-weight: 760;
      letter-spacing: -.03em;
      word-break: break-word;
    }

    .text-box {
      background: rgba(6,9,18,.72);
      color: #dbe4ff;
      border: 1px solid rgba(255,255,255,.06);
      border-radius: 20px;
      padding: 18px;
      white-space: pre-wrap;
      word-wrap: break-word;
      line-height: 1.55;
      max-height: 78vh;
      overflow: auto;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 12.5px;
      box-shadow: inset 0 1px 0 rgba(255,255,255,.03);
    }

    .empty-state {
      padding: 20px;
      border-radius: 18px;
      background: rgba(255,255,255,.03);
      border: 1px dashed rgba(255,255,255,.08);
    }

    .empty-state .label {
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: .12em;
      margin-bottom: 8px;
    }

    .empty-state .value {
      font-size: 16px;
      font-weight: 650;
      line-height: 1.5;
    }

    @media (max-width: 1180px) {
      .hero,
      .toolbar-grid,
      .dashboard-grid {
        grid-template-columns: 1fr;
      }

      .hero-panel { min-height: auto; }
    }

    @media (max-width: 780px) {
      .wrap { padding: 18px 14px 34px; }
      .topbar {
        border-radius: 24px;
        padding: 14px;
        flex-direction: column;
        align-items: flex-start;
      }
      .hero-panel,
      .hero-side,
      .toolbar,
      .card { border-radius: 22px; }
      .hero-panel { padding: 24px; }
      .toolbar, .card { padding: 16px; }
      .dropzone { min-height: 200px; padding: 18px; }
      .actions { flex-direction: column; }
      .btn { width: 100%; }
      .meta { grid-template-columns: 1fr 1fr; }
      .field-footer {
        align-items: flex-start;
        flex-direction: column;
      }
    }

    @media (max-width: 560px) {
      .meta { grid-template-columns: 1fr; }
      .hero h1 { max-width: none; }
      .dropzone .title { font-size: 20px; }
      .stat .v { font-size: 24px; }
      th, td { padding: 10px; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="topbar">
      <div class="brand">
        <div class="brand-mark">FX</div>
        <div class="brand-copy">
          <p class="brand-eyebrow">Invoice Intelligence</p>
          <p class="brand-title">Extrator local de faturas PDF</p>
        </div>
      </div>
      <div class="topbar-status">
        <span class="status-dot"></span>
        Local • parsing por coordenadas • pronto a extrair
      </div>
    </div>

    <section class="hero">
      <div class="hero-panel">
        <div class="eyebrow">UI refresh • Linear x Stripe</div>
        <h1>Transforma PDFs em dados prontos a usar.</h1>
        <p>
          Leitor de Faturas
        </p>
        <div class="hero-actions">
          <button class="btn" id="send">Extrair dados</button>
          <button class="btn secondary" id="copy-json" disabled>Copiar JSON</button>
          <button class="btn secondary" id="download-json" disabled>Exportar JSON</button>
          <button class="btn secondary" id="download-csv" disabled>Exportar CSV</button>
        </div>
        <div class="hero-note">
          Ideal para validação rápida de cabeçalhos, linhas de artigo e preparação do payload para Sage.
        </div>
      </div>

      <aside class="hero-side">
        <div>
          <div class="side-label">Visão rápida</div>
          <div class="stats">
            <div class="stat">
              <div class="k">Modo</div>
              <div class="v" id="hero-mode">Aguardando</div>
              <div class="hint">O modo de extração aparece aqui logo após o processamento.</div>
            </div>
            <div class="stat">
              <div class="k">Linhas processadas</div>
              <div class="v" id="hero-lines">0</div>
              <div class="hint">Resumo visual do texto limpo e consolidado.</div>
            </div>
            <div class="stat">
              <div class="k">Campos detetados</div>
              <div class="v" id="hero-fields">0</div>
              <div class="hint">Cabeçalho e metadados encontrados automaticamente.</div>
            </div>
          </div>
        </div>
      </aside>
    </section>

    <section class="toolbar">
      <div class="toolbar-grid">
        <div>
          <div id="dropzone" class="dropzone" role="button" tabindex="0" aria-label="Escolher PDF">
            <input id="file" type="file" accept="application/pdf" />
            <div class="dropzone-beams" aria-hidden="true">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <div class="inner">
              <div class="upload-orb">
                <div class="upload-icon">↑</div>
              </div>
              <div class="title">Arrasta o PDF para aqui</div>
              <div class="subtitle">ou clica para escolher um ficheiro. A dropzone agora usa abertura nativa do input para não falhar mesmo se o JavaScript atrasar.</div>
              <div class="dropzone-actions">
                <span class="dropzone-cta">Escolher PDF</span>
                <span class="dropzone-tip">Drag & drop · PDF only</span>
              </div>
              <div id="selected-file" class="filename"></div>
            </div>
          </div>
          <div id="status" class="status"></div>
        </div>

        <div class="upload-panel">
          <div class="stack-card">
            <h3>Fluxo de extração</h3>
            <p>Upload → limpeza de linhas → inferência de cabeçalho → extração de artigos → exportação.</p>
            <div class="chip-row">
              <span class="chip">Header fields</span>
              <span class="chip">Invoice items</span>
              <span class="chip">Clean text</span>
              <span class="chip">JSON / CSV</span>
            </div>
          </div>
          <div class="stack-card">
            <h3>Experiência pensada para análise</h3>
            <p>Mais contraste, melhor spacing, estados mais claros e cards mais próximos de ferramentas modernas tipo Linear e Stripe.</p>
          </div>
        </div>
      </div>
    </section>

    <section class="dashboard-grid">
      <div class="card">
        <div class="card-head">
          <div>
            <h2>Cabeçalho da fatura</h2>
            <div class="card-subtitle">Campos extraídos com badge de confiança e barra visual para leitura imediata.</div>
          </div>
          <div class="section-badge">Structured output</div>
        </div>
        <div id="fields" class="fields"></div>

        <div class="card-head" style="margin-top:22px;">
          <div>
            <h2>Linhas de artigo</h2>
            <div class="card-subtitle">Tabela com leitura mais confortável e hover discreto.</div>
          </div>
          <div class="section-badge">Line items</div>
        </div>
        <div id="items"></div>
      </div>

      <div class="card">
        <div class="card-head">
          <div>
            <h2>Texto processado</h2>
            <div class="card-subtitle">Preview do texto normalizado com métricas operacionais em cima.</div>
          </div>
          <div class="section-badge">Debug / review</div>
        </div>
        <div id="meta" class="meta"></div>
        <div id="text" class="text-box"></div>
      </div>
    </section>
  </div>

  <script>
    const btn = document.getElementById('send');
    const copyJsonBtn = document.getElementById('copy-json');
    const downloadJsonBtn = document.getElementById('download-json');
    const downloadCsvBtn = document.getElementById('download-csv');

    const fileInput = document.getElementById('file');
    const status = document.getElementById('status');
    const textBox = document.getElementById('text');
    const fieldsBox = document.getElementById('fields');
    const metaBox = document.getElementById('meta');
    const itemsBox = document.getElementById('items');
    const dropzone = document.getElementById('dropzone');
    const selectedFileBox = document.getElementById('selected-file');
    const heroMode = document.getElementById('hero-mode');
    const heroLines = document.getElementById('hero-lines');
    const heroFields = document.getElementById('hero-fields');

    let lastResult = null;
    let selectedFile = null;
    let isUploading = false;

    function escapeHtml(value) {
      return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
    }

    function confidenceBadge(conf) {
      const n = Number(conf || 0);
      if (n >= 0.8) return '<span class="pill">Alta</span>';
      if (n >= 0.6) return '<span class="pill warn">Média</span>';
      return '<span class="pill warn">Baixa</span>';
    }

    function setActionButtonsEnabled(enabled) {
      copyJsonBtn.disabled = !enabled;
      downloadJsonBtn.disabled = !enabled;
      downloadCsvBtn.disabled = !enabled;
    }

    function showStatus(message, loading = false) {
      status.innerHTML = loading
        ? `<div class="status-card"><span class="spinner"></span>${escapeHtml(message)}</div>`
        : `<div class="status-card">${escapeHtml(message)}</div>`;
    }

    function showSelectedFile(file) {
      selectedFileBox.textContent = file ? `Selecionado: ${file.name}` : '';
    }

    function setSinglePdfFile(file) {
      if (!file) return false;
      const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
      if (!isPdf) {
        showStatus('Só PDFs são suportados.');
        return false;
      }
      selectedFile = file;
      showSelectedFile(file);
      showStatus('PDF pronto para extrair.');
      return true;
    }

    function highlightText(value) {
      const text = lastResult?.cleaned_text || lastResult?.raw_text || '';
      if (!text) {
        textBox.textContent = '';
        return;
      }
      if (!value) {
        textBox.textContent = text;
        return;
      }
      const safeValue = String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const regex = new RegExp(safeValue, 'gi');
      textBox.innerHTML = escapeHtml(text).replace(regex, (match) => `<mark>${match}</mark>`);
    }

    function renderFields(data) {
      const entries = Object.entries(data.header || {});
      heroFields.textContent = String(entries.length);

      if (!entries.length) {
        fieldsBox.innerHTML = '<div class="empty-state"><div class="label">Sem resultados</div><div class="value">Nenhum campo identificado.</div></div>';
        return;
      }

      fieldsBox.innerHTML = entries.map(([key, value]) => {
        const percent = Math.max(0, Math.min(100, Math.round(Number(value.confidence || 0) * 100)));
        return `
          <div class="field" data-key="${escapeHtml(key)}">
            <div class="field-top">
              <div class="label">${escapeHtml(key.replaceAll('_', ' '))}</div>
              ${confidenceBadge(value.confidence)}
            </div>
            <input class="editable" value="${escapeHtml(value.value ?? '')}" data-key="${escapeHtml(key)}" />
            <div class="field-footer">
              <div class="confidence">Confiança: ${escapeHtml(value.confidence ?? '')}</div>
              <div class="confidence-bar"><span style="width:${percent}%"></span></div>
            </div>
          </div>
        `;
      }).join('');

      fieldsBox.querySelectorAll('.editable').forEach((input) => {
        input.addEventListener('input', (e) => {
          const key = e.target.dataset.key;
          if (lastResult?.header?.[key]) {
            lastResult.header[key].value = e.target.value;
          }
        });
        input.addEventListener('focus', () => highlightText(input.value));
        input.addEventListener('click', () => highlightText(input.value));
      });
    }

    function renderItems(data) {
      const items = data.items || [];
      if (!items.length) {
        itemsBox.innerHTML = '<div class="empty-state"><div class="label">Sem artigos</div><div class="value">Nenhuma linha de artigo identificada.</div></div>';
        return;
      }

      itemsBox.innerHTML = `
        <div class="items-shell" style="overflow:auto;">
          <table>
            <thead>
              <tr>
                <th>Tipo</th>
                <th>Código</th>
                <th>Descrição</th>
                <th>Qtd</th>
                <th>Un</th>
                <th>P. Unit.</th>
                <th>Desc.</th>
                <th>IVA</th>
                <th>Total linha</th>
              </tr>
            </thead>
            <tbody>
              ${items.map(item => `
                <tr>
                  <td>${escapeHtml(item.type || '')}</td>
                  <td>${escapeHtml(item.code || '')}</td>
                  <td>${escapeHtml(item.description || '')}</td>
                  <td>${escapeHtml(item.qty || '')}</td>
                  <td>${escapeHtml(item.unit || '')}</td>
                  <td>${escapeHtml(item.unit_price || '')}</td>
                  <td>${escapeHtml(item.discount || '')}</td>
                  <td>${escapeHtml(item.vat_rate || '')}</td>
                  <td>${escapeHtml(item.line_total || '')}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    }

    function renderMeta(data) {
      metaBox.innerHTML = `
        <div class="mini"><div class="k">Ficheiro</div><div class="v">${escapeHtml(data.filename || '-')}</div></div>
        <div class="mini"><div class="k">Linhas úteis</div><div class="v">${escapeHtml(data.line_count || 0)}</div></div>
        <div class="mini"><div class="k">Texto repetido removido</div><div class="v">${escapeHtml(data.removed_repeated_lines || 0)}</div></div>
        <div class="mini"><div class="k">Modo</div><div class="v">${escapeHtml(data.extraction_mode || '-')}</div></div>
      `;
      heroMode.textContent = data.extraction_mode || '—';
      heroLines.textContent = String(data.line_count || 0);
    }

    function escapeCsv(value) {
      const s = String(value ?? '');
      if (s.includes('\"') || s.includes(';') || s.includes('\n')) {
        return '"' + s.replaceAll('"', '""') + '"';
      }
      return s;
    }

    function buildCsv(items) {
      const headers = ['type', 'code', 'description', 'qty', 'unit', 'unit_price', 'discount', 'vat_rate', 'line_total'];
      const rows = [headers.join(';'), ...items.map(item => headers.map(h => escapeCsv(item[h] ?? '')).join(';'))];
      return rows.join('\n');
    }

    function downloadFile(content, filename, contentType) {
      const blob = new Blob([content], { type: contentType });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    }

    function baseFilename(name) {
      if (!name) return 'resultado';
      return name.replace(/\.pdf$/i, '');
    }

    async function sendFile() {
      const f = selectedFile || (fileInput.files && fileInput.files[0]);
      if (!f) {
        showStatus('Escolhe um PDF primeiro.');
        return;
      }
      if (isUploading) return;

      isUploading = true;
      btn.disabled = true;
      setActionButtonsEnabled(false);
      showStatus('A processar PDF...', true);
      textBox.textContent = '';
      fieldsBox.innerHTML = '';
      itemsBox.innerHTML = '';
      metaBox.innerHTML = '';
      heroMode.textContent = 'A processar';
      heroLines.textContent = '—';
      heroFields.textContent = '—';
      lastResult = null;

      const form = new FormData();
      form.append('file', f, f.name || 'documento.pdf');

      try {
        const res = await fetch('/extract', { method: 'POST', body: form });
        const contentType = res.headers.get('content-type') || '';
        const data = contentType.includes('application/json') ? await res.json() : { detail: await res.text() };

        if (!res.ok) {
          throw new Error(data.detail || 'Erro ao processar PDF');
        }

        lastResult = data;
        renderFields(data);
        renderItems(data);
        renderMeta(data);
        textBox.textContent = data.cleaned_text || data.raw_text || '';
        showStatus('Extração concluída com sucesso.');
        setActionButtonsEnabled(true);
      } catch (err) {
        heroMode.textContent = 'Falhou';
        heroLines.textContent = '0';
        heroFields.textContent = '0';
        showStatus(err?.message || 'Erro ao processar PDF.');
      } finally {
        isUploading = false;
        btn.disabled = false;
      }
    }

    async function handlePickedFile(file, originMessage) {
      if (!setSinglePdfFile(file)) return;
      showStatus(originMessage || 'PDF carregado. A extrair automaticamente...');
      await sendFile();
    }

    function openFilePicker() {
      fileInput.value = '';
      fileInput.click();
    }

    dropzone.addEventListener('click', openFilePicker);
    dropzone.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        openFilePicker();
      }
    });

    fileInput.addEventListener('change', async () => {
      const file = fileInput.files && fileInput.files[0];
      if (!file) return;
      await handlePickedFile(file, 'PDF carregado. A extrair automaticamente...');
    });

    window.addEventListener('dragover', (e) => {
      e.preventDefault();
    });

    window.addEventListener('drop', (e) => {
      e.preventDefault();
    });

    dropzone.addEventListener('dragenter', (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', (e) => {
      e.preventDefault();
      if (!dropzone.contains(e.relatedTarget)) {
        dropzone.classList.remove('dragover');
      }
    });

    dropzone.addEventListener('drop', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dragover');
      const files = e.dataTransfer?.files;
      if (!files || !files.length) return;
      await handlePickedFile(files[0], 'PDF largado. A extrair automaticamente...');
    });

    btn.addEventListener('click', sendFile);

    copyJsonBtn.addEventListener('click', async () => {
      if (!lastResult) return;
      const json = JSON.stringify(lastResult, null, 2);
      await navigator.clipboard.writeText(json);
      showStatus('JSON copiado para a área de transferência.');
    });

    downloadJsonBtn.addEventListener('click', () => {
      if (!lastResult) return;
      const name = baseFilename(lastResult.filename) + '.json';
      downloadFile(JSON.stringify(lastResult, null, 2), name, 'application/json;charset=utf-8');
    });

    downloadCsvBtn.addEventListener('click', () => {
      if (!lastResult) return;
      const name = baseFilename(lastResult.filename) + '_items.csv';
      const csv = buildCsv(lastResult.items || []);
      downloadFile(csv, name, 'text/csv;charset=utf-8');
    });
  </script>
</body>
</html>

"""

FIELD_ALIASES = {
    "invoice_date": ["invoice date", "date", "data", "data da fatura"],
    "due_date": ["vencimento", "due date"],
    "customer_nif": ["v. contribuinte", "cliente", "customer vat", "customer vat number", "nif cliente"],
    "supplier_nif": ["contrib nº", "contribuinte", "vat", "nif", "tax id", "vat number", "vat no", "nipc"],
    "subtotal": ["valor liquido", "subtotal", "sub total", "valor sem iva", "ilíquido", "base"],
    "iva_amount": ["i.v.a.", "iva", "vat amount", "tax", "imposto", "montante taxa"],
    "total": ["total documento", "liquido", "líquido", "total", "total amount", "amount due", "valor total", "total a pagar", "montante total"],
}

MONEY_RE = re.compile(r"(?<!\d)(?:€\s?)?[-+]?\d{1,3}(?:[ .]\d{3})*(?:,\d{2}|\.\d{2,3})(?![./]\d)(?!\d)")
DATE_PATTERNS = [
    re.compile(r"\b\d{{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b\d{2}/\d2}/\d{4}\b"),
    re.compile(r"\b\d{2}-\d{2}-\d{4}\b"),
    re.compile(r"\b\d{2}\.\d{2}\.\d{4}\b"),
]
PT_VAT_RE = re.compile(r"\bPT\s?\d{9}\b|\b\d{9}\b")
INVOICE_NO_RE = re.compile(r"\b\d{4}\.[A-Z]{2}\.\d+/\d+\b")


def normalize_whitespace(text: str) -> str:
    text = text.replace("\xa0", " ").replace("\r", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_for_compare(line: str) -> str:
    line = line.lower().strip()
    line = re.sub(r"\b(original|duplicado|triplicado|quadruplicado)\b", "", line)
    line = re.sub(r"\s+", " ", line)
    return line.strip()


def cleanup_lines(text: str) -> Tuple[List[str], int]:
    raw_lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    seen: Dict[str, int] = {}
    cleaned: List[str] = []
    removed = 0

    for line in raw_lines:
        norm = normalize_for_compare(line)
        if not norm:
            continue

        count = seen.get(norm, 0)
        if count >= 1 and len(norm) > 8:
            removed += 1
            seen[norm] = count + 1
            continue

        seen[norm] = count + 1
        cleaned.append(line)

    return cleaned, removed


def join_broken_label_lines(lines: List[str]) -> List[str]:
    merged: List[str] = []
    i = 0

    while i < len(lines):
        current = lines[i]

        if i + 1 < len(lines):
            nxt = lines[i + 1]
            pair = f"{current} {nxt}"

            if any(k in pair.lower() for k in [
                "factura fn",
                "fatura fn",
                "data",
                "valor liquido",
                "total documento",
                "i.v.a.",
                "vencimento",
            ]):
                if len(current) < 40 or current.endswith(":") or current.isupper():
                    merged.append(pair)
                    i += 2
                    continue

        merged.append(current)
        i += 1

    return merged


def money_candidates_in_line(line: str) -> List[str]:
    vals = MONEY_RE.findall(line)
    cleaned: List[str] = []
    for v in vals:
        if re.search(r"\d{2}[./]\d{2}[./]\d{2,4}", v):
            continue
        cleaned.append(v.strip())
    return cleaned

def get_first_date(text: str) -> Optional[str]:
    for pat in DATE_PATTERNS:
        m = pat.search(text)
        if m:
            return m.group(0)
    return None


def parse_money_value(value: str) -> Optional[float]:
    if value is None:
        return None
    s = value.strip().replace("€", "").replace(" ", "")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def format_money_pt(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")


def reconstruct_lines_from_words_pdfplumber(data: bytes) -> List[str]:
    import pdfplumber

    final_lines: List[str] = []

    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            words = page.extract_words(
                use_text_flow=False,
                keep_blank_chars=False,
                x_tolerance=2,
                y_tolerance=3,
            ) or []

            if not words:
                page_text = page.extract_text(layout=True) or ""
                final_lines.extend([ln.strip() for ln in page_text.splitlines() if ln.strip()])
                continue

            words = sorted(words, key=lambda w: (round(float(w["top"]), 1), float(w["x0"])))

            grouped: List[List[Dict[str, Any]]] = []
            current_group: List[Dict[str, Any]] = []
            current_top: Optional[float] = None
            tolerance = 3.0

            for w in words:
                top = float(w["top"])
                if current_top is None:
                    current_top = top
                    current_group = [w]
                    continue

                if abs(top - current_top) <= tolerance:
                    current_group.append(w)
                else:
                    grouped.append(current_group)
                    current_group = [w]
                    current_top = top

            if current_group:
                grouped.append(current_group)

            for group in grouped:
                group = sorted(group, key=lambda w: float(w["x0"]))
                pieces: List[str] = []
                prev_x1: Optional[float] = None

                for w in group:
                    text = str(w["text"]).strip()
                    x0 = float(w["x0"])
                    x1 = float(w["x1"])

                    if not text:
                        continue

                    if prev_x1 is None:
                        pieces.append(text)
                    else:
                        gap = x0 - prev_x1
                        if gap > 25:
                            pieces.append("    " + text)
                        else:
                            pieces.append(" " + text)

                    prev_x1 = x1

                line = "".join(pieces).strip()
                if line:
                    final_lines.append(line)

    return final_lines


def extract_text_from_pdf_bytes(data: bytes) -> Tuple[str, str]:
    parts: List[str] = []

    try:
        lines = reconstruct_lines_from_words_pdfplumber(data)
        text = normalize_whitespace("\n".join(lines))
        if len(text) > 40:
            return text, "pdfplumber_words"
    except Exception:
        pass

    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                parts.append(page_text)

        text = normalize_whitespace("\n".join(parts))
        if len(text) > 40:
            return text, "pypdf"
    except Exception:
        pass

    try:
        import pdfplumber
        plumber_parts: List[str] = []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text(layout=True) or ""
                if page_text.strip():
                    plumber_parts.append(page_text)
        text = normalize_whitespace("\n".join(plumber_parts))
        if len(text) > 40:
            return text, "pdfplumber_layout"
    except Exception:
        pass

    return "", "none"


def extract_value_near_alias(lines: List[str], aliases: List[str], kind: str) -> Optional[Tuple[str, float]]:
    for i, line in enumerate(lines):
        low = line.lower()

        for alias in aliases:
            if alias in low:
                if kind == "money":
                    vals = money_candidates_in_line(line)
                    if vals:
                        return vals[-1], 0.88
                    if i + 1 < len(lines):
                        vals = money_candidates_in_line(lines[i + 1])
                        if vals:
                            return vals[0], 0.76

                elif kind == "date":
                    date = get_first_date(line)
                    if date:
                        return date, 0.88
                    if i + 1 < len(lines):
                        date = get_first_date(lines[i + 1])
                        if date:
                            return date, 0.76

                elif kind == "vat":
                    m = PT_VAT_RE.search(line)
                    if m:
                        return m.group(0).replace(" ", ""), 0.82
                    if i + 1 < len(lines):
                        m = PT_VAT_RE.search(lines[i + 1])
                        if m:
                            return m.group(0).replace(" ", ""), 0.70

    return None


def infer_supplier_name(lines: List[str]) -> Optional[Tuple[str, float]]:
    blacklist = [
        "exmo.(s)", "faturado ao cliente", "documento nº", "documento no", "data ",
        "n/ contribuinte", "v/ contribuinte", "condições de pagamento", "condicoes de pagamento",
        "data de vencimento", "entrega em", "item nº do produto", "item no do produto",
        "descrição do produto", "descricao do produto", "quantidade", "preço unitário",
        "preco unitario", "preço total", "preco total", "iban", "atcud", "modo de expedição",
        "modo de expedicao", "cliente:", "nr. doc.:", "nif:", "transportador", "pag. ",
        "tel:", "fax:", "porto :", "lisboa :", "cond.pgt", "email:", "www.", "capital social", "licenciado a:"
    ]
    positive_hints = [
        "lda", "lda.", "s.a.", "sa", "unipessoal", "portugal", "computadores",
        "informáticos", "informaticos", "distribution", "distribuição", "distribuicao",
        "software", "material informático", "material informatico"
    ]
    def clean_supplier_candidate(s: str) -> str:
        s = re.sub(r"\bFatura\b", "", s, flags=re.IGNORECASE).strip(" -")
        s = re.sub(r"\s*[|*]\s.*$", "", s).strip()
        s = re.sub(r"\s+-\s+Rua .*$", "", s, flags=re.IGNORECASE).strip()
        s = re.sub(r"\s{2,}", " ", s)
        return s.strip(" -")
    def is_bad_supplier_candidate(s: str) -> bool:
        low = s.lower().strip()
        if len(s) < 4 or "microlagos" in low:
            return True
        if any(x in low for x in blacklist):
            return True
        if get_first_date(s):
            return True
        if re.search(r"\b(?:tel|fax)\b", low):
            return True
        if re.search(r"\b\d{4}-\d{3}\b", s):
            return True
        if ":" in s and not any(h in low for h in positive_hints):
            return True
        if re.search(r"\b(?:rua|av\.?|avenida|largo|edifício|edificio|piso|loja|apartado)\b", low) and not any(h in low for h in positive_hints):
            return True
        if low in {"portugal", "faro", "lagos", "porto", "lisboa", "loja b"}:
            return True
        return False
    for i, line in enumerate(lines[:10]):
        s = clean_supplier_candidate(line.strip())
        low = s.lower()
        if is_bad_supplier_candidate(s):
            continue
        if any(h in low for h in positive_hints):
            return s, max(0.97 - i * 0.04, 0.82)
    footer_priority = []
    for idx, line in enumerate(lines):
        s = clean_supplier_candidate(line.strip())
        low = s.lower()
        if is_bad_supplier_candidate(s):
            continue
        if "eticadata software" in low:
            s = re.sub(r"^.*?(eticadata software,?\s*lda\.?)(?:.*)?$", r"", s, flags=re.IGNORECASE)
            return s, 0.98
        if any(h in low for h in positive_hints):
            score = 0.91 + (0.03 if idx > len(lines)//2 else 0)
            if "sage portugal" in low or "wdmi" in low or "also portugal" in low:
                score += 0.05
            if re.search(r"\d[A-Za-z]|[A-Za-z]\d", s):
                score -= 0.08
            footer_priority.append((s, score))
    if footer_priority:
        footer_priority.sort(key=lambda x: x[1], reverse=True)
        return footer_priority[0]
    return None

def parse_generic_item_line_simple(line: str) -> Optional[Dict[str, Any]]:
    s = re.sub(r"\s+", " ", line).strip()
    parts = s.split()
    if len(parts) < 6:
        return None
    if len(parts) >= 5:
        q, u = split_attached_unit_token(parts[-4])
        if q and u and is_money_token(parts[-3]) and is_money_token(parts[-2]) and is_money_token(parts[-1]):
            return None
    if not is_money_token(parts[-1]) or not is_money_token(parts[-2]) or not is_number_token(parts[-3]):
        return None
    line_total = parts[-1]
    unit_price = parts[-2]
    qty = parts[-3]
    left = parts[:-3]
    if len(left) < 2:
        return None
    origin = ""
    code = ""
    description_tokens = left[:]
    if description_tokens and re.fullmatch(r"\d{1,6}", description_tokens[0]):
        origin = description_tokens[0]
        description_tokens = description_tokens[1:]
    if description_tokens and looks_like_code_token(description_tokens[0]):
        code = description_tokens[0]
        description_tokens = description_tokens[1:]
    description = " ".join(description_tokens).strip()
    if len(description) < 2:
        return None
    return {"type": "item", "origin": origin, "code": code, "description": description, "qty": qty, "unit": "", "unit_price": unit_price, "discount": "", "vat_rate": "", "line_total": line_total}

def infer_invoice_number(lines: List[str]) -> Optional[Tuple[str, float]]:
    for line in lines:
        m_doc = re.search(r"documento\s*n[ºo]\.?\s+\S+\s+([A-Z0-9./_-]+)", line, re.IGNORECASE)
        if m_doc:
            return m_doc.group(1), 0.97
        m_nr = re.search(r"nr\.\s*doc\.:\s*[A-Z0-9]+\s+([A-Z0-9./_-]+)", line, re.IGNORECASE)
        if m_nr:
            return m_nr.group(1), 0.97
        m_ft = re.search(r"fatura\s*n[ºo]\s*[A-Z]{1,4}\s+([A-Z0-9./_-]+)", line, re.IGNORECASE)
        if m_ft:
            return m_ft.group(1), 0.97
        m_fatee = re.search(r"\b(FATEE\s+\d{3,}/\d+)\b", line, re.IGNORECASE)
        if m_fatee:
            return m_fatee.group(1), 0.98
        low = line.lower()
        if ("factura" in low or "fatura" in low) and len(line) < 80:
            m = re.search(r"(?:factura|fatura)\s+[A-Z]{1,4}\s+([A-Z0-9./-]+)", line, re.IGNORECASE)
            if m:
                return m.group(1), 0.95
            m2 = INVOICE_NO_RE.search(line)
            if m2:
                return m2.group(0), 0.90
    return None

def infer_dates(lines: List[str]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    inv = None
    due = None
    for i, line in enumerate(lines):
        low = line.lower()
        if "data venc" in low and "data doc" in low and i + 1 < len(lines):
            ds = []
            for pat in DATE_PATTERNS:
                ds.extend(pat.findall(lines[i + 1]))
            if len(ds) >= 2:
                due = (ds[0], 0.95)
                inv = (ds[1], 0.95)
        if inv is None and ("data doc" in low or re.search(r"\bdata:\b", low) or low.startswith("data ")):
            d = get_first_date(line)
            if d:
                inv = (d, 0.92)
        if due is None and ("vencimento" in low or "data venc" in low or "data de venct" in low):
            d = get_first_date(line)
            if d:
                due = (d, 0.92)
    if inv is None:
        inv = extract_value_near_alias(lines, FIELD_ALIASES["invoice_date"], "date")
    if due is None:
        due = extract_value_near_alias(lines, FIELD_ALIASES["due_date"], "date")
    if inv:
        out["invoice_date"] = {"value": inv[0], "confidence": round(inv[1], 2)}
    if due:
        out["due_date"] = {"value": due[0], "confidence": round(due[1], 2)}
    return out

def infer_best_total(lines: List[str]) -> Optional[Tuple[str, float]]:
    for i, line in enumerate(lines):
        low = line.lower()
        if "total documento" in low:
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.96

            nearby = []
            for j in range(i + 1, min(i + 8, len(lines))):
                nearby.extend(money_candidates_in_line(lines[j]))

            if nearby:
                return nearby[-1], 0.90

    return extract_value_near_alias(lines, FIELD_ALIASES["total"], "money")


def infer_subtotal(lines: List[str]) -> Optional[Tuple[str, float]]:
    for line in lines:
        low = line.lower()
        if "montante líquido total sem iva" in low or "montante liquido total sem iva" in low:
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.96
        if "mercadoria:" in low:
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.97
        if "total ilíquido" in low or "total iliquido" in low:
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.97
        if "base de incidência de i.v.a." in low or "base de incidencia de i.v.a." in low:
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.94
    return extract_value_near_alias(lines, FIELD_ALIASES["subtotal"], "money")

def infer_vat_amount(lines: List[str]) -> Optional[Tuple[str, float]]:
    for line in lines:
        low = line.lower()
        if "montante de iva" in low:
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.97
        if "total de i.v.a." in low or "iva:" in low or "resumo do iva iva:" in low:
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.97
        if "observações: i.v.a." in low or "observacoes: i.v.a." in low or re.search(r"\bi\.v\.a\.\b", low):
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.95
    for i, line in enumerate(lines):
        low = line.lower()
        if "base taxa valor eur" in low:
            for j in range(i + 1, min(i + 4, len(lines))):
                vals = money_candidates_in_line(lines[j])
                if len(vals) >= 2:
                    return vals[1], 0.90
    return None

def infer_total_document(lines: List[str]) -> Optional[Tuple[str, float]]:
    for i, line in enumerate(lines):
        low = line.lower()
        if "montante total incluindo iva" in low:
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.98
        if "total documento" in low:
            after = re.split(r"total documento", line, flags=re.IGNORECASE)[-1]
            vals = money_candidates_in_line(after)
            if vals:
                return vals[-1], 0.99
            for j in range(i + 1, min(i + 3, len(lines))):
                vals = money_candidates_in_line(lines[j])
                if vals:
                    return vals[-1], 0.95
        if "total em eur" in low:
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.98
        if re.match(r"^total:\s*", low):
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.98
    return None

def infer_vat_amount(lines: List[str]) -> Optional[Tuple[str, float]]:
    for line in lines:
        low = line.lower()
        if "montante de iva" in low:
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.97
        if "total de i.v.a." in low or "iva:" in low or "resumo do iva iva:" in low:
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.97
        if "observações: i.v.a." in low or "observacoes: i.v.a." in low or re.search(r"\bi\.v\.a\.\b", low):
            vals = money_candidates_in_line(line)
            if vals:
                return vals[-1], 0.95
    for i, line in enumerate(lines):
        low = line.lower()
        if "base taxa valor eur" in low:
            for j in range(i + 1, min(i + 4, len(lines))):
                vals = money_candidates_in_line(lines[j])
                if len(vals) >= 2:
                    return vals[1], 0.90
    return None

def find_customer_nif(lines: List[str]) -> Optional[Tuple[str, float]]:
    for i, line in enumerate(lines):
        low = line.lower()
        if "cliente:" in low and "nif:" in low:
            m = PT_VAT_RE.search(line)
            if m:
                return m.group(0).replace(" ", ""), 0.95
        if "v/ contribuinte" in low or "v. contribuinte" in low:
            m = PT_VAT_RE.search(line)
            if m:
                return m.group(0).replace(" ", ""), 0.93
        if re.match(r"^contribuinte:", low):
            m = PT_VAT_RE.search(line)
            if m:
                return m.group(0).replace(" ", ""), 0.92
        if "nº de contribuinte cliente" in low or "contribuinte cliente" in low:
            m = PT_VAT_RE.search(line)
            if m:
                return m.group(0).replace(" ", ""), 0.90
        if "cliente" in low:
            m = PT_VAT_RE.search(line)
            if m:
                return m.group(0).replace(" ", ""), 0.82
            if i + 1 < len(lines):
                m = PT_VAT_RE.search(lines[i + 1])
                if m:
                    return m.group(0).replace(" ", ""), 0.75
    return None

def find_supplier_nif(lines: List[str], customer_nif: Optional[str]) -> Optional[Tuple[str, float]]:
    candidates: List[Tuple[str, float]] = []
    for line in lines:
        low = line.lower()
        for m in PT_VAT_RE.finditer(line):
            nif = m.group(0).replace(" ", "")
            score = 0.45
            if customer_nif and nif == customer_nif:
                score -= 0.40
            if ".contribuinte nº" in low or "contribuinte nº" in low or "nif pt" in low or "nipc" in low:
                score += 0.35
            if "sage" in low or "eticadata" in low or "wdmi" in low or "also" in low:
                score += 0.10
            if "cliente" in low or "v/ contribuinte" in low or "v. contribuinte" in low:
                score -= 0.25
            candidates.append((nif, score))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0]

def extract_header_fields(lines: List[str], raw_text: str) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for line in lines:
        low = line.lower()
        if "factura" in low or "fatura" in low:
            result["document_type"] = {"value": "FACTURA", "confidence": 0.98}
            break
    supplier = infer_supplier_name(lines)
    if supplier:
        result["supplier_name"] = {"value": supplier[0], "confidence": round(supplier[1], 2)}
    invoice_number = infer_invoice_number(lines)
    if invoice_number:
        result["invoice_number"] = {"value": invoice_number[0], "confidence": round(invoice_number[1], 2)}
    result.update(infer_dates(lines))
    customer_nif = find_customer_nif(lines)
    customer_nif_value = None
    if customer_nif:
        customer_nif_value = customer_nif[0]
        result["customer_nif"] = {"value": customer_nif[0], "confidence": round(customer_nif[1], 2)}
    supplier_nif = find_supplier_nif(lines, customer_nif_value)
    if supplier_nif:
        result["supplier_nif"] = {"value": supplier_nif[0], "confidence": round(supplier_nif[1], 2)}
    subtotal = infer_subtotal(lines)
    if subtotal:
        result["subtotal"] = {"value": subtotal[0], "confidence": round(subtotal[1], 2)}
    vat_amount = infer_vat_amount(lines)
    if vat_amount:
        result["vat_amount"] = {"value": vat_amount[0], "confidence": round(vat_amount[1], 2)}
    total = infer_total_document(lines) or infer_best_total(lines)
    if total:
        result["total"] = {"value": total[0], "confidence": round(total[1], 2)}
    subtotal_num = parse_money_value(result.get("subtotal", {}).get("value"))
    vat_num = parse_money_value(result.get("vat_amount", {}).get("value"))
    total_num = parse_money_value(result.get("total", {}).get("value"))
    if subtotal_num is not None and vat_num is not None:
        expected_total = round(subtotal_num + vat_num, 2)
        if total_num is None or abs(total_num - expected_total) > 0.01:
            result["total"] = {"value": format_money_pt(expected_total), "confidence": 0.93}
    if "EUR" in raw_text.upper() or "€" in raw_text:
        result["currency"] = {"value": "EUR", "confidence": 0.95}
    return result

def is_item_header_line(line: str) -> bool:
    low = line.lower()
    return (
        ("código" in low and "designação" in low)
        or ("codigo" in low and "designacao" in low)
        or ("qtd" in low and "iva" in low)
        or ("origem" in low and "código" in low and "designação" in low)
        or ("origem" in low and "codigo" in low and "designacao" in low)
    )


def is_total_or_footer_line(line: str) -> bool:
    low = line.lower().strip()
    stop_terms = [
        "valor liquido",
        "valor líquido",
        "i.v.a.",
        "iva ",
        "iva\t",
        "total documento",
        "pagamento",
        "vencimento",
        "observações",
        "observacoes",
        "atcud",
        "iban",
        "local de carga",
        "local de descarga",
        "válido como recibo",
        "valido como recibo",
        "contrib nº",
        "cliente ",
        "expedição",
        "expedicao",
        "requisição",
        "requisicao",
        "peso picking",
        "pág",
        "pag :",
        "contribuinte",
        "processado por programa certificado",
    ]
    return any(term in low for term in stop_terms)


def is_blocked_admin_line(line: str) -> bool:
    low = line.lower().strip()
    blocked = [
        "factura",
        "fatura",
        "exmos srs",
        "original",
        "duplicado",
        "triplicado",
        "quadruplicado",
        "eur",
        "origem",
        "porto :",
        "lisboa :",
        "cpc",
        "local de carga",
        "local de descarga",
        "observações",
        "observacoes",
        "atcud",
        "dd6 -",
        "v. contribuinte",
        "cliente ",
        "pagamento",
        "expedição",
        "expedicao",
        "total em pte",
    ]
    return any(x in low for x in blocked)


def is_description_candidate(line: str) -> bool:
    s = line.strip()
    low = s.lower()

    if not s or len(s) < 2:
        return False
    if is_total_or_footer_line(s):
        return False
    if is_blocked_admin_line(s):
        return False
    if is_item_header_line(s):
        return False
    if re.fullmatch(r"[\d\s.,€:+/-]+", s):
        return False
    if low in {"un", "iva", "taxa", "valor"}:
        return False

    return True


def is_number_token(tok: str) -> bool:
    return bool(re.fullmatch(r"\d+(?:[.,]\d+)?", tok))


def is_money_token(tok: str) -> bool:
    return bool(re.fullmatch(r"\d+(?:[.,]\d{2,3})", tok))


def is_unit_token(tok: str) -> bool:
    return tok.upper() in {"UN", "UNI", "KG", "G", "L", "LT", "ML", "CX", "PC", "PÇ", "PCA", "ROL", "ROLO"}


def looks_like_code_token(tok: str) -> bool:
    if len(tok) < 2:
        return False
    if not re.fullmatch(r"[A-Z0-9#./_+-]+", tok, re.IGNORECASE):
        return False
    has_letter = bool(re.search(r"[A-Z]", tok, re.IGNORECASE))
    has_digit = bool(re.search(r"\d", tok))
    return has_letter or has_digit


def parse_item_numeric_line(line: str) -> Optional[Dict[str, Any]]:
    compact = re.sub(r"\s+", " ", line).strip()

    p3 = re.match(
        r"^(?P<code>[A-Z0-9./_-]{6,})\s+"
        r"(?P<qty>\d+(?:[.,]\d+)?)\s+"
        r"(?P<unit>[A-Z]{1,5})\s+"
        r"(?P<unit_price>\d+(?:[.,]\d{2,3})?)\s+"
        r"(?P<discount>\d+(?:[.,]\d{2})?)\s+"
        r"(?P<vat_rate>\d+(?:[.,]\d{2})?)\s+"
        r"(?P<line_total>\d+(?:[.,]\d{2}))$",
        compact
    )
    if p3:
        d = p3.groupdict()
        return {
            "type": "item",
            "origin": "",
            "code": d["code"],
            "description": "",
            "qty": d["qty"],
            "unit": d["unit"],
            "unit_price": d["unit_price"],
            "discount": d["discount"],
            "vat_rate": d["vat_rate"],
            "line_total": d["line_total"],
        }

    p2 = re.match(
        r"^(?P<code>[A-Z0-9./_-]{6,})\s+"
        r"(?P<qty>\d+(?:[.,]\d+)?)\s+"
        r"(?P<unit>[A-Z]{1,5})\s+"
        r"(?P<unit_price>\d+(?:[.,]\d{2,3})?)\s+"
        r"(?P<line_total>\d+(?:[.,]\d{2}))$",
        compact
    )
    if p2:
        d = p2.groupdict()
        return {
            "type": "item",
            "origin": "",
            "code": d["code"],
            "description": "",
            "qty": d["qty"],
            "unit": d["unit"],
            "unit_price": d["unit_price"],
            "discount": "",
            "vat_rate": "",
            "line_total": d["line_total"],
        }

    p1 = re.match(
        r"^(?P<code>[A-Z0-9./_-]{6,})\s+"
        r"(?P<qty>\d+(?:[.,]\d+)?)\s+"
        r"(?P<unit_price>\d+(?:[.,]\d{2,3})?)\s+"
        r"(?P<line_total>\d+(?:[.,]\d{2}))$",
        compact
    )
    if p1:
        d = p1.groupdict()
        return {
            "type": "item",
            "origin": "",
            "code": d["code"],
            "description": "",
            "qty": d["qty"],
            "unit": "",
            "unit_price": d["unit_price"],
            "discount": "",
            "vat_rate": "",
            "line_total": d["line_total"],
        }

    return None


def parse_structured_extra_line(line: str) -> Optional[Dict[str, Any]]:
    s = re.sub(r"\s+", " ", line).strip()

    m = re.match(
        r"^(?:(?P<code>[A-Z])\s+)?"
        r"(?P<description>portes|desconto|descontos|ecotaxa|ecotaxas|transporte)\s+"
        r"(?P<discount>\d+(?:[.,]\d{2})?)\s+"
        r"(?P<line_total>\d+(?:[.,]\d{2})?)\s+"
        r"(?P<vat_rate>\d{1,2}(?:[.,]\d{1,2})?)$",
        s,
        re.IGNORECASE
    )
    if not m:
        return None

    d = m.groupdict()

    return {
        "type": "extra",
        "origin": "",
        "code": d.get("code") or "",
        "description": (d.get("description") or "").strip().title(),
        "qty": "",
        "unit": "",
        "unit_price": "",
        "discount": d.get("discount") or "",
        "vat_rate": d.get("vat_rate") or "",
        "line_total": d.get("line_total") or "",
    }


def is_service_period_line(line: str) -> bool:
    low = line.lower().strip()
    return (
        "serviço de" in low
        or "servico de" in low
        or ("até" in low and re.search(r"\d{2}/\d{2}/\d{4}", line))
        or ("ate" in low and re.search(r"\d{2}/\d{2}/\d{4}", line))
    )


def collect_description_before(lines: List[str], idx: int, max_back: int = 6) -> str:
    parts: List[str] = []

    start = max(0, idx - max_back)
    for j in range(start, idx):
        candidate = lines[j].strip()

        if not is_description_candidate(candidate):
            continue
        if parse_item_numeric_line(candidate):
            continue
        if parse_extra_charge_line(candidate, []):
            continue

        parts.append(candidate)

    unique_parts: List[str] = []
    seen = set()
    for p in parts:
        key = p.lower().strip()
        if key in seen:
            continue
        seen.add(key)
        unique_parts.append(p)

    return " ".join(unique_parts).strip()


def find_nearest_money_after(lines: List[str], start_idx: int, max_forward: int = 6) -> Optional[str]:
    for j in range(start_idx + 1, min(len(lines), start_idx + 1 + max_forward)):
        vals = money_candidates_in_line(lines[j])
        if vals:
            return vals[0]
    return None


def enrich_items_with_lonely_amounts(items: List[Dict[str, Any]], lines: List[str]) -> List[Dict[str, Any]]:
    for item in items:
        if item.get("type") != "extra":
            continue
        if item.get("line_total"):
            continue

        desc = item.get("description", "").strip().lower()
        if not desc:
            continue

        for i, line in enumerate(lines):
            if line.strip().lower() == desc:
                for nxt in lines[i + 1:i + 4]:
                    vals = money_candidates_in_line(nxt)
                    if vals:
                        item["line_total"] = vals[0]
                        break
                break

    return items


def find_items_section(lines: List[str]) -> List[str]:
    start_idx = None
    end_idx = None
    for i, line in enumerate(lines):
        low = line.lower()
        if (("código" in low and "designação" in low) or ("codigo" in low and "designacao" in low)
            or ("designação" in low and "qtd" in low) or ("designacao" in low and "qtd" in low)
            or ("qtd" in low and "iva" in low) or ("artigo" in low and "descrição" in low)
            or ("artigo" in low and "descricao" in low) or ("origem" in low and "código" in low and "designação" in low)
            or ("origem" in low and "codigo" in low and "designacao" in low)
            or ("item" in low and "descrição do produto" in low) or ("item" in low and "descricao do produto" in low)
            or ("item" in low and "preço total" in low) or ("item" in low and "preco total" in low)
            or ("referência" in low and "designação" in low and "qtd" in low)
            or ("referencia" in low and "designacao" in low and "qtd" in low)):
            start_idx = i + 1
            break
    if start_idx is None:
        return lines
    for i in range(start_idx, len(lines)):
        low = lines[i].lower()
        if any(term in low for term in [
            "valor liquido", "valor líquido", "subtotal", "total documento", "total a pagar",
            "montante líquido total sem iva", "montante liquido total sem iva", "montante de iva",
            "montante total incluindo iva", "observações", "observacoes", "atcud", "iban",
            "modo de pagamento", "condições de pagamento", "condicoes de pagamento", "vencimento",
            "transportador", "base taxa valor", "modo de expedição", "modo de expedicao",
            "taxa base de incidência", "taxa base de incidencia", "resumo do iva", "mercadoria:",
            "total ilíquido", "total iliquido", "desconto comercial:", "total de i.v.a.", "total:"]):
            end_idx = i
            break
    return lines[start_idx:end_idx] if end_idx is not None else lines[start_idx:]

def is_noise_item_line(line: str) -> bool:
    low = line.lower().strip()
    blocked_contains = [
        "base taxa valor", "montante taxa", "ecotaxas devidas", "não sujeitas a descontos",
        "nao sujeitas a descontos", "início de transporte", "inicio de transporte", "local de carga",
        "local de descarga", "exmos srs", "contribuinte", "v. contribuinte", "cliente", "atcud",
        "iban", "total documento", "valor liquido", "valor líquido", "observações", "observacoes",
        "resumo do iva", "desconto comercial:", "desconto financeiro:", "total de i.v.a.",
        "mercadoria:", "meio de expedição", "meio de expedicao", "entidade ", "referência designação",
        "referencia designacao"
    ]
    if any(x in low for x in blocked_contains):
        return True
    if len(line.strip()) > 110:
        return True
    if re.match(r"^base\s+taxa\s+valor", low):
        return True
    if "ecotaxas devidas para reciclagem" in low:
        return True
    if re.search(r"\bdata\s+\d{4}-\d{2}-\d{2}\b", low):
        return True
    if re.search(r"\blote\b", low) and re.search(r"\bloja\b", low):
        return True
    return False

def is_serial_reference_line(line: str) -> bool:
    s = re.sub(r"\s+", " ", line).strip()

    if re.match(r"^[A-Z0-9]{8,}\s+[A-Z0-9#./_-]{2,}\s+[A-Z0-9_-]{8,}(?:\s+[A-Z0-9_-]{8,})*$", s, re.IGNORECASE):
        return True

    return False


def looks_like_item_candidate(line: str) -> bool:
    s = re.sub(r"\s+", " ", line).strip()
    if not s or len(s) < 8:
        return False
    if is_item_header_line(s) or is_total_or_footer_line(s) or is_noise_item_line(s) or is_serial_reference_line(s) or is_group_header_line(s):
        return False
    if re.search(r"\d+(?:[.,]\d+)?\s+(?:UN|UNI|KG|G|L|LT|ML|CX|PC|PÇ|PCA|ROL|ROLO)\s+\d+(?:[.,]\d{2,3})\s+\d+(?:[.,]\d{2,3})\s+\d+(?:[.,]\d{2,3})\s*$", s, re.IGNORECASE):
        return True
    if re.search(r"\d+(?:[.,]\d+)?[A-Z]{1,5}\s+\d+(?:[.,]\d{2,3})(?:\s+\d+(?:[.,]\d{2,3})){2,4}\s*$", s, re.IGNORECASE):
        return True
    if re.search(r"\d+(?:[.,]\d+)?\s+(?:UN|UNI|KG|G|L|LT|ML|CX|PC|PÇ|PCA|ROL|ROLO)\s+\d+(?:[.,]\d{2,3})\s+\d+(?:[.,]\d{1,2})\s+\d+(?:[.,]\d{2})\s*$", s, re.IGNORECASE):
        return True
    if re.search(r"\d+(?:[.,]\d{2})\s+\d{1,2}(?:[.,]\d{1,2})?\s*$", s):
        return True
    if re.search(r"\b\d+(?:[.,]\d+)?\s+\d+(?:[.,]\d{2,3})\s+\d+(?:[.,]\d{2})\s*$", s):
        return True
    return False

def parse_generic_item_line(line: str) -> Optional[Dict[str, Any]]:
    s = re.sub(r"\s+", " ", line).strip()
    parts = s.split()
    if len(parts) < 6:
        return None
    i = len(parts) - 1
    if i < 0 or not re.fullmatch(r"\d{1,2}(?:[.,]\d{1,2})?", parts[i]):
        return None
    vat_rate = parts[i]
    i -= 1
    if i < 0 or not is_money_token(parts[i]):
        return None
    line_total = parts[i]
    i -= 1
    if i < 0 or not is_money_token(parts[i]):
        return None
    discount = parts[i]
    i -= 1
    if i < 0 or not is_money_token(parts[i]):
        return None
    unit_price = parts[i]
    i -= 1
    if i < 0:
        return None
    q, u = split_attached_unit_token(parts[i])
    if q and u:
        qty, unit = q, u
        i -= 1
    elif i >= 1 and is_unit_token(parts[i]) and is_number_token(parts[i-1]):
        qty, unit = parts[i-1], parts[i].upper()
        i -= 2
    else:
        return None
    left = parts[:i + 1]
    if not left:
        return None
    code = left[0] if looks_like_code_token(left[0]) else ""
    description_tokens = left[1:] if code else left[:]
    origin = ""
    if description_tokens and re.fullmatch(r"[A-Z]{2,8}", description_tokens[0], re.IGNORECASE):
        origin = description_tokens[0]
        description_tokens = description_tokens[1:]
    description = " ".join(description_tokens).strip()
    if len(description) < 2:
        return None
    return {"type": "item", "origin": origin, "code": code, "description": description, "qty": qty, "unit": unit, "unit_price": unit_price, "discount": discount, "vat_rate": vat_rate, "line_total": line_total}

def is_description_continuation_line(line: str) -> bool:
    s = re.sub(r"\s+", " ", line).strip()
    low = s.lower()
    if not s:
        return False
    if is_item_header_line(s) or is_total_or_footer_line(s) or is_noise_item_line(s):
        return False
    if looks_like_item_candidate(s) or parse_structured_extra_line(s) or is_serial_reference_line(s):
        return False
    if len(s) > 90 or re.fullmatch(r"[\d\s.,€:+/-]+", s):
        return False
    if re.fullmatch(r"[A-Za-zÀ-ÿ.-]+", s) and len(s.split()) <= 3:
        return False
    blocked = ["n.º de peça do fabricante", "n.o de peça do fabricante", "nº de peça do fabricante", "code ean/upc", "ean/upc", "remessa", "encomenda", "modo de expedição", "modo de expedicao", "incoterm", "disponibilizado em", "loja b", "faro", "portugal", "fatura", "duplicado", "original", "cliente:", "nr. doc.:", "licenciado a:", "valor em falta", "o próximo escalão", "facturas à cobrança", "facturas à cobranca", "software phc", "material usado/recondicionado", "o 3º ano de garantia", "pagamento por multibanco"]
    if any(x in low for x in blocked):
        return False
    return True

def split_attached_unit_token(tok: str) -> Tuple[Optional[str], Optional[str]]:
    m = re.fullmatch(r"(\d+(?:[.,]\d+)?)([A-Z]{1,5})", tok, re.IGNORECASE)
    if not m:
        return None, None
    return m.group(1), m.group(2).upper()

def is_group_header_line(line: str) -> bool:
    s = re.sub(r"\s+", " ", line).strip()
    if re.match(r"^ECR-[A-Z0-9/.-]+\s+\(\d{2}/\d{2}/\d{4}\)\s+-\s+\d+", s, re.IGNORECASE):
        return True
    if re.match(r"^ref\.\s+ao\s+doc\.", s, re.IGNORECASE):
        return True
    if re.match(r"^nota\s+encomenda\s+cliente", s, re.IGNORECASE):
        return True
    return False

def parse_generic_item_line_with_rowno(line: str) -> Optional[Dict[str, Any]]:
    s = re.sub(r"\s+", " ", line).strip()
    parts = s.split()
    if len(parts) < 7:
        return None
    if not is_money_token(parts[-1]):
        return None
    row_no = parts[-1]
    row_val = parse_money_value(row_no)
    if row_val is None or row_val <= 0 or row_val > 200 or abs(row_val - round(row_val)) > 0.001:
        return None
    q, u = split_attached_unit_token(parts[-5]) if len(parts) >= 5 else (None, None)
    if not (q and u):
        return None
    if not is_money_token(parts[-4]) or not is_money_token(parts[-3]) or not is_money_token(parts[-2]):
        return None
    qty, unit = q, u
    unit_price = parts[-4]
    discount = parts[-3]
    line_total = parts[-2]
    left = parts[:-5]
    if len(left) < 2:
        return None
    code = left[0]
    if not looks_like_code_token(code):
        return None
    origin = ""
    description_tokens = left[1:]
    if description_tokens and re.fullmatch(r"[A-Z]{2,6}", description_tokens[0], re.IGNORECASE):
        origin = description_tokens[0]
        description_tokens = description_tokens[1:]
    description = " ".join(description_tokens).strip()
    if len(description) < 2:
        return None
    return {"type": "item", "origin": origin, "code": code, "description": description, "qty": qty, "unit": unit, "unit_price": unit_price, "discount": discount, "vat_rate": "", "line_total": line_total, "line_no": row_no}

def parse_generic_item_line_with_vat_before_total(line: str) -> Optional[Dict[str, Any]]:
    s = re.sub(r"\s+", " ", line).strip()
    parts = s.split()
    if len(parts) < 7:
        return None
    if not is_money_token(parts[-1]) or not re.fullmatch(r"\d{1,2}(?:[.,]\d{1,2})?", parts[-2]) or not is_money_token(parts[-3]):
        return None
    line_total = parts[-1]
    vat_rate = parts[-2]
    unit_price = parts[-3]
    if len(parts) < 5 or not is_unit_token(parts[-4]) or not is_number_token(parts[-5]):
        return None
    qty = parts[-5]
    unit = parts[-4].upper()
    left = parts[:-5]
    if len(left) < 2:
        return None
    code = left[0] if looks_like_code_token(left[0]) else ""
    description_tokens = left[1:] if code else left[:]
    origin = ""
    if description_tokens and re.fullmatch(r"[A-Z]{2,8}", description_tokens[0], re.IGNORECASE):
        origin = description_tokens[0]
        description_tokens = description_tokens[1:]
    description = " ".join(description_tokens).strip()
    if len(description) < 2:
        return None
    return {"type": "item", "origin": origin, "code": code, "description": description, "qty": qty, "unit": unit, "unit_price": unit_price, "discount": "", "vat_rate": vat_rate, "line_total": line_total}


def parse_extra_charge_line(line: str, next_lines: List[str]) -> Optional[Dict[str, Any]]:
    s = re.sub(r"\s+", " ", line).strip()
    low = s.lower()
    if is_noise_item_line(s):
        return None
    structured = parse_structured_extra_line(s)
    if structured:
        return structured
    labels = ["portes", "desconto", "descontos", "ecotaxa", "ecotaxas", "transporte"]
    if not any(label in low for label in labels):
        return None
    if len(s) > 60:
        return None
    if any(x in low for x in ["base taxa", "montante taxa", "valor eur", "desconto comercial", "desconto financeiro"]):
        return None
    vals = money_candidates_in_line(s)
    if vals:
        desc = s
        desc = re.sub(r"\s+\d+(?:[.,]\d{2})?\s+\d+(?:[.,]\d{2})?\s+\d{1,2}(?:[.,]\d{1,2})?$", "", desc).strip()
        desc = re.sub(r"^[A-Z]\s+", "", desc).strip()
        return {"type": "extra", "origin": "", "code": "", "description": desc, "qty": "", "unit": "", "unit_price": "", "discount": "", "vat_rate": "", "line_total": vals[-1]}
    for nxt in next_lines[:2]:
        if is_noise_item_line(nxt):
            continue
        vals = money_candidates_in_line(nxt)
        if vals:
            return {"type": "extra", "origin": "", "code": "", "description": s, "qty": "", "unit": "", "unit_price": "", "discount": "", "vat_rate": "", "line_total": vals[0]}
    return None

def extract_item_lines(lines: List[str]) -> List[Dict[str, Any]]:
    section = find_items_section(lines)
    items: List[Dict[str, Any]] = []
    used_keys = set()
    last_item_idx: Optional[int] = None
    for idx, line in enumerate(section):
        s = re.sub(r"\s+", " ", line).strip()
        low = s.lower()
        if not s:
            continue
        if is_item_header_line(s) or is_total_or_footer_line(s) or is_noise_item_line(s) or is_serial_reference_line(s):
            continue
        if low.startswith("transportado da página anterior") or low.startswith("transportado da pagina anterior") or low.startswith("transporte para a página seguinte") or low.startswith("transporte para a pagina seguinte"):
            continue
        if is_group_header_line(s):
            continue
        if looks_like_item_candidate(s):
            item = parse_generic_item_line_with_rowno(s)
            if not item:
                item = parse_generic_item_line(s)
            if not item:
                item = parse_generic_item_line_with_vat_before_total(s)
            if not item:
                item = parse_generic_item_line_simple(s)
            if item:
                key = (item.get("code", ""), item.get("description", ""), item.get("qty", ""), item.get("line_total", ""))
                if key not in used_keys:
                    used_keys.add(key)
                    items.append(item)
                    last_item_idx = len(items) - 1
                continue
        parsed = parse_item_numeric_line(s)
        if parsed:
            desc = collect_description_before(section, idx, max_back=3)
            if is_noise_item_line(desc):
                desc = ""
            parsed["description"] = desc
            key = (parsed.get("type", ""), parsed.get("code", ""), parsed.get("description", ""), parsed.get("line_total", ""))
            if key not in used_keys:
                used_keys.add(key)
                items.append(parsed)
                last_item_idx = len(items) - 1
            continue
        if is_service_period_line(s):
            service_item = {"type": "service", "origin": "", "code": "", "description": s, "qty": "1", "unit": "", "unit_price": "", "discount": "", "vat_rate": "", "line_total": ""}
            key = (service_item["type"], service_item["description"])
            if key not in used_keys:
                used_keys.add(key)
                items.append(service_item)
                last_item_idx = len(items) - 1
            continue
        if not items or ("portes" in low or low.startswith("desconto ") or low.startswith("descontos ")):
            extra = parse_extra_charge_line(s, section[idx + 1: idx + 3])
            if extra:
                key = (extra.get("type", ""), extra.get("description", ""), extra.get("line_total", ""))
                if key not in used_keys:
                    used_keys.add(key)
                    items.append(extra)
                    last_item_idx = len(items) - 1
                continue
        if is_description_continuation_line(s) and last_item_idx is not None and items[last_item_idx].get("type") == "item":
            prev = items[last_item_idx].get("description", "").strip()
            if s.lower() not in prev.lower():
                items[last_item_idx]["description"] = (prev + " " + s).strip()
            continue
    items = enrich_items_with_lonely_amounts(items, section)
    cleaned: List[Dict[str, Any]] = []
    for item in items:
        desc = item.get("description", "").strip().lower()
        if not desc:
            continue
        if is_noise_item_line(desc):
            continue
        if desc in {"base taxa valor", "base taxa valor eur", "descarga transporte"}:
            continue
        cleaned.append(item)
    return cleaned



SUPPLIER_MAP_BY_NIF = {
    # "501111111": "FOR0001",
}

SUPPLIER_MAP_BY_NAME = {
    "sage portugal, s.a.": "1",
}

ARTICLE_MAP_BY_CODE = {
    # "A001": "A001",
}

ARTICLE_MAP_BY_DESC = {
    # "artigo exemplo": "A001",
}

DEFAULT_DOC_TYPE = "COMPRA"
DEFAULT_SERIE = "2025"
DEFAULT_CURRENCY = "EUR"

GENERIC_ARTICLE_BY_TYPE = {
    "service": "SRV-GEN",
    "extra": "OUTROS",
}


def get_header_value(extracted: Dict[str, Any], key: str) -> Optional[str]:
    node = extracted.get("header", {}).get(key)
    if not node:
        return None
    value = node.get("value")
    if value is None:
        return None
    return str(value).strip()


def parse_pt_money_or_none(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    return parse_money_value(str(value))


def parse_number_or_none(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None

    s = str(value).strip()
    if not s:
        return None

    s = s.replace(" ", "")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")

    try:
        return float(s)
    except ValueError:
        return None


def parse_date_to_iso(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    raw = str(value).strip()
    formats = ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d")

    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue

    return None


def normalize_name_key(value: Optional[str]) -> str:
    if not value:
        return ""
    s = value.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def normalize_nif(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    digits = re.sub(r"\D", "", str(value))
    return digits or None


def resolve_supplier_code(supplier_name: Optional[str], supplier_nif: Optional[str]) -> Optional[str]:
    nif_key = normalize_nif(supplier_nif)
    if nif_key and nif_key in SUPPLIER_MAP_BY_NIF:
        return SUPPLIER_MAP_BY_NIF[nif_key]

    name_key = normalize_name_key(supplier_name)
    if name_key and name_key in SUPPLIER_MAP_BY_NAME:
        return SUPPLIER_MAP_BY_NAME[name_key]

    return None


def resolve_article_code(item: Dict[str, Any]) -> Optional[str]:
    raw_code = (item.get("code") or "").strip()
    if raw_code and raw_code in ARTICLE_MAP_BY_CODE:
        return ARTICLE_MAP_BY_CODE[raw_code]

    desc_key = normalize_name_key(item.get("description"))
    if desc_key and desc_key in ARTICLE_MAP_BY_DESC:
        return ARTICLE_MAP_BY_DESC[desc_key]

    item_type = (item.get("type") or "").strip().lower()
    if item_type in GENERIC_ARTICLE_BY_TYPE:
        return GENERIC_ARTICLE_BY_TYPE[item_type]

    return None


def build_extracted_payload(
    filename: str,
    raw_text: str,
    cleaned_text: str,
    cleaned_lines: List[str],
    removed_repeated_lines: int,
    extraction_mode: str,
) -> Dict[str, Any]:
    header = extract_header_fields(cleaned_lines, cleaned_text)
    items = extract_item_lines(cleaned_lines)

    return {
        "filename": filename,
        "raw_text": raw_text,
        "cleaned_text": cleaned_text,
        "line_count": len(cleaned_lines),
        "removed_repeated_lines": removed_repeated_lines,
        "extraction_mode": extraction_mode,
        "header": header,
        "items": items,
    }


def build_payload_sage(extracted: Dict[str, Any]) -> Dict[str, Any]:
    supplier_name = get_header_value(extracted, "supplier_name")
    supplier_nif = get_header_value(extracted, "supplier_nif")
    customer_nif = get_header_value(extracted, "customer_nif")
    invoice_number = get_header_value(extracted, "invoice_number")
    invoice_date = get_header_value(extracted, "invoice_date")
    due_date = get_header_value(extracted, "due_date")
    currency = get_header_value(extracted, "currency") or DEFAULT_CURRENCY

    supplier_code = resolve_supplier_code(supplier_name, supplier_nif)

    subtotal = parse_pt_money_or_none(get_header_value(extracted, "subtotal"))
    vat_amount = parse_pt_money_or_none(get_header_value(extracted, "vat_amount"))
    total = parse_pt_money_or_none(get_header_value(extracted, "total"))

    lines: List[Dict[str, Any]] = []
    errors: List[str] = []
    warnings: List[str] = []

    for idx, item in enumerate(extracted.get("items", []), start=1):
        item_type = (item.get("type") or "item").strip().lower()
        article_code = resolve_article_code(item)

        qty = parse_number_or_none(item.get("qty"))
        if qty is None:
            qty = 1.0 if item_type in {"service", "extra"} else None

        unit_price = parse_pt_money_or_none(item.get("unit_price"))
        discount_percent = parse_number_or_none(item.get("discount")) or 0.0
        vat_rate = parse_number_or_none(item.get("vat_rate"))
        line_total = parse_pt_money_or_none(item.get("line_total"))

        line = {
            "line_no": idx,
            "type": item_type,
            "article_code": article_code,
            "raw_code": (item.get("code") or "").strip(),
            "description": (item.get("description") or "").strip(),
            "qty": qty,
            "unit": (item.get("unit") or "UN").strip() or "UN",
            "unit_price": unit_price,
            "discount_percent": discount_percent,
            "vat_rate": vat_rate,
            "line_total": line_total,
        }

        if not line["description"]:
            warnings.append(f"Linha {idx}: descrição vazia")
        if item_type == "item" and not article_code:
            warnings.append(f"Linha {idx}: artigo não resolvido")
        if item_type in {"service", "extra"} and not article_code:
            warnings.append(f"Linha {idx}: sem artigo genérico configurado para tipo '{item_type}'")

        lines.append(line)

    if not supplier_code:
        errors.append("Fornecedor não resolvido para código Sage")

    if not invoice_number:
        errors.append("Número externo da fatura não encontrado")

    if not parse_date_to_iso(invoice_date):
        errors.append("Data do documento inválida ou não encontrada")

    if not lines:
        errors.append("Nenhuma linha encontrada")

    if subtotal is not None and vat_amount is not None and total is not None:
        expected_total = round(subtotal + vat_amount, 2)
        if abs(total - expected_total) > 0.01:
            errors.append("Total inconsistente com subtotal + IVA")

    ready_to_post = len(errors) == 0

    return {
        "source": {
            "filename": extracted.get("filename"),
            "extraction_mode": extracted.get("extraction_mode"),
            "raw_supplier_name": supplier_name,
            "raw_supplier_nif": supplier_nif,
            "raw_invoice_number": invoice_number,
            "raw_customer_nif": customer_nif,
        },
        "document": {
            "document_type": DEFAULT_DOC_TYPE,
            "serie": DEFAULT_SERIE,
            "external_number": invoice_number,
            "document_date": parse_date_to_iso(invoice_date),
            "due_date": parse_date_to_iso(due_date),
            "currency": currency,
            "supplier_code": supplier_code,
            "supplier_name": supplier_name,
            "supplier_nif": normalize_nif(supplier_nif),
            "customer_nif": normalize_nif(customer_nif),
            "subtotal": subtotal,
            "vat_amount": vat_amount,
            "total": total,
            "notes": "Importado automaticamente de PDF",
        },
        "lines": lines,
        "validation": {
            "ready_to_post": ready_to_post,
            "errors": errors,
            "warnings": warnings,
        },
    }

SAGE_BRIDGE_URL = os.getenv("SAGE_BRIDGE_URL", "http://127.0.0.1:5055")

SUPPLIER_MAP_BY_NIF = {
    # "501111111": "FOR0001",
}

SUPPLIER_MAP_BY_NAME = {
    # "sage portugal, s.a.": "FOR0001",
}

ARTICLE_MAP_BY_CODE = {
    # "A001": "A001",
}

ARTICLE_MAP_BY_DESC = {
    # "artigo exemplo": "A001",
}

DEFAULT_DOC_TYPE = "COMPRA"
DEFAULT_SERIE = "2025"
DEFAULT_CURRENCY = "EUR"

GENERIC_ARTICLE_BY_TYPE = {
    "service": "SERVICO",
    "extra": "OUTROS",
}


class SageSourceModel(BaseModel):
    filename: Optional[str] = None
    extraction_mode: Optional[str] = None
    raw_supplier_name: Optional[str] = None
    raw_supplier_nif: Optional[str] = None
    raw_invoice_number: Optional[str] = None
    raw_customer_nif: Optional[str] = None


class SageDocumentModel(BaseModel):
    document_type: str = DEFAULT_DOC_TYPE
    serie: str = DEFAULT_SERIE
    external_number: Optional[str] = None
    document_date: Optional[str] = None
    due_date: Optional[str] = None
    currency: str = DEFAULT_CURRENCY
    supplier_code: Optional[str] = None
    supplier_name: Optional[str] = None
    supplier_nif: Optional[str] = None
    customer_nif: Optional[str] = None
    subtotal: Optional[float] = None
    vat_amount: Optional[float] = None
    total: Optional[float] = None
    notes: Optional[str] = None


class SageLineModel(BaseModel):
    line_no: int
    type: str = "item"
    article_code: Optional[str] = None
    raw_code: Optional[str] = None
    description: str = ""
    qty: Optional[float] = None
    unit: str = "UN"
    unit_price: Optional[float] = None
    discount_percent: float = 0.0
    vat_rate: Optional[float] = None
    line_total: Optional[float] = None


class SageValidationModel(BaseModel):
    ready_to_post: bool = False
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class SagePayloadModel(BaseModel):
    source: SageSourceModel
    document: SageDocumentModel
    lines: List[SageLineModel]
    validation: SageValidationModel


def get_header_value(extracted: Dict[str, Any], key: str) -> Optional[str]:
    node = extracted.get("header", {}).get(key)
    if not node:
        return None
    value = node.get("value")
    if value is None:
        return None
    return str(value).strip()


def parse_pt_money_or_none(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    return parse_money_value(str(value))


def parse_number_or_none(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None

    s = str(value).strip()
    if not s:
        return None

    s = s.replace(" ", "")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")

    try:
        return float(s)
    except ValueError:
        return None


def parse_date_to_iso(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    raw = str(value).strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue

    return None


def normalize_name_key(value: Optional[str]) -> str:
    if not value:
        return ""
    s = value.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def normalize_nif(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    digits = re.sub(r"\D", "", str(value))
    return digits or None


def resolve_supplier_code(supplier_name: Optional[str], supplier_nif: Optional[str]) -> Optional[str]:
    nif_key = normalize_nif(supplier_nif)
    if nif_key and nif_key in SUPPLIER_MAP_BY_NIF:
        return SUPPLIER_MAP_BY_NIF[nif_key]

    name_key = normalize_name_key(supplier_name)
    if name_key and name_key in SUPPLIER_MAP_BY_NAME:
        return SUPPLIER_MAP_BY_NAME[name_key]

    return None


def resolve_article_code(item: Dict[str, Any]) -> Optional[str]:
    raw_code = (item.get("code") or "").strip()
    if raw_code and raw_code in ARTICLE_MAP_BY_CODE:
        return ARTICLE_MAP_BY_CODE[raw_code]

    desc_key = normalize_name_key(item.get("description"))
    if desc_key and desc_key in ARTICLE_MAP_BY_DESC:
        return ARTICLE_MAP_BY_DESC[desc_key]

    item_type = (item.get("type") or "").strip().lower()
    if item_type in GENERIC_ARTICLE_BY_TYPE:
        return GENERIC_ARTICLE_BY_TYPE[item_type]

    return None


def build_extracted_payload(
    filename: str,
    raw_text: str,
    cleaned_text: str,
    cleaned_lines: List[str],
    removed_repeated_lines: int,
    extraction_mode: str,
) -> Dict[str, Any]:
    header = extract_header_fields(cleaned_lines, cleaned_text)
    items = extract_item_lines(cleaned_lines)

    return {
        "filename": filename,
        "raw_text": raw_text,
        "cleaned_text": cleaned_text,
        "line_count": len(cleaned_lines),
        "removed_repeated_lines": removed_repeated_lines,
        "extraction_mode": extraction_mode,
        "header": header,
        "items": items,
    }


def build_payload_sage(extracted: Dict[str, Any]) -> SagePayloadModel:
    supplier_name = get_header_value(extracted, "supplier_name")
    supplier_nif = get_header_value(extracted, "supplier_nif")
    customer_nif = get_header_value(extracted, "customer_nif")
    invoice_number = get_header_value(extracted, "invoice_number")
    invoice_date = get_header_value(extracted, "invoice_date")
    due_date = get_header_value(extracted, "due_date")
    currency = get_header_value(extracted, "currency") or DEFAULT_CURRENCY

    supplier_code = resolve_supplier_code(supplier_name, supplier_nif)

    subtotal = parse_pt_money_or_none(get_header_value(extracted, "subtotal"))
    vat_amount = parse_pt_money_or_none(get_header_value(extracted, "vat_amount"))
    total = parse_pt_money_or_none(get_header_value(extracted, "total"))

    lines: List[SageLineModel] = []
    errors: List[str] = []
    warnings: List[str] = []

    for idx, item in enumerate(extracted.get("items", []), start=1):
        item_type = (item.get("type") or "item").strip().lower()
        article_code = resolve_article_code(item)

        qty = parse_number_or_none(item.get("qty"))
        if qty is None and item_type in {"service", "extra"}:
            qty = 1.0

        line = SageLineModel(
            line_no=idx,
            type=item_type,
            article_code=article_code,
            raw_code=(item.get("code") or "").strip(),
            description=(item.get("description") or "").strip(),
            qty=qty,
            unit=((item.get("unit") or "UN").strip() or "UN"),
            unit_price=parse_pt_money_or_none(item.get("unit_price")),
            discount_percent=parse_number_or_none(item.get("discount")) or 0.0,
            vat_rate=parse_number_or_none(item.get("vat_rate")),
            line_total=parse_pt_money_or_none(item.get("line_total")),
        )

        if not line.description:
            warnings.append(f"Linha {idx}: descrição vazia")
        if item_type == "item" and not line.article_code:
            warnings.append(f"Linha {idx}: artigo não resolvido")
        if item_type in {"service", "extra"} and not line.article_code:
            warnings.append(f"Linha {idx}: sem artigo genérico configurado para tipo '{item_type}'")

        lines.append(line)

    if not supplier_code:
        errors.append("Fornecedor não resolvido para código Sage")

    if not invoice_number:
        errors.append("Número externo da fatura não encontrado")

    if not parse_date_to_iso(invoice_date):
        errors.append("Data do documento inválida ou não encontrada")

    if not lines:
        errors.append("Nenhuma linha encontrada")

    if subtotal is not None and vat_amount is not None and total is not None:
        expected_total = round(subtotal + vat_amount, 2)
        if abs(total - expected_total) > 0.01:
            errors.append("Total inconsistente com subtotal + IVA")

    payload = SagePayloadModel(
        source=SageSourceModel(
            filename=extracted.get("filename"),
            extraction_mode=extracted.get("extraction_mode"),
            raw_supplier_name=supplier_name,
            raw_supplier_nif=supplier_nif,
            raw_invoice_number=invoice_number,
            raw_customer_nif=customer_nif,
        ),
        document=SageDocumentModel(
            document_type=DEFAULT_DOC_TYPE,
            serie=DEFAULT_SERIE,
            external_number=invoice_number,
            document_date=parse_date_to_iso(invoice_date),
            due_date=parse_date_to_iso(due_date),
            currency=currency,
            supplier_code=supplier_code,
            supplier_name=supplier_name,
            supplier_nif=normalize_nif(supplier_nif),
            customer_nif=normalize_nif(customer_nif),
            subtotal=subtotal,
            vat_amount=vat_amount,
            total=total,
            notes="Importado automaticamente de PDF",
        ),
        lines=lines,
        validation=SageValidationModel(
            ready_to_post=(len(errors) == 0),
            errors=errors,
            warnings=warnings,
        ),
    )

    return payload


def to_bridge_payload(payload: SagePayloadModel) -> Dict[str, Any]:
    return {
        "supplier_code": payload.document.supplier_code,
        "serie": payload.document.serie,
        "document_type": payload.document.document_type,
        "external_number": payload.document.external_number,
        "document_date": payload.document.document_date,
        "due_date": payload.document.due_date,
        "currency": payload.document.currency,
        "notes": payload.document.notes,
        "lines": [
            {
                "line_no": line.line_no,
                "article_code": line.article_code,
                "description": line.description,
                "qty": line.qty,
                "unit": line.unit,
                "unit_price": line.unit_price,
                "discount_percent": line.discount_percent,
                "vat_rate": line.vat_rate,
                "line_total": line.line_total,
                "type": line.type,
                "raw_code": line.raw_code,
            }
            for line in payload.lines
        ],
    }

@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return INDEX_HTML


@app.get("/extract")
def extract_info():
    return {"message": "Este endpoint aceita apenas POST com um ficheiro PDF no campo 'file'. Usa a interface em /."}


@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        return JSONResponse(
            status_code=400,
            content={"detail": "Só PDFs são suportados."}
        )

    data = await file.read()
    raw_text, extraction_mode = extract_text_from_pdf_bytes(data)

    if not raw_text:
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Não foi possível extrair texto. Este PDF pode ser um scan/imagem. O próximo passo é adicionar OCR local como fallback."
            }
        )

    cleaned_lines, removed_repeated_lines = cleanup_lines(raw_text)
    cleaned_lines = join_broken_label_lines(cleaned_lines)
    cleaned_text = "\n".join(cleaned_lines)

    extracted = build_extracted_payload(
        filename=file.filename,
        raw_text=raw_text,
        cleaned_text=cleaned_text,
        cleaned_lines=cleaned_lines,
        removed_repeated_lines=removed_repeated_lines,
        extraction_mode=extraction_mode,
    )

    payload_sage = build_payload_sage(extracted)

    return {
        **extracted,
        "payload_sage": payload_sage.model_dump(),
    }

@app.post("/build-payload")
async def build_payload(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        return JSONResponse(
            status_code=400,
            content={"detail": "Só PDFs são suportados."}
        )

    data = await file.read()
    raw_text, extraction_mode = extract_text_from_pdf_bytes(data)

    if not raw_text:
        return JSONResponse(
            status_code=422,
            content={"detail": "Não foi possível extrair texto do PDF."}
        )

    cleaned_lines, removed_repeated_lines = cleanup_lines(raw_text)
    cleaned_lines = join_broken_label_lines(cleaned_lines)
    cleaned_text = "\n".join(cleaned_lines)

    extracted = build_extracted_payload(
        filename=file.filename,
        raw_text=raw_text,
        cleaned_text=cleaned_text,
        cleaned_lines=cleaned_lines,
        removed_repeated_lines=removed_repeated_lines,
        extraction_mode=extraction_mode,
    )

    payload_sage = build_payload_sage(extracted)

    return {
        "extracted": extracted,
        "payload_sage": payload_sage.model_dump(),
    }

@app.post("/send-to-sage")
async def send_to_sage(payload: SagePayloadModel = Body(...)):
    if not payload.validation.ready_to_post:
        return JSONResponse(
            status_code=400,
            content={
                "detail": "O payload não está pronto para envio.",
                "validation": payload.validation.model_dump(),
            },
        )

    bridge_payload = to_bridge_payload(payload)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{SAGE_BRIDGE_URL}/purchase-invoices",
                json=bridge_payload,
            )
    except httpx.RequestError as exc:
        return JSONResponse(
            status_code=502,
            content={
                "detail": "Não foi possível contactar o bridge do Sage.",
                "bridge_url": SAGE_BRIDGE_URL,
                "error": str(exc),
            },
        )

    try:
        bridge_result = response.json()
    except Exception:
        bridge_result = {"raw_response": response.text}

    if response.status_code >= 400:
        return JSONResponse(
            status_code=502,
            content={
                "detail": "O bridge do Sage devolveu erro.",
                "bridge_status": response.status_code,
                "bridge_response": bridge_result,
            },
        )

    return {
        "ok": True,
        "bridge_url": SAGE_BRIDGE_URL,
        "sent_payload": bridge_payload,
        "bridge_response": bridge_result,
    }