# Datos simulados - Fauna Silvestre

Archivos incluidos:
- deteccionesSimuladas.js: registros simulados de detecciones por video.
- especiesInfo.js: catálogo auxiliar de especies, gremio trófico y si es presa potencial del jaguar.
- estaciones.js: estaciones simuladas con latitud y longitud.
- datosSimulados.json: todos los datos en un solo JSON.

Uso rápido en React:

```js
import { deteccionesSimuladas } from "./data/deteccionesSimuladas";
import { especiesInfo } from "./data/especiesInfo";
import { estaciones } from "./data/estaciones";
```

Campos principales de detecciones:
id, idVideo, idCamara, estacion, fecha, hora, temperatura, especie, latitud, longitud, validado, confianzaModelo.
