#!/bin/bash
set -e
VIDEO="/home/totora/Documents/PROFESIONAL/video-report/inputs/video/2026-10-04 13-52-34.mp4"
OUTDIR="/home/totora/Documents/PROFESIONAL/video-report/media"

generate_gif() {
    local start=$1
    local duration=$2
    local output=$3
    echo "Generating $output..."
    ffmpeg -y -ss "$start" -t "$duration" -i "$VIDEO" \
        -vf "fps=12,scale=640:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer:bayer_scale=3" \
        "$OUTDIR/$output"
    if which gifsicle >/dev/null 2>&1; then
        gifsicle -O3 --lossy=80 -o "$OUTDIR/opt_$output" "$OUTDIR/$output"
        mv "$OUTDIR/opt_$output" "$OUTDIR/$output"
    fi
}

# GIF 1: Movimiento con tambaleo (818s a 824s, 5 seg)
generate_gif 818 5 "animacion_movimiento_rotacion_error.gif"

# GIF 2: Movimiento corregido (942s a 948s, 5 seg)
generate_gif 942 5 "animacion_movimiento_exitoso.gif"

# GIF 3: Salto del gato en bucle (1340s a 1346s, 5 seg)
generate_gif 1340 5 "animacion_salto_gato.gif"

ls -lh "$OUTDIR"/*.gif
