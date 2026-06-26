# Generador de Cotizaciones Hauler (PDF)

Genera cotizaciones comerciales en **PDF de alta calidad** a partir de archivos
**YAML**, renderizando HTML con **Jinja2** y exportando con **Playwright +
Chromium**. Diseño minimalista de varias páginas A4, **100% data-driven**:
ningún texto de negocio está hardcodeado en los templates.

## Estructura

```
config/
  empresa.yaml      ← datos del emisor (logo, contacto, firmante)
  defaults.yaml     ← valores por defecto y texto fijo (sobreescribible)
  design.yaml       ← tokens de diseño (colores, fuentes, tamaños)
cotizaciones/
  COT-0216-2026.yaml ← datos de cada cotización (precedencia sobre defaults)
templates/
  base.html.j2      ← chrome de página + CSS embebido (sistema de diseño)
  sections/         ← una plantilla por sección (portada, servicio, vehículo,
                      precios, condiciones, firma)
generate.py         ← CLI
output/             ← PDFs generados (ignorados por git)
```

## Instalación

```bash
pip install -r requirements.txt
playwright install chromium      # descarga el navegador (una sola vez)
```

## Uso

```bash
# Generar una cotización → output/COT-0216-2026.pdf
python generate.py cotizaciones/COT-0216-2026.yaml

# Salida en otra carpeta
python generate.py cotizaciones/COT-0216-2026.yaml --output ./entregables/

# Vista previa en el navegador (sin generar PDF)
python generate.py cotizaciones/COT-0216-2026.yaml --preview

# Crear una cotización nueva a partir de la plantilla
python generate.py --new COT-0217-2026
```

## Cómo se arman los datos

1. Se cargan `config/empresa.yaml`, `config/defaults.yaml` y `config/design.yaml`.
2. Se hace **deep-merge** de `defaults` con el YAML de la cotización; la
   **cotización siempre gana**. Las listas se reemplazan por completo.
3. Se renderiza el HTML con Jinja2 (filtro `clp` para precios estilo chileno:
   `7500000 → $ 7.500.000`).
4. Playwright genera el PDF A4 con `print_background=True`.

## Personalización

- **Colores / tipografía / tamaños**: editar `config/design.yaml` (se inyectan
  como variables CSS; re-tematiza todo el PDF sin tocar HTML).
- **Logo**: definir `logo_path` en `config/empresa.yaml` (PNG/SVG). Se embebe
  como base64 → PDF autónomo. Si es `null`, se usa el wordmark de texto.
- **Texto fijo** (normativa, condiciones, textos legales): vive en
  `config/defaults.yaml` y se puede sobreescribir por cotización.
- **Secciones / orden de páginas**: lista `PAGES` en `generate.py`.

## Notas

- Solo se usa **Playwright + Chromium** para el PDF (no ReportLab/WeasyPrint/
  wkhtmltopdf).
- El CSS está **embebido** en el HTML; no hay archivos CSS externos.
