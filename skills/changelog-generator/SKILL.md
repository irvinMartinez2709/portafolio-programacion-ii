---
name: changelog-generator
description: Crea automáticamente changelogs para usuarios a partir del historial de commits. Organiza cambios por tipo y versión.
metadata:
  category: desarrollo
  tags: changelog,commits,release,notas
---

## Qué hace
- Analiza el historial de commits entre dos puntos (tags, ramas o fechas)
- Clasifica commits por tipo (feature, fix, docs, refactor, etc.)
- Agrupa cambios por versión siguiendo Keep a Changelog
- Genera formato Markdown listo para publicar
- Detecta breaking changes y cambios importantes automáticamente

## Cuándo usarlo
- Antes de crear un release o tag nuevo
- Para preparar notas de release automáticas
- Cuando necesitas comunicar cambios a stakeholders
- Para mantener un CHANGELOG.md actualizado sin esfuerzo manual

## Cómo usarlo
1. Especifica el rango (tags, ramas, SHA commits, o desde última versión)
2. Indica el formato deseado para el changelog
3. Revisa y ajusta la clasificación antes de escribir el archivo
