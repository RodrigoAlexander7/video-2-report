# -*- coding: utf-8 -*-
"""Revisión del texto del reporte: tono directo, ortografía, afirmaciones técnicas y citas.

Reglas (salen de los defectos vistos en los reportes generados por agente frente al de nota 18):
  * Nada de superlativos, adjetivos de relleno ni juicios propios («Advertencia Técnica Clave», «sinergia»).
  * Etiquetas en Mayúsculas Iniciales con dos puntos ("Advertencia Técnica Clave (Ámbito de Clases):") delatan texto genérico.
  * Sin voseo ni mezcla de voces; frases completas; sin muletillas de introducción («En esta etapa se…»).
  * Afirmaciones técnicas conocidas que suelen salir mal (p. ej. `Update()` no corre "cada milisegundo").
  * Ortografía con el diccionario hunspell es_ES del sistema (más un glosario de Unity y los identificadores del código).
  * Cada cita [n] existe y cada referencia se cita.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

HUNSPELL_DIRS = ("/usr/share/hunspell", "/usr/share/myspell", "/usr/share/myspell/dicts", "/app/share/hunspell")

# palabra -> motivo. Se compara sin acentos y en minúsculas, como palabra completa.
BANNED = {
    "clave": "relleno", "critico": "juicio", "critica": "juicio", "criticos": "juicio", "criticas": "juicio",
    "fundamental": "relleno", "fundamentales": "relleno", "indispensable": "relleno", "indispensables": "relleno",
    "imprescindible": "relleno", "imprescindibles": "relleno", "esencial": "relleno", "esenciales": "relleno",
    "crucial": "relleno", "vital": "relleno", "determinante": "relleno", "altamente": "intensificador",
    "sumamente": "intensificador", "rigurosamente": "intensificador", "riguroso": "intensificador",
    "rigurosa": "intensificador", "estrictamente": "intensificador", "robusto": "juicio", "robusta": "juicio",
    "optimo": "juicio", "optima": "juicio", "perfecto": "juicio", "perfecta": "juicio", "excelente": "juicio",
    "impresionante": "juicio", "increible": "juicio", "sorprendente": "juicio", "poderoso": "juicio",
    "poderosa": "juicio", "magistral": "juicio", "sinergia": "jerga", "paradigma": "jerga", "trascendencia": "jerga",
    "trascendental": "jerga", "pilar": "jerga", "magico": "jerga", "magica": "jerga", "magicos": "jerga",
    "magicas": "jerga", "armonioso": "jerga", "armoniosa": "jerga", "idoneidad": "jerga", "meticuloso": "jerga",
    "exhaustivo": "jerga", "exhaustiva": "jerga", "holistico": "jerga", "integral": "jerga",
}
OPINION = re.compile(r"\b(consideramos que|creemos que|opinamos|nos parece|me parece|considero|creo que|pienso que|"
                     r"en mi opini[oó]n|desde nuestro punto de vista|a nuestro juicio)\b", re.I)
# solo la forma acentuada del voseo; "configura" / "crea" sin tilde son imperativos de tú o tercera persona
VOSEO_ACCENTED = re.compile(r"\b(configurá|ponelo|dejalo|hacé|fijate|tenés|podés|querés|sabés|agregá|seleccioná|abrí|"
                            r"creá|usá|elegí|probá|ejecutá|asegurate|recordá)\b", re.I)
META = re.compile(r"\b(en esta (etapa|secci[oó]n|fase|parte)|el objetivo de (esta|la) (etapa|secci[oó]n|fase)|"
                  r"a continuaci[oó]n se (presenta|describe|detalla)|cabe (destacar|mencionar|se[ñn]alar)|es importante (destacar|se[ñn]alar|mencionar))\b", re.I)
# "Advertencia Técnica Clave (Ámbito de Clases):" -> 3+ palabras con inicial mayúscula seguidas de dos puntos
TITLE_LABEL = re.compile(r"(?:^|(?<=[.!?]\s))((?:[A-ZÁÉÍÓÚÑ][\wáéíóúñ]+)(?:\s+(?:de|del|la|el|los|las|y|en|a|con|por|para)?\s*[A-ZÁÉÍÓÚÑ][\wáéíóúñ]+){2,})\s*(?:\([^)]{1,40}\))?:")
DANGLING = {"de", "del", "la", "el", "los", "las", "un", "una", "para", "con", "y", "o", "que", "por", "en", "a", "al", "se", "su", "sus", "como", "e"}
FACTS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"update\s*(\(\s*\))?[^.\n]{0,70}(cada milisegundo|cada segundo|cada milisegundos)", re.I),
     "`Update()` se ejecuta una vez por fotograma (frame), no cada milisegundo ni cada segundo"),
    (re.compile(r"fixedupdate\s*(\(\s*\))?[^.\n]{0,60}cada (frame|fotograma)", re.I),
     "`FixedUpdate()` corre a intervalos fijos de física (0,02 s por defecto), no una vez por fotograma"),
    (re.compile(r"getkey\s*(\(\s*[^)]*\))?[^.\n]{0,60}(una sola vez|solo una vez|únicamente al presionar)", re.I),
     "`GetKey` devuelve true en cada fotograma mientras la tecla sigue presionada; `GetKeyDown` solo en el fotograma de la pulsación"),
    (re.compile(r"getkeydown\s*(\(\s*[^)]*\))?[^.\n]{0,60}(mientras (se )?(mantiene|mantenga|siga))", re.I),
     "`GetKeyDown` devuelve true solo en el fotograma de la pulsación; para teclas mantenidas es `GetKey`"),
    (re.compile(r"deltatime[^.\n]{0,60}(aumenta|incrementa) (la )?velocidad", re.I),
     "`Time.deltaTime` es la duración del último fotograma; sirve para que el movimiento no dependa de los FPS, no para acelerar"),
]
UNITY_GLOSSARY = """
rigidbody collider capsule mesh gameobject gameobjects inspector hierarchy prefab prefabs script scripts input update
fixedupdate lateupdate start awake audio audiosource audiolistener clip clips audioclip playoneshot freeze rotation
constraints interpolate interpolation deltatime framerate fps shader sprite tilemap canvas transform vector quaternion
raycast trigger layer layers tag tags build play pause game scene scenes asset assets package packages editor component
components spatial blend loop mixer listener mute bypass effects priority volume pitch stereo pan freesound creative
commons attribution sampling noncommercial unity visual studio code github https www http wav mp3 ogg flac click
drag drop checkbox slider dropdown frame frames collision continuous discrete dynamic kinematic gravity mass drag
angular linear damping detection overrides select open static material physic physics layout default console debug
log warning error true false null bool float int string void public private class using namespace override
project main camera cameras settings window layout toolbar menu button label field slider panel tab tabs mesh
""".split()

_WORD = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+")
_SKIP_SPELL = re.compile(r"`[^`]*`|https?://\S+|\{fig:[\w\-]+\}|\[\d+\]|\*\*")


@dataclass
class Issue:
    level: str            # "error" | "warning"
    where: str
    message: str

    def __str__(self) -> str:
        return f"[{self.level}] {self.where}: {self.message}"


def _plain(word: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", word.lower()) if not unicodedata.combining(c))


def lint_text(text: str, where: str, allow: Iterable[str] = (), sentence: bool = True) -> List[Issue]:
    """Reglas de tono. ``allow``: palabras de BANNED que este proyecto permite (p. ej. «clave» en «clave foránea»).
    ``sentence=False`` (encabezados y pies de figura) no exige punto final."""
    issues: List[Issue] = []
    allowed = {_plain(a) for a in allow}
    visible = _SKIP_SPELL.sub(" ", text)
    for m in _WORD.finditer(visible):
        key = _plain(m.group())
        if key in BANNED and key not in allowed:
            issues.append(Issue("error", where, f"«{m.group()}»: {BANNED[key]}; di el hecho en una frase directa"))
    for m in OPINION.finditer(visible):
        issues.append(Issue("error", where, f"«{m.group()}»: sin apreciaciones personales; describe lo que se hizo y lo que se observó"))
    for m in VOSEO_ACCENTED.finditer(visible):
        issues.append(Issue("error", where, f"«{m.group()}»: voseo; usa la forma del resto del reporte («Configuramos…», «configura»)"))
    for m in META.finditer(visible):
        issues.append(Issue("error", where, f"«{m.group()}»: muletilla de introducción; empieza por la acción"))
    for m in TITLE_LABEL.finditer(text):
        issues.append(Issue("error", where, f"«{m.group(1)}:»: etiqueta en Mayúsculas Iniciales; escribe la frase normal"))
    for pattern, msg in FACTS:
        if pattern.search(text):
            issues.append(Issue("error", where, f"afirmación técnica dudosa: {msg}"))
    stripped = _SKIP_SPELL.sub("", text).strip().rstrip("*")
    if stripped:
        last = _WORD.findall(stripped)[-1].lower() if _WORD.findall(stripped) else ""
        if last in DANGLING and stripped[-1] not in ".!?)":
            issues.append(Issue("error", where, f"frase incompleta (termina en «{last}»)"))
        elif sentence and stripped[-1] not in ".!?:)]\"”`" and not stripped.endswith("…"):
            issues.append(Issue("warning", where, "la frase no termina en punto"))
    return issues


def _find_dictionary(lang: str = "es_ES") -> Optional[str]:
    for base in HUNSPELL_DIRS:
        stem = Path(base) / lang
        if stem.with_suffix(".dic").is_file() and stem.with_suffix(".aff").is_file():
            return str(stem)
    return None


class Speller:
    """Ortografía con hunspell (vía `spylls`, en Python puro). Sin diccionario instalado, avisa y no revisa."""

    def __init__(self, extra_words: Iterable[str] = ()):
        self.words: Set[str] = {_plain(w) for w in UNITY_GLOSSARY} | {_plain(w) for w in extra_words}
        self.dictionary = None
        self.error: Optional[str] = None
        stem = _find_dictionary()
        if stem is None:
            self.error = "no hay diccionario hunspell es_ES (sudo apt install hunspell-es): no se revisa la ortografía"
            return
        try:
            from spylls.hunspell import Dictionary
            self.dictionary = Dictionary.from_files(stem)
        except Exception as exc:                                    # diccionario corrupto, spylls ausente
            self.error = f"no se pudo cargar el diccionario ortográfico: {exc}"

    def known(self, word: str) -> bool:
        if _plain(word) in self.words:
            return True
        return bool(self.dictionary.lookup(word) or self.dictionary.lookup(word.lower()))

    def check(self, text: str, where: str) -> List[Issue]:
        if self.dictionary is None:
            return []
        issues: List[Issue] = []
        cleaned = _SKIP_SPELL.sub(" ", text)
        seen: Set[str] = set()
        for m in _WORD.finditer(cleaned):
            word = m.group()
            if len(word) < 4 or word in seen:
                continue
            if any(c.isupper() for c in word[1:]):                  # PlayOneShot, GameObject, FPS
                continue
            if not self.known(word):
                seen.add(word)
                issues.append(Issue("warning", where, f"ortografía: «{word}»"))
        return issues


def identifiers_from_code(files: Iterable[Path]) -> Set[str]:
    """Palabras de los identificadores del código (camelCase y snake_case partidos) para no marcarlas como errata."""
    out: Set[str] = set()
    for f in files:
        try:
            text = Path(f).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for ident in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text):
            for part in re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])", ident.replace("_", " ")):
                out.add(part.lower())
    return out


def check_citations(texts: Dict[str, str], n_refs: int) -> List[Issue]:
    """Toda cita [n] existe en la lista de referencias y toda referencia se cita al menos una vez."""
    issues: List[Issue] = []
    cited: Set[int] = set()
    for where, text in texts.items():
        without_code = re.sub(r"`[^`]*`", " ", text)
        for m in re.finditer(r"\[(\d+)\]", without_code):
            n = int(m.group(1))
            cited.add(n)
            if not 1 <= n <= n_refs:
                issues.append(Issue("error", where, f"cita [{n}] sin referencia (hay {n_refs})"))
    for n in range(1, n_refs + 1):
        if n not in cited:
            issues.append(Issue("error", "referencias", f"la referencia [{n}] no se cita en el texto: cítala donde la usas o quítala"))
    return issues
