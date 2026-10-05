from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class Integrante:
    nombres_apellidos: str
    rol: str = "Miembro del Equipo"
    cui: str = ""
    funciones: List[str] = field(default_factory=list)

@dataclass
class ReportMetadata:
    institucion: str = "UNIVERSIDAD NACIONAL DE SAN AGUSTÍN DE AREQUIPA"
    facultad: str = "FACULTAD DE INGENIERÍA DE PRODUCCIÓN Y SERVICIOS"
    escuela: str = "ESCUELA PROFESIONAL DE INGENIERÍA DE SISTEMAS"
    curso: str = ""
    docente: str = ""
    titulo: str = ""
    semestre: str = ""
    fecha: str = ""
    ano_lectivo: str = ""
    numero_practica: str = ""
    integrantes: List[Integrante] = field(default_factory=list)

@dataclass
class SectionContent:
    title: str
    body_paragraphs: List[str] = field(default_factory=list)
    bullets: List[Dict[str, str]] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    placeholders: List[Dict[str, str]] = field(default_factory=list)
    code_blocks: List[str] = field(default_factory=list)
    subsections: List['SectionContent'] = field(default_factory=list)
