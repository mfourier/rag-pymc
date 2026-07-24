# Evaluación predictiva y comparación de modelos

## Contenido

1. [Separar preguntas de evaluación](#separar-preguntas-de-evaluación)
2. [Chequeo prior predictivo](#chequeo-prior-predictivo)
3. [Chequeo posterior predictivo](#chequeo-posterior-predictivo)
4. [Calibración y agudeza](#calibración-y-agudeza)
5. [Scores predictivos](#scores-predictivos)
6. [Validación cruzada y ELPD](#validación-cruzada-y-elpd)
7. [PSIS-LOO y Pareto k](#psis-loo-y-pareto-k)
8. [WAIC y otros criterios](#waic-y-otros-criterios)
9. [Comparación, averaging y selección](#comparación-averaging-y-selección)
10. [Métricas auxiliares](#métricas-auxiliares)
11. [Selección rápida](#selección-rápida)
12. [Contrato de reporte](#contrato-de-reporte)

## Separar preguntas de evaluación

No existe una métrica única de “calidad del modelo”. Separar:

1. **Plausibilidad previa:** ¿el modelo genera datos razonables antes de observarlos?
2. **Adecuación descriptiva:** ¿la posterior predictiva reproduce aspectos relevantes de los datos usados?
3. **Generalización:** ¿predice unidades no usadas en el ajuste bajo el escenario objetivo?
4. **Calibración:** ¿las probabilidades o distribuciones concuerdan con frecuencias/rangos bajo un régimen?
5. **Agudeza:** entre predicciones calibradas, ¿qué tan concentradas son?
6. **Utilidad:** ¿qué consecuencias tienen las predicciones para una decisión?
7. **Explicación/causalidad:** ¿los supuestos identifican el mecanismo o contraste deseado?
8. **Cómputo:** ¿los draws representan la distribución que se pretende evaluar?

Un modelo puede ajustar bien y generalizar mal, predecir bien y tener parámetros no identificados, estar calibrado y ser poco informativo, o tener ELPD alto y ser causalmente inválido.

## Chequeo prior predictivo

Simular:

`θ_s ~ p(θ)`, luego `ỹ_s ~ p(ỹ | θ_s)`.

Comparar `ỹ_s` con conocimiento del dominio, límites físicos, escalas, tasas, conteos, patrones y agregados. Preguntar:

- ¿Aparecen datasets imposibles o absurdos con frecuencia material?
- ¿El prior excluye escenarios plausibles?
- ¿La combinación de muchos priors marginales induce predicciones extremas?
- ¿El modelo genera la estructura de dependencia, no solo marginales?
- ¿El mecanismo de muestreo simulado coincide con el diseño?

No calibrar el prior para que replique estrechamente los datos observados sin documentar que se volvió dependiente de datos. Usar conocimiento previo o una fase formal de entrenamiento si corresponde.

`GELMAN20` destaca que la simulación prior predictiva revela implicaciones no obvias del prior conjunto y facilita elicitar conocimiento en cantidades observables `[GELMAN20, §2.4, pp. 10–11]`.

## Chequeo posterior predictivo

Simular:

`θ_s ~ p(θ|y)`, luego `ỹ_s ~ p(ỹ|θ_s)`.

Comparar `y` y `ỹ` con una discrepancia `T(y)` o una visualización. Elegir `T` orientada al fallo que afectaría la conclusión:

- Distribución completa, colas, ceros, máximos o outliers.
- Media, varianza, sobredispersión o asimetría.
- Autocorrelación, estacionalidad o rachas.
- Correlaciones, covarianzas o estructura espacial.
- Proporciones y conteos por subgrupos, especialmente no usados en el modelo.
- Residuos respecto de predictores o tiempo.
- Estadísticos vinculados a la decisión, no solo fáciles de graficar.

Tipos de comparación:

- Superposición de datos y múltiples réplicas.
- Distribución de `T(ỹ)` con `T(y)` marcado.
- Residuos o errores de cuantiles por covariables.
- Gráficos por grupo o nivel jerárquico.
- Chequeos condicionados que preservan partes del diseño.

Interpretación correcta:

- Una discrepancia fuerte localiza un aspecto no capturado; no invalida automáticamente todo uso.
- Una coincidencia indica que ese chequeo no encontró un fallo; no valida globalmente el modelo.
- Como los datos informan la posterior y luego se comparan con ella, el chequeo puede ser optimista, especialmente en modelos flexibles.

Un posterior predictive p-value típico es

`p_B = P[T(ỹ,θ) ≥ T(y,θ) | y]`.

No es un p-value frecuentista uniforme bajo la nula; suele ser conservador por el uso doble de datos. Usarlo como resumen descriptivo del chequeo, no como regla universal de rechazo.

`GELMAN20` recomienda pruebas “severas”: discrepancias propensas a fallar si el modelo indujera respuestas engañosas para la pregunta central `[GELMAN20, §6.1, p. 30]`.

## Calibración y agudeza

### PIT y LOO-PIT

Para predicción continua con CDF `F_i`, el probability integral transform es `u_i = F_i(y_i)`. Bajo predicciones condicionales calibradas y condiciones apropiadas, los `u_i` son uniformes.

Usar LOO-PIT con `F_{-i}` estimada sin `y_i` para reducir el optimismo del ajuste en muestra. Patrones orientativos:

- U pronunciada: predicciones demasiado estrechas o colas insuficientes.
- Montículo central: predicciones demasiado dispersas.
- Sesgo hacia 0 o 1: localización sistemática incorrecta.

No diagnosticar solo por forma cuando hay dependencia, discreción o pocos datos. Para outcomes discretos usar PIT aleatorizado o una versión adecuada; el PIT ordinario no será uniforme continuo.

`GELMAN20` presenta LOO-PIT y muestra cómo una concentración central señala predictivas condicionales demasiado anchas `[GELMAN20, §6.2, pp. 30–33]`.

### Cobertura

Para intervalos predictivos nominales de masa `1-α`, calcular la fracción de observaciones futuras contenidas. Reportar cobertura por horizonte y subgrupo.

- Cobertura nominal sin agudeza puede lograrse con intervalos inútilmente anchos.
- Cobertura marginal puede ocultar mala calibración condicional.
- Evaluarla en datos realmente fuera de muestra o con CV coherente.

### Curvas de calibración para binarios

Agrupar o suavizar `y` frente a probabilidades predichas `p`. Revisar intercepto y pendiente de calibración con incertidumbre.

- Intercepto distinto de cero: sesgo global en escala logit.
- Pendiente menor que uno: probabilidades demasiado extremas.
- Pendiente mayor que uno: probabilidades poco extremas.

El binning es inestable y puede ocultar estructura; mostrar incertidumbre, tamaños de grupo y calibración por subpoblaciones.

## Scores predictivos

Un scoring rule propio incentiva reportar la distribución predictiva verdadera bajo el régimen evaluado. Calcular scores por unidad y conservar contribuciones puntuales para detectar heterogeneidad.

### Log score y log predictive density

Para observación `y_i` y densidad predictiva `p_i`:

- Log predictive density: `log p_i(y_i)`; mayor es mejor.
- Negative log score/log loss: `-log p_i(y_i)`; menor es mejor.

Ventajas:

- Score estrictamente propio bajo condiciones regulares.
- Usa la distribución completa y penaliza fuertemente asignar poca densidad al observado.
- Es aditivo, lo que permite ELPD.

Riesgos:

- Muy sensible a colas y densidades casi nulas.
- Depende de la unidad de factorización y de la densidad respecto de una medida.
- Sumas no son comparables si cambian observaciones, escalas o transformaciones sin jacobiano.

### Brier score

Para outcome binario `y_i ∈ {0,1}` y probabilidad `p_i`:

`Brier = N⁻¹Σ_i (p_i-y_i)²`; menor es mejor.

Es propio y combina calibración con resolución. Puede descomponerse bajo esquemas específicos, pero no inferir causalidad ni escoger umbral de decisión.

Para múltiples clases usar la suma cuadrática sobre clases y declarar normalización.

### CRPS

Para CDF predictiva `F` y observación `y`:

`CRPS(F,y) = ∫_{-∞}^{∞}[F(z)-I(y≤z)]² dz`; menor es mejor.

- Evalúa la distribución completa en unidades del resultado.
- Generaliza el error absoluto y suele ser menos dominado por outliers que log score.
- Puede estimarse con draws predictivos.

### Interval score y WIS

Para intervalo central `[l,u]` de nivel `1-α`:

`IS_α = (u-l) + (2/α)(l-y)I(y<l) + (2/α)(y-u)I(y>u)`.

Penaliza ancho y falta de cobertura. El weighted interval score combina múltiples niveles y una mediana; aproxima CRPS bajo elecciones apropiadas. Declarar niveles y pesos.

### RMSE y MAE

Para predicción puntual `ŷ_i`:

- `RMSE = √[N⁻¹Σ_i(y_i-ŷ_i)²]`.
- `MAE = N⁻¹Σ_i|y_i-ŷ_i|`.

RMSE enfatiza errores grandes; MAE es más robusto. Ambos ignoran la distribución predictiva y la calibración si se usan solos. La predicción óptima depende de la pérdida: media para error cuadrático, mediana para absoluto.

No calcular RMSE de medias in-sample y llamarlo rendimiento predictivo fuera de muestra.

### Accuracy, sensibilidad, especificidad y AUC

Estas métricas evalúan clasificaciones o rankings, no probabilidades completas:

- Accuracy depende de umbral y prevalencia.
- Sensibilidad/recall y especificidad separan clases, pero requieren una regla de decisión.
- Precision/PPV cambia con prevalencia.
- AUROC mide ranking sobre umbrales y puede ocultar mala calibración.
- AUPRC puede ser informativa con clases raras, pero depende de prevalencia.

Elegir umbral mediante costos/utilidad y reportar una métrica probabilística como log score o Brier además de la métrica de decisión.

## Validación cruzada y ELPD

La cantidad ideal de generalización es:

`elpd = E_{ỹ~p_t}[log p(ỹ | y)]`,

donde `p_t` es la distribución de casos futuros objetivo. No puede observarse directamente; se estima con validación.

Leave-one-out:

`elpd_LOO = Σ_i log p(y_i | y_{-i})`.

La unidad `i` debe representar lo que se dejará fuera al usar el modelo. Para datos jerárquicos, temporales, espaciales o repetidos:

- Leave-one-observation-out predice otra medición condicionando en el grupo conocido.
- Leave-one-group-out predice un grupo nuevo.
- Forward/rolling validation predice el futuro desde el pasado.
- Bloques espaciales evalúan transporte a zonas no observadas.
- K-fold estratificado o agrupado debe preservar la estructura relevante.

Elegir la partición antes de comparar modelos y explicar qué generalización aproxima. LOO puede ser inapropiado cuando unidades están fuertemente dependientes o se filtra información de preprocesamiento.

Para modelos `A` y `B`, definir contribuciones `d_i = elpd_{i,A}-elpd_{i,B}`:

`Δelpd = Σ_i d_i`.

Bajo unidades aproximadamente independientes, un estimador convencional es:

`SE(Δelpd) ≈ √[N Var_i(d_i)]`.

Inspeccionar la distribución de `d_i`, no solo suma y SE. Con pocos datos, colas, dependencia o modelos muy similares, la aproximación normal del SE puede ser pobre. Evitar declarar ganador cuando `Δelpd` es pequeño respecto de su incertidumbre o proviene de pocos casos influyentes.

## PSIS-LOO y Pareto k

PSIS aproxima LOO reponderando draws de la posterior completa y suavizando la cola de pesos de importancia. Para cada observación produce:

- Contribución `elpd_loo,i`.
- Diagnóstico de forma de cola `k_i`.
- A menudo ESS o advertencias adicionales.

Interpretar `k` como diagnóstico de fiabilidad de la aproximación e influencia, no como score del modelo. Referencias heurísticas comunes:

- `k < 0.5`: comportamiento favorable.
- `0.5 ≤ k < 0.7`: generalmente utilizable, con eficiencia decreciente.
- `0.7 ≤ k < 1`: estimación potencialmente inestable; considerar LOO exacto, moment matching o K-fold.
- `k ≥ 1`: importance sampling ordinario no tiene media finita asintótica; no confiar en la aproximación.

Los límites y correcciones dependen del número de draws y de la implementación; seguir los avisos de la versión instalada. Un `k` alto puede identificar una observación influyente, un outlier, un grupo mal modelado o simplemente una posterior leave-one-out muy distinta.

Ante `k` alto:

1. Inspeccionar el dato y su procesamiento sin borrarlo automáticamente.
2. Examinar ajuste predictivo y contribución de ELPD.
3. Reajustar dejando el caso fuera o usar una corrección soportada.
4. Cambiar a K-fold si muchos casos son problemáticos.
5. Mejorar un likelihood frágil o modelar heterogeneidad si está justificado.

`GELMAN20` usa contribuciones puntuales de LOO para localizar observaciones difíciles y recalca que validación jerárquica debe coincidir con el objetivo `[GELMAN20, §6.2, pp. 30–34]`.

## WAIC y otros criterios

WAIC estima rendimiento predictivo punto a punto usando:

`lppd = Σ_i log E_{post}[p(y_i|θ)]`,

`p_WAIC = Σ_i Var_{post}(log p(y_i|θ))`,

`elpd_WAIC = lppd - p_WAIC`.

- Es asintóticamente relacionado con Bayesian LOO bajo condiciones regulares/singulares apropiadas.
- Puede ser inestable cuando la varianza de log-likelihood puntual es alta.
- PSIS-LOO ofrece diagnósticos puntuales más útiles y suele preferirse cuando está disponible.

Si el software reporta `WAIC = -2 elpd_WAIC`, menor es mejor; si reporta `elpd_WAIC`, mayor es mejor. Verificar convención antes de interpretar diferencias.

### AIC, BIC y DIC

- AIC aproxima riesgo predictivo desde máxima verosimilitud y un conteo paramétrico regular; no resume automáticamente una posterior.
- BIC aproxima una evidencia marginal bajo condiciones y priors implícitos; su objetivo no es ELPD.
- DIC usa un punto posterior y un número efectivo de parámetros que puede comportarse mal en jerarquías, asimetría o multimodalidad.

No mezclar rankings de criterios con objetivos distintos. Para workflow predictivo bayesiano, preferir predicción fuera de muestra y diagnósticos explícitos.

## Comparación, averaging y selección

### Comparación predictiva

Comparar solo modelos:

- Ajustados a observaciones compatibles.
- Evaluados con la misma unidad, partición y score.
- Con log-likelihood que representa el mismo outcome conjunto.
- Cuyos diagnósticos computacionales son aceptables.

Reportar `Δelpd`, incertidumbre, contribuciones puntuales y diferencias sustantivas. Una mejora numérica puede no importar para la decisión.

### Stacking

Elegir pesos `w_m ≥ 0`, `Σ_m w_m=1`, que maximizan el log score leave-one-out de la mezcla predictiva:

`Σ_i log[Σ_m w_m p_m(y_i | y_{-i})]`.

Ventajas:

- Optimiza predicción combinada fuera de muestra.
- Puede aprovechar modelos complementarios.
- Es menos sensible que el model averaging por evidencia marginal a priors difusos sobre parámetros.

Límites:

- Pesos no son probabilidades posteriores de que un modelo sea verdadero.
- Dependen del conjunto candidato, unidad de CV y región de datos.
- No rescatan modelos con fallos de cómputo o errores de código.

`GELMAN20` recomienda conservar incertidumbre de comparación y presenta stacking como alternativa predictiva a elegir mecánicamente el mejor modelo `[GELMAN20, §8.2, pp. 44–45]`.

### Bayesian model averaging y Bayes factors

Con modelos discretos:

`p(M_m|y) ∝ p(y|M_m)p(M_m)`,

y la predictiva promediada es `Σ_m p(ỹ|y,M_m)p(M_m|y)`.

La evidencia `p(y|M_m)=∫p(y|θ_m,M_m)p(θ_m|M_m)dθ_m` integra sobre todo el prior. Es muy sensible al prior y a su constante normalizadora; priors impropios hacen Bayes factors indefinidos. Usar si las hipótesis discretas, priors de modelo y objetivo evidencial son defendibles, no como sustituto automático de validación predictiva.

### Selección de variables y proyección predictiva

Elegir el mejor de muchos submodelos por CV puede sobreajustar la propia estimación de CV. Una estrategia es ajustar un modelo de referencia regularizado y proyectar sus predicciones a submodelos más pequeños, seleccionando el tamaño con incertidumbre. `GELMAN20` describe esta motivación y la proyección predictiva `[GELMAN20, §8.3, p. 45]`.

La selección altera la incertidumbre. No reportar la posterior del modelo seleccionado como si este hubiera sido fijado de antemano sin sensibilidad o ajuste.

## Métricas auxiliares

### Bayesian R²

Para regresión con draws de media ajustada `μ_s` y residual `ε_s`, una forma es:

`R²_s = Var_i(μ_{i,s}) / [Var_i(μ_{i,s}) + Var_i(ε_{i,s})]`.

Resumir la distribución de `R²_s`.

- Describe variación explicada dentro de datos/modelo.
- No es un score propio ni garantía de generalización.
- La definición residual cambia por familia; documentarla.
- Un `R²` alto puede coexistir con sesgo, mala calibración o leakage.

### Número efectivo de parámetros

`p_LOO` o `p_WAIC` describen flexibilidad predictiva efectiva, no un conteo literal. Valores extraños pueden señalar observaciones influyentes, priors fuertes o inestabilidad. No usarlos solos para decidir complejidad.

### Posterior predictive loss y residuales

Definir residuales en relación con el outcome:

- Residuos crudos `y-E[ỹ|y]`.
- Residuos estandarizados o de Pearson.
- Residuos de cuantiles/PIT.
- Residuos leave-one-out para reducir reutilización de datos.

En modelos discretos o heterocedásticos, un residual crudo puede tener patrón aun bajo modelo correcto; preferir chequeos simulados o cuantiles aleatorizados.

## Selección rápida

| Objetivo | Métrica/chequeo | Dirección | Advertencia principal |
|---|---|---|---|
| Plausibilidad del prior | Prior predictive checks | Sin ranking universal | No ajustar ocultamente al observado |
| Misfit sustantivo | PPC dirigido | Discrepancia contextual | Optimista en muestra |
| Distribución predictiva | Log score o CRPS | Log mayor; CRPS menor | Sensibilidad distinta a colas |
| Probabilidad binaria | Log loss + Brier | Menor | Añadir calibración y utilidad |
| Intervalos | WIS/interval score | Menor | Evaluar varios niveles |
| Predicción puntual | MAE/RMSE | Menor | Ignoran incertidumbre completa |
| Generalización | ELPD por CV apropiada | Mayor | Unidad de partición define objetivo |
| Fiabilidad de PSIS | Pareto `k` | Menor | No es rendimiento predictivo |
| Comparar dos modelos | `Δelpd ± SE` + `d_i` | Contextual | Dependencia y pocos casos influyentes |
| Combinar modelos | Stacking | Log score CV mayor | Pesos no son probabilidades de verdad |
| Evidencia entre hipótesis | Bayes factor | Según numerador | Alta sensibilidad a priors |
| Ajuste descriptivo | Bayesian `R²` | Contextual | No sustituye validación |
| Decisión de clase | Utilidad, sensibilidad, PPV, etc. | Según costo | Depende de umbral/prevalencia |

## Contrato de reporte

Incluir:

- Outcome, unidad predictiva, población y horizonte.
- Distribución predictiva y si condiciona en grupos/covariables conocidos.
- Estrategia de partición y prevención de leakage, incluido preprocesamiento dentro de cada fold.
- Score con convención de signo, escala y agregación.
- Estimación puntual, incertidumbre y contribuciones por unidad/subgrupo.
- Diagnósticos PSIS o estabilidad entre folds.
- Chequeos de calibración y agudeza.
- Sensibilidad a casos influyentes, priors y especificación.
- Traducción de la diferencia predictiva a consecuencias o unidades del problema.

No afirmar “modelo validado”. Precisar: “no se detectó este fallo”, “predijo mejor bajo este score y esquema” o “la aproximación LOO fue/no fue confiable”.
