# Ejemplos trabajados y patrones pedagógicos

## Contenido

1. [Cómo usar los ejemplos](#cómo-usar-los-ejemplos)
2. [Beta–binomial: actualización y predicción](#betabinomial-actualización-y-predicción)
3. [Diagnóstico médico: tasas base y decisión](#diagnóstico-médico-tasas-base-y-decisión)
4. [Normal–normal: precisión ponderada](#normalnormal-precisión-ponderada)
5. [Modelo jerárquico: partial pooling](#modelo-jerárquico-partial-pooling)
6. [Propagación no lineal](#propagación-no-lineal)
7. [Scores binarios](#scores-binarios)
8. [Diagnóstico MCMC orientado a la decisión](#diagnóstico-mcmc-orientado-a-la-decisión)
9. [Caso golf: expansión guiada por misfit](#caso-golf-expansión-guiada-por-misfit)
10. [Caso planetario: multimodalidad inesperada](#caso-planetario-multimodalidad-inesperada)
11. [Patrones de respuesta](#patrones-de-respuesta)

## Cómo usar los ejemplos

Adaptar cada ejemplo en cinco capas:

1. Pregunta en lenguaje natural.
2. Historia generativa y supuestos.
3. Derivación o simulación.
4. Interpretación con unidades y condicionamiento.
5. Chequeo o límite que impide sobreinterpretar.

No reemplazar los números del usuario con estos ejemplos. Usarlos como plantilla de razonamiento y recalcular las cantidades del caso real.

## Beta–binomial: actualización y predicción

### Pregunta

Estimar la probabilidad `θ` de éxito de un proceso Bernoulli después de observar 8 éxitos en 10 ensayos, con prior `Beta(2,2)`.

### Modelo

`θ ~ Beta(α=2, β=2)`

`y | θ ~ Binomial(n=10, θ)`

La densidad conjunta es proporcional a:

`θ^(α-1)(1-θ)^(β-1) × θ^y(1-θ)^(n-y)`.

### Posterior

Por conjugación:

`θ | y ~ Beta(α+y, β+n-y) = Beta(10,4)`.

Resúmenes:

- Media previa: `2/(2+2)=0.5`.
- Media posterior: `10/(10+4)=0.714`.
- Moda posterior: `(10-1)/(10+4-2)=0.75`, porque ambos parámetros son mayores que 1.
- Predictiva para el próximo ensayo: `P(ỹ=1|y)=E[θ|y]=0.714`.

### Interpretación

> Condicionado al modelo binomial, al prior `Beta(2,2)` y a 8 éxitos de 10, la probabilidad posterior media de éxito es aproximadamente 0.714. La misma cantidad es la probabilidad posterior predictiva de éxito en un ensayo nuevo exchangeable.

No decir que “hay 71.4% de éxitos en el futuro” sin aclarar que se refiere a un ensayo exchangeable y al modelo.

### Prior y posterior predictiva

Antes de datos, el número de éxitos `ỹ` en `m` ensayos sigue una beta-binomial:

`P(ỹ=k) = C(m,k) B(k+α, m-k+β)/B(α,β)`.

Después de datos, reemplazar `(α,β)` por `(10,4)`. Esta distribución incorpora variación binomial e incertidumbre en `θ`; usar `Binomial(m, E[θ|y])` omite la segunda y suele subestimar dispersión.

### Sensibilidad

Comparar con priors plausibles, por ejemplo `Beta(1,1)` y uno informativo sustentado. Con solo 10 ensayos, el prior puede mover materialmente la posterior; reportarlo en vez de ocultarlo.

## Diagnóstico médico: tasas base y decisión

### Pregunta

Calcular `P(enfermedad | positivo)` si:

- Prevalencia `P(D)=0.01`.
- Sensibilidad `P(+|D)=0.95`.
- Especificidad `P(-|Dᶜ)=0.90`, por lo que `P(+|Dᶜ)=0.10`.

### Cálculo

`P(D|+) = P(+|D)P(D) / [P(+|D)P(D)+P(+|Dᶜ)P(Dᶜ)]`

`= 0.95×0.01 / [0.95×0.01 + 0.10×0.99]`

`= 0.0095 / 0.1085 ≈ 0.0876`.

Aunque el test tiene alta sensibilidad, la mayoría de positivos son falsos en una población con prevalencia baja y especificidad de 90%.

### Forma de frecuencias naturales

En 10 000 personas:

- 100 enfermas → 95 positivas.
- 9900 no enfermas → 990 positivas falsas.
- Total positivo 1085 → 95/1085 ≈ 8.8% enfermas.

### Extensión bayesiana

Si prevalencia, sensibilidad y especificidad son inciertas, asignarles distribuciones posteriores y calcular `P(D|+)` por draw. No insertar solo estimaciones puntuales. Incluir dependencia o spectrum bias si el rendimiento del test cambia entre poblaciones.

### Decisión

La probabilidad posterior no determina por sí sola si tratar. Definir costos de tratar sin enfermedad, de no tratar con enfermedad, de un test confirmatorio y efectos adversos. Un umbral de acción surge de esos costos y puede ser muy distinto de 0.5.

## Normal–normal: precisión ponderada

### Modelo

Supóngase una media desconocida con varianza observacional conocida:

`μ ~ Normal(μ₀, τ₀²)`

`y_i | μ ~ Normal(μ, σ²)`, para `i=1,…,n`.

### Posterior

Definir precisiones `λ₀=1/τ₀²` y `λ_y=n/σ²`. Entonces:

`τ_n² = 1/(λ₀+λ_y)`

`μ_n = (λ₀ μ₀ + λ_y ȳ)/(λ₀+λ_y)`

`μ | y ~ Normal(μ_n, τ_n²)`.

La media posterior es un promedio ponderado por precisión. Más datos o menor `σ` dan más peso a `ȳ`; un prior más estrecho da más peso a `μ₀`.

### Predictiva

Para una nueva observación:

`ỹ | y ~ Normal(μ_n, σ² + τ_n²)`.

El intervalo predictivo incluye `σ²` y es más ancho que el intervalo para `μ`. Esta diferencia es una de las confusiones más frecuentes.

### Límite

Si `σ` es desconocida, la conjugación y predictiva cambian. Si datos tienen colas o heterogeneidad, la normal puede dar intervalos demasiado estrechos; comprobar con PPC.

## Modelo jerárquico: partial pooling

### Modelo simplificado

Para el grupo `j`, supóngase:

`ȳ_j | θ_j ~ Normal(θ_j, s_j²)`

`θ_j | μ,τ ~ Normal(μ,τ²)`.

Tratando `μ` y `τ` como conocidos, la media posterior es:

`E[θ_j|ȳ_j] = w_j ȳ_j + (1-w_j)μ`,

con

`w_j = τ²/(τ²+s_j²)`.

La varianza posterior es:

`Var(θ_j|ȳ_j) = 1/(1/s_j² + 1/τ²)`.

### Interpretación

- Grupo preciso (`s_j` pequeño) → `w_j` cerca de 1 → poca contracción.
- Grupo ruidoso (`s_j` grande) → `w_j` menor → mayor contracción hacia `μ`.
- Heterogeneidad grande (`τ` grande) → grupos se comparten menos.
- Heterogeneidad pequeña (`τ` pequeña) → pooling fuerte.

En el modelo real, `μ` y `τ` son inciertos y deben propagarse por draws. No presentar `w_j` como fijo salvo que esa aproximación sea deliberada.

### Validación

Elegir validación según uso:

- Nueva observación del mismo grupo: puede usar información del grupo.
- Grupo nuevo: debe integrar `θ_new ~ Normal(μ,τ²)` y dejar grupos completos fuera para evaluar.

LOO por observación puede sobreestimar desempeño para grupos nuevos.

## Propagación no lineal

Supóngase un coeficiente log-odds `β` con posterior. El odds ratio es `OR=exp(β)`.

No usar `exp(E[β|y])` como si fuera `E[OR|y]`; por convexidad, en general difieren. Para draws:

1. Calcular `OR_s=exp(β_s)`.
2. Resumir `{OR_s}` con mediana/intervalo o media si la pérdida lo requiere.
3. Convertir además a diferencias de probabilidad para riesgos base relevantes:

`p_{1,s}=logit⁻¹(logit(p₀)+β_s)`,

`RD_s=p_{1,s}-p₀`.

Un mismo OR produce diferencias absolutas distintas según `p₀`. Reportar el efecto en la escala de decisión.

## Scores binarios

Para una observación `y=1`:

- Modelo A predice `p_A=0.8`.
- Modelo B predice `p_B=0.6`.

Brier:

- A: `(0.8-1)²=0.04`.
- B: `(0.6-1)²=0.16`.

Log predictive density:

- A: `log(0.8)≈-0.223`.
- B: `log(0.6)≈-0.511`.

Para este caso A obtiene mejor score. No concluir superioridad general con una observación; sumar contribuciones fuera de muestra y estimar incertidumbre.

Si ambos predijeran un evento que no ocurre (`y=0`), el score cambia. El log score castiga especialmente la confianza extrema equivocada, mientras Brier tiene penalización cuadrática acotada para binarios.

Un clasificador que siempre predice la clase mayoritaria puede tener alta accuracy y mala utilidad/calibración en la clase rara. Mantener separadas métrica probabilística y regla de decisión.

## Diagnóstico MCMC orientado a la decisión

### Escenario

Un análisis reporta:

- `R-hat=1.00` para todos los coeficientes.
- 50 divergencias posteriores al warmup.
- `SD_post(δ)=2`.
- `ESS` para la media de `δ` igual a 1600.
- Umbral de decisión en `δ=0` y media posterior `0.08`.

### Lectura

El MCSE aproximado de la media es `2/√1600=0.05`. La media está a solo 1.6 MCSE del umbral, por lo que el error numérico puede importar para esa decisión. Además, las divergencias invalidan la tranquilidad que daría `R-hat`; pueden sesgar regiones relevantes.

### Acción

1. Mapear divergencias contra `δ`, escalas jerárquicas y parámetros correlacionados.
2. Revisar parametrización y prior.
3. Reajustar hasta resolver o acotar el sesgo.
4. Aumentar draws solo después de una exploración sana para reducir MCSE.
5. Reportar `P(δ>0|y)` con su MCSE y sensibilidad, no decidir desde la media sola.

## Caso golf: expansión guiada por misfit

### Secuencia del artículo

1. Ajustar una regresión logística a probabilidad de embocar según distancia.
2. Construir un modelo geométrico de un parámetro basado en error angular; ajusta mejor con menos parámetros.
3. Evaluar en nuevos datos: aparecen diferencias en putts cortos y fallo sistemático a larga distancia.
4. Añadir error de control de distancia. El ajuste MCMC converge mal.
5. Graficar el ajuste aproximado y notar que enormes conteos en bins cortos fuerzan demasiado la likelihood binomial.
6. Añadir un término transparente de error de modelo a la escala de proporciones.
7. Reajustar, revisar residuos y reconocer expansiones futuras por jugador/condición.

### Lecciones

- Construir desde mecanismos puede superar una forma estándar y mejorar interpretación.
- Datos nuevos son una prueba externa y una fuente de expansión.
- Mala convergencia puede señalar incompatibilidad modelo–datos, no solo sampler.
- Con grandes muestras, pequeños errores sistemáticos dominan una likelihood demasiado rígida: “datos mayores requieren modelos mayores”.
- Un parámetro “fudge” puede ser útil si su función y límites son explícitos; no fingir interpretación mecanística.
- El modelo final sigue siendo provisional.

Fuente: `[GELMAN20, §10, pp. 49–56]`.

## Caso planetario: multimodalidad inesperada

### Secuencia del artículo

1. Un modelo mecanístico con ODE falla: cadenas lentas y sin mezcla.
2. Reducir a un parámetro de fuerza `k`, con los demás fijados y datos simulados.
3. Usar múltiples cadenas, trazas incluyendo warmup y log-posterior; observar modos dependientes de inicialización.
4. Calcular la likelihood unidimensional por cuadratura y simular órbitas.
5. Descubrir modos menores por aliasing periódico: ajustan mal y tienen masa despreciable, pero atrapan cadenas y hacen lento el solver.
6. Evaluar priors, stacking e inicializaciones; elegir iniciales compatibles con prior y dominio después de entender los modos.
7. Reconstruir gradualmente el modelo completo y usar likelihoods condicionales para aislar nuevos modos.

### Lecciones

- No descartar cadenas solo porque su log posterior sea bajo.
- Usar predicciones por cadena para interpretar dónde quedó atrapada.
- Simplificar hasta que una herramienta exacta o una visualización haga visible la geometría.
- Un problema determinista fácil puede ser difícil al resolverlo sobre toda la posterior.
- Iniciales plausibles pueden ser parte del workflow, pero deben mantener capacidad para detectar modos relevantes.
- Multimodalidad matemática sin contenido y multimodalidad sustantiva requieren respuestas distintas.

Fuente: `[GELMAN20, §11, pp. 56–63]`.

## Patrones de respuesta

### Explicación corta pero completa

> **Concepto.** Definición en una frase.
> **Fórmula.** Notación con todos los condicionamientos.
> **Intuición.** Qué cambia al observar datos.
> **Ejemplo.** Un cálculo mínimo.
> **Cuidado.** La confusión más probable.

### Interpretación de posterior

> La cantidad objetivo es `Q=g(θ)` en **unidades**. Condicionado al modelo, prior y datos, su **resumen elegido** es X y su **intervalo de masa declarada** es [L,U]. La probabilidad de la región práctica es P. Los diagnósticos computacionales indican **evidencia**, con MCSE M. Los resultados son/ no son sensibles a **alternativas**. Esto apoya la acción A bajo la pérdida L, pero no identifica **límite**.

### Revisión de análisis

Organizar hallazgos:

1. **Objetivo/datos:** desalineaciones del estimando o medición.
2. **Modelo/prior:** supuestos y prior predictiva.
3. **Cómputo:** diagnósticos y precisión.
4. **Adecuación:** PPC dirigido.
5. **Generalización:** partición, score e influencia.
6. **Decisión/comunicación:** unidades, pérdida y límites.

Priorizar hallazgos que puedan cambiar la conclusión. Para cada uno dar evidencia, consecuencia y próxima comprobación.
