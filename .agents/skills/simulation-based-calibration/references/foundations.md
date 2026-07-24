# Fundamentos y procedimiento de prior SBC

## Contenido

1. Pregunta que responde
2. Identidad y rango
3. Procedimiento
4. Interpretación gráfica
5. MCMC y autocorrelación
6. Presupuesto y sensibilidad
7. Límites

## Pregunta que responde

Prior SBC evalúa si un generador, una implementación de modelo y un algoritmo de inferencia producen resultados mutuamente calibrados sobre conjuntos de datos simulados desde el prior predictivo. Una falla puede deberse al generador, al programa probabilístico, al algoritmo o a su configuración; SBC aislado no identifica el componente culpable `[MODRAK23, §1.3, p. 4]`.

El alcance es computacional dentro del modelo asumido. No garantiza que el modelo describa el proceso real ni que un intervalo posterior cubra la verdad para una observación particular. Combinar con chequeos predictivos o residuales para estudiar desajuste del modelo `[TALTS20, §4, pp. 4–5; MODRAK23, §1.3, p. 4]`.

## Identidad y rango

Para un modelo `π(y,θ)=π(y|θ)π(θ)`:

1. Simular una verdad `θ̃ ~ π(θ)`.
2. Simular datos `ỹ ~ π(y|θ̃)`.
3. Obtener `M` muestras posteriores `θ₁,…,θ_M ~ π(θ|ỹ)` con el algoritmo bajo prueba.

Condicionado a `ỹ`, la verdad simulada y cada muestra posterior exacta tienen la misma distribución. Para una cantidad escalar `f`, el rango

`r = Σ_m I[f(θ_m,ỹ) < f(θ̃,ỹ)]`

es uniforme discreto en `{0,…,M}` bajo inferencia correcta, muestras independientes y ausencia de empates. La formulación original usa `f(θ)` `[TALTS20, §4.1, teorema 1 y alg. 1, pp. 5–6]`; la extensión dependiente de datos y con empates aparece en `test-quantities.md` `[MODRAK23, §1.2, p. 3]`.

No derivar SBC únicamente de la igualdad entre el prior y el posterior promediado sobre datos. La propiedad de rangos compara distribuciones condicionales dentro de la distribución conjunta SBC; ambos chequeos no son equivalentes `[MODRAK23, §§1.1 y 3.5, pp. 2 y 10]`.

## Procedimiento

1. Implementar el generador y el programa inferencial por rutas de código suficientemente independientes para que un mismo error no se replique silenciosamente.
2. Elegir cantidades de prueba antes de observar los rangos. Incluir parámetros de interés y cantidades dirigidas a riesgos de implementación.
3. Repetir `N` veces la secuencia prior → datos → ajuste → `M` muestras → rango.
4. Registrar fallas del ajuste y diagnósticos por réplica. No eliminar ajustes problemáticos sin una regla predefinida y una explicación, porque pueden ser la señal buscada.
5. Comparar los `N` rangos con la uniforme discreta sobre `0,…,M` mediante histograma y ECDF/PIT con bandas de referencia.
6. Analizar cada cantidad por separado y después buscar patrones compartidos. No agrupar parámetros de manera que se oculte cuál falla.

`[TALTS20, §4.1, p. 6]` construye una banda por bin a partir de cuantiles 0.005 y 0.995 de `Binomial(N,1/(M+1))`. Fuentes posteriores favorecen gráficos ECDF/PIT y señalan que los tests visuales son más informativos y desalientan pensamiento dicotómico `[MODRAK23, §1.2, p. 3]`.

## Interpretación gráfica

Tomar las formas siguientes como patrones diagnósticos históricos, no como causas identificadas de manera única:

| Patrón | Lectura de `[TALTS20]` | Comprobaciones alternativas |
|---|---|---|
| Compatible con uniforme | No se detecta desviación con este diseño | Potencia finita, cantidades insensibles, cancelación entre regiones |
| Picos en ambos extremos | Dependencia/autocorrelación entre muestras posteriores | Infra-dispersión real también puede elevar extremos; revisar ESS y cadenas |
| Forma `∩` | Posteriores computados sobre-dispersos en promedio | Revisar convención del rango, mezcla y heterogeneidad entre datos |
| Forma `∪` | Posteriores computados infra-dispersos en promedio | Revisar autocorrelación antes de atribuir dispersión |
| Asimetría | Sesgo de ubicación; muestras posteriores sesgadas hacia valores bajos producen rangos altos y viceversa | Revisar transformaciones, parametrización y código generador |

Fuente de las formas: `[TALTS20, §4.2, figs. 3–7, pp. 6–8]`. El paper advierte que varias desviaciones pueden coexistir. La aclaración posterior de que SBC y el chequeo del posterior promediado sobre datos son distintos exige presentar estas formas como heurísticas interpretables, no como una identificación matemática completa `[MODRAK23, §3.5, p. 10]`.

Para desviaciones pequeñas, complementar el histograma con ECDF y diferencia ECDF respecto de la uniforme. El paper fundacional señala que la ECDF reduce variación cerca de rangos extremos y que resúmenes especializados pueden ganar sensibilidad pero perder interpretabilidad `[TALTS20, §5.2, p. 10]`.

## MCMC y autocorrelación

Los rangos uniformes suponen muestras posteriores independientes. La autocorrelación agrupa muestras y puede producir picos extremos aunque el objetivo posterior sea correcto `[TALTS20, §4.2, fig. 4, pp. 6–7]`.

El procedimiento histórico de `[TALTS20, §5.1, alg. 2, pp. 9–10]` propone:

1. Ejecutar una cadena más larga que `M`.
2. Estimar ESS para funciones indicadoras de cuantiles de cada cantidad —el texto propone 19 cuantiles equiespaciados—.
3. Elegir una sola tasa de thinning conservadora usando la peor cantidad monitoreada.
4. Repetir o alargar la cadena si no alcanza `M` muestras efectivas; adelgazar y truncar a `M`.

Los autores presentan esa estrategia como basada en experiencia y reconocen autocorrelación residual. No convertirla en regla universal. Si la desviación persiste tras mitigar dependencia, `[TALTS20, §5.1, p. 10]` la considera evidencia fuerte de exploración inadecuada o ausencia del comportamiento CLT requerido para esos estimadores.

## Presupuesto y sensibilidad

El costo principal son `N` ajustes, aunque son paralelizables `[TALTS20, §4.3, p. 8]`. Reglas publicadas, que deben rotularse como heurísticas:

- Al reagrupar rangos en `B` bins, `[TALTS20, §4.1, p. 6]` reporta que `N/B ≈ 20` dio un compromiso útil en sus experimentos; también sugiere escoger `M+1` divisible por una potencia de 2 para reagrupar con facilidad.
- Pocas simulaciones pueden encontrar fallas graves, pero reducir `N` o `M` disminuye sensibilidad `[TALTS20, §4.3, p. 8]`.
- `[MODRAK23, §6.2, pp. 21–22]` razona que, sin costos fijos, órdenes de magnitud similares para datasets simulados y draws posteriores pueden equilibrar las dos aproximaciones ECDF. En la práctica, warmup y diagnóstico de cada ajuste motivan al menos alrededor de 100 muestras independientes por ajuste en sus ejemplos/discusión; no es un umbral universal de validez.

Planificar el presupuesto desde el tamaño mínimo de desviación relevante, costo por ajuste, cantidad de pruebas y tasa esperada de fallas. Reportar precisión Monte Carlo y ejecuciones fallidas.

## Límites

- Pasar SBC sólo significa que no se detectó una desviación con las cantidades, región y presupuesto usados.
- Cantidades unidimensionales pueden perder estructura multivariada; usar cantidades derivadas dirigidas a dependencias `[TALTS20, §7, p. 15; MODRAK23, §6.1, p. 21]`.
- Promediar sobre el prior predictivo puede ocultar regiones con sesgos opuestos o asignar poco esfuerzo a la región relevante tras observar datos `[POSTSBC25, §2, pp. 4–5]`.
- Muchas cantidades aumentan riesgo de falsos positivos o exigen corrección con pérdida de potencia; la dependencia entre pruebas no está resuelta en general `[MODRAK23, §6.2, pp. 21–22]`.
- Usar diagnósticos de convergencia por ajuste y chequeos predictivos; SBC no los sustituye.
