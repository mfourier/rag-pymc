# Posterior SBC condicionado a datos observados

## Contenido

1. Pregunta que responde
2. Identidad y procedimiento
3. Elección entre prior y posterior SBC
4. Evidencia de casos
5. Relación con otros diagnósticos
6. Límites

## Pregunta que responde

Posterior SBC pregunta si la inferencia es calibrada en la región de parámetros y datasets relevante después de observar `y_obs`. Prior SBC pregunta por el promedio sobre datos generados desde el prior predictivo. Una puede pasar y la otra fallar porque ponderan regiones distintas `[POSTSBC25, §§2–3, pp. 4–6]`.

Usar posterior SBC cuando la confianza en la inferencia para un dataset concreto sea el objetivo principal, especialmente con priors débiles, regiones problemáticas pequeñas, algoritmos nuevos o inferencia amortizada. No usarlo como sustituto de prior SBC si importa el desempeño prospectivo sobre todo el prior predictivo.

## Identidad y procedimiento

La identidad secuencial del paper es:

`π(y_obs,y,θ′,θ″) = π(θ′|y_obs) π(y|θ′,y_obs) π(θ″|y,y_obs)`.

En el modelo usual, el nuevo `y` se genera desde el modelo observacional condicionado a `θ′`; escribir explícitamente cualquier dependencia de diseño respecto a `y_obs`. Bajo actualización coherente, condicionado a los datos aumentados, `θ′` y `θ″` tienen la misma distribución `[POSTSBC25, §3, ec. (3), p. 5]`.

Proceder así:

1. Ajustar el modelo a `y_obs` con el algoritmo bajo prueba y obtener draws `θ′_i ~ π(θ|y_obs)` aproximados.
2. Para cada `θ′_i`, simular datos nuevos `y_i ~ π(y|θ′_i,y_obs)` con el generador.
3. Ajustar el modelo aumentado a `(y_obs,y_i)` con el algoritmo bajo prueba y obtener draws `θ″_{i,1:M} ~ π(θ|y_obs,y_i)` aproximados.
4. Calcular el rango/PIT de `θ′_i` respecto a los draws aumentados para cada cantidad de prueba; aplicar desempate aleatorio cuando corresponda.
5. Repetir y evaluar uniformidad con histograma o ECDF/PIT.
6. Registrar diagnósticos tanto del ajuste original como de cada ajuste aumentado.

No se requieren draws del posterior verdadero. Normalmente el mismo algoritmo genera draws del posterior original y de los aumentados. El argumento de los autores es que una falla en cualquiera rompe la igualdad salvo el caso poco plausible de sesgos consistentes a través de la actualización; no convertir esa plausibilidad en garantía formal `[POSTSBC25, §3, p. 5]`.

## Elección entre prior y posterior SBC

| Pregunta | Variante | Cobertura y costo |
|---|---|---|
| ¿Funciona la implementación sobre datasets plausibles según el prior? | Prior SBC | Cubre el prior predictivo; puede gastar esfuerzo en regiones irrelevantes tras observar datos |
| ¿Funciona la inferencia cerca del posterior de `y_obs`? | Posterior SBC | Enfoca la región condicionada; no certifica el resto del prior predictivo |
| ¿Puede haber cancelación de sesgos en regiones distintas? | Ambas, más cantidades dependientes de datos | Prior SBC agregado puede ocultarla; posterior SBC reduce el dominio, pero tampoco ofrece suficiencia finita |
| ¿Se usará el algoritmo de forma amortizada en muchos datos futuros? | Prior SBC para dominio de entrenamiento; posterior SBC para el dataset actual | Responden desempeño global y local respectivamente |

Explicar siempre cuál distribución genera las verdades y datos de cada réplica. “SBC sobre datos observados” sin especificar la actualización aumentada puede confundirse con PPC o recuperación de parámetros.

## Evidencia de casos

Usar estos casos sólo como demostraciones contextualizadas:

- **Modelo jerárquico:** prior SBC no mostró problemas claros para parametrizaciones centrada y no centrada; posterior SBC condicionado a dos datasets extremos favoreció parametrizaciones diferentes según la fuerza relativa de likelihood y jerarquía. Los diagnósticos estándar también avisaron, pero los gráficos PIT ayudaron a leer dirección del sesgo `[POSTSBC25, §4.1, figs. 3–5, pp. 6–10]`.
- **Lotka–Volterra:** prior SBC encontró problemas en combinaciones plausibles bajo priors débiles pero irrelevantes tras condicionar a datos históricos. Posterior SBC no mostró el problema en esa región y fue más barato en ese caso: 250 iteraciones de prior SBC tomaron 6.5 h, mientras 500 de posterior SBC tomaron 2.5 h después de un ajuste inicial de 10 s. No generalizar esta ventaja temporal `[POSTSBC25, §4.2, figs. 6–8, pp. 10–13]`.
- **Inferencia amortizada:** el paper muestra un caso donde posterior SBC señaló problemas no visibles en prior SBC. Tras entrenar el aproximador, repetir inferencia era casi instantáneo, por lo que el costo incremental fue pequeño en ese entorno `[POSTSBC25, §4.3, pp. 13–16]`.

## Relación con otros diagnósticos

- Revisar `R-hat`, ESS, divergencias y diagnósticos del algoritmo antes de gastar en posterior SBC cuando ya muestran problemas grandes. Posterior SBC puede complementar al cuantificar dirección y magnitud aparente del sesgo `[POSTSBC25, §5, pp. 16–17]`.
- No confundir posterior SBC con PPC. PPC compara datos simulados desde el posterior predictivo con datos observados para estudiar adecuación; posterior SBC usa la regla de cadena y compara un draw del posterior original con draws del posterior aumentado para estudiar computación `[POSTSBC25, §3, pp. 5–6]`.
- No confundirlo con recuperación informal de parámetros, que suele escoger valores factibles y comparar visualmente sin el test de uniformidad formal `[POSTSBC25, §3, p. 5]`.
- Considerarlo especialmente cuando no hay diagnósticos rápidos bien establecidos, como en implementaciones nuevas o inferencia amortizada `[POSTSBC25, §5, pp. 16–17]`.

## Límites

- Pasar posterior SBC es necesario pero no suficiente para confiar en inferencia con computación finita `[POSTSBC25, §5, p. 16]`.
- Evalúa el posterior original y posteriores aumentados cercanos, no toda geometría posible ni la adecuación del modelo al mundo real.
- El aumento puede aproximar duplicar el tamaño de datos y cambiar la geometría. Si preocupa que sea demasiado distinto, el paper propone usar sólo parte de los datos en el primer posterior para acercar tamaños; documentar esta modificación `[POSTSBC25, §5, p. 16]`.
- Una falla puede provenir del ajuste original, los aumentados, el generador o la implementación; inspeccionar registros por réplica.
- La relevancia del dominio depende de que `y_obs` y el esquema de datos nuevos representen la pregunta inferencial. Posterior SBC no arregla desajuste del modelo.
- Las afirmaciones del paper sobre casos ODE y amortizados son demostraciones, no garantías generales de detección ni costo.
