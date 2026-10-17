# CantinAPP MVP v0.1: Desglose de documentos y requerimientos mínimos
 
**Documentos analizados**
1. `Presentacion_MVP_1.docx`: Arquitectura de software (contexto, contenedores, módulos, dependencias, contrato de operación, ADR-001, Walking Skeleton).
2. `Cantinapp.docx`: Propuesta de valor, alcance funcional, backlog de historias de usuario (HU01 a HU09) y priorización MoSCoW.
---
 
## 1. Desglose del documento 1: Arquitectura (`Presentacion_MVP_1.docx`)
 
### 1.1 Contexto
- **Qué es:** plataforma SaaS para pequeñas y medianas empresas (pymes) que gestiona inventario y predice demanda a partir de datos históricos de ventas.
- **Usuarios:**
  - *Administrador de negocio:* registra productos, carga ventas, consulta inventario y recibe recomendaciones.
  - *Sistema:* analiza datos, predice demanda y genera alertas.
- **Restricciones técnicas:**
  - Multitenancy: cada negocio solo accede a sus datos.
  - Seguridad: autenticación y autorización por negocio.
  - Escalabilidad: soportar crecimiento del historial de datos.
  - Performance: las predicciones deben responder en menos de 2 segundos.
- **Decisiones de negocio:**
  - Stack: React (frontend), FastAPI (backend), PostgreSQL (base de datos).
  - Modelo predictivo inicial: regresión lineal o promedio móvil.
  - Mínimo 30 días de historial para predecir.
### 1.2 Arquitectura en capas
| Capa | Componente | Tecnología |
|---|---|---|
| Presentación | Frontend (SPA) | React, Material UI, React Router |
| Lógica de negocio | Backend API | FastAPI, Layers Architecture, CQRS |
| Persistencia | Base de datos | PostgreSQL, ORM, Core |
 
Flujo: Usuario → Frontend → Backend API → PostgreSQL.
 
### 1.3 Módulos (9)
| # | Módulo | Responsabilidad | Entrada → Salida |
|---|---|---|---|
| 3.1 | Autenticación | Registro, login y autorización por negocio | Email + contraseña → JWT |
| 3.2 | Productos | CRUD de productos | Datos del producto → producto guardado |
| 3.3 | Ventas | Registrar ventas individuales o por CSV | Venta / CSV → ventas registradas |
| 3.4 | Inventario | Consultar stock y estado | ID producto → stock + estado |
| 3.5 | Análisis histórico | Procesar ventas y detectar tendencias | Ventas → tendencias |
| 3.6 | Predicción | Estimar demanda futura | Historial → demanda futura |
| 3.7 | Recomendación | Calcular cantidad de compra | Inventario + predicción → cantidad |
| 3.8 | Dashboard | Agregar KPIs de todos los módulos | Módulos → indicadores |
| 3.9 | Alertas | Notificar bajo stock | Inventario → alerta |
 
### 1.4 Reglas de dependencia
- Predicción llama a Análisis.
- Recomendación llama a Predicción e Inventario.
- Alertas llama a Inventario.
- Ventas llama a Productos e Inventario.
- Dashboard puede llamar a todos los módulos.
- Cada módulo puede llamar a la base de datos.
- **Prohibido:** llamadas circulares y saltarse capas (por ejemplo, Frontend → BD directo).
### 1.5 Contrato de una operación (ejemplo)
`POST /api/sales/forecast` con `businessId`, `productId`, `forecastDays`.
 
Flujo de procesamiento:
1. Validar usuario autenticado.
2. Validar autorización por negocio.
3. Obtener historial de ventas.
4. Validar que haya datos suficientes (≥ 30 días).
5. Ejecutar modelo predictivo.
6. Guardar predicción en BD.
7. Retornar resultado (`predictedDemand`, `confidence`).
Códigos de error definidos: **401** (no autenticado), **403/404** (producto no pertenece al negocio o no existe; el número no está explícito en el documento), **422** (datos insuficientes), **500** (error del modelo).
 
### 1.6 ADR-001: Monolito modular vs. microservicios
- **Fecha:** 28/09/2026. **Estado:** Aceptado.
- **Decisión:** monolito modular con Clean Architecture.
- **Razón:** velocidad de desarrollo para el MVP, código escalable por módulos y migración futura a microservicios por bajo acoplamiento.
### 1.7 Walking Skeleton (47 horas)
Versión mínima funcional de extremo a extremo para validar la arquitectura.
 
**Incluye:** login básico, lista de productos desde BD, registrar una venta, ver inventario, gráfico de análisis básico.
**Excluye:** UI pulida, predicción, recomendaciones y alertas.
 
| Tarea | Módulo | Responsable | Horas |
|---|---|---|---|
| BD setup | Infrastructure | Backend | 4 |
| Domain entities | Domain | Backend | 4 |
| Repositories | Infrastructure | Backend | 6 |
| Controllers | API | Backend | 6 |
| Handlers | Application | Backend | 7 |
| React setup | Frontend | Frontend | 5 |
| UI básico | Frontend | Frontend | 8 |
| Integración | Full stack | Ambos | 3 |
| Testing | Testing | Backend | 4 |
| **Total** | | | **47** |
 
**Criterios de aceptación del skeleton:**
- Login con credenciales.
- Lista de productos desde BD.
- Registrar una venta manualmente.
- El inventario se actualiza automáticamente.
- Gráfico de las últimas 30 ventas.
- La API responde con errores adecuados (401, 403, 404).
- Código con Layers Architecture.
- Tests unitarios para los servicios principales.
---
 
## 2. Desglose del documento 2: Alcance funcional (`Cantinapp.docx`)
 
### 2.1 Propuesta y problema
- **Propuesta:** SaaS para pymes que gestiona inventario, analiza ventas históricas, predice demanda y genera recomendaciones de abastecimiento.
- **Problema:** las compras se basan en experiencia, percepción, revisión manual y hojas de cálculo desorganizadas, y suelen ser reactivas.
- **Consecuencias:** exceso de inventario (dinero inmovilizado) y falta de inventario (ventas perdidas).
### 2.2 Componentes funcionales
- **4.1 Autenticación:** registro, inicio de sesión seguro, control de acceso por negocio.
- **4.2 Productos:** alta con nombre, categoría, precio, cantidad disponible, stock mínimo, proveedor y tiempo de abastecimiento; editar; eliminar; consultar catálogo.
- **4.3 Ventas:** registro manual, carga masiva por CSV, actualización automática del inventario.
- **4.4 Inventario:** stock actual por producto, identificación de bajo stock o agotado, comparación contra stock mínimo.
- **4.5 Análisis histórico:** ventas por producto y período (diario, mensual, anual), más y menos vendidos, tendencias, gráfica.
- **4.6 Predicción:** seleccionar producto, ejecutar modelo sobre el historial, mostrar demanda estimada del próximo período. Modelo base: regresión lineal o promedio móvil.
- **4.7 Recomendación:** considera inventario, demanda, stock mínimo y tiempo de abastecimiento; sugiere cantidad a comprar y la justifica.
- **4.8 Dashboard:** total de productos, stock total, ventas del período, productos que requieren abastecimiento, gráficas de tendencia y predicción.
### 2.3 Fuera de alcance (v0.1)
App móvil; pagos y suscripciones; facturación electrónica / DIAN; integración con múltiples proveedores o ERP; chatbot o IA generativa; reconocimiento de imágenes o códigos de barras; predicción para todos los productos.
 
### 2.4 Historias de usuario y criterios de aceptación
| ID | Historia | Prioridad (MoSCoW) |
|---|---|---|
| HU01 | Registro e inicio de sesión | Must |
| HU02 | Gestionar productos | Must |
| HU03 | Registrar / cargar ventas históricas | Must |
| HU04 | Consultar inventario | Must |
| HU05 | Analizar ventas históricas | Must |
| HU06 | Predicción de demanda | Must |
| HU07 | Recomendación de abastecimiento | Must |
| HU08 | Dashboard de indicadores | Should |
| HU09 | Alertas de abastecimiento | Should |
 
**HU01: Registro e inicio de sesión**
- Crear cuenta con email y contraseña.
- Email único.
- Login con credenciales válidas.
- El usuario solo accede a la información de su negocio.
- Cerrar sesión.
**HU02: Gestionar productos**
- Registrar producto con nombre, categoría, precio, cantidad, stock mínimo, proveedor y tiempo de abastecimiento.
- Editar producto.
- Desactivar o eliminar producto.
- Listar productos.
**HU03: Registrar / cargar ventas**
- Venta manual con fecha, producto y cantidad.
- Carga de CSV con historial.
- Actualización automática del inventario.
- Validación del formato CSV con mensajes de error.
**HU04: Consultar inventario**
- Lista con nombre, stock actual, stock mínimo y estado.
- Estado: NORMAL, BAJO o AGOTADO.
- Ordenar y filtrar.
- Resaltar visualmente bajo stock o agotados.
**HU05: Analizar ventas históricas**
- Ventas totales por período (diario, mensual, anual).
- Productos más vendidos y de menor rotación.
- Gráfica de tendencia.
- Filtro por rango de fechas.
**HU06: Predicción de demanda**
- Seleccionar producto.
- Ejecutar modelo sobre el historial.
- Mostrar demanda estimada del próximo período.
- Gráfica histórico vs. predicción.
**HU07: Recomendación de abastecimiento**
- Considera inventario, demanda, stock mínimo y tiempo de abastecimiento.
- Sugiere cantidad a comprar.
- Justifica con análisis de datos.
- Indica urgencia: bajo, medio o alto.
**HU08: Dashboard**
- Total de productos.
- Inventario total.
- Ventas del período actual.
- Lista de productos con bajo stock.
- Gráfica de tendencia histórica y predicción.
**HU09: Alertas**
- Alerta cuando stock actual < stock mínimo.
- Incluir demanda estimada.
- Mostrar cantidad recomendada a abastecer.
- Marcar alertas como revisadas.
### 2.5 Priorización MoSCoW
- **Must:** login, productos, ventas, inventario, análisis, predicción, recomendación.
- **Should:** dashboard, alertas.
- **Could (futuro):** gráficas avanzadas y reportes personalizados, comparación de modelos, múltiples proveedores, análisis de promociones y factores externos.
- **Won't (actual):** pagos y facturación, app móvil, integración con ERP, chatbot o IA generativa.
---
 
## 3. Requerimientos mínimos que debe cumplir la app
 
### 3.1 Requerimientos funcionales (MUST: sin esto no hay MVP)
| ID | Requerimiento | Fuente |
|---|---|---|
| RF-01 | Registro de negocio/usuario con email único y contraseña | HU01 |
| RF-02 | Login y logout; sesión con token (JWT) | HU01, doc 1 (3.1) |
| RF-03 | Cada usuario ve y modifica solo los datos de su negocio | HU01, doc 1 (multitenancy) |
| RF-04 | CRUD de productos con los 7 campos definidos (nombre, categoría, precio, cantidad, stock mínimo, proveedor, tiempo de abastecimiento) | HU02 |
| RF-05 | Desactivar/eliminar productos | HU02 |
| RF-06 | Registrar venta manual (fecha, producto, cantidad) | HU03 |
| RF-07 | Cargar historial de ventas por CSV con validación de formato y errores visibles | HU03 |
| RF-08 | Actualizar inventario automáticamente al registrar ventas | HU03, doc 1 |
| RF-09 | Consultar inventario con estado NORMAL / BAJO / AGOTADO, con orden, filtro y resaltado | HU04 |
| RF-10 | Análisis de ventas por período (diario, mensual, anual), con filtro por rango de fechas y gráfica | HU05 |
| RF-11 | Identificar productos más y menos vendidos | HU05 |
| RF-12 | Predicción de demanda por producto para el próximo período, con gráfica histórico vs. predicción | HU06 |
| RF-13 | Recomendación de cantidad a comprar con justificación y nivel de urgencia | HU07 |
 
### 3.2 Requerimientos funcionales (SHOULD: versión inicial importante)
| ID | Requerimiento | Fuente |
|---|---|---|
| RF-14 | Dashboard con total de productos, inventario total, ventas del período, productos con bajo stock y gráfica de tendencia + predicción | HU08 |
| RF-15 | Alertas cuando stock < stock mínimo, con demanda estimada y cantidad sugerida; marcar como revisadas | HU09 |
 
### 3.3 Requerimientos no funcionales
| ID | Requerimiento | Fuente |
|---|---|---|
| RNF-01 | **Multitenancy:** aislamiento estricto de datos por negocio en cada consulta | Doc 1 |
| RNF-02 | **Seguridad:** autenticación en todos los endpoints protegidos y autorización por negocio | Doc 1 |
| RNF-03 | **Rendimiento:** predicciones en menos de 2 segundos | Doc 1 |
| RNF-04 | **Datos mínimos:** no predecir sin al menos 30 días de historial (responder 422 si no hay datos suficientes) | Doc 1 |
| RNF-05 | **Escalabilidad:** el esquema y las consultas deben soportar crecimiento del historial de ventas | Doc 1 |
| RNF-06 | **Códigos de error HTTP adecuados:** 401, 403, 404, 422, 500 | Doc 1 |
| RNF-07 | **Arquitectura:** monolito modular con Layers / Clean Architecture; sin llamadas circulares ni saltos de capa | ADR-001, doc 1 |
| RNF-08 | **Stack:** React + Material UI (frontend), FastAPI (backend), PostgreSQL (BD) | Doc 1 |
| RNF-09 | **Pruebas:** tests unitarios para los servicios principales | Doc 1 (skeleton) |
 
### 3.4 Requisitos del Walking Skeleton (primer entregable técnico, 47 h)
1. Login básico funcional.
2. Lista de productos leída desde la BD.
3. Registro manual de una venta.
4. Inventario que se actualiza tras la venta.
5. Gráfica de las últimas 30 ventas.
6. Errores de API correctos (401, 403, 404).
7. Tests unitarios de servicios.
### 3.5 Fuera del MVP (no requerido)
Aplicación móvil, pagos/suscripciones, facturación electrónica (DIAN), integración con ERP o múltiples proveedores, IA generativa / chatbot, reconocimiento de imágenes o códigos de barras.
 
---
 
## 4. Inconsistencias y puntos abiertos detectados
 
Conviene resolverlos antes de desarrollar:
 
1. **Stock como campo vs. stock calculado.** HU02 pide "cantidad disponible" como dato del producto, y HU03 exige que la venta actualice el inventario. No queda claro si el stock es un campo que se descuenta o un valor derivado de compras menos ventas (falta registrar compras/entradas de stock).
2. **Ventas sin fecha en el skeleton.** El walking skeleton pide "gráfico de las últimas 30 ventas", pero HU05 pide análisis por período. Hay que definir si el gráfico base es por venta individual o por día.
3. **Código de error de "producto de otro negocio".** El contrato lo lista sin código; el skeleton lo asocia a 403 o 404. Definir uno (recomendado: 404 para no revelar la existencia del recurso de otro negocio).
4. **Eliminar vs. desactivar producto (HU02).** No está claro si eliminar borra el historial de ventas. Recomendado: desactivar (borrado lógico).
5. **Umbral de urgencia (HU07).** Se piden niveles bajo, medio y alto, pero no se define el criterio (por ejemplo, días de cobertura de stock).
6. **Frecuencia de la predicción.** Se habla de "próximo período" sin definir si son 7, 30 o N días. El contrato usa `forecastDays`, pero no hay valor por defecto ni máximo.
7. **Confianza del modelo.** La respuesta incluye `confidence`, pero el modelo base (regresión lineal o promedio móvil) no define cómo calcularla.
8. **Mínimo de 30 días.** Se aplica a la predicción; no queda claro si también aplica a los gráficos de análisis.
9. **Alertas en el skeleton.** Están fuera del skeleton pero el módulo Alertas aparece en la arquitectura. Es coherente con SHOULD, pero conviene confirmar la fase.
10. **Formato de moneda y zona horaria.** El precio y las fechas del CSV no especifican moneda (COP sería lo esperable) ni formato de fecha.
11. **Calidad del documento 1.** Hay textos sueltos (por ejemplo, "35013901693545" y "172435332398800") que parecen restos de una conversión desde otra herramienta. Conviene revisar el documento fuente.
---
 
## 5. Resumen
 
- **Documento 1** define *cómo* construir la app: arquitectura, módulos, reglas de dependencia, contrato de API, decisiones técnicas y un primer entregable de 47 horas.
- **Documento 2** define *qué* construir: 9 historias de usuario, 7 de ellas críticas (MUST).
- **Requerimiento mínimo:** la app debe permitir a un negocio aislado (multitenant) iniciar sesión, gestionar productos, registrar ventas (manual o CSV), ver inventario con estados, analizar ventas, obtener una predicción con al menos 30 días de historial y recibir una recomendación de compra. El dashboard y las alertas son importantes, pero se pueden entregar después del núcleo.