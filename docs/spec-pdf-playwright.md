Tengo un repositorio que genera cotizaciones en PDF. Quiero que lo 
refactorices completamente para que adopte un nuevo sistema de diseño 
minimalista y produzca PDFs de alta calidad usando Playwright + Chromium.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PASO 1 — LEE EL REPO PRIMERO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Antes de tocar cualquier archivo:
1. Lee toda la estructura del proyecto (árbol de directorios).
2. Entiende cómo genera PDFs actualmente (qué librería usa, qué templates 
   existen, cómo se pasan los datos).
3. Identifica qué partes puedes reutilizar y qué hay que reemplazar.
4. Dime tu plan antes de escribir una sola línea de código.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PASO 2 — ARQUITECTURA OBJETIVO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

El sistema debe quedar con esta separación clara:

  config/
    empresa.yaml          ← datos del emisor (logo, nombre, contacto)
    defaults.yaml         ← valores por defecto (vigencia, condiciones, 
                             términos legales, texto de secciones fijas)
    design.yaml           ← tokens de diseño (colores, fuentes, tamaños)

  cotizaciones/
    COT-XXXX-2026.yaml    ← datos específicos de cada cotización

  templates/
    base.html.j2          ← template HTML Jinja2 con el diseño
    sections/
      portada.html.j2
      servicio.html.j2
      vehiculo.html.j2
      precios.html.j2
      condiciones.html.j2
      firma.html.j2

  generate.py             ← CLI principal
  
  output/                 ← PDFs generados

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PASO 3 — SISTEMA DE DISEÑO (OBLIGATORIO)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

El PDF tiene exactamente 5 páginas, una por sección. Cada página usa 
este sistema visual — respétalo al pie de la letra:

PALETA:
  --blue:   #1B5EFF   ← acento principal
  --ink:    #0f172a   ← títulos
  --body:   #475569   ← texto de cuerpo
  --muted:  #94a3b8   ← labels, metadata
  --line:   #e2e8f0   ← líneas divisorias
  --tint:   #fafafa   ← fondos alternos en tablas
  --light:  #f8faff   ← fondo card opción destacada

ESTRUCTURA DE CADA PÁGINA:
  - Barra de acento (3px, gradiente #1B5EFF → #6366f1 → #e2e8f0) 
    en la parte superior
  - Header: logo izquierda · número de cotización + tag de sección derecha
  - Línea divisora 1px #e2e8f0 bajo el header
  - Contenido principal con padding 14mm laterales
  - Footer: nombre empresa · COT number izquierda / número de página derecha
  - Todo en fondo blanco. Sin fondos oscuros, sin degradados en fondos.

TIPOGRAFÍA:
  - Font: 'Helvetica Neue', Arial, sans-serif
  - Hero title: 24-30pt, weight 800, color --ink, line-height 1.0
  - Label de sección: 6.5pt, weight 700, letter-spacing 2.5px, 
    uppercase, color --blue, display block con margin-bottom 3mm
  - Body: 8.5pt, color --body, line-height 1.65
  - KV keys: 7pt, color --muted, weight 500, ancho fijo 34mm
  - KV values: 8pt, color --ink, weight 500

COMPONENTES CSS (implementa todos estos):

  .accent-bar     → barra 3px top con gradiente azul
  .kv             → tabla clave-valor sin bordes, filas pares en #fafafa
  .pc             → price card: border 1px #e2e8f0, radius 12px
  .pc-blue        → price card destacada: border 1.5px --blue, bg #f8faff
  .badge          → chip flotante "Cobertura máxima": bg --blue, texto blanco
  .price-num      → número de precio: 28pt, weight 800, color --blue
  .chk            → checklist item con ✓ azul a la izquierda
  .resp-item      → item de respaldo con ● azul
  .feat           → feature item con — azul
  .callout        → highlight: bg #f8fafc, border-left 3px --blue, radius 0 8px 8px 0
  .callout-blue   → callout azul: bg #eff6ff, border-left 3px --blue, texto #1e40af
  .stat           → stat card: border 1px #f1f5f9, radius 8px, bg #fafafa
  .rule / .rule-blue / .rule-dark → divisores 1px de distintos pesos
  .col2 / .col3   → grids de 2 y 3 columnas con gap 4-5mm

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PASO 4 — CAMPOS CONFIGURABLES POR SECCIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Todos estos campos deben venir del YAML de la cotización 
y ser sobreescribibles. Ningún valor debe estar hardcodeado en el template.

EMPRESA (empresa.yaml):
  - nombre, rut, ciudad, email, telefono
  - logo_path (ruta al archivo de imagen)
  - representante_nombre, representante_cargo

COTIZACIÓN (COT-XXXX.yaml):
  numero_cotizacion    # e.g. "COT-0216-2026"
  fecha                # auto si se omite
  vigencia_dias        # días corridos de validez

  cliente:
    razon_social
    rut
    contacto_nombre
    contacto_cargo
    email
    referencia          # texto libre de referencia del proyecto

  servicio:
    descripcion_corta   # subtítulo bajo el hero title
    inicio_referencial  # "01 de agosto de 2026"
    duracion            # "4 meses con opción de renovación"
    ruta                # "Antofagasta → Mantos Blancos → Antofagasta · Ruta 5 Norte"
    tiempo_viaje        # "50 – 60 min por tramo"
    peaje               # descripción del peaje o null
    servicio_en_faena   # descripción de lo que hace el conductor en faena
    dotacion            # "14 personas por turno"
    modalidad           # "Minibús dedicado · conductor en faena · rotación incluida"
    embarque            # texto del punto de embarque
    
    incluido:           # lista dinámica — se renderizan como .chk
      - titulo: "Combustible"
        detalle: "consumo total ida/vuelta y traslados internos en faena"
      - titulo: "Peajes"
        detalle: "Ruta 5 Norte, ambos sentidos"
      # ... (todos los ítems que sean necesarios)

    respaldo:           # lista dinámica — se renderizan como .resp-item
      - "Vehículo de respaldo disponible desde [ciudad]"
      # ...

    normativa:          # lista de textos cortos para el strip de normativa
      - "D.S. N° 80/2004 MTT"
      - "Licencia A-2 vigente"
      # ...

  vehiculo:
    marca               # "Ford"
    modelo              # "Transit 350 HD Wagon"
    anio                # "2023 / 2024"
    nota                # "Acreditada para faena minera · O similar"
    motor               # "2.0L EcoBlue Diesel turbocargado, 170 HP"
    transmision         # "Automática 10 velocidades SelectShift"
    capacidad           # "15 pasajeros incluido conductor"
    pbv                 # "3.175 kg — cumple D.S. N° 80 (mín. 2.700 kg)"
    norma_emisiones     # "Euro V / Euro VI"
    equipamiento:       # lista dinámica — .resp-item
      - "ABS + EBD, control de tracción (TCS) y control de estabilidad (ESC)"
      # ...

  opciones:             # lista dinámica — genera una .pc o .pc-blue por cada una
    - id: 1
      nombre: "Opción 1"
      subtitulo: "Jornada Estándar"
      badge: null        # null o texto del badge (e.g. "Cobertura máxima")
      destacada: false
      jornada: "Lun – Jue 08:00–18:00 · Vie 08:00–14:00"
      dotacion: "14 personas · Rotación de conductores incluida"
      precio: 7500000    # entero, se formatea automáticamente con puntos
      precio_label: "CLP neto · por mes · todo incluido"
      features:
        - "Conductor permanece en faena toda la jornada"
        - "Traslados internos sin límite"
        # ...
      comparativo:       # datos para la tabla comparativa
        jornada_diaria: "10 hrs (L–J) / 6 hrs (V)"
        dias: "Lun – Vie"
        rotacion: true

    - id: 2
      nombre: "Opción 2"
      subtitulo: "Jornada Extendida"
      badge: "Cobertura máxima"
      destacada: true    # usa .pc-blue
      # ...

  condiciones:
    pago:               # tabla KV dinámica
      - clave: "Moneda"
        valor: "Pesos Chilenos (CLP) netos"
      - clave: "Garantía inicio"
        valor: "50% del valor mensual a la firma del contrato"
      # ...
    operacion:          # tabla KV dinámica
      - clave: "Dotación máxima"
        valor: "14 personas/turno. Incrementos requieren cotización adicional"
      # ...
    texto_callout: >
      Hauler SpA asume la responsabilidad total del servicio...

  firma:
    texto_cierre: >
      Hauler SpA tiene la flota, los conductores acreditados...
    texto_legal: >
      Al firmar esta propuesta, [cliente.razon_social] confirma...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PASO 5 — CLI (generate.py)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Debe funcionar así:

  # Genera una cotización específica
  python generate.py cotizaciones/COT-0216-2026.yaml

  # Con salida personalizada
  python generate.py cotizaciones/COT-0216-2026.yaml --output ./output/

  # Vista previa en browser sin generar PDF
  python generate.py cotizaciones/COT-0216-2026.yaml --preview

  # Crea una cotización nueva desde template
  python generate.py --new COT-0217-2026

El script debe:
1. Cargar empresa.yaml + defaults.yaml + el YAML de la cotización
2. Mergear defaults con los valores del YAML (el YAML específico tiene 
   precedencia siempre)
3. Renderizar el template HTML con Jinja2
4. Usar Playwright para generar el PDF con print_background=True
5. Guardar en output/ con el nombre del número de cotización
6. Imprimir en consola: ruta del archivo generado + número de páginas

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PASO 6 — FORMATO DEL PRECIO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

El precio viene como entero en el YAML (7500000).
Crea un filtro Jinja2 llamado `clp` que lo formatee como:
  $ 7.500.000
Usa punto como separador de miles (estilo chileno).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PASO 7 — RESTRICCIONES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- NO uses ReportLab, WeasyPrint ni wkhtmltopdf. Solo Playwright + Chromium.
- El CSS debe estar embebido en el HTML (no archivos externos).
- El logo se embebe como base64 en el HTML para que el PDF sea autónomo.
- NO hardcodees ningún texto de negocio en los templates — todo viene del YAML.
- Sí puedes hardcodear la estructura HTML/CSS del diseño.
- Las secciones fijas (callouts de normativa, textos legales genéricos) 
  viven en defaults.yaml y se pueden sobreescribir por cotización.
- El PDF resultante debe ser visualmente idéntico al diseño descrito: 
  fondo blanco, paleta azul/gris, 5 páginas A4, una sección por página.
- Incluye un requirements.txt con todas las dependencias.
- Incluye un README.md con instrucciones de instalación y uso.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REFERENCIA DEL DISEÑO FINAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Las 5 páginas en orden:
  1. Portada   → hero title + stats strip + datos cliente + resumen + callout
  2. Servicio  → operación + respaldo + incluido (2 col) + normativa strip
  3. Vehículo/Precios → specs vehículo + cards de opciones + tabla comparativa
  4. Condiciones → pago (col izq) + operación (col der) + callout protección
  5. Firma     → texto cierre + contacto emisor + firma + aceptación cliente

Empieza leyendo el repo y dime tu plan antes de modificar nada.