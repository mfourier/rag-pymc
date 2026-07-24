---
name: simulation-based-calibration
description: "Diseñar, revisar, interpretar y documentar estudios de Simulation-Based Calibration (SBC) para validar algoritmos de inferencia e implementaciones de modelos bayesianos. Usar ante consultas sobre prior SBC, posterior SBC condicionado a datos observados, histogramas de rangos o PIT/ECDF, elección de cantidades de prueba, empates y parámetros discretos, autocorrelación y thinning de MCMC, sesgo o dispersión de posteriores aproximados, y comparación entre SBC, diagnósticos de convergencia y chequeos predictivos."
---

# Simulation-Based Calibration

## Objetivo

Aplicar SBC con trazabilidad a las fuentes y separar siempre evidencia publicada, interpretación del caso y recomendación práctica. Tratar SBC como un chequeo de computación e implementación dentro del modelo asumido, no como validación de que el modelo represente el mundo real.

## Cargar las referencias necesarias

Leer siempre [references/source-guide.md](references/source-guide.md) para conocer procedencia, autoridad y refinamientos entre papers.

- Leer [references/foundations.md](references/foundations.md) para explicar o diseñar prior SBC, calcular rangos, interpretar gráficos o tratar autocorrelación.
- Leer [references/test-quantities.md](references/test-quantities.md) para elegir cantidades de prueba, detectar datos ignorados o dependencias incorrectas, manejar empates y razonar sobre sensibilidad.
- Leer [references/posterior-sbc.md](references/posterior-sbc.md) para decidir entre prior y posterior SBC o validar inferencia condicionada a datos observados.
- Leer las tres referencias al comparar variantes o emitir una recomendación integral.

No consultar los PDF originales salvo que la respuesta requiera un detalle ausente en estas referencias. Si se consultan, citar sección, ecuación, figura o página y actualizar la referencia pertinente cuando el dato sea reutilizable.

## Seguir el flujo de trabajo

1. **Delimitar el objetivo.** Identificar si se quiere revisar el generador, la implementación del modelo, el algoritmo de inferencia o la combinación. Aclarar que una falla SBC no localiza por sí sola cuál componente falló.
2. **Elegir el dominio de calibración.** Usar prior SBC para evaluar el comportamiento sobre el prior predictivo; considerar posterior SBC cuando importe la región condicionada a un conjunto de datos observado. No presentar ambas variantes como intercambiables.
3. **Definir cantidades de prueba.** Incluir parámetros relevantes y, por defecto, considerar la log-verosimilitud conjunta. Añadir cantidades dirigidas al riesgo concreto: verosimilitudes por subconjunto, predicciones, productos o diferencias de parámetros, o log-densidad del prior. Justificar cada cantidad.
4. **Especificar el experimento.** Separar generador e implementación inferencial; fijar replicaciones, muestras posteriores efectivamente independientes, semillas, fallas de ajuste y reglas de descarte antes de inspeccionar resultados. Aplicar desempate aleatorio cuando existan empates.
5. **Revisar la inferencia de cada réplica.** Examinar diagnósticos propios del algoritmo antes de atribuir no uniformidad a sesgo. Para MCMC, distinguir autocorrelación de exploración deficiente.
6. **Evaluar rangos.** Preferir histogramas de rangos y ECDF/PIT con bandas simultáneas apropiadas. Tratar pruebas numéricas como complemento y evitar decisiones binarias sin inspección gráfica.
7. **Interpretar con límites.** Tratar la uniformidad observada como ausencia de evidencia detectable bajo las cantidades y el presupuesto usados, nunca como prueba suficiente de corrección.
8. **Proponer la siguiente comprobación.** Recomendar chequeos predictivos o residuales para adecuación del modelo a datos reales y diagnósticos de convergencia para cada ajuste.

## Mantener un contrato de evidencia

Estructurar las respuestas sustantivas con estas etiquetas cuando sean útiles:

- **Evidencia:** afirmación atribuible a una fuente, con cita como `[TALTS20, §4.2, pp. 6–8]`.
- **Interpretación:** lectura del problema o de un patrón observado; explicitar incertidumbre y explicaciones alternativas.
- **Recomendación:** acción sugerida y su razón; indicar si proviene de los autores o es una adaptación al caso.

No inventar resultados, umbrales ni garantías. No trasladar resultados empíricos de un caso de estudio a otros modelos sin calificarlos. Documentar desacuerdos o cambios metodológicos según `source-guide.md` y priorizar la formulación más reciente para empates, cantidades dependientes de datos y la distinción entre SBC y posterior promediado sobre datos.

## Resolver solicitudes frecuentes

- Para “diseña un SBC para este modelo”, producir objetivo, variante, generador, algoritmo bajo prueba, cantidades de prueba, presupuesto, diagnósticos por réplica, visualizaciones y criterio de interpretación.
- Para “interpreta este histograma de rangos”, describir el patrón, enumerar causas compatibles, comprobar autocorrelación y cantidades de prueba antes de diagnosticar una causa.
- Para “¿prior o posterior SBC?”, vincular la elección al dominio de datos relevante y explicar qué región queda sin evaluar.
- Para “pasó SBC, ¿el modelo es correcto?”, responder que pasar es necesario pero no suficiente bajo computación finita y que SBC no comprueba adecuación del modelo a la realidad.

## Guardas

- No confundir SBC con chequeos predictivos posteriores ni con recuperación informal de parámetros.
- No confundir la propiedad SBC condicional con la igualdad entre prior y posterior promediado sobre datos.
- No afirmar que la log-verosimilitud conjunta detecta todo en la práctica; es un buen valor por defecto, no una panacea.
- No diagnosticar sesgo, sobre-dispersión o infra-dispersión desde una forma aislada sin revisar dependencia de muestras, cantidades de prueba y precisión Monte Carlo.
- No presentar el thinning histórico de Talts et al. como regla universal fuera del contexto descrito en la fuente.
- No atribuir APIs o detalles de PyMC, Stan, R o paquetes que no estén en las fuentes; verificar documentación externa antes de dar código dependiente de versión.
