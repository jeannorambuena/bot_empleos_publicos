# Parámetros iniciales

## Objetivo comunitario

Radar Laboral Público Chile busca facilitar el acceso a convocatorias laborales del
sector público mediante una vista clara, actualizable y abierta a la comunidad. Esta
primera versión usa datos de ejemplo. Más adelante, un bot Python podrá mantener los
archivos JSON con nuevas oportunidades.

## Patrones laborales buscados

El radar prioriza oportunidades relacionadas con informática, soporte TI, redes,
servidores Linux y Windows, ciberseguridad, desarrollo web, frontend, backend, bases
de datos, SQL, compras públicas, transparencia pública, transformación digital y
gobierno digital. También considera cargos tecnológicos y administrativos en SLEP,
municipalidades y ministerios.

## Regiones priorizadas

- Maule
- O’Higgins
- Metropolitana
- Nacional

## Fuentes iniciales

- Empleos Públicos
- Servicio Civil
- Portales municipales

## Rangos de coincidencia

Los umbrales vigentes, ajustados tras la calibración inicial, son:

- Alta: 80 a 100
- Media: 60 a 79
- Baja: 35 a 59
- Descartada: 0 a 34 o descarte fuerte

## Alertas futuras

En etapas posteriores se podrán incorporar alertas por correo electrónico y eventos
o recordatorios de calendario para convocatorias relevantes y cierres próximos.

## Advertencia de seguridad

No subir archivos `.env`, claves, credenciales, bases de datos reales ni logs privados
al repositorio. Los datos publicados deben ser aptos para exposición pública.
