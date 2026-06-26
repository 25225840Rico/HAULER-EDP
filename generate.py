#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de cotizaciones Hauler — HTML (Jinja2) → PDF (Playwright + Chromium).

Uso:
    python generate.py cotizaciones/COT-0216-2026.yaml
    python generate.py cotizaciones/COT-0216-2026.yaml --output ./output/
    python generate.py cotizaciones/COT-0216-2026.yaml --preview
    python generate.py --new COT-0217-2026

Diseño 100% data-driven: ningún texto de negocio vive en los templates.
Todo viene de config/*.yaml + el YAML de la cotización (que tiene precedencia).
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import mimetypes
import sys
import webbrowser
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

# La consola de Windows suele ser cp1252; forzamos UTF-8 para los mensajes.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass

# ─── Rutas base ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
CONFIG_DIR = ROOT / "config"
TEMPLATES_DIR = ROOT / "templates"
COTIZ_DIR = ROOT / "cotizaciones"
OUTPUT_DIR = ROOT / "output"

# Orden de las páginas del documento. Cada entrada = una hoja A4.
# foot_kind: brand (tagline) | compact (empresa·COT) | confidential (cliente·COT)
PAGES = [
    {"tag": "Propuesta Comercial",                  "template": "portada.html.j2",     "foot_kind": "brand"},
    {"tag": "El Servicio",                          "template": "servicio.html.j2",    "foot_kind": "compact"},
    {"tag": "Propuesta Económica",                  "template": "precios.html.j2",     "foot_kind": "compact"},
    {"tag": "Condiciones Comerciales y Operacionales", "template": "condiciones.html.j2", "foot_kind": "compact"},
    {"tag": "Contacto y Firma",                     "template": "firma.html.j2",       "foot_kind": "confidential"},
]

MESES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


# ─── Utilidades ──────────────────────────────────────────────────────────────
def load_yaml(path: Path) -> dict:
    if not path.exists():
        sys.exit(f"✗ No existe el archivo: {path}")
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def deep_merge(base: dict, override: dict) -> dict:
    """Merge recursivo. `override` gana. Las listas se reemplazan completas."""
    out = dict(base)
    for k, v in (override or {}).items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = deep_merge(out[k], v)
        elif v is not None:
            out[k] = v
        elif k not in out:
            out[k] = v
    return out


def clp(value) -> str:
    """7500000 → '$ 7.500.000' (separador de miles estilo chileno)."""
    try:
        n = int(round(float(value)))
    except (TypeError, ValueError):
        return str(value)
    return "$ " + f"{n:,.0f}".replace(",", ".")


def fmt_fecha(d: dt.date) -> str:
    return f"{d.day:02d} de {MESES[d.month]} de {d.year}"


def embed_image(path, label: str = "imagen") -> str | None:
    """Embebe una imagen como data-URI base64 (PDF autónomo). None si no hay/falta."""
    if not path:
        return None
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    if not p.exists():
        print(f"⚠ {label}: archivo inexistente ({p}) — se omite.")
        return None
    mime = mimetypes.guess_type(str(p))[0] or "image/png"
    data = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def build_context(cotiz_path: Path) -> dict:
    """Carga + mergea config/defaults/cotización y arma el contexto del template."""
    empresa = load_yaml(CONFIG_DIR / "empresa.yaml")
    defaults = load_yaml(CONFIG_DIR / "defaults.yaml")
    design = load_yaml(CONFIG_DIR / "design.yaml")
    cotiz = load_yaml(cotiz_path)

    data = deep_merge(defaults, cotiz)  # la cotización tiene precedencia

    # Fechas
    fecha_raw = data.get("fecha")
    if fecha_raw:
        fecha = fecha_raw if isinstance(fecha_raw, dt.date) else dt.date.fromisoformat(str(fecha_raw))
    else:
        fecha = dt.date.today()
    vigencia = int(data.get("vigencia_dias", 30))
    valida_hasta = fecha + dt.timedelta(days=vigencia)

    ctx = dict(data)
    ctx.update(
        empresa=empresa,
        design=design,
        pages=PAGES,
        logo_data_uri=embed_image(empresa.get("logo_path"), "logo_path"),
        firma_data_uri=embed_image(empresa.get("firma_emisor_path"), "firma_emisor_path"),
        fecha_fmt=fmt_fecha(fecha),
        valida_hasta_fmt=fmt_fecha(valida_hasta),
        vigencia_dias=vigencia,
    )
    return ctx


def render_html(ctx: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["clp"] = clp
    return env.get_template("base.html.j2").render(**ctx)


def render_pdf(html: str, out_path: Path) -> int:
    """Genera el PDF con Playwright. Devuelve el número de páginas (len(PAGES))."""
    from playwright.sync_api import sync_playwright

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="networkidle")
        page.pdf(
            path=str(out_path),
            format="A4",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        browser.close()
    return len(PAGES)


# ─── Comandos ────────────────────────────────────────────────────────────────
def cmd_generate(cotiz_arg: str, output: str | None, preview: bool) -> None:
    cotiz_path = Path(cotiz_arg)
    if not cotiz_path.is_absolute() and not cotiz_path.exists():
        alt = COTIZ_DIR / cotiz_path.name
        if alt.exists():
            cotiz_path = alt

    ctx = build_context(cotiz_path)
    html = render_html(ctx)
    numero = ctx.get("numero_cotizacion", cotiz_path.stem)

    if preview:
        prev = OUTPUT_DIR / f"{numero}.preview.html"
        prev.parent.mkdir(parents=True, exist_ok=True)
        prev.write_text(html, encoding="utf-8")
        print(f"👁  Vista previa: {prev}")
        webbrowser.open(prev.resolve().as_uri())
        return

    out_dir = Path(output) if output else OUTPUT_DIR
    out_path = out_dir / f"{numero}.pdf"
    pages = render_pdf(html, out_path)
    print(f"✓ PDF generado: {out_path.resolve()}")
    print(f"  Páginas: {pages}")


def cmd_new(name: str) -> None:
    """Crea una cotización nueva copiando el ejemplo como plantilla."""
    if not name.lower().endswith(".yaml"):
        name = f"{name}.yaml"
    dest = COTIZ_DIR / name
    if dest.exists():
        sys.exit(f"✗ Ya existe: {dest}")
    template = COTIZ_DIR / "COT-0216-2026.yaml"
    COTIZ_DIR.mkdir(parents=True, exist_ok=True)
    if template.exists():
        dest.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        dest.write_text("numero_cotizacion: \"\"\n", encoding="utf-8")
    print(f"✓ Cotización creada: {dest}")
    print("  Edita los datos y luego:")
    print(f"  python generate.py {dest.as_posix()}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Generador de cotizaciones Hauler (PDF).")
    ap.add_argument("cotizacion", nargs="?", help="Ruta al YAML de la cotización.")
    ap.add_argument("--output", "-o", help="Directorio de salida (def: ./output/).")
    ap.add_argument("--preview", action="store_true", help="Abre el HTML en el navegador sin generar PDF.")
    ap.add_argument("--new", metavar="NUMERO", help="Crea una cotización nueva desde plantilla.")
    args = ap.parse_args()

    if args.new:
        cmd_new(args.new)
        return
    if not args.cotizacion:
        ap.error("Indica un YAML de cotización o usa --new NUMERO.")
    cmd_generate(args.cotizacion, args.output, args.preview)


if __name__ == "__main__":
    main()
