# Métricas posteriores y decisiones

## Contenido

1. [Principio de selección](#principio-de-selección)
2. [Localización](#localización)
3. [Dispersión e intervalos](#dispersión-e-intervalos)
4. [Probabilidades de eventos y efectos](#probabilidades-de-eventos-y-efectos)
5. [Actualización e información](#actualización-e-información)
6. [Cantidades derivadas y propagación](#cantidades-derivadas-y-propagación)
7. [Teoría bayesiana de decisión](#teoría-bayesiana-de-decisión)
8. [Selección rápida de métricas](#selección-rápida-de-métricas)
9. [Plantilla de comunicación](#plantilla-de-comunicación)

## Principio de selección

Una posterior completa es el objeto inferencial. Una métrica es una proyección elegida para una pregunta concreta y siempre pierde información. Antes de resumir:

1. Especificar `g(θ)` en unidades relevantes.
2. Inspeccionar forma, colas, multimodalidad y dependencia.
3. Elegir una función resumen o una pérdida coherente con el uso.
4. Reportar incertidumbre posterior y precisión Monte Carlo por separado.
5. Propagar draws a la escala final en lugar de transformar solo un estimador puntual.

Para draws `g_s = g(θ_s)`, `s=1,…,S`, calcular la métrica sobre `{g_s}`. Si `g` es no lineal, en general `g(E[θ|y]) ≠ E[g(θ)|y]`.

## Localización

### Media posterior

`E[θ | y] = ∫ θ p(θ | y)dθ`, estimada por `θ̄ = S⁻¹Σ_s θ_s`.

- Minimiza pérdida cuadrática posterior esperada.
- Usa toda la masa y es útil para cantidades aditivas.
- Es sensible a colas y puede caer en una región de baja densidad en posteriores sesgadas o multimodales.

Interpretar con unidad: “La media posterior del cambio es 3.2 puntos”, no “el parámetro verdadero es 3.2”.

### Mediana posterior

El cuantil `q_0.5` satisface `P(θ ≤ q_0.5 | y) ≥ 0.5` y `P(θ ≥ q_0.5 | y) ≥ 0.5`.

- Minimiza pérdida absoluta.
- Es robusta a colas largas.
- No representa por sí sola multimodalidad ni asimetría.

### Moda y MAP

`θ_MAP = argmax_θ p(θ | y)` para una densidad continua.

- Se relaciona con pérdida 0–1 solo en problemas discretos o límites idealizados.
- Depende de parametrización para densidades continuas.
- Puede ignorar un modo ancho con mucha masa y privilegiar un pico estrecho.
- Es frágil en alta dimensión; el modo conjunto no equivale al vector de modos marginales.

No usar MAP como resumen predeterminado si se dispone de draws posteriores.

### Media geométrica y escala log

Para una cantidad positiva con interpretación multiplicativa, resumir `log θ` y volver a escala puede ser más natural. `exp(E[log θ | y])` es la media geométrica posterior, no la media aritmética de `θ`.

## Dispersión e intervalos

### Varianza y desviación estándar posteriores

`Var(θ|y) = E[(θ-E[θ|y])² | y]` y `SD(θ|y) = √Var(θ|y)`.

- Miden dispersión alrededor de la media en la escala elegida.
- Son incompletas para asimetría, colas pesadas y multimodalidad.
- No confundir `SD posterior` con `MCSE` de la estimación de esa media.

### Desviación absoluta mediana

`MAD = median(|θ - median(θ)| | y)`.

Es una medida robusta de escala. Declarar si se usa la versión cruda o multiplicada por una constante de consistencia normal.

### Intervalo central o equal-tailed interval (ETI)

Un ETI de masa `1-α` es `[q_{α/2}, q_{1-α/2}]`.

- Deja `α/2` de masa en cada cola.
- Sus extremos se transforman coherentemente bajo transformaciones monótonas.
- Puede incluir regiones de baja densidad en distribuciones multimodales.

### Intervalo o conjunto de mayor densidad (HDI/HDS)

Un conjunto de mayor densidad de masa `1-α` contiene puntos cuya densidad no es menor que la de los excluidos, sujeto a contener esa masa.

- Produce un intervalo corto en distribuciones unimodales regulares.
- Puede ser un conjunto disjunto en una posterior multimodal; forzarlo a un intervalo continuo oculta el valle.
- No es invariante a reparametrizaciones no lineales porque compara alturas de densidad.
- Su estimación desde draws depende del algoritmo y del tamaño de muestra.

Declarar masa y método: “HDI 90% estimado desde draws”. No llamar “95% de confianza” a un intervalo creíble.

### Intervalos simultáneos y marginales

Un intervalo marginal de 95% para cada uno de `K` parámetros no produce una región conjunta con 95% de probabilidad. Para bandas de una curva o múltiples contrastes, construir una banda simultánea o una región conjunta cuando la afirmación sea global.

### Intervalo predictivo frente a intervalo de parámetro

Un intervalo para `E[ỹ|θ]` refleja incertidumbre sobre la media condicional. Un intervalo para una nueva `ỹ` añade variación observacional y suele ser más ancho. Nombrar siempre el objeto.

## Probabilidades de eventos y efectos

### Probabilidad de superar un umbral

`P(g(θ) > c | y) ≈ S⁻¹Σ_s I[g(θ_s)>c]`.

Es directa y útil si `c` tiene significado. Reportar:

- Evento y umbral en unidades.
- Condicionamiento en modelo y datos.
- MCSE, especialmente si la probabilidad está cerca de 0 o 1.
- Sensibilidad al prior y a la definición del evento.

### Probabilidad de signo o dirección

Para un efecto `δ`, usar `P(δ>0|y)` o `max{P(δ>0|y), P(δ<0|y)}`. Esta última a veces se llama probabilidad de dirección.

- Resume dirección, no magnitud.
- Puede ser alta para un efecto prácticamente trivial.
- Depende del punto nulo y no reemplaza una función de pérdida.

### ROPE: región de equivalencia práctica

Definir una región sustantiva `[−δ₀, δ₀]` o asimétrica si los costos difieren. Calcular:

- `P(δ ∈ ROPE | y)`.
- `P(δ > límite superior | y)`.
- `P(δ < límite inferior | y)`.

Elegir el ROPE antes de mirar la posterior cuando sea posible y justificarlo con dominio, medición o decisión. No convertir reglas como “todo el intervalo dentro/fuera” en una prueba universal. Una gran masa dentro del ROPE apoya equivalencia práctica condicional; no demuestra una igualdad puntual.

### Efectos absolutos y relativos

Para probabilidades `p₁` y `p₀`, derivar por draw:

- Diferencia de riesgo: `RD = p₁ - p₀`.
- Riesgo relativo: `RR = p₁/p₀`.
- Odds ratio: `OR = [p₁/(1-p₁)]/[p₀/(1-p₀)]`.
- Número necesario a tratar: `NNT = 1/RD` cuando la definición y el signo lo permiten.

No intercambiarlos: un OR puede parecer grande cuando el riesgo base es pequeño, y NNT se vuelve inestable cerca de `RD=0`. Reportar riesgos absolutos junto con métricas relativas.

### Efectos estandarizados

Los tamaños estandarizados ayudan a comparar escalas, pero heredan la definición del denominador. Explicar si la desviación es residual, total, previa, posterior o de una población de referencia. Preferir también unidades originales.

## Actualización e información

### Contracción prior-posterior

Una medida descriptiva simple es `1 - SD_post/SD_prior`, si ambas desviaciones existen y se comparan en la misma escala.

- Valores mayores sugieren reducción de dispersión marginal.
- Puede ser negativa si la posterior es más dispersa.
- No captura desplazamientos, multimodalidad o dependencia.
- No es una fracción universal de “información aprendida”.

Comparar densidades, cuantiles y cantidades predictivas además de un cociente. `GELMAN20` discute comparación de desviaciones o cuantiles como aproximación de sensibilidad/informatividad `[GELMAN20, §6.3, pp. 34–36]`.

### Entropía

Para una distribución discreta, `H(p) = -Σ_x p(x)log p(x)`. Para densidades continuas, la entropía diferencial depende de unidades y parametrización.

- Menor entropía suele implicar mayor concentración.
- No comparar entropías diferenciales entre escalas sin cuidado.

### Divergencia de Kullback–Leibler

`KL(p || q) = E_p[log p(X) - log q(X)] ≥ 0`.

- Mide discrepancia dirigida; no es simétrica ni distancia métrica.
- `KL(posterior || prior)` puede cuantificar actualización bajo condiciones de soporte adecuadas.
- Infinita o inestable si `q` asigna densidad nula donde `p` no.
- Un valor agregado puede ocultar qué región o cantidad cambió.

La información mutua `I(Θ;Y) = E_Y[KL(p(θ|Y)||p(θ))]` es una expectativa pre-data útil para diseño, no el mismo objeto que KL observado para un dataset.

## Cantidades derivadas y propagación

Propagar cada draw por toda la transformación:

`θ_s → η_s = g(θ_s, x) → ỹ_s ~ p(ỹ | η_s) → u_s = U(a, ỹ_s)`.

Esto preserva:

- Dependencia posterior entre parámetros.
- No linealidad.
- Incertidumbre de parámetros.
- Variación observacional, si se simula `ỹ_s`.

Distinguir cuatro objetos:

1. `g(E[θ|y])`: predicción plug-in; suele subestimar incertidumbre y puede estar sesgada por no linealidad.
2. `E[g(θ)|y]`: promedio sobre incertidumbre paramétrica.
3. `E[ỹ|y]`: media posterior predictiva.
4. `ỹ_s`: distribución de una observación o conjunto futuro.

Para agregados, simular la estructura conjunta apropiada. Sumar cuantiles marginales no produce cuantiles del total, y asumir independencia puede destruir correlaciones relevantes.

## Teoría bayesiana de decisión

Definir:

- Estado desconocido `θ` o resultado futuro `ỹ`.
- Acción `a ∈ A`.
- Pérdida `L(a, θ)` o utilidad `U(a, θ)`.
- Riesgo posterior `ρ(a|y) = E[L(a,θ)|y]`.
- Acción de Bayes `a* = argmin_a ρ(a|y)`; equivalentemente maximizar utilidad esperada.

Resultados básicos para estimar una cantidad escalar:

- Pérdida cuadrática `(a-θ)²` → media posterior.
- Pérdida absoluta `|a-θ|` → mediana posterior.
- Pérdida de cuantiles `ρ_τ(θ-a)` → cuantil posterior `τ`.
- Pérdida 0–1 discreta → moda posterior.

Para decisión binaria con acción positiva `a=1`, costo de falso positivo `C_FP` y falso negativo `C_FN`, actuar si:

`P(estado positivo | y) > C_FP / (C_FP + C_FN)`,

bajo pérdidas cero para decisiones correctas y sin otros costos. Este umbral no es universal: cambia con prevalencia modelada, beneficios, capacidad y utilidad.

### Regret y valor de información

- Regret para estado `θ`: `R(a,θ) = L(a,θ) - min_{a'}L(a',θ)`.
- EVPI: mejora esperada al conocer perfectamente el estado antes de decidir.
- EVSI: mejora esperada de una fuente de datos propuesta, promediada sobre su distribución predictiva.

Usar EVSI para preguntar si recolectar datos vale el costo. Exige modelar cómo los nuevos datos actualizarían la decisión, no solo cuánto reducirían un intervalo.

### Decisión robusta

Si decisiones cambian mucho entre priors o modelos plausibles:

- Reportar la frontera de decisión.
- Calcular utilidad bajo cada especificación.
- Considerar minimax regret o una política conservadora si no puede asignarse una mezcla defendible.
- Buscar datos que resuelvan la sensibilidad relevante.

No ocultar incertidumbre de modelo dentro de una única probabilidad posterior.

## Selección rápida de métricas

| Pregunta | Métrica primaria | Acompañar con | Evitar como único resumen |
|---|---|---|---|
| Valor típico bajo pérdida cuadrática | Media posterior | SD, intervalo y forma | MAP |
| Valor típico robusto | Mediana | ETI/HDI y densidad | Media si hay colas fuertes |
| Rango plausible | ETI o HDI con masa declarada | Densidad/draws | Solo ancho |
| Dirección | `P(δ>0|y)` | Magnitud y ROPE | Etiqueta significativo/no |
| Relevancia práctica | Masa dentro/fuera de ROPE | Pérdida/utilidad | Umbral no justificado |
| Predicción individual | Posterior predictiva | Cobertura y score | Intervalo de la media |
| Actualización por datos | Prior vs posterior | Predictivas y sensibilidad | Contracción aislada |
| Acción | Riesgo o utilidad posterior | Regret y sensibilidad | Probabilidad sin costos |
| Datos adicionales | EVSI menos costo | EVPI y escenarios | Solo reducción de SD |

## Plantilla de comunicación

Usar una formulación como:

> Condicionado al modelo `M`, al prior `π` y a los datos `y`, la mediana posterior de `δ` es **X unidades** y el intervalo creíble central de 90% es **[L, U]**. La probabilidad posterior de superar el umbral práctico `c` es **P**. El MCSE de estos resúmenes es **...**, por lo que el error de simulación es pequeño/grande respecto de la precisión requerida. La decisión **a** minimiza la pérdida esperada definida, pero cambia/no cambia bajo los priors y modelos alternativos examinados.

Añadir una visualización de la distribución cuando asimetría, colas o multimodalidad afecten la lectura. Evitar lenguaje de certeza ontológica: todas las probabilidades posteriores son condicionales al modelo y a la información incorporada.
