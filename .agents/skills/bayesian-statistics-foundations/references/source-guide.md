# Guía de fuentes y trazabilidad

## Contenido

1. [Fuente local principal](#fuente-local-principal)
2. [Alcance de la síntesis](#alcance-de-la-síntesis)
3. [Mapa del documento](#mapa-del-documento)
4. [Reglas de atribución](#reglas-de-atribución)
5. [Límites temporales y conceptuales](#límites-temporales-y-conceptuales)

## Fuente local principal

Usar la clave `GELMAN20` para:

> Andrew Gelman, Aki Vehtari, Daniel Simpson, Charles C. Margossian, Bob Carpenter, Yuling Yao, Lauren Kennedy, Jonah Gabry, Paul-Christian Bürkner y Martin Modrák. *Bayesian workflow*. Borrador del 2 de noviembre de 2020, 77 páginas en el archivo local.

Ubicación en el repositorio: `.local-learning/Bayesian_Workflow.pdf`.

El documento distingue inferencia bayesiana —la formulación y el cálculo de `p(θ | y)`— de un workflow que incorpora construcción, cómputo, comprobación, modificación, comparación, comprensión y uso de modelos. Esta distinción organiza la skill.

## Alcance de la síntesis

La skill combina dos capas:

- **Síntesis atribuible a `GELMAN20`:** workflow iterativo, modelos generativos, chequeos predictivos, datos simulados, SBC, diagnóstico computacional, modificación y comparación de modelos, prácticas de software y los casos de golf y movimiento planetario.
- **Base didáctica añadida:** axiomas y reglas de probabilidad, conjugación, resúmenes posteriores, teoría de decisión, fórmulas de métricas y un catálogo más amplio de scores predictivos y diagnósticos.

No atribuir automáticamente la segunda capa al artículo. Cuando una respuesta mezcle ambas, citar solo las afirmaciones que efectivamente provengan del PDF y presentar las demás como definiciones, derivaciones o práctica estadística general.

## Mapa del documento

Las páginas siguientes son las impresas en el artículo, que coinciden con las páginas de contenido del PDF salvo la convención propia del visor.

| Tema | Sección | Páginas | Uso en la skill |
|---|---:|---:|---|
| Inferencia frente a workflow | §1.1–1.5 | 3–8 | Definir el análisis como proceso no lineal |
| Modelo inicial y módulos | §2.1–2.2 | 8–9 | Empezar con plantillas y componentes reemplazables |
| Escalas y transformaciones | §2.3 | 9–10 | Hacer parámetros y priors interpretables |
| Prior predictive checks | §2.4 | 10–11 | Evaluar implicaciones conjuntas del prior y likelihood |
| Modelos generativos o parciales | §2.5 | 11–12 | Determinar qué puede simularse y qué se condiciona |
| Ajuste, warmup y longitud | §3.1–3.2 | 13–14 | Distinguir exploración temprana y precisión final |
| Algoritmos/modelos aproximados | §3.3 | 14–15 | Alinear fidelidad computacional con la fase |
| Fallar rápido | §3.4 | 15–16 | Detectar pronto modelos inadecuados |
| Datos falsos y recuperación | §4.1 | 16–18 | Probar diseño, identificabilidad e implementación |
| Simulation-Based Calibration | §4.2 | 18–20 | Validar coherencia del algoritmo sobre simulaciones |
| Experimentos construidos | §4.3 | 20–22 | Estudiar robustez y sesgo bajo escenarios |
| Problemas computacionales | §5.1–5.10 | 22–30 | Relacionar geometría, información y modelado |
| Posterior predictive checks | §6.1 | 30 | Criticar aspectos de los datos relevantes |
| CV, calibración e influencia | §6.2 | 30–34 | Generalización, LOO-PIT y puntos influyentes |
| Sensibilidad al prior | §6.3 | 34–36 | Comparar prior/posterior y perturbaciones |
| Resumen y propagación | §6.4 | 36 | Comunicar múltiples niveles de incertidumbre |
| Modificación de modelos | §7.1–7.4 | 36–42 | Expandir datos, likelihood, priors y topología |
| Múltiples modelos | §8.1–8.3 | 42–45 | Comprender, comparar, apilar o proyectar modelos |
| Modelado como software | §9.1–9.4 | 45–49 | Versionar, probar, reproducir y mantener |
| Caso de golf | §10 | 49–56 | Mostrar expansión guiada por nuevos datos y misfit |
| Caso planetario | §11 | 56–63 | Mostrar multimodalidad, simplificación e inicialización |
| Perspectivas y límites | §12.1–12.6 | 63–68 | Justificar iteración, advertir sobre selección y extrapolación |

## Reglas de atribución

Usar el formato corto:

- `[GELMAN20, §2.4, pp. 10–11]`
- `[GELMAN20, §5.1, p. 22]`
- `[GELMAN20, fig. 14, p. 31]`

Preferir sección y página. Añadir figura solo si la interpretación depende de ella. No citar una página de bibliografía del artículo como si fuera la fuente primaria de un método allí mencionado.

Mantener estas distinciones:

- “El artículo recomienda o ilustra...” para afirmaciones textuales claras.
- “La skill operacionaliza esta idea como...” para procedimientos añadidos.
- “Bajo los supuestos declarados se deriva...” para identidades matemáticas.
- “Una práctica contemporánea es...” para recomendaciones externas al documento; verificar una fuente actual si la precisión temporal o de software importa.

## Límites temporales y conceptuales

- El PDF es un borrador de 2020. Sus valores de referencia, defaults de software y estado de algoritmos pueden haber cambiado.
- El artículo se centra especialmente en HMC y Stan, aunque sus principios son más amplios. No trasladar diagnósticos específicos de HMC a todos los algoritmos.
- El artículo no pretende cubrir en detalle diseño, medición, recolección, decisión o comunicación; la skill añade fundamentos en esas áreas para cerrar el ciclo.
- El workflow no es una lista lineal ni una garantía. Cualquier análisis puede recorrer solo algunas ramas y volver a pasos anteriores.
- Los ejemplos de golf y movimiento planetario ilustran razonamiento contextual. No generalizar sus soluciones concretas como recetas universales.
- Un chequeo exitoso solo indica que no se detectó un fallo con las cantidades, datos y presupuesto usados. No demostrar verdad del modelo ni corrección global.
