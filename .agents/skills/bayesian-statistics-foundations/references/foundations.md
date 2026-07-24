# Fundamentos probabilísticos y de modelado

## Contenido

1. [Lenguaje de probabilidad](#lenguaje-de-probabilidad)
2. [Teorema de Bayes](#teorema-de-bayes)
3. [Anatomía de un modelo bayesiano](#anatomía-de-un-modelo-bayesiano)
4. [Predicción y modelo generativo](#predicción-y-modelo-generativo)
5. [Elección e interpretación del prior](#elección-e-interpretación-del-prior)
6. [Aprendizaje, identificabilidad e información](#aprendizaje-identificabilidad-e-información)
7. [Modelos jerárquicos y pooling](#modelos-jerárquicos-y-pooling)
8. [Parametrización, transformaciones y escalas](#parametrización-transformaciones-y-escalas)
9. [Asociación, causalidad y generalización](#asociación-causalidad-y-generalización)
10. [Distinciones que no deben colapsarse](#distinciones-que-no-deben-colapsarse)

## Lenguaje de probabilidad

Tratar la probabilidad como una medida coherente de incertidumbre condicional a información y supuestos.

Para eventos `A` y `B`:

- `0 ≤ P(A) ≤ 1`.
- `P(Ω) = 1`.
- Si `A ∩ B = ∅`, entonces `P(A ∪ B) = P(A) + P(B)`.
- Complemento: `P(Aᶜ) = 1 - P(A)`.
- Unión: `P(A ∪ B) = P(A) + P(B) - P(A ∩ B)`.
- Condicional: `P(A | B) = P(A ∩ B) / P(B)` cuando `P(B) > 0`.
- Producto: `P(A ∩ B) = P(A | B)P(B)`.
- Probabilidad total, para una partición `{B_k}`: `P(A) = Σ_k P(A | B_k)P(B_k)`.

No confundir:

- **Independencia:** `P(A, B) = P(A)P(B)`.
- **Independencia condicional:** `P(A, B | C) = P(A | C)P(B | C)`.
- **Exclusión mutua:** `A ∩ B = ∅`; salvo eventos degenerados, no implica independencia.

Para variables continuas, `p(x)` es densidad, no probabilidad puntual. Las probabilidades son integrales: `P(a < X < b) = ∫_a^b p(x) dx`. Una densidad puede ser mayor que uno sin violar axiomas.

La esperanza `E[g(X)] = ∫ g(x)p(x)dx` resume una función bajo una distribución; la varianza `Var(X) = E[(X-E[X])²]` mide dispersión cuadrática. La covarianza y correlación describen dependencia lineal, no causalidad ni independencia general.

## Teorema de Bayes

Para hipótesis o parámetros `θ` y datos `y`:

`p(θ | y) = p(y | θ)p(θ) / p(y)`,

donde

`p(y) = ∫ p(y | θ)p(θ)dθ`

para un parámetro continuo, o una suma para hipótesis discretas.

Interpretar:

- `p(θ)`: incertidumbre previa o restricción probabilística antes de condicionar en `y`.
- `p(y | θ)`: verosimilitud como función de `θ` para el `y` observado.
- `p(y)`: evidencia o densidad predictiva marginal que normaliza.
- `p(θ | y)`: incertidumbre actualizada dentro del modelo.

La forma proporcional

`p(θ | y) ∝ p(y | θ)p(θ)`

es útil para inferir parámetros, pero la constante omitida importa en predicción marginal y comparación mediante Bayes factors.

En odds:

`odds posteriores = Bayes factor × odds previas`,

con `BF₁₀ = p(y | M₁) / p(y | M₀)`. Un Bayes factor no es una probabilidad posterior de modelo sin odds previas.

## Anatomía de un modelo bayesiano

Definir explícitamente:

- Datos observados `y` y covariables tratadas como fijas o aleatorias `x`.
- Parámetros `θ`, hiperparámetros `φ` y variables latentes `z`.
- Modelo de observación `p(y | θ, z, x)`.
- Modelo latente `p(z | θ, x)` cuando corresponda.
- Priors `p(θ, φ)` y dependencias entre ellos.
- Cantidades derivadas `g(θ, z)` y observaciones futuras `ỹ`.

Factorizar la conjunta, por ejemplo:

`p(y, z, θ, φ | x) = p(y | z, θ, x)p(z | θ, φ, x)p(θ | φ)p(φ)`.

La factorización aclara supuestos de independencia, unidades de replicación y qué se mantiene fijo. Usar diagramas causales o grafos probabilísticos si la dependencia no cabe en una oración.

Recordar que la verosimilitud no es una distribución de probabilidad sobre `θ` por sí sola. El estimador de máxima verosimilitud maximiza `p(y | θ)`; el MAP maximiza `p(θ | y)` y cambia bajo reparametrización por el jacobiano.

## Predicción y modelo generativo

La distribución prior predictiva es:

`p(ỹ) = ∫ p(ỹ | θ)p(θ)dθ`.

La distribución posterior predictiva es:

`p(ỹ | y) = ∫ p(ỹ | θ)p(θ | y)dθ`.

La primera muestra qué datos considera plausibles el modelo antes de observar `y`; la segunda propaga incertidumbre paramétrica y variación observacional después de aprender de `y`.

Un modelo plenamente generativo define una conjunta propia de datos y parámetros y permite simular todos los elementos estocásticos. Modelos condicionales, como `p(y | x, θ)`, pueden ser parcialmente generativos: predicen `y` condicionando en `x`, pero no generan nuevos `x` salvo que se añada `p(x)`.

Dos diseños pueden producir likelihoods proporcionales para `θ` y, sin embargo, distribuciones predictivas diferentes. Especificar el mecanismo de muestreo y la unidad que se replica. `GELMAN20` usa binomial frente a binomial negativa para mostrar esta diferencia `[GELMAN20, §2.5, pp. 11–12]`.

## Elección e interpretación del prior

Elegir priors en cuatro pasos:

1. Identificar soporte, unidades y restricciones.
2. Expresar valores plausibles y extremos en cantidades observables o efectos sustantivos.
3. Traducirlos a la parametrización del modelo.
4. simular del prior predictivo y revisar implicaciones conjuntas.

Distinguir propósitos que pueden coexistir:

- Incorporar conocimiento específico.
- Regularizar parámetros débilmente identificados.
- Mantener predicciones en escalas plausibles.
- Romper simetrías o expresar restricciones reales.
- Servir de componente jerárquico aprendido parcialmente de grupos.

Clasificar, sin fingir fronteras absolutas:

- Prior plano impropio: puede producir posterior impropia y no genera datos.
- Prior propio extremadamente amplio: puede asignar masa a regiones absurdas.
- Débilmente informativo: descarta extremos implausibles sin fijar estrechamente el resultado.
- Informativo específico: codifica conocimiento sustantivo verificable.
- Prior de referencia/default: depende de objetivo, escala y régimen asintótico; no es neutral universal.

La información conjunta puede ser fuerte aunque cada marginal parezca débil. Con más predictores o parámetros, la masa se concentra geométricamente y puede inducir predicciones extremas. Revisar el prior sobre resultados, `R²`, escalas y combinaciones, no solo coeficientes marginales `[GELMAN20, §2.4, pp. 10–11; §7.3, pp. 39–41]`.

No usar los datos dos veces de forma oculta. Los priors empíricos o escalados con datos son modelos/procedimientos distintos; documentar la dependencia y evaluar su efecto.

## Aprendizaje, identificabilidad e información

Distinguir:

- **Identificabilidad estructural:** parámetros distintos inducen distribuciones observacionales distintas en el modelo ideal.
- **Identificabilidad práctica:** los datos finitos y el prior separan suficientemente regiones del parámetro.
- **Recuperación de parámetros:** en datos simulados, la posterior localiza cantidades verdaderas con incertidumbre coherente.
- **Capacidad predictiva:** pueden existir buenas predicciones aun con parámetros latentes poco identificados.

Comparar prior y posterior ayuda a preguntar cuánto aprendieron los datos, pero una posterior similar al prior no implica automáticamente un error: los datos pueden no ser informativos para esa cantidad. Una posterior estrecha tampoco garantiza verdad si el likelihood o el prior son incorrectos.

Medidas posibles de actualización incluyen cambio en desviación estándar o cuantiles, divergencia KL y cambio en entropía. Usarlas con cuidado:

- Dependen de parametrización o dirección de KL.
- No indican por sí solas si la información es correcta.
- En múltiples dimensiones, los marginales pueden ocultar cambios de dependencia.

Probar datos simulados en regiones centrales, extremas y cercanas a no-identificabilidad. Una simulación aislada detecta fallos graves, pero no calibra un algoritmo; para ello usar SBC repetida `[GELMAN20, §4.1–4.2, pp. 16–20]`.

## Modelos jerárquicos y pooling

En un modelo de grupos:

`y_ij ~ p(y_ij | θ_j)`

`θ_j ~ p(θ_j | μ, τ)`

`(μ, τ) ~ p(μ, τ)`.

Comparar:

- **No pooling:** estimar cada `θ_j` por separado; alta varianza en grupos pequeños.
- **Complete pooling:** imponer un único `θ`; puede borrar heterogeneidad.
- **Partial pooling:** aprender similitud entre grupos y contraer estimaciones ruidosas hacia la distribución poblacional.

La contracción depende del ruido de cada grupo y de `τ`; no es un porcentaje fijo. Interpretar `μ` y `τ` como parámetros de una población de grupos solo si la exchangeability condicional es defendible.

**Exchangeability** significa que el orden de unidades no cambia la conjunta bajo la información modelada. No significa que sean idénticas; covariables y estructuras temporales/espaciales pueden hacer razonable una exchangeability condicional.

Al validar, decidir si la predicción objetivo es para:

- Otra observación de un grupo conocido.
- Un grupo conocido sin datos actuales.
- Un grupo nuevo de la misma población.
- Una población de grupos distinta.

Cada objetivo requiere una partición de validación y una posterior predictiva diferentes.

## Parametrización, transformaciones y escalas

Preferir parámetros con significado y escala aproximadamente unitaria. Centrar o estandarizar predictores cuando simplifique priors e inferencia, pero conservar la transformación para volver a unidades originales.

Transformaciones frecuentes:

- Positivos: `log θ` o una parametrización positiva explícita.
- Probabilidades: `logit(p) = log[p/(1-p)]`.
- Proporciones composicionales: coordenadas log-ratio adecuadas.
- Matrices de correlación: parametrizaciones que preserven positividad definida.

Recordar que un prior uniforme cambia al transformar: si `φ = g(θ)`, entonces

`p_φ(φ) = p_θ(g⁻¹(φ)) |d g⁻¹(φ)/dφ|`.

En jerarquías, comparar parametrización centrada y no centrada. La no centrada escribe, por ejemplo, `θ_j = μ + τ z_j`, `z_j ~ Normal(0,1)`, y suele mejorar geometría cuando los grupos informan poco; la centrada puede ser mejor cuando informan mucho. Diagnosticar, no dogmatizar.

El escalado facilita priors, partial pooling e interpretación `[GELMAN20, §2.3, pp. 9–10]`. No reportar solo coeficientes estandarizados si la decisión vive en otra unidad.

## Asociación, causalidad y generalización

Una posterior para `p(y | x)` responde una pregunta asociacional salvo que el diseño y los supuestos causales identifiquen una intervención. Para interpretar `E[Y(1)-Y(0)]` se requieren, según el diseño, supuestos como consistencia, positividad, ausencia de confusión no medida y una unidad/interferencia bien definidas.

La probabilidad bayesiana cuantifica incertidumbre dentro de esos supuestos; no elimina confusión, sesgo de selección, error de medición ni falta de transporte.

Generalizar puede significar:

- De muestra a población.
- De control a tratamiento o de una intervención a otra.
- De mediciones a constructos latentes.
- Del periodo observado al futuro.
- De grupos conocidos a grupos nuevos.

Modelar el mecanismo relevante, usar ponderación/postestratificación cuando corresponda y validar en una partición que imite el uso. `GELMAN20` destaca que predicción, generalización y postestratificación extienden el workflow más allá del ajuste `[GELMAN20, §12.5, pp. 66–67]`.

## Distinciones que no deben colapsarse

| Concepto | Responde | No responde por sí solo |
|---|---|---|
| Prior | ¿Qué valores/modelos son plausibles antes de `y`? | ¿Qué dicen los datos observados? |
| Likelihood | ¿Qué tan compatibles son distintos parámetros con `y`? | Probabilidad de `θ` sin prior |
| Posterior | ¿Qué incertidumbre queda sobre `θ` dado modelo y datos? | Adecuación del modelo al mundo |
| Prior predictiva | ¿Qué datos permite el modelo antes de `y`? | Ajuste a los datos observados |
| Posterior predictiva | ¿Qué réplicas/futuros implica el modelo ajustado? | Generalización fuera del dominio sin supuestos |
| Error Monte Carlo | ¿Cuánto varía el resumen por simulación finita? | Incertidumbre científica o predictiva |
| Intervalo creíble | ¿Qué masa posterior contiene un conjunto? | Cobertura frecuentista automática |
| Intervalo de confianza | ¿Qué procedimiento cubre bajo repeticiones? | Probabilidad posterior del parámetro |
| Calibración | ¿Coinciden probabilidades y frecuencias bajo un régimen? | Agudeza, utilidad o causalidad |
| Identificabilidad | ¿Pueden distinguirse parámetros dentro del modelo? | Verdad del modelo o calidad de medición |
