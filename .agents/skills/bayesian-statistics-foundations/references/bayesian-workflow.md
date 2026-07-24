# Workflow bayesiano de principio a fin

## Contenido

1. [Principios de navegación](#principios-de-navegación)
2. [Mapa de fases](#mapa-de-fases)
3. [Fase 0: decisión, pregunta y diseño](#fase-0-decisión-pregunta-y-diseño)
4. [Fase 1: datos y medición](#fase-1-datos-y-medición)
5. [Fase 2: modelo generativo inicial](#fase-2-modelo-generativo-inicial)
6. [Fase 3: escalas, priors y simulación previa](#fase-3-escalas-priors-y-simulación-previa)
7. [Fase 4: implementación y datos construidos](#fase-4-implementación-y-datos-construidos)
8. [Fase 5: ajuste exploratorio](#fase-5-ajuste-exploratorio)
9. [Fase 6: validación computacional](#fase-6-validación-computacional)
10. [Fase 7: crítica predictiva](#fase-7-crítica-predictiva)
11. [Fase 8: generalización e influencia](#fase-8-generalización-e-influencia)
12. [Fase 9: sensibilidad, expansión y comparación](#fase-9-sensibilidad-expansión-y-comparación)
13. [Fase 10: decisión, comunicación y mantenimiento](#fase-10-decisión-comunicación-y-mantenimiento)
14. [Bucles de diagnóstico](#bucles-de-diagnóstico)
15. [Artefactos y trazabilidad](#artefactos-y-trazabilidad)
16. [Criterios de parada](#criterios-de-parada)
17. [Auditoría integral](#auditoría-integral)

## Principios de navegación

La identidad `p(θ|y) ∝ p(θ)p(y|θ)` define inferencia dentro de un modelo. Un workflow añade construcción, cómputo, comprobación, comparación, modificación, interpretación y uso. En un problema real se ajustan varios modelos, incluidos prototipos fallidos y andamios deliberadamente simples `[GELMAN20, §1.1–1.4, pp. 3–7]`.

Aplicar estos principios:

- **Iterar con trazabilidad:** cada revisión debe responder a evidencia y quedar registrada.
- **Separar fallos:** datos, modelo, código y algoritmo pueden producir síntomas parecidos.
- **Construir modularmente:** tratar likelihood, priors, efectos, medición y jerarquías como componentes reemplazables `[GELMAN20, §2.2, p. 9]`.
- **Ajustar fidelidad al momento:** prototipos rápidos al explorar; inferencia precisa para conclusiones delicadas `[GELMAN20, §3.2–3.4, pp. 13–16]`.
- **Comparar para comprender:** usar modelos vecinos como contrastes, no solo para declarar un ganador `[GELMAN20, §8.1, pp. 42–44]`.
- **Modelar como software:** versionar, probar, reproducir y mantener `[GELMAN20, §9, pp. 45–49]`.
- **Orientar chequeos al uso:** un defecto importa por su efecto sobre la pregunta o decisión.

## Mapa de fases

| Fase | Pregunta dominante | Artefacto mínimo | Puerta para avanzar |
|---:|---|---|---|
| 0 | ¿Qué decisión/pregunta se resolverá? | Estimando, población, acción, pérdida | Objetivo y éxito definidos |
| 1 | ¿Qué proceso produjo los datos? | Diccionario, diagrama, auditoría | Unidades y sesgos comprendidos |
| 2 | ¿Qué historia generativa representa el problema? | Factorización y modelo mínimo | Simulación posible y supuestos visibles |
| 3 | ¿Qué implica el prior conjunto? | Justificación + prior predictive | Predicciones previas plausibles |
| 4 | ¿Código y diseño pueden recuperar señales conocidas? | Tests + datasets simulados | Casos simples pasan y límites conocidos |
| 5 | ¿El modelo puede fallar rápido? | Ajuste corto + gráficos básicos | No hay fallo bruto sin explicación |
| 6 | ¿La inferencia numérica es confiable? | Diagnósticos + MCSE | Precisión suficiente para el uso |
| 7 | ¿El modelo reproduce aspectos relevantes? | PPC dirigido | Misfit tolerado o plan de mejora |
| 8 | ¿Generaliza al caso objetivo? | CV/holdout + influencia | Estimación estable y partición adecuada |
| 9 | ¿Conclusión robusta a elecciones plausibles? | Multiverso/sensibilidad + comparación | Decisión estable o incertidumbre expuesta |
| 10 | ¿Puede usarse y reproducirse responsablemente? | Informe, tarjeta del modelo, pipeline | Límites, versión y monitoreo definidos |

Las puertas no son pruebas binarias universales. Documentar por qué la evidencia es suficiente dado el costo de error.

## Fase 0: decisión, pregunta y diseño

### Definir

- Unidad de análisis y población objetivo.
- Horizonte temporal y dominio de despliegue.
- Outcome y su mecanismo de medición.
- Estimando o distribución predictiva.
- Acción posible, utilidad/pérdida y capacidad operativa.
- Diferencia mínima relevante y precisión necesaria.
- Riesgo de falso positivo, falso negativo, mala calibración o cola omitida.

Escribir una frase:

> Estimar/predecir **Q** para **P**, condicionado a **I**, con el fin de elegir **A** bajo la pérdida **L**.

### Diseñar antes de observar cuando sea posible

- Planificar muestra, asignación, frecuencia y calidad de medición.
- Simular diseños candidatos y calcular precisión/utilidad esperada.
- Definir partición de validación según generalización objetivo.
- Preespecificar chequeos críticos sin prohibir mejoras posteriores; registrar toda adaptación.

El PDF se concentra en análisis después de obtener datos y reconoce que diseño, medición y decisión pertenecen al workflow ampliado `[GELMAN20, §1.1, p. 3; §12.6, pp. 67–68]`.

## Fase 1: datos y medición

### Auditar datos

- Procedencia, consentimiento/licencia y versión.
- Claves, duplicados, unidades, límites y codificaciones.
- Missingness y razones de ausencia.
- Censura, truncamiento, redondeo, heaping y top-coding.
- Selección, no respuesta y cobertura de población.
- Dependencia por persona, grupo, lugar o tiempo.
- Transformaciones y algoritmos previos que generaron variables.
- Leakage entre entrenamiento y validación.

### Representar medición

Distinguir constructo latente, instrumento y dato registrado. Incorporar cuando afecte la pregunta:

- Error de medición.
- Sesgo sistemático.
- Sensibilidad/especificidad de un test.
- Fiabilidad entre observadores.
- Agregación o datos binned.
- Cambios de instrumento o definición.

Los datos suelen llegar preprocesados, por lo que cualquier generador es aproximado. `GELMAN20` resalta que sesgo puede importar más que error aleatorio y motivar expansión del modelo `[GELMAN20, §7.1, p. 38]`.

### Salida

- Diccionario de datos con unidades.
- Diagrama del proceso de selección y medición.
- Tabla de exclusiones/transformaciones.
- Gráficos exploratorios sin usar la exploración como inferencia final no registrada.

## Fase 2: modelo generativo inicial

### Empezar desde una plantilla defendible

Adaptar un modelo probado en un problema semejante puede reducir errores y carga cognitiva. Tratarlo como punto de partida y contraste, no autoridad `[GELMAN20, §2.1, pp. 8–9]`.

### Especificar módulos

1. Distribución de observación.
2. Predictor estructural o mecanístico.
3. Efectos de grupo/tiempo/espacio.
4. Medición, missingness y selección.
5. Priors e hiperpriors.
6. Cantidades derivadas y predictivas.

Para cada módulo registrar:

- Supuesto.
- Evidencia de dominio.
- Alternativa simple y alternativa más rica.
- Qué patrón de datos lo pondría en duda.
- Qué cantidad de interés afecta.

### Elegir complejidad inicial

Dos rutas son válidas:

- Empezar simple y añadir estructura.
- Empezar con un modelo rico y simplificar hasta comprenderlo.

Mantener un modelo base, uno mínimo de cordura y, si es viable, un modelo de referencia rico. Definir relaciones entre modelos como una topología de expansiones/restricciones, no solo una lista plana `[GELMAN20, §7.4, pp. 41–42]`.

### Comprobar generatividad

Intentar simular la conjunta. Si se condiciona en `x`, declarar que el modelo es parcialmente generativo y qué pregunta predictiva permite. Usar priors propios cuando se requiera prior predictive o comparación por evidencia.

## Fase 3: escalas, priors y simulación previa

### Escalar y parametrizar

- Centrar parámetros en valores interpretables.
- Usar unidades naturales o transformaciones log/logit.
- Escalar predictores para que priors de coeficientes expresen cambios reales.
- Preservar la ruta de retorno a unidades originales.
- Anticipar parametrización centrada/no centrada en jerarquías.

El escalado ayuda a interpretar priors y favorece partial pooling `[GELMAN20, §2.3, pp. 9–10]`.

### Elicitar priors

- Traducir conocimiento de expertos a observables.
- Distinguir soporte, regularización y conocimiento específico.
- Revisar el prior conjunto en alta dimensión.
- Justificar hiperpriors y parámetros de escala/cola con especial cuidado.
- Preparar alternativas más débiles y fuertes para sensibilidad.

### Ejecutar prior predictive checks

Simular condiciones centrales y extremas. Revisar:

- Rango y forma del outcome.
- Variación entre grupos y dentro de grupos.
- Frecuencia de eventos raros y extremos.
- Correlación/autocorrelación.
- Combinaciones que violan restricciones del dominio.
- Implicaciones del número de predictores.

Revisar el modelo o prior si asigna masa material a datos absurdos o excluye escenarios plausibles. No exigir coincidencia con el dataset observado.

### Salida

- Tabla parámetro → interpretación → prior → justificación.
- Gráficos prior predictivos.
- Decisiones de escala y transformaciones.
- Riesgos de sensibilidad previstos.

## Fase 4: implementación y datos construidos

### Probar de abajo hacia arriba

- Testear transformaciones, distribuciones personalizadas y solvers.
- Comparar log densidad con casos calculables.
- Verificar shapes, índices, jacobianos y unidades.
- Separar generador de datos de implementación inferencial cuando sea posible.
- Probar casos frontera e inputs inválidos.

`GELMAN20` conecta modelado incremental con desarrollo modular y pruebas de software `[GELMAN20, §9.2, pp. 46–47]`.

### Simular escenarios

Construir:

- Caso nulo o sin efecto.
- Efecto sustantivo conocido.
- Parámetros bien identificados.
- Región débilmente identificada.
- Datos pequeños y grandes.
- Outliers, colas o misspecification deliberada.
- Dependencia, desbalance o selección relevantes.

Para cada escenario revisar:

- Recuperación con incertidumbre.
- Cambio prior-posterior.
- Diagnósticos computacionales.
- Predictivas.
- Decisión final.

Una simulación de punto verdadero es un test útil, no calibración completa. SBC repetida valida el algoritmo bajo el prior; escenarios fuera del modelo estudian robustez `[GELMAN20, §4, pp. 16–22]`.

### Salida

- Suite reproducible de datasets simulados.
- Resultados esperados cualitativos, no valores sobreajustados al sampler.
- Lista de limitaciones de identificabilidad.

## Fase 5: ajuste exploratorio

### Fallar rápido

- Usar pocos draws, subconjuntos o una aproximación para detectar errores gruesos.
- Empezar con modelo mínimo y añadir un módulo por vez.
- Paralelamente simplificar el modelo objetivo hasta aislar el fallo.
- Graficar predicciones tempranas y cantidades intermedias.
- No buscar precisión final para un prototipo que probablemente cambiará.

El propósito es ahorrar tiempo en modelos destinados a abandonarse, no legitimar conclusiones con inferencia burda `[GELMAN20, §3.4, pp. 15–16; §5.2–5.4, pp. 22–24]`.

### Elegir aproximación conscientemente

Registrar si se aproximó:

- Posterior del mismo modelo.
- Modelo/likelihood.
- Datos o resolución.
- Los tres.

Definir qué rasgos deben preservarse para tomar la siguiente decisión. Al acercarse al informe final, comparar con un método más fiel.

## Fase 6: validación computacional

### Revisar por cadena y cantidad

- Errores y valores no finitos.
- Divergencias y profundidad para HMC.
- Energía/BFMI cuando aplique.
- Trazas y rank plots.
- `R-hat` rank-normalizado/split.
- Bulk y tail ESS.
- MCSE de cada cantidad decisiva.
- Estabilidad a iniciales y presupuesto.

### Diagnosticar, no tunear a ciegas

Si falla:

1. Revisar código y unidades.
2. Ajustar una versión más simple a datos simulados.
3. Inspeccionar qué predicciones produce la región problemática.
4. Examinar geometría e identificabilidad.
5. Reparametrizar o marginalizar.
6. Añadir prior/datos solo si la información es defendible.
7. Cambiar algoritmo si el objetivo lo requiere.

No avanzar a interpretación sustantiva con diagnósticos inexplicados. Si se acepta una aproximación, acotar su impacto sobre cantidades objetivo.

## Fase 7: crítica predictiva

### Diseñar chequeos severos

Para cada conclusión, preguntar qué patrón observado la volvería poco confiable. Comparar réplicas posteriores con:

- Distribuciones y colas.
- Variabilidad y ceros.
- Grupos no incluidos.
- Tiempo/espacio.
- Residuos por predictores.
- Agregados y extremos relevantes para la decisión.

El ejemplo del artículo muestra que un chequeo marginal puede parecer bueno y fallar al estratificar por una covariable omitida `[GELMAN20, fig. 14, p. 31]`.

### Clasificar el fallo

- Irrelevante para la pregunta actual, pero documentable.
- Tolerable con una limitación cuantificada.
- Requiere likelihood robusta, sobredispersión o error de medición.
- Requiere nueva estructura, predictor o jerarquía.
- Revela un error de datos/código.
- Indica que la pregunta no es identificable con estos datos.

No perseguir ajuste perfecto. La complejidad debe responder a consecuencias, no a cada fluctuación.

## Fase 8: generalización e influencia

### Elegir la unidad de validación

Simular el uso real:

- Observación nueva de unidad conocida.
- Persona/grupo nuevo.
- Tiempo futuro.
- Región nueva.
- Dataset o instrumento externo.

Aplicar todo preprocesamiento aprendido solo con el training de cada fold. Mantener grupos relacionados en el mismo lado para evitar leakage.

### Evaluar

- ELPD/log score para distribución completa.
- CRPS/WIS para probabilidades o cuantiles.
- Métrica de decisión cuando haya acción.
- Calibración y agudeza por subgrupo/horizonte.
- Contribuciones puntuales y observaciones influyentes.
- PSIS `k` o estabilidad entre folds.

LOO aproximado es eficiente, pero leave-one-group-out puede requerir refits porque la posterior cambia más `[GELMAN20, §6.2, pp. 30–34]`.

### Salida

- Justificación de partición.
- Métricas con incertidumbre.
- Lista de casos/grupos difíciles.
- Límite claro de transporte.

## Fase 9: sensibilidad, expansión y comparación

### Sensibilidad

Variar razonablemente:

- Priors e hiperpriors.
- Likelihood/colas/sobredispersión.
- Transformaciones y parametrización.
- Missingness, medición y selección.
- Inclusión de predictores/interacciones.
- Casos influyentes y reglas de limpieza.
- Unidad de validación.

Comparar cantidades objetivo y decisiones, no solo parámetros auxiliares. Reponderación puede aproximar pequeñas perturbaciones, pero refitar si los pesos degeneran `[GELMAN20, §6.3, pp. 34–36]`.

### Expandir o simplificar

Usar cuatro señales:

- Nuevos datos requieren heterogeneidad o medición adicional.
- PPC revela un patrón faltante.
- Cómputo revela una geometría o no-identificación.
- La pregunta cambia o requiere una cantidad nueva.

Actualizar también priors al crecer dimensión; no añadir parámetros manteniendo defaults marginales sin revisar el prior conjunto `[GELMAN20, §7.2–7.3, pp. 38–41]`.

### Comparar para aprender

- Graficar predicciones y efectos comunes entre modelos.
- Usar `ΔELPD` con incertidumbre, no rankings desnudos.
- Mantener modelos andamio fuera de promedios finales.
- Usar stacking si la meta es predicción combinada.
- Considerar proyección predictiva para un submodelo pequeño desde referencia rica.
- Reportar desacuerdo estructural como incertidumbre cuando no haya resolución defendible.

### Controlar sobreajuste del workflow

La adaptación al observar discrepancias usa información más de una vez. Mitigar con:

- Registro de todas las iteraciones.
- Datos externos o holdout intacto cuando sea viable.
- CV anidada si se selecciona mucho.
- Regularización y modelos amplios que incorporen alternativas.
- Sensibilidad/multiverso.
- Lenguaje condicional, no una falsa preespecificación.

`GELMAN20` reconoce el problema de post-selección y defiende construir modelos justificables en lugar de buscar el mejor ajuste entre muchas opciones `[GELMAN20, §12.3, pp. 64–66]`.

## Fase 10: decisión, comunicación y mantenimiento

### Propagar a la decisión

- Transformar cada draw a predicciones y utilidad.
- Calcular riesgo posterior por acción.
- Mostrar cómo cambia la acción bajo modelos/priors plausibles.
- Cuantificar valor de información si recolectar más datos es una opción.
- Separar riesgo estimado, costo operacional y restricciones éticas.

### Comunicar

Incluir:

- Pregunta, población y estimando.
- Historia generativa y supuestos decisivos.
- Priors en escala observable.
- Diagnósticos computacionales.
- PPC y validación fuera de muestra.
- Resumen posterior con unidades y MCSE.
- Sensibilidad e incertidumbre de modelo.
- Decisión/predicción y función de pérdida.
- Límites causales y de transporte.
- Historial de cambios relevantes.

Usar gráficos de datos, modelo y predictivas. Marginales aisladas no capturan dependencia ni múltiples niveles de variación `[GELMAN20, §6.4, p. 36]`.

### Mantener en producción

- Versionar datos, modelo, entorno y reporte.
- Monitorear drift de covariables, calibración, missingness y subgrupos.
- Definir umbrales de revisión, no de automatización irreversible.
- Reajustar/revalidar bajo un protocolo.
- Conservar rollback y auditoría de decisiones.

## Bucles de diagnóstico

### Si el ajuste es lento o no converge

`cómputo → predicciones por cadena → modelo simple → datos simulados → geometría/prior → nuevo ajuste`

No asumir que más cómputo basta. Empezar desde el modelo complejo y el simple, y localizar dónde aparece el fallo `[GELMAN20, §5.2, pp. 22–23]`.

### Si el PPC falla

`discrepancia → relevancia para Q → datos/código → módulo responsable → expansión → prior predictive → reajuste`

### Si la validación falla

`casos difíciles → leakage/partición → heterogeneidad → likelihood/modelo → nueva validación`

### Si modelos plausibles discrepan

`cantidad común → sensibilidad → datos que separan modelos → decisión robusta/averaging → comunicar incertidumbre`

### Si el modelo pasa todos los chequeos

Preguntar aún:

- ¿Los chequeos tenían potencia para los fallos importantes?
- ¿La cantidad de interés estaba identificada?
- ¿La partición imitaba el uso?
- ¿Faltó incertidumbre de medición/modelo?
- ¿La decisión es sensible en un borde no examinado?

## Artefactos y trazabilidad

Mantener un **ledger de modelos** con una fila por versión:

| Campo | Contenido |
|---|---|
| ID/version | Identificador inmutable y commit |
| Motivo | Evidencia que originó el cambio |
| Diferencia | Módulo, prior, datos o algoritmo alterado |
| Expectativa | Qué patrón debería mejorar y por qué |
| Diagnóstico | R-hat, ESS, MCSE, divergencias |
| PPC | Chequeos que pasan/fallan |
| Validación | Partición, score, incertidumbre, influencia |
| Conclusión | Cambios en `Q` y decisión |
| Estado | Andamio, candidato, descartado, reportado |

Guardar además:

- Script reproducible de punta a punta.
- Ambiente y versiones.
- Semillas o estrategia de replicación.
- Datos crudos inmutables y transformaciones versionadas.
- Figuras generadas por código.
- Registro de fallos, no solo modelo ganador.

Evitar nombres manuales tipo `final_final`; usar control de versiones y releases `[GELMAN20, §9.1–9.3, pp. 46–48]`.

## Criterios de parada

Detener la iteración cuando, dada la severidad del uso:

- La cantidad objetivo y decisión estén definidas y sean identificables en grado suficiente.
- El error Monte Carlo sea pequeño respecto de la precisión sustantiva.
- Los fallos predictivos relevantes se hayan corregido, acotado o aceptado explícitamente.
- La generalización se haya evaluado en el régimen objetivo.
- La decisión sea estable bajo perturbaciones plausibles o la inestabilidad esté comunicada.
- El beneficio esperado de otra iteración sea menor que su costo/tiempo.
- Exista un plan de nueva información o monitoreo para incertidumbre irresoluble.

“No encontramos más problemas con los chequeos disponibles” es defendible. “El modelo es correcto” no lo es. `GELMAN20` concluye que todos los workflows tienen huecos y que nueva información suele ser necesaria `[GELMAN20, §12.6, pp. 67–68]`.

## Auditoría integral

### Pregunta y datos

- [ ] Población, unidad, horizonte y acción están explícitos.
- [ ] Estimando/predictivo tiene fórmula y unidades.
- [ ] Selección, medición, missingness y dependencia están descritos.
- [ ] La partición de validación representa el uso.

### Modelo y prior

- [ ] La conjunta/factorización es explícita.
- [ ] Cada módulo tiene justificación y alternativa.
- [ ] Priors son propios cuando el procedimiento lo requiere.
- [ ] Prior predictivas cubren casos centrales/extremos plausibles.
- [ ] Escalas y transformaciones son reversibles e interpretables.

### Implementación y cómputo

- [ ] Generador y funciones críticas tienen tests.
- [ ] Datos simulados recuperan cantidades en escenarios relevantes.
- [ ] Diagnósticos por cadena y algoritmo fueron revisados.
- [ ] ESS/MCSE satisfacen la precisión de la decisión.
- [ ] Aproximaciones están identificadas y comparadas.

### Adecuación y generalización

- [ ] PPC prueba fallos vinculados a la conclusión.
- [ ] Calibración y agudeza se evalúan fuera de muestra.
- [ ] Scores tienen unidad, dirección y convención declaradas.
- [ ] Observaciones/grupos influyentes se inspeccionan.
- [ ] Sensibilidad cubre priors, likelihood y decisiones de datos.

### Comunicación y gobernanza

- [ ] Incertidumbre posterior, predictiva, Monte Carlo y de modelo están separadas.
- [ ] Conclusiones son condicionales y vuelven a unidades reales.
- [ ] Decisión declara pérdida/utilidad.
- [ ] Iteraciones y descartes están versionados.
- [ ] Límites causales, éticos y de transporte están explícitos.
- [ ] Reproducción, rollback y monitoreo están definidos.
