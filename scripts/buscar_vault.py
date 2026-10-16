#!/usr/bin/env python3
"""Buscador del vault con orden por relevancia (SQLite FTS5 + BM25).

Para cuando no sé con qué palabra se escribió algo: grep exige la palabra
exacta y devuelve los ficheros sin orden; esto devuelve los pocos que mejor
casan y el párrafo donde está. Para rutas, ids y errores literales, grep.

Nació el 16-10-2026 tras probar XERJ contra el vault: lo que ordenaba bien era
BM25, nada neuronal. Esto hace lo mismo sin servicio corriendo, sin MCP y sin
dependencias (solo la biblioteca estándar).

El índice vive en ~/.cache/buscar_vault/ (fuera del vault, no se versiona) y se
pone al día solo en cada búsqueda: rehace únicamente los ficheros cambiados.

Uso:
    buscar_vault.py "controladora USB corrompe escrituras"
    buscar_vault.py -n 8 --dentro Knowledge/Infrastructure "cachear rutas en prod"
    buscar_vault.py --reindexar
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
import time
from pathlib import Path

VAULT = Path(os.environ.get("RAW_VAULT", Path.home() / "Raw_Vault"))
INDICE = Path.home() / ".cache" / "buscar_vault" / "vault.db"

# Texto que se escribe a mano. Fuera: logs, json, csv, listas y binarios, que
# ahogan la prosa por volumen (lo mismo vio XERJ con el código).
EXTENSIONES = {".md", ".txt", ".py", ".sh", ".yml", ".yaml", ".toml", ".conf", ".ini", ".service", ".bb"}
MAX_BYTES = 2_000_000
TROZO = 1200  # caracteres por pasaje

VACIAS = set(
    """a al algo como con cual cuando de del desde donde el ella en entre es esa ese
    eso esta este esto hay la las le lo los mas me mi muy no o para pero por porque
    que se si sin sobre su sus te tu un una uno y ya qué cómo dónde cuál por qué
    the a an and are as at be by for from how in is it of on or that the this to
    was what when where which why with""".split()
)

ESQUEMA = """
CREATE TABLE IF NOT EXISTS ficheros (ruta TEXT PRIMARY KEY, mtime REAL, tam INTEGER);
CREATE VIRTUAL TABLE IF NOT EXISTS pasajes USING fts5(
    ruta, titulo, texto, linea UNINDEXED,
    tokenize = 'unicode61 remove_diacritics 2'
);
"""


def candidatos() -> dict[str, os.stat_result]:
    out: dict[str, os.stat_result] = {}
    for raiz, dirs, ficheros in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
        for nombre in ficheros:
            p = Path(raiz, nombre)
            # Fuera también este script: sus ejemplos casan con todo.
            if p.suffix.lower() not in EXTENSIONES or nombre.startswith(".") or p.resolve() == Path(__file__).resolve():
                continue
            st = p.stat()
            if st.st_size <= MAX_BYTES:
                out[str(p.relative_to(VAULT))] = st
    return out


def pasajes(texto: str) -> list[tuple[str, int, str]]:
    """Trocea por encabezados markdown y luego por tamaño. (título, línea, texto)."""
    out: list[tuple[str, int, str]] = []
    titulo, inicio, buf = "", 1, []

    def volcar() -> None:
        bloque = "\n".join(buf).strip()
        if not bloque:
            return
        linea = inicio
        for i in range(0, len(bloque), TROZO):
            out.append((titulo, linea, bloque[i : i + TROZO]))
            linea += bloque[i : i + TROZO].count("\n")

    for n, linea in enumerate(texto.splitlines(), 1):
        if re.match(r"#{1,6}\s", linea):
            volcar()
            titulo, inicio, buf = linea.lstrip("#").strip(), n, [linea]
        else:
            buf.append(linea)
    volcar()
    return out


def actualizar(db: sqlite3.Connection, forzar: bool = False) -> tuple[int, int]:
    if forzar:
        db.executescript("DELETE FROM ficheros; DELETE FROM pasajes;")
    ahora = candidatos()
    previos = {r: (m, t) for r, m, t in db.execute("SELECT ruta, mtime, tam FROM ficheros")}
    cambiados = [r for r, st in ahora.items() if previos.get(r) != (st.st_mtime, st.st_size)]
    borrados = [r for r in previos if r not in ahora]

    for ruta in borrados + cambiados:
        db.execute("DELETE FROM pasajes WHERE ruta = ?", (ruta,))
        db.execute("DELETE FROM ficheros WHERE ruta = ?", (ruta,))

    for ruta in cambiados:
        try:
            texto = (VAULT / ruta).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        db.executemany(
            "INSERT INTO pasajes (ruta, titulo, texto, linea) VALUES (?, ?, ?, ?)",
            [(ruta, t, x, l) for t, l, x in pasajes(texto)],
        )
        st = ahora[ruta]
        db.execute("INSERT INTO ficheros VALUES (?, ?, ?)", (ruta, st.st_mtime, st.st_size))

    db.commit()
    return len(cambiados), len(borrados)


def consulta_fts(texto: str) -> str:
    """Lenguaje natural → OR de términos. Las palabras largas van por prefijo
    («cachean» casa con «cachear» y «caché»), un apaño barato de lematización."""
    terminos = []
    for palabra in re.findall(r"[\w.-]+", texto.lower()):
        palabra = palabra.strip(".-")
        if not palabra or palabra in VACIAS:
            continue
        if re.fullmatch(r"[\w]+", palabra) and len(palabra) > 6:
            terminos.append(f'"{palabra[:5]}"*')
        else:
            terminos.append('"' + palabra.replace('"', "") + '"')
    return " OR ".join(terminos)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("consulta", nargs="*")
    ap.add_argument("-n", type=int, default=5, help="ficheros a devolver (5)")
    ap.add_argument("--dentro", default="", help="solo rutas que empiecen por esto")
    ap.add_argument("--reindexar", action="store_true", help="rehacer el índice entero")
    args = ap.parse_args()

    INDICE.parent.mkdir(parents=True, exist_ok=True)
    nuevo = not INDICE.exists()
    db = sqlite3.connect(INDICE)
    if nuevo:
        os.chmod(INDICE, 0o600)
    db.executescript(ESQUEMA)

    t0 = time.monotonic()
    cambiados, borrados = actualizar(db, args.reindexar)
    if args.reindexar or not args.consulta:
        total = db.execute("SELECT count(*) FROM ficheros").fetchone()[0]
        print(f"índice: {total} ficheros, {cambiados} rehechos, {borrados} quitados, {time.monotonic() - t0:.1f}s")
        if not args.consulta:
            return 0

    fts = consulta_fts(" ".join(args.consulta))
    if not fts:
        print("consulta vacía tras quitar palabras vacías")
        return 1

    # Pesos BM25: ruta 2, título 3, texto 1. Mejor pasaje por fichero; se
    # agrupa aquí porque FTS5 no deja usar bm25() dentro de una ventana.
    filas, vistos = [], set()
    for fila in db.execute(
        """
        SELECT ruta, titulo, linea,
               bm25(pasajes, 2.0, 3.0, 1.0) AS score,
               snippet(pasajes, 2, '»', '«', ' … ', 24)
        FROM pasajes
        WHERE pasajes MATCH ? AND ruta LIKE ?
        ORDER BY score LIMIT 500
        """,
        (fts, args.dentro + "%"),
    ):
        if fila[0] not in vistos:
            vistos.add(fila[0])
            filas.append(fila)
            if len(filas) == args.n:
                break

    if not filas:
        print("sin resultados")
        return 1

    for ruta, titulo, linea, score, snip in filas:
        print(f"{score:7.2f}  {VAULT / ruta}:{linea}" + (f"  — {titulo}" if titulo else ""))
        print("         " + " ".join(snip.split()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
