# Diagnósticos computacionales e inferencia aproximada

## Contenido

1. [Objetivo y orden de revisión](#objetivo-y-orden-de-revisión)
2. [Warmup, cadenas y draws](#warmup-cadenas-y-draws)
3. [R-hat](#r-hat)
4. [ESS y autocorrelación](#ess-y-autocorrelación)
5. [MCSE y precisión requerida](#mcse-y-precisión-requerida)
6. [Diagnósticos específicos de HMC](#diagnósticos-específicos-de-hmc)
7. [Geometría difícil y multimodalidad](#geometría-difícil-y-multimodalidad)
8. [Datos simulados y validación del algoritmo](#datos-simulados-y-validación-del-algoritmo)
9. [Inferencia aproximada](#inferencia-aproximada)
10. [Matriz de síntomas y acciones](#matriz-de-síntomas-y-acciones)
11. [Contrato de reporte](#contrato-de-reporte)

## Objetivo y orden de revisión

Los draws solo representan la posterior objetivo si el algoritmo exploró adecuadamente y la implementación corresponde al modelo pretendido. Revisar en este orden:

1. Errores, valores no finitos y fallos durante inicialización o evaluación de densidad.
2. Diagnósticos específicos del algoritmo: divergencias, saturación de profundidad, energía o degeneración de pesos.
3. Acuerdo entre cadenas mediante trazas, rangos y `R-hat`.
4. Cantidad de información efectiva mediante ESS.
5. Precisión del resumen concreto mediante MCSE.
6. Recuperación en datos simulados y, si procede, SBC.
7. Adecuación del modelo con chequeos predictivos; esto es una pregunta distinta.

No “arreglar” diagnósticos ejecutando más iteraciones sin investigar. Más draws reducen error Monte Carlo cuando la cadena ya explora la distribución; no corrigen una geometría que el algoritmo no atraviesa, una posterior impropia o un modelo mal codificado.

`GELMAN20` formula un principio práctico: muchos problemas computacionales revelan problemas de modelado, aunque no todos `[GELMAN20, §5.1, p. 22]`.

## Warmup, cadenas y draws

Separar:

- **Inicialización:** punto inicial de cada cadena.
- **Warmup/adaptación:** fase transitoria que aproxima la región típica y ajusta paso, métrica u otros parámetros.
- **Sampling:** draws usados para estimar la posterior después de congelar la adaptación.

No incluir warmup en resúmenes posteriores salvo para diagnosticar. Los valores iniciales dejan de importar solo en un régimen asintótico bien explorado; en práctica pueden determinar qué modo alcanza una cadena `[GELMAN20, §3.1, p. 13; §11.2–11.5, pp. 57–63]`.

Usar múltiples cadenas con inicializaciones dispersas y plausibles. Las cadenas permiten detectar falta de mezcla, pero no garantizan encontrar modos desconocidos. Aumentar su número puede ayudar a descubrir modos o paralelizar, aunque no sustituye razonamiento sobre geometría.

Distinguir:

- Draw total: cantidad almacenada.
- Draw efectivo: información equivalente a draws independientes para un resumen.
- Draw independiente entre cadenas: la independencia de semillas no elimina autocorrelación dentro de cadenas.

El thinning ordinario descarta información y rara vez mejora precisión por costo computacional. Usarlo por restricciones de almacenamiento o requisitos de un procedimiento específico, no para “crear independencia” ni reparar mezcla.

## R-hat

`R-hat` compara variación entre cadenas y dentro de cadenas. Si todas exploran la misma distribución estacionaria, ambas deberían concordar y `R-hat` aproximarse a uno.

Preferir la versión:

- Dividida (*split*) para detectar no estacionariedad dentro de cada cadena.
- Normalizada por rangos para robustez ante colas y no normalidad.
- Plegada (*folded*) para detectar diferencias de escala entre cadenas.

Interpretación:

- Cerca de 1: no se detectó una discrepancia entre cadenas con este diagnóstico.
- Elevado: cadenas con localizaciones, escalas o tendencias distintas; los resúmenes combinados no son confiables.
- Exactamente 1 por redondeo: no constituye prueba de convergencia.

`GELMAN20` recomienda ejecutar al menos hasta `R-hat < 1.01` para parámetros y cantidades de interés, y considerar diagnósticos multivariados `[GELMAN20, §3.2, pp. 13–14]`. Tratar `1.01` como objetivo exigente, no como certificado universal ni como sustituto de trazas, ESS, MCSE y diagnósticos HMC.

Calcular `R-hat` también para:

- Predicciones y log-verosimilitudes puntuales.
- Contrastes, ratios y cuantiles relevantes.
- Variables latentes o hiperparámetros que controlan geometría.
- Energía u otras cantidades del algoritmo si la herramienta las ofrece.

Un `R-hat` no definido puede indicar draws constantes, cadenas demasiado cortas o problemas numéricos; no asumir que equivale a convergencia perfecta.

## ESS y autocorrelación

Para una cadena estacionaria y una función escalar `g(θ)`, la autocorrelación en lag `t` es `ρ_t`. Idealmente:

`ESS ≈ S / τ`, con `τ = 1 + 2Σ_{t≥1}ρ_t`,

donde `τ` es el tiempo integrado de autocorrelación. En práctica usar estimadores robustos que combinen cadenas y estabilicen la suma; no calcularla ingenuamente hasta todos los lags.

### Bulk ESS

Mide información efectiva en el cuerpo de la distribución mediante transformaciones por rangos. Es relevante para medias, medianas y localización general.

### Tail ESS

Mide información en colas, típicamente a partir de indicadores de cuantiles bajos y altos. Es relevante para límites de intervalos, probabilidades extremas, VaR u otras decisiones de cola.

### ESS local o para indicadores

Para `P(g(θ)>c|y)`, el ESS de la secuencia indicadora `I[g(θ_s)>c]` es más pertinente que el ESS del parámetro crudo. Cada transformación tiene autocorrelación distinta.

Interpretar ESS respecto de la precisión requerida, no con un mínimo universal. Un ESS de cientos puede bastar para una media burda y ser insuficiente para una probabilidad de 0.001 o un cuantil extremo.

ESS puede superar el número nominal de draws cuando hay correlación negativa; no asumir automáticamente un error. Aun así, revisar estabilidad del estimador y la implementación.

## MCSE y precisión requerida

El Monte Carlo standard error cuantifica cuánto cambiaría un estimador posterior si se repitiera la simulación bajo el mismo modelo y datos.

Para una media posterior:

`MCSE(mean) ≈ SD_post / √ESS_mean`.

No confundir:

- `SD_post`: incertidumbre sobre el parámetro dentro del modelo.
- `MCSE`: incertidumbre numérica al estimar un resumen de esa posterior.
- `SE` de una diferencia de ELPD: incertidumbre de generalización estimada entre unidades de datos.

Definir tolerancia en la escala de decisión. Ejemplos:

- Si un efecto se reporta a 0.1 unidades, exigir MCSE mucho menor que 0.1.
- Si una decisión cambia en `P(δ>c)=0.90`, exigir MCSE suficientemente pequeño para distinguir lados relevantes del umbral.
- Para límites de intervalos, usar MCSE de cuantiles, no MCSE de la media.

Una regla relativa útil es comparar `MCSE` con `SD_post` o con la mínima diferencia sustantiva, pero documentar la tolerancia concreta. Redondear resultados a una precisión compatible con MCSE.

Para probabilidades estimadas por una indicadora con draws independientes, `SE ≈ √[p(1-p)/S]`; con MCMC sustituir `S` por un ESS apropiado. Cerca de 0 o 1, revisar además cuántos eventos efectivos se observaron.

## Diagnósticos específicos de HMC

### Transiciones divergentes

Una divergencia indica que la integración numérica no siguió fielmente la trayectoria Hamiltoniana, a menudo en regiones de alta curvatura. Consecuencias:

- Draws sesgados si regiones relevantes quedan subexploradas.
- Localización no aleatoria en parámetros o cantidades derivadas.
- Señal de funnels, restricciones, colas o parametrización problemática.

Tratar cualquier divergencia posterior al warmup como advertencia que requiere investigación. Mapear divergencias en pares de parámetros, coordenadas no centradas y cantidades predictivas. Aumentar la probabilidad objetivo de aceptación reduce el paso y puede eliminar errores numéricos leves, pero no debe ocultar una geometría estructural. Priorizar reparametrización, escalado y priors defendibles.

### Profundidad máxima del árbol

Alcanzar la profundidad máxima significa que NUTS necesitó trayectorias más largas que el límite permitido.

- Puede reducir eficiencia y truncar exploración.
- No implica por sí solo el mismo sesgo que una divergencia.
- Aumentar el límite puede ser costoso y no corrige una mala geometría.

Inspeccionar ESS por tiempo, step size, correlaciones y parametrización antes de elevar el límite.

### Energía y BFMI

El Bayesian fraction of missing information basado en energía evalúa si los cambios de energía inducidos por el momento permiten recorrer la distribución marginal de energía. Valores bajos sugieren exploración deficiente, con frecuencia por colas o escala mal adaptada.

Usar el umbral que documente la versión de software como heurística, no ley universal. Examinar el histograma de energía y la relación entre energía marginal y cambios de energía por cadena.

### Step size, aceptación y métrica de masa

- Step size muy pequeño puede indicar alta curvatura y costo elevado.
- Tasa de aceptación distinta del objetivo puede indicar adaptación insuficiente o inestabilidad.
- Una métrica de masa mal adaptada reduce eficiencia; una métrica densa puede ayudar con correlaciones globales, pero no resuelve curvatura cambiante.

No optimizar estas métricas antes de comprobar que el modelo, escalas y priors tienen sentido.

## Geometría difícil y multimodalidad

Patologías frecuentes:

- **Funnel jerárquico:** fuerte cambio de escala según un hiperparámetro.
- **Ridges/no identificabilidad:** muchas combinaciones producen predicciones similares.
- **Multimodalidad simétrica:** por etiquetas intercambiables en mezclas.
- **Multimodalidad sustantiva:** regímenes distintos con masa relevante.
- **Modos menores:** trampas de baja masa que pueden consumir cadenas.
- **Colas pesadas o inestables:** momentos inexistentes o exploración lenta.
- **Fronteras:** escalas cercanas a cero, probabilidades extremas o matrices casi singulares.

Acciones posibles, justificadas por el caso:

1. Simplificar y fijar componentes para aislar el problema.
2. Escalar predictores y parámetros.
3. Reparametrizar, por ejemplo centrada/no centrada.
4. Marginalizar variables latentes si la estructura lo permite.
5. Añadir información previa real o datos; no inventarla para que el sampler “pase”.
6. Imponer identificabilidad a simetrías sin contenido sustantivo.
7. Usar inicializaciones plausibles después de demostrar qué modos son artefactos y cuál es su masa.
8. Cambiar de algoritmo si el objetivo requiere atravesar modos o explorar colas.

El caso planetario muestra por qué no se deben descartar cadenas problemáticas sin analizar: los autores simplifican, visualizan la likelihood y las predicciones, entienden los modos y solo entonces ajustan inicializaciones `[GELMAN20, §11.2–11.5, pp. 57–63]`.

La marginalización puede eliminar interacciones geométricas y recuperar variables condicionadas después `[GELMAN20, §5.8, p. 26]`. Si se aproxima la marginalización, separar el sesgo de aproximación del error Monte Carlo.

## Datos simulados y validación del algoritmo

### Prueba con un punto verdadero

1. Elegir parámetros plausibles `θ*`.
2. Simular `y* ~ p(y|θ*)` con estructura realista.
3. Ajustar el modelo a `y*`.
4. Examinar recuperación, diagnósticos y predicciones.

Sirve como test de integración y para detectar errores graves. No exigir que `θ*` caiga siempre en un intervalo de 95%; aun con algoritmo correcto fallará aproximadamente según el régimen de cobertura. La no recuperación puede reflejar datos poco informativos, no un bug `[GELMAN20, §4.1–4.2, pp. 16–20]`.

### Simulation-Based Calibration

Repetir:

`θ_r ~ prior → y_r ~ likelihood → draws de p(θ|y_r) → rango/PIT de θ_r`.

La uniformidad de rangos bajo condiciones apropiadas evalúa calibración del algoritmo promediada sobre el prior. No valida que el modelo represente datos reales. Priors excesivamente amplios pueden generar datasets absurdos y convertir SBC en una prueba de regiones irrelevantes; revisar primero el prior predictivo.

Usar la skill `simulation-based-calibration` para diseño, cantidades de prueba, empates, autocorrelación y posterior SBC.

## Inferencia aproximada

### Variational inference

Revisar:

- Estabilidad de la evidencia lower bound (ELBO), sin confundir estabilización con exactitud.
- Sensibilidad a inicializaciones y familia variacional.
- Sesgo en varianzas, colas, correlaciones y multimodalidad.
- Comparación con MCMC en una versión reducida o subconjunto.
- Importance sampling/PSIS si hay densidades evaluables y soporte adecuado.
- SBC para cantidades que importan.

Una aproximación puede ser útil al explorar muchos modelos, pero la fase final exige fidelidad suficiente para la decisión. `GELMAN20` propone ajustar el compromiso velocidad–precisión a la fase del workflow `[GELMAN20, §3.3, pp. 14–15]`.

### Laplace y aproximaciones gaussianas

Comprobar si la posterior es aproximadamente unimodal, interior y cuadrática cerca del modo. Son frágiles con asimetría, fronteras, colas o múltiples modos. Comparar cantidades derivadas, no solo medias de parámetros.

### SMC e importance sampling

Revisar ESS de pesos, máximo peso normalizado, degeneración entre etapas y replicaciones independientes. Un ESS de pesos alto no garantiza que la propuesta cubra un modo nunca visitado.

### Aproximación del modelo frente al algoritmo

Declarar cuál cambia:

- Algoritmo aproximado para el mismo modelo.
- Modelo aproximado con algoritmo preciso.
- Ambos.

No atribuir la discrepancia al cómputo si se simplificó likelihood, datos o estructura.

## Matriz de síntomas y acciones

| Síntoma | Explicaciones compatibles | Revisar primero | Acción posible |
|---|---|---|---|
| `R-hat` alto | Modos, tendencia, escala distinta | Trazas/rangos por cadena | Simplificar, reparametrizar, mejores iniciales justificadas |
| Bulk ESS bajo | Autocorrelación central | Step size, correlaciones | Escalar, reparametrizar, más draws solo si mezcla |
| Tail ESS bajo | Colas mal exploradas | Trazas de cuantiles, energía | Reparametrizar o cambiar algoritmo |
| MCSE alto con diagnósticos sanos | Simulación insuficiente | ESS de la cantidad | Ejecutar más cadenas/draws |
| Divergencias | Alta curvatura/funnel | Pares marcados por divergencia | No centrar/centrar, priors, escala |
| Profundidad saturada | Trayectorias largas | ESS/segundo y geometría | Mejorar parametrización; luego límite |
| BFMI bajo | Energía mal explorada | Distribuciones de energía | Escalar, reparametrizar, colas |
| Cadenas en modos simétricos | Label switching | Predicciones e invariantes | Restricción identificadora o resúmenes invariantes |
| Cadenas en modos sustantivos | Regímenes alternativos | Masa y predicciones por modo | Algoritmo multimodal o análisis por regímenes |
| Posterior igual al prior | Datos no informativos o datos ignorados | Likelihood y datos simulados | Corregir código o reconocer no-identificación |
| Ajuste lento y malo | Modelo inadecuado | Predictivas tempranas | Fallar rápido y revisar modelo |

## Contrato de reporte

Reportar como mínimo:

- Algoritmo, versión, número de cadenas, warmup, draws y semillas o política de semillas.
- Divergencias y saturaciones por cadena cuando apliquen.
- Máximo `R-hat`, mínimo bulk/tail ESS y MCSE para cantidades decisivas.
- Trazas o rank plots de parámetros estructurales y cantidades de interés.
- Decisiones tomadas después de ver diagnósticos y su justificación.
- Comparación con datos simulados o aproximación de referencia cuando el riesgo lo amerite.
- Limitaciones: modos no explorados, colas, aproximación, costo o sensibilidad.

No reportar “convergió” como propiedad binaria. Escribir qué evidencia se revisó, para qué cantidades y con qué resolución.
