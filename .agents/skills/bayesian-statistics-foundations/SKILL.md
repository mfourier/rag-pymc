---
name: bayesian-statistics-foundations
description: "Explicar, aplicar, revisar y comunicar conceptos fundamentales de estadística bayesiana y sus métricas. Usar ante consultas sobre probabilidad condicional, teorema de Bayes, prior, verosimilitud, posterior, distribución predictiva, modelos jerárquicos, intervalos creíbles, ROPE, decisiones bajo incertidumbre, diagnósticos MCMC, R-hat, ESS, MCSE, divergencias, chequeos predictivos, calibración, LOO/PSIS, WAIC, ELPD, comparación o promediado de modelos, sensibilidad a priors y diseño de un Bayesian workflow completo."
---

# Fundamentos de Estadística Bayesiana

## Objetivo

Razonar desde la pregunta sustantiva hasta una conclusión calibrada, separando el modelo probabilístico, la información aportada por los datos, el error de cómputo, la adecuación predictiva y la decisión. Tratar el análisis bayesiano como un proceso iterativo de construcción, ajuste, crítica y mejora, no como el cálculo aislado de una posterior.

## Cargar las referencias necesarias

Leer siempre [references/source-guide.md](references/source-guide.md) para conocer la procedencia, alcance y forma de citar la fuente local `Bayesian_Workflow.pdf`.

- Leer [references/foundations.md](references/foundations.md) para explicar probabilidad condicional, Bayes, modelo generativo, prior, verosimilitud, posterior, predicción, jerarquías, identificabilidad o causalidad.
- Leer [references/posterior-metrics-and-decisions.md](references/posterior-metrics-and-decisions.md) para resumir posteriores, elegir intervalos y probabilidades, valorar relevancia práctica o formalizar decisiones.
- Leer [references/computation-diagnostics.md](references/computation-diagnostics.md) para revisar MCMC/HMC, convergencia, precisión Monte Carlo, geometría difícil o inferencia aproximada.
- Leer [references/predictive-evaluation-and-comparison.md](references/predictive-evaluation-and-comparison.md) para chequeos predictivos, scores, calibración, LOO/PSIS, WAIC, validación cruzada, Bayes factors, stacking o selección de variables.
- Leer [references/bayesian-workflow.md](references/bayesian-workflow.md) para diseñar, auditar o documentar un análisis de principio a fin.
- Leer [references/worked-examples.md](references/worked-examples.md) para enseñar con ejemplos conjugados, jerárquicos o de diagnóstico.
- Leer todas las referencias al hacer una revisión integral o una recomendación de modelado de alto impacto.

Si la consulta se centra en Simulation-Based Calibration, usar además la skill `simulation-based-calibration`; esta skill cubre su lugar conceptual dentro del workflow, mientras aquella contiene el procedimiento especializado.

## Establecer el contrato del análisis

Antes de elegir una métrica:

1. **Definir la pregunta y la acción.** Precisar población, unidad, horizonte, resultado, intervención o decisión, y costo de equivocarse.
2. **Definir la cantidad objetivo.** Escribir el estimando o cantidad predictiva con símbolos y unidades. Distinguir parámetro, función de parámetros, dato futuro, contraste causal y utilidad.
3. **Identificar el nivel de incertidumbre.** Separar variación aleatoria, incertidumbre posterior, error Monte Carlo, incertidumbre de modelo, sesgo de medición y extrapolación.
4. **Aclarar el condicionamiento.** Indicar qué datos y supuestos condicionan cada probabilidad. Evitar probabilidades sin sujeto, horizonte o conjunto de información.
5. **Elegir la métrica por su propósito.** Usar una métrica solo si su cantidad objetivo, escala y dirección responden a la pregunta. No elegirla por disponibilidad del software.

## Seguir el flujo de razonamiento

1. Formular una historia generativa y factorizar la distribución conjunta.
2. Escalar y parametrizar cantidades para que priors y efectos sean interpretables.
3. Justificar el prior en la escala observacional y examinar el prior predictivo.
4. Simular datos construidos para probar el generador, la identificabilidad práctica y la implementación.
5. Ajustar primero una versión mínima; aumentar fidelidad y presupuesto computacional conforme madure el modelo.
6. Revisar diagnósticos del algoritmo antes de interpretar draws como posterior.
7. Resumir cantidades de interés preservando asimetría, multimodalidad, dependencia y unidades.
8. Comprobar el ajuste con simulación posterior predictiva y pruebas dirigidas a fallos relevantes.
9. Evaluar generalización con una partición coherente con la unidad predictiva; comparar modelos con incertidumbre.
10. Examinar sensibilidad a priors, datos influyentes, likelihood, parametrización y decisiones de preprocesamiento.
11. Propagar draws hasta predicciones, utilidades o decisiones; no sustituir esta propagación por plug-in de medias.
12. Documentar iteraciones, fallos, decisiones y límites; mantener código y resultados reproducibles.

Tratar el orden como una guía con bucles. Volver al modelo cuando el cómputo, los chequeos o la interpretación revelen un problema.

## Presentar cada métrica con una ficha mínima

Al explicar o recomendar una métrica, incluir:

- **Definición:** fórmula o construcción.
- **Objeto:** qué variable, distribución o predicción resume.
- **Interpretación:** frase en unidades del problema.
- **Dirección:** qué valores son preferibles, si aplica.
- **Incertidumbre:** error Monte Carlo, error estándar o variación entre particiones.
- **Supuestos:** condiciones que hacen válida la lectura.
- **Fallo típico:** qué no puede detectar o cuándo engaña.
- **Acción:** qué revisar o cambiar ante un valor problemático.

No convertir umbrales orientativos en pruebas binarias. Priorizar patrones conjuntos y consecuencias para las cantidades de interés.

## Mantener un contrato de evidencia

Distinguir explícitamente cuando sea útil:

- **Identidad matemática:** resultado derivado de definiciones y supuestos declarados.
- **Resultado del modelo:** afirmación condicional al modelo, prior, datos y cómputo.
- **Diagnóstico:** evidencia sobre el algoritmo o una discrepancia concreta, no garantía global.
- **Interpretación:** traducción sustantiva que puede requerir conocimiento del dominio.
- **Recomendación:** elección dependiente de objetivos, costos y tolerancia al error.

Citar el PDF local como `[GELMAN20, §sección, p. página]` al usar una idea específica del workflow. No atribuir al PDF fórmulas, umbrales o métricas añadidas por esta skill si no aparecen allí. Explicitar cuando una conclusión sea una extensión pedagógica.

## Responder según la tarea

- Para **“explica este concepto”**, dar intuición, notación, ejemplo mínimo, interpretación y confusión frecuente.
- Para **“interpreta este resumen”**, comprobar primero la validez computacional, traducir a unidades originales y separar magnitud, incertidumbre y relevancia práctica.
- Para **“¿qué métrica uso?”**, empezar por la cantidad objetivo y comparar solo alternativas que midan el mismo aspecto.
- Para **“revisa este análisis”**, organizar hallazgos por modelo/datos, cómputo, ajuste predictivo, sensibilidad y comunicación.
- Para **“compara modelos”**, definir la unidad de validación, reportar diferencias con incertidumbre y revisar observaciones influyentes; evitar declarar un ganador por el ranking puntual.
- Para **“diseña un workflow”**, entregar fases, artefactos, diagnósticos, criterios de revisión y bucles de decisión.
- Para código dependiente de PyMC, ArviZ, Stan u otra biblioteca, verificar la documentación de la versión instalada antes de afirmar nombres de API o valores por defecto.

## Guardas

- No interpretar una probabilidad posterior como frecuencia de repetición ni un intervalo creíble como intervalo de confianza.
- No llamar “no informativo” a un prior sin discutir parametrización y escala; la uniformidad no es invariante.
- No usar una posterior bien muestreada como evidencia de que el modelo describe bien los datos.
- No usar un buen chequeo predictivo como prueba de verdad, causalidad o validez fuera del dominio observado.
- No inferir convergencia solo porque `R-hat` esté cerca de uno; revisar ESS, MCSE, cadenas y diagnósticos específicos del algoritmo.
- No resumir una posterior multimodal solo con media y desviación estándar.
- No equiparar densidad posterior, masa de probabilidad, odds, Bayes factor y probabilidad de modelo.
- No tratar HDI, ROPE, probabilidad de signo o Bayes factor como decisiones automáticas independientes de pérdidas y contexto.
- No comparar ELPD, WAIC, RMSE u otra métrica calculada sobre observaciones, particiones o escalas distintas.
- No seleccionar una estrategia de validación ignorando agrupación, tiempo, espacio, dependencia o el objetivo de generalización.
- No ocultar iteración ni selección posterior al observar los datos; incluir sensibilidad o validación externa cuando la adaptabilidad pueda sobreajustar.
