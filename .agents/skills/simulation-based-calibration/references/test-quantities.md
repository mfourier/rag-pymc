# Cantidades de prueba, empates y sensibilidad

## Contenido

1. Formulación ampliada
2. Selección práctica
3. Qué detecta cada familia
4. Resultados teóricos
5. Evidencia de casos
6. Límites

## Formulación ampliada

Usar una cantidad escalar medible `f: Θ × Y → R`. Para una verdad simulada `θ̃`, datos `y` y `M` muestras posteriores `θ_m`, calcular:

- `N_less = Σ_m I[f(θ_m,y) < f(θ̃,y)]`
- `N_equals = Σ_m I[f(θ_m,y) = f(θ̃,y)]`
- `K ~ Uniforme discreta{0,…,N_equals}`
- `N_total = N_less + K`

Bajo el posterior correcto, `N_total` es uniforme discreto en `{0,…,M}`. El desempate aleatorio permite masas puntuales, subflujo numérico y parámetros discretos `[MODRAK23, §1.2, ec. (5), p. 3; §§3.1 y apéndice A]`.

Registrar semilla y método de desempate para reproducibilidad. No usar jitter arbitrario como sustituto sin justificar que conserva el orden pertinente.

## Selección práctica

Construir un conjunto pequeño y motivado:

1. **Parámetros individuales.** Incluir parámetros de interés y aquellos sensibles a parametrización. Son inmediatos e inspeccionan sus marginales `[MODRAK23, §6.1, p. 21]`.
2. **Log-verosimilitud conjunta.** Considerarla por defecto porque depende de datos y parámetros, combina estructura y fue útil en todos los casos normales multivariados estudiados por los autores `[MODRAK23, §§3.3 y 6.1, pp. 9 y 21]`.
3. **Log-verosimilitudes de subconjuntos o puntos.** Añadirlas si existe riesgo de datos omitidos, censura, indexación o preprocesamiento incorrecto. Pueden localizar una parte ignorada que la conjunta diluye `[MODRAK23, §4.3, pp. 12–14]`.
4. **Cantidades inferenciales.** Añadir predicciones, contrastes o funciones que correspondan a la decisión científica. Comprueban directamente la incertidumbre relevante y pueden revelar dependencias `[MODRAK23, §6.1, p. 21]`.
5. **Estructura de dependencia.** Usar productos, diferencias o sumas de parámetros si interesan correlaciones o estructura de orden superior `[MODRAK23, §§4.4 y 6.1, pp. 15 y 21]`.
6. **Log-densidad del prior.** Añadirla si se sospechan transformaciones, Jacobianos o implementación del prior; el caso de simplex ordenado la detectó antes que la log-verosimilitud `[MODRAK23, §5.2, pp. 19–20]`.
7. **Transformaciones no monótonas.** Considerarlas sólo con una hipótesis de cancelación entre regiones. Transformaciones estrictamente monótonas producen un chequeo equivalente; las no monótonas pueden cambiar sensibilidad `[MODRAK23, §§3.6 y 4.5, pp. 10 y 16]`.

No seleccionar cantidades sólo después de ver cuáles fallan sin declarar la exploración. Separar análisis confirmatorio de exploratorio.

## Qué detecta cada familia

| Riesgo | Cantidades prioritarias | Razón respaldada |
|---|---|---|
| Posterior igual al prior; datos ignorados | Log-verosimilitud conjunta y por subconjunto | Cantidades sólo paramétricas pueden pasar por construcción `[MODRAK23, §§3.4 y 4.3]` |
| Un dato o bloque omitido | Log-verosimilitud del bloque sospechoso | La conjunta puede diluir un error pequeño en datasets grandes `[MODRAK23, §4.3]` |
| Correlación posterior incorrecta | Productos/diferencias y log-verosimilitud conjunta | Las marginales individuales pueden ser correctas mientras la dependencia falla `[MODRAK23, §4.4]` |
| Prior o Jacobiano incorrecto | Log-prior y parámetros afectados | La log-verosimilitud no fue una panacea en el simplex ordenado `[MODRAK23, §5.2]` |
| Sesgo pequeño repartido | Cantidades derivadas que combinen parámetros/datos | Pueden acumular discrepancias, aunque no resuelven falta general de precisión `[MODRAK23, §§4.6 y 6.2]` |
| Objetivo científico específico | Predicción o contraste de interés | Comprueba la parte del posterior que importa para la inferencia `[MODRAK23, §6.1]` |

## Resultados teóricos

- El posterior correcto pasa SBC para cualquier cantidad de prueba, incluidos empates con el procedimiento aleatorio `[MODRAK23, §3.1, teoremas 3–4, p. 8]`.
- Para una cantidad fija y un dato fijo, pasar SBC continuo equivale a que la distribución posterior inducida por esa cantidad sea correcta. Al promediar sobre datos, desviaciones de regiones distintas pueden cancelarse `[MODRAK23, §3.2, teorema 5, pp. 8–9]`.
- Si existe cualquier diferencia entre el posterior correcto y uno implementado, existe alguna cantidad dependiente de datos que la detecta. La razón de densidades construida en el teorema 6 es completa en teoría pero impráctica porque requiere conocer ambos posteriores `[MODRAK23, §3.3, teorema 6, p. 9]`.
- Un procedimiento que usa sólo un resumen `t(y)` de los datos puede pasar todas las cantidades que también dependen sólo de `t(y)`. El caso constante recupera un posterior que ignora todos los datos y devuelve el prior `[MODRAK23, §3.4, teorema 7, pp. 9–10]`.
- SBC y la igualdad del posterior promediado sobre datos con el prior imponen restricciones diferentes; ninguno debe usarse como definición del otro `[MODRAK23, §3.5, p. 10]`.
- Transformaciones estrictamente crecientes conservan rangos y estrictamente decrecientes los invierten, por lo que inducen chequeos equivalentes; transformaciones no monótonas no tienen esa garantía `[MODRAK23, §3.6, teorema 8, pp. 10–11]`.

## Evidencia de casos

Los siguientes resultados pertenecen a modelos concretos y sirven para formular hipótesis, no para prometer potencia universal:

- En un modelo normal multivariado cuyo “posterior” era el prior, los parámetros y otras cantidades sin datos pasaron, mientras cantidades de verosimilitud mostraron discrepancias grandes tras pocas simulaciones `[MODRAK23, §4.3, figs. 3–4, pp. 12–13]`.
- Al ignorar un dato de `n=3`, la verosimilitud puntual del dato omitido fue más sensible que la conjunta; con `n=20`, la discrepancia conjunta seguía pequeña después de 1000 simulaciones, mientras la puntual detectaba antes `[MODRAK23, §4.3, figs. 5–6, pp. 13–14]`.
- Con marginales correctas pero correlación incorrecta, los parámetros individuales pasaron y la log-verosimilitud conjunta fue la primera cantidad estudiada en mostrar problemas serios `[MODRAK23, §4.4, fig. 7, p. 15]`.
- En una implementación de simplex ordenado con error de Jacobiano, un parámetro y la log-densidad del prior detectaron antes que la log-verosimilitud; esto fundamenta que la conjunta es un buen valor por defecto pero no una panacea `[MODRAK23, §5.2, fig. 11, pp. 19–20]`.

## Límites

- Un conjunto finito de cantidades no garantiza detectar toda posterior incorrecta `[MODRAK23, §6.2, p. 21]`.
- Añadir cantidades aumenta comparaciones múltiples; corregir puede reducir potencia. La estructura de dependencia entre chequeos sigue abierta `[MODRAK23, §6.2, pp. 21–22]`.
- La log-verosimilitud puede ser numéricamente extrema o estar afectada por constantes/convenciones. Comparar la misma definición entre verdad y draws y documentar si se usa suma, media o subconjunto. Las transformaciones estrictamente monótonas son equivalentes para rangos, pero cambios no monótonos no lo son.
- Datos y parámetros de alta dimensión no desaparecen conceptualmente al reducirlos a una cantidad: la reducción determina qué errores son visibles.
- Preferir visualización de rangos/ECDF y magnitud de desviación a una única decisión de hipótesis `[MODRAK23, §1.2, p. 3]`.
