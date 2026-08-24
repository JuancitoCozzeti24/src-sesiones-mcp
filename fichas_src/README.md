# SRC Fichas Didácticas v0.1.0

Complemento MCP independiente para generar fichas de Matemática en PDF con la identidad visual de Santa Rita de Casia.

## Principio de diseño

La plantilla visual se deriva del modelo institucional aportado por el docente. Se conservan como identidad fija:

- encabezado institucional con logo y nombre del colegio;
- título grande, datos de estudiante, sección y fecha;
- bloque curricular completo o compacto;
- niveles visuales: fácil (azul), intermedio (verde), reto (morado);
- cajas redondeadas y espacios de resolución adecuados al tipo de ejercicio;
- autoevaluación con acciones concretas;
- pie institucional con lema y logos.

## Herramientas MCP

- `get_ficha_template_info`: devuelve reglas, tipos de página y estructura del spec.
- `generate_ficha_src_pdf`: genera la ficha PDF.
- `get_generated_ficha`: consulta un PDF generado.

## Tipos de página v0.1.0

1. `theory`: teoría visual mediante tarjetas, reglas, ejemplos, palabras clave, aplicaciones y consejo.
2. `practice_easy`: práctica fácil en dos columnas, normalmente 6 ejercicios.
3. `practice_levels`: continuación con nivel intermedio, reto y autoevaluación; no repite el encabezado institucional.

## Matemática estructurada

Los enunciados pueden incluir `prompt_lines` formados por runs. Los runs soportados inicialmente son:

- texto: `{"type":"text","text":"Si A = "}`
- matriz: `{"type":"matrix","value":[[1,2],[3,4]]}`

Esto evita matrices escritas como texto plano y mantiene el aspecto visual de la ficha.
