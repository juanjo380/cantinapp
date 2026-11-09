# Datos de prueba: 3 negocios para evaluar la predicción

Ventas de **120 días** que terminan el **07/11/2026**, con un patrón distinto por negocio. Los
tres comparten productos (Gaseosa 400 ml, Agua 600 ml, Papas fritas) para comparar el mismo
artículo en negocios diferentes.

| Archivos | Negocio | Patrón |
|---|---|---|
| `negocio1Productos.csv` / `negocio1Ventas.csv` | **Cantina escolar** (tipo `CANTINA_ESCOLAR`) | Lunes a viernes; **cerrada sábado y domingo**; **semana de receso** del 5 al 9/10 en 0; picos de empanada (día del jean) seguidos de más gaseosa |
| `negocio2Productos.csv` / `negocio2Ventas.csv` | **Tienda de barrio** (`TIENDA`) | Abre todos los días; **viernes y sábado fuertes**; **quincena** (1, 15, 16 y fin de mes ×1,5); *Gaseosa 1,5 L* **en alza** (+0,8 %/día); *Pila AA* **intermitente**; picos de cerveza (partidos) seguidos de más agua |
| `negocio3Productos.csv` / `negocio3Ventas.csv` | **Cafetería** (`CAFETERIA`) | Estable, domingo flojo; *Chocolate caliente* **a la baja** (−0,6 %/día); *Torta de cumpleaños* por encargo (**intermitente**); promos de pandebono seguidas de más café con leche |

Formato: igual que las plantillas (UTF-8 con BOM, separador `;`, fechas `DD/MM/AAAA`). Varios
productos empiezan con **stock bajo el mínimo** para que aparezcan alertas.

## Cómo cargarlos

1. (Opcional) Vaciar la base: `db/reset_datos.sql` en el SQL Editor de Supabase.
2. Regístrate en la app → se crea el primer negocio. Crea los otros dos con el selector de negocio.
3. En **cada** negocio, en este orden:
   1. **Productos → Cargar CSV** → `negocioNProductos.csv`.
   2. **Ventas → Cargar historial por CSV** → `negocioNVentas.csv`, con «Descontar del inventario»
      **apagado** (es historial; el stock queda como en el CSV de productos).
   3. **Alertas → Generar** (o esperar al trabajo diario) y **Reabastecimiento → Recalcular** la co-ocurrencia.
4. Prueba también la deduplicación: vuelve a cargar el mismo CSV de ventas → debe pedir confirmación y,
   si confirmas, decir «N omitidas porque ya estaban cargadas».

Cada CSV de ventas tiene entre 800 y 1.230 filas: en Render gratis la carga puede tardar un minuto.

**Si cargas los datos días o semanas después del 07/11/2026**, regenéralos para que terminen ayer
(si no, los últimos días cuentan como 0 ventas y la predicción baja):

```powershell
python docs/datos-prueba/generar_datos.py              # termina ayer
python docs/datos-prueba/generar_datos.py --end 2026-12-01
```

## Resultado esperado

Calculado con el código real de la app (parsers de CSV, `forecasting/domain/models.py` y
`recommendations/domain/cooccurrence.py`) sobre estos archivos, con hoy = 08/11/2026 y predicción
**Automático** a 30 días. Error = WAPE del backtest de los últimos 14 días (0 = perfecto).

### negocio1 — Cantina escolar: gana **Semanal** en los 10 productos

| Producto | Gana | Confianza | Error semanal / promedio / regresión |
|---|---|---|---|
| Empanada | Semanal | 73 % | 0,27 / 0,61 / 0,52 |
| Gaseosa 400 ml | Semanal | 76 % | 0,24 / 0,52 / 0,59 |
| Galletas de avena | Semanal | 77 % | 0,23 / 0,51 / 0,63 |
| (el resto) | Semanal | 63–69 % | ≈ 0,33 / 0,58 / 0,67 |

El promedio móvil se equivoca el doble: reparte la venta en los fines de semana en que la cantina está cerrada.
Alertas: Pastel de pollo, Jugo en caja y Papas fritas (agotado).

### negocio2 — Tienda de barrio: gana **Semanal** en 8 de 11

| Producto | Gana | Confianza | Por qué |
|---|---|---|---|
| Arroz, Aceite, Leche, Pan, Gaseosas, Agua, Papas | Semanal | 66–75 % | Fines de semana fuertes |
| Huevos x30 | Promedio móvil | 71 % | Pocas unidades por día: el patrón semanal es ruido |
| Cerveza lata | Promedio móvil | 57 % | Los picos de partidos (al azar) rompen el patrón semanal |
| Gaseosa 1,5 L (en alza) | Semanal | 71 % | El nivel de 28 días ya sigue la subida; la regresión queda cerca (0,35 vs 0,29) |
| Pila AA (intermitente) | Promedio móvil | **0 %** | Ver hallazgo 2 |

Alerta: Aceite 1 L.

### negocio3 — Cafetería

| Producto | Gana | Confianza | Por qué |
|---|---|---|---|
| Chocolate caliente (a la baja) | **Regresión lineal** | 77 % | Único con tendencia clara: 0,23 vs 0,38 de los otros |
| Café con leche | Promedio móvil | 77 % | Empate a 0,23: gana el más simple |
| Café tinto, Pandebono, Croissant, Tortas, Gaseosa, Agua | Semanal | 70–84 % | Domingo flojo |
| Torta de cumpleaños (intermitente) | Promedio móvil | **0 %**, demanda **0** | Ver hallazgo 2 |

Alerta: Croissant. Co-ocurrencia: **Pandebono → Café con leche** (9 de 9 picos), el par sembrado.

## Hallazgos de la evaluación (límites de los algoritmos actuales)

1. **Co-ocurrencia con falsos positivos por el calendario.** En la cantina, *Empanada* aparece ligada a
   **todos** los productos (7 de 7): tras un fin de semana cerrado, cualquier lunes supera la media de 14 días.
   En la tienda pasa con la quincena (p. ej. Huevos → Papas fritas, Pila AA → Aceite, 10 de 10). Es la
   limitación ya anotada en memoria.md («no descuenta subidas generales del negocio»). Corrección posible:
   comparar contra el mismo día de la semana o normalizar por la venta total del negocio ese día.
2. **Demanda intermitente.** Pila AA y Torta de cumpleaños se venden pocos días: el WAPE pasa de 1 y la
   confianza queda en 0 %; si la última semana no hubo ventas, la predicción a 30 días es **0** (la torta).
   Corrección posible: un modelo para demanda intermitente (Croston/SBA) en el modo AUTO.
3. **Tendencias de subida contra el modelo semanal.** Con +0,8 %/día, el semanal (nivel de 28 días) todavía
   gana a la regresión; con tendencias más fuertes o más largas la regresión debería ganar. La de bajada
   (chocolate) sí la detecta.
4. **«Qué tan acertadas» no se puede probar con CSV:** compara predicciones guardadas con ventas posteriores,
   así que necesita que pasen los días de una predicción (o registrar ventas manuales después).
