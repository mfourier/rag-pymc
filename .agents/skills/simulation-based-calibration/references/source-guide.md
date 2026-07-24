# Guía de fuentes y trazabilidad

## Contenido

1. Fuentes primarias
2. Jerarquía por tema
3. Refinamientos y tensiones
4. Información insuficiente
5. Convención de citas

## Fuentes primarias

### `[TALTS20]`

Sean Talts, Michael Betancourt, Daniel Simpson, Aki Vehtari y Andrew Gelman, *Validating Bayesian Inference Algorithms with Simulation-Based Calibration*, arXiv:1804.06788v2, 21 de octubre de 2020, 19 páginas.

- Archivo local: `.local-learning/SBC-Validating Bayesian Inference-Algorithms with Simulation-Based-Calibration.pdf`
- SHA-256: `64ed9a85a4467380afb446588d4cb34788cc3a90ab4c95986f230f0372b9fed6`
- Aporte principal: formulación operativa del prior SBC mediante rangos; interpretación gráfica; tratamiento histórico de autocorrelación; casos de MCMC, ADVI e INLA.

### `[MODRAK23]`

Martin Modrák, Angie H. Moon, Shinyoung Kim, Paul Bürkner, Niko Huurre, Kateřina Faltejsková, Andrew Gelman y Aki Vehtari, *Simulation-Based Calibration Checking for Bayesian Computation: The Choice of Test Quantities Shapes Sensitivity*, arXiv:2211.02383v3, 19 de octubre de 2023, 50 páginas.

- Archivo local real: `.local-learning/Simulation-Based Calibration Checking for Bayesian Computation:` seguido de un salto de línea y `The Choice of Test Quantities Shapes Sensitivity.pdf`.
- SHA-256: `ffe2c8ebea1ceae0466eb3a16af1f0a8c06a06c13966627efcabc03ac9d8dd77`
- Aporte principal: cantidades de prueba dependientes de parámetros y datos; desempate aleatorio; caracterización teórica de sensibilidad; distinción entre SBC y posterior promediado sobre datos; recomendaciones prácticas.

### `[POSTSBC25]`

Teemu Säilynoja, Marvin Schmitt, Paul-Christian Bürkner y Aki Vehtari, *Posterior SBC: Simulation-Based Calibration Checking Conditional on Data*, arXiv:2502.03279v2, 10 de marzo de 2025, 25 páginas.

- Archivo local real: `.local-learning/Posterior SBC_ Simulation-Based Calibration_Checking Conditional on Data.pdf`
- SHA-256: `e6bbf65f2ade7535534523ff4e6f129cc62642e6d10d688009955cd08f6fd6f4`
- Aporte principal: posterior SBC condicionado a datos observados; comparación con prior SBC; aplicaciones a MCMC, ecuaciones diferenciales e inferencia amortizada.

## Jerarquía por tema

Usar `[TALTS20]` para la construcción fundacional, los patrones gráficos históricos y el procedimiento MCMC descrito allí. Usar `[MODRAK23]` como autoridad posterior para cantidades de prueba, empates, variables discretas, sensibilidad y la relación con el posterior promediado sobre datos. Usar `[POSTSBC25]` para cualquier afirmación específica sobre posterior SBC.

No tratar un caso de estudio como ley general. Cuando una recomendación de una fuente se base en experiencia o simulaciones, identificarla como recomendación de los autores y conservar su contexto.

## Refinamientos y tensiones

### SBC frente al posterior promediado sobre datos

`[TALTS20, §2, ec. (1), pp. 2–3]` usa la identidad que recupera el prior al promediar posteriores sobre datos para motivar la validación. `[MODRAK23, §§1.1 y 3.5, pp. 2 y 10]` aclara que el chequeo de rangos SBC explota una propiedad conjunta condicional y no equivale a verificar aquella identidad; construye ejemplos donde uno de los chequeos pasa y el otro falla. Adoptar esta distinción más reciente. Presentar las formas de histogramas de `[TALTS20, §4.2]` como interpretaciones diagnósticas, no como una equivalencia matemática general con el posterior promediado sobre datos.

### Empates y variables discretas

La formulación de rangos de `[TALTS20, §4.1]` cuenta valores estrictamente menores y no desarrolla desempate para masas puntuales. `[MODRAK23, §1.2 y teoremas 3–4, pp. 3 y 8]` añade un rango aleatorio entre posiciones empatadas y sostiene que esto permite cantidades con masas puntuales y parámetros discretos. Usar el procedimiento de 2023 cuando puedan existir empates.

### Cantidades de prueba

`[TALTS20, §§4.1 y 4.3]` formula cantidades escalares `f(θ)`. `[MODRAK23, §§1.2, 3.3–3.4 y 6.1]` amplía a `f(θ,y)` y demuestra que cantidades sólo paramétricas no detectan clases como un algoritmo que devuelve el prior e ignora datos. Adoptar la formulación ampliada; conservar parámetros individuales porque siguen siendo recomendados.

### Alcance global frente a alcance condicional

`[TALTS20]` y `[MODRAK23]` estudian principalmente prior SBC sobre el prior predictivo. `[POSTSBC25, §3]` propone posterior SBC para enfocar el chequeo en la región relevante después de observar datos. No es una refutación: ambas variantes responden preguntas distintas.

## Información insuficiente o ambigua

- Los papers no proporcionan una implementación específica para PyMC ni una API estable. Verificar documentación del software antes de generar código ejecutable.
- `[POSTSBC25]` es un preprint arXiv v2 en el material proporcionado. Tratar sus propuestas y casos como evidencia de ese manuscrito, no como consenso definitivo.
- `[POSTSBC25, §3, p. 5]` dice que sería “muy improbable” que un sesgo fuese consistente a través de la actualización bayesiana; esto es un argumento de plausibilidad, no una garantía formal.
- `[MODRAK23, §6.1]` recomienda la log-verosimilitud conjunta por teoría y casos empíricos, pero `[MODRAK23, §5.2, pp. 19–20]` muestra que no fue la cantidad más rápida para un error en el prior/Jacobiano. Mantener ambas afirmaciones.
- Las fuentes no fijan un tamaño universal de simulaciones o muestras. Sus reglas presupuestarias dependen del costo, efecto buscado y precisión.
- Las fuentes no resuelven de manera general comparaciones múltiples entre muchas cantidades de prueba; `[MODRAK23, §6.2, pp. 21–22]` lo deja como limitación práctica.

## Convención de citas

Citar afirmaciones reutilizables como `[CLAVE, §sección, ec./fig./alg. si aplica, p./pp.]`. Ejemplos:

- `[TALTS20, §4.1, alg. 1, p. 6]`
- `[MODRAK23, §3.3, teorema 6, p. 9]`
- `[POSTSBC25, §3, ec. (3), p. 5]`

Para recomendaciones adaptadas, citar primero la evidencia y rotular la adaptación como interpretación o recomendación. Si un detalle no aparece en estas referencias, declararlo y consultar el PDF original antes de atribuirlo.
