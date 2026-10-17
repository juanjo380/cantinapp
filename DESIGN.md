<!-- SEED: mundo visual establecido con el usuario antes de implementar «Kraft y sello». Volver a ejecutar /impeccable document cuando exista código para capturar los tokens y componentes reales. -->
---
name: CantinAPP
description: Inventario y predicción de demanda para el dueño de una tienda de barrio colombiana.
colors:
  kraft-ground: "#F1E5CD"
  kraft-panel: "#FBF5E8"
  kraft-line: "#DBC9A4"
  ink: "#241B10"
  ink-soft: "#5F523C"
  green-market: "#1F5C3D"
  green-market-deep: "#153A28"
  tomato: "#B3310F"
  bronze: "#8A5A14"
  stain: "#8A5A2B"
  slate-ground: "#14110B"
  slate-panel: "#201B13"
  slate-line: "#3A3223"
  paper-ink: "#F0E6D2"
  paper-ink-soft: "#B3A488"
  green-market-bright: "#57A874"
  tomato-bright: "#EE6A45"
  mustard-bright: "#E7B44C"
typography:
  wordmark:
    fontFamily: "Chivo, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 900
    lineHeight: 1
    letterSpacing: "-0.02em"
  display:
    fontFamily: "Chivo, system-ui, sans-serif"
    fontSize: "clamp(1.75rem, 3vw, 2.375rem)"
    fontWeight: 800
    lineHeight: 1.1
    letterSpacing: "-0.015em"
  title:
    fontFamily: "Chivo, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 700
    lineHeight: 1.25
  body:
    fontFamily: "Chivo, system-ui, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.55
  num:
    fontFamily: "Chivo Mono, ui-monospace, monospace"
    fontSize: "1rem"
    fontWeight: 600
    fontFeature: "\"tnum\" 1"
  stamp:
    fontFamily: "Chivo Mono, ui-monospace, monospace"
    fontSize: "0.6875rem"
    fontWeight: 600
    letterSpacing: "0.08em"
rounded:
  sm: "2px"
  md: "4px"
  lg: "6px"
  pill: "999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "40px"
components:
  button-primary:
    backgroundColor: "{colors.green-market}"
    textColor: "{colors.kraft-panel}"
    rounded: "{rounded.sm}"
    padding: "10px 18px"
  button-primary-hover:
    backgroundColor: "{colors.green-market-deep}"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "10px 18px"
  stamp-normal:
    backgroundColor: "{colors.kraft-panel}"
    textColor: "{colors.green-market}"
    rounded: "{rounded.sm}"
    padding: "2px 8px"
  stamp-low:
    backgroundColor: "{colors.kraft-panel}"
    textColor: "{colors.bronze}"
    rounded: "{rounded.sm}"
    padding: "2px 8px"
  stamp-out:
    backgroundColor: "{colors.kraft-panel}"
    textColor: "{colors.tomato}"
    rounded: "{rounded.sm}"
    padding: "2px 8px"
---

# Design System: CantinAPP

## Overview

**Creative North Star: "El mostrador de empaque"**

El mundo es el mostrador de una tienda de barrio: papel kraft, piola, sellos de goma, tableros de precios y el verde de la plaza de mercado. La app no imita un recibo ni un cuaderno — sería un disfraz de herramienta —; toma de ese mundo solo cuatro cosas y las usa a fondo: **tipografía, paleta, densidad y un movimiento firma**.

El movimiento firma es el **sello**: el estado (`NORMAL`, `BAJO`, `AGOTADO`) y la procedencia de todo lo que genera el Sistema se estampan con un rótulo de texto + icono, nunca solo con color, con la fecha de generación y la base usada. El sello materializa el principio de transparencia del producto: el dueño decide, y para decidir tiene que poder creer el número.

La superficie es una herramienta de trabajo: densa, escaneable, con cifras en COP claras y navegación y controles web estándar. El mundo nunca organiza la página; solo le da voz. Claro (kraft) y oscuro (pizarra) con el mismo sistema.

**Key Characteristics:**
- Verde de mercado como color comprometido de todo el riel de navegación, no como acento suelto.
- Superficie plana: la jerarquía se logra con capas tonales y líneas capilares, no con sombras.
- Cifras siempre tabulares, en monoespaciada, alineadas a la derecha.
- Estado y procedencia como sello con texto e icono; el color acompaña, nunca comunica solo.

## Colors

Paleta de dos suelos (kraft y pizarra) con un verde de marca que ocupa superficies enteras y tres colores de estado que hacen trabajo real de señal.

### Primary
- **Verde de mercado** (`green-market`): riel de navegación, botón principal, enlaces y foco. Es el color de marca y ocupa una región completa de la pantalla, no salpicaduras.
- **Verde de mercado profundo** (`green-market-deep`): estados activos y hover del botón principal.

### Secondary
- **Cobre de estado normal** (`stain`): el tinte de los sellos y marcas secundarias, la tinta "gastada" del sello.

### Tertiary
- **Tomate** (`tomato`): urgencia ALTO, agotado y errores.
- **Bronce** (`bronze`): urgencia MEDIO y bajo stock.

### Neutral
- **Kraft** (`kraft-ground` / `slate-ground`): suelo de la aplicación.
- **Panel** (`kraft-panel` / `slate-panel`): tarjetas, tablas y campos; una capa por encima del suelo.
- **Línea de kraft** (`kraft-line` / `slate-line`): separadores capilares, bordes de campos y tabla.
- **Tinta** (`ink` / `paper-ink`): texto principal.
- **Tinta suave** (`ink-soft` / `paper-ink-soft`): texto secundario, etiquetas, unidades.

### Named Rules
**La Regla del Sello.** Ningún estado ni dato generado por el Sistema se comunica solo con color: lleva texto, icono y, si viene del Sistema, su fecha de generación. El color es refuerzo.

**La Regla del Riel.** El verde de mercado posee una región entera (el riel o la banda de cabecera). Nunca aparece como acentos dispersos sobre un fondo neutro.

## Typography

**Display Font:** Chivo (con `system-ui`, `Segoe UI`, sans-serif)
**Body Font:** Chivo (misma familia)
**Label/Mono Font:** Chivo Mono (con `ui-monospace`, `Cascadia Mono`, monospace)

**Character:** Una superfamilia grotesca de trabajo, con oficio latinoamericano y sin folclor, más su monoespaciada para las cifras. Da el tono de una herramienta seria con acento de barrio, sin caer en el look tipográfico por defecto de plantilla.

### Hierarchy
- **Wordmark** (900, 1.5rem, tracking −0.02em): el nombre **CantinAPP** como logotipo tipográfico, con "APP" en mayúsculas; vive en el riel de navegación.
- **Display** (800, `clamp(1.75rem, 3vw, 2.375rem)`, lh 1.1): títulos de pantalla y el número protagonista de una vista.
- **Title** (700, 1.125rem, lh 1.25): encabezados de sección, celdas destacadas, nombres de producto.
- **Body** (400, 0.9375rem, lh 1.55): texto corrido; ancho de línea no mayor a 70ch.
- **Number** (600, 1rem, cifras tabulares `.tnum`): todos los precios, cantidades y montos en COP, alineados a la derecha.
- **Stamp** (600, 0.6875rem, tracking 0.08em, monoespaciada): el contenido de los sellos: estado, fecha de generación, base de datos usada.

### Named Rules
**La Regla de la Cifra Tabular.** Toda cifra se compone en Chivo Mono con figuras tabulares; nunca en la fuente de texto. Las columnas de números se alinean a la derecha y al dígito.

## Layout

Modelo de dos zonas: un **riel de navegación** verde fijo a la izquierda (wordmark, secciones, nombre del negocio y cerrar sesión) y el área de trabajo sobre el suelo kraft. La zona de trabajo se limita a un ancho legible (~1200px) y respira con una retícula de 4px (`--spacing: 0.25rem`) y el ritmo de espaciado `xs/sm/md/lg/xl`.

En móvil el riel colapsa a una barra superior con menú desplegable y el contenido pasa a una columna. Las tablas densas priorizan las columnas de decisión (producto, stock, estado) y ocultan las secundarias. Los filtros se colocan encima de lo que acotan, siempre visibles.

La densidad es de herramienta: filas compactas, espaciado cómodo pero no aireado, jerarquía por peso y tamaño de tipo más que por cajas.

## Elevation & Depth

Sistema **plano por defecto**: la profundidad se transmite con capas tonales (suelo → panel) y líneas capilares de 1px, no con sombras. Una sombra tenue existe solo para capas flotantes reales (diálogos, menús, tooltips), nunca para tarjetas en reposo. Se evitan las elevaciones pesadas y difusas de MUI.

### Named Rules
**La Regla de la Línea Única.** La separación se dibuja con una línea de 1px en `kraft-line`/`slate-line`. Un borde de caja y una sombra no describen lo mismo: no se apilan.

## Shapes

Forma de papel cortado y etiqueta: esquinas apenas redondeadas (`sm` 2px, `md` 4px, `lg` 6px) y bordes de 1px. El sello es la única silueta blanda: una píldora (`pill`) o un rectángulo `sm` con doble contorno fino que evoca la estampa. Nada de tarjetas grandes y muy redondeadas, ni radios de un solo valor aplicados a todo.

## Components

### Buttons
- **Shape:** esquina apenas cortada (2px).
- **Primary:** verde de mercado, texto kraft, padding 10px × 18px, sin elevación.
- **Hover / Focus:** hover a verde profundo; foco con anillo de 2px en verde de mercado separado 2px del borde.
- **Secondary / Ghost:** contorno de 1px en línea de kraft, texto en tinta; hover con relleno tonal de panel.

### Chips (Sellos)
- **Style:** rectángulo `sm` o píldora con borde fino de 1px y ligera estampa interior; texto en monoespaciada `stamp`, más un icono.
- **State:** `NORMAL` (verde), `BAJO` (bronce), `AGOTADO` (tomate); siempre coexisten color, icono y texto.

### Cards / Containers
- **Corner Style:** 4px (`md`).
- **Background:** panel sobre suelo; nada de degradados.
- **Shadow Strategy:** plana (ver Elevation & Depth); borde capilar de 1px.
- **Internal Padding:** `md` a `lg`.

### Inputs / Fields
- **Style:** fondo panel, borde de 1px en línea de kraft, radio 2px.
- **Focus:** borde cambia a verde de mercado más anillo de foco visible; nunca solo un cambio de color de borde.
- **Error / Disabled:** error en tomate con texto de apoyo; deshabilitado con texto en tinta suave y fondo tonal.

### Navigation
Riel verde de mercado con el wordmark **CantinAPP** arriba y las secciones en Chivo 500. La sección activa se marca con fondo profundo, texto kraft e indicador de 3px, no solo con color. En móvil, barra superior con el wordmark y menú desplegable. El nombre del negocio y "Cerrar sesión" viven al pie del riel.

### Sello de procedencia (signature)
El componente que distingue a CantinAPP: un sello que acompaña a toda salida del Sistema (predicción, recomendación, alerta) e indica **cuándo se generó**, **sobre qué base** (días de historial, cobertura, confianza) y su **urgencia**. Va en Chivo Mono `stamp`, con borde doble fino y una marca de fecha. Es la cara visible del principio de transparencia.

## Do's and Don'ts

### Do:
- **Do** usar los tokens de `src/index.css` (`@theme`) y `src/theme.js`; ninguna decisión visual fuera de esos dos archivos.
- **Do** mostrar estado y procedencia con texto e icono además del color.
- **Do** componer toda cifra en COP en Chivo Mono con figuras tabulares, alineada a la derecha.
- **Do** separar con líneas capilares y capas tonales antes que con sombras.
- **Do** cubrir carga, vacío y error en toda vista de datos, incluido el arranque en frío del servidor.

### Don't:
- **Don't** caer en el dashboard SaaS genérico: rejilla de tarjetas iguales, azul por defecto, Roboto, sombras difusas.
- **Don't** usar degradados morados, glassmorphism ni tarjetas enormes y muy redondeadas.
- **Don't** comunicar un estado solo con color.
- **Don't** usar radios, colores, fuentes o tamaños arbitrarios (`text-[#3a7bd5]`): siempre tokens.
