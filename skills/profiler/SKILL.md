---
name: profiler
description: Análisis de rendimiento con Linux perf y generación de flamegraphs. Identifica cuellos de botella en CPU y optimiza código.
metadata:
  category: testing
  tags: rendimiento,perf,flamegraph,linux,optimizacion
---

## Qué hace
- Ejecuta sampling con perf para capturar perfiles de CPU
- Genera flamegraphs interactivos para visualizar cuellos de botella
- Identifica funciones que consumen más tiempo de CPU
- Analiza call stacks y patrones de ejecución
- Sugiere optimizaciones basadas en los datos del perfil

## Cuándo usarlo
- Cuando una aplicación consume más CPU de lo esperado
- Para identificar funciones lentas en código de producción
- Antes y después de optimizaciones para medir impacto
- Para entender el flujo de ejecución de código complejo

## Cómo usarlo
1. El proceso debe estar ejecutándose en un sistema Linux con perf disponible
2. Indica el proceso o comando a profilear
3. Se ejecutará la captura y se analizarán los resultados
