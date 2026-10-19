import os
import subprocess
from PIL import Image, ImageDraw
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, project_root)
sys.path.append(os.path.join(project_root, ".agents/skills/figure-enhancer/scripts"))
from enhance_image import crop_image, draw_focus_box, draw_arrow, add_technical_frame
from config import ReportConfig, DEFAULT_CONFIG
from src.video_engine.media_extractor import generate_gif

def generate_enhanced_images():
    media_dir = os.path.join(project_root, "output/IDSE/lab07/figures")
    os.makedirs(media_dir, exist_ok=True)
    video = os.path.join(project_root, "inputs/IDSE/lab07/2026-10-16 10-43-58.mp4")

    # Helper para extraer frame en segundos específicos
    def extract_frame(ss_time, out_name):
        out_path = os.path.join(media_dir, out_name)
        subprocess.run([
            "ffmpeg", "-y", "-ss", str(ss_time), "-i", video, "-vframes", "1", out_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return out_path

    # --- FIGURA 1: Búsqueda y Licencias en Freesound.org ---
    print("Generando Figura 1: Freesound y Licencias...")
    f1_raw = extract_frame(115, "raw_fig1.png")
    img1 = Image.open(f1_raw)
    panel1 = crop_image(img1, (60, 420, 950, 980))
    panel1_focus = draw_focus_box(panel1, (10, 45, 240, 305), label="Filtros de Licencias Libres (CC0, CC BY, Sampling+)", color=(27, 54, 93, 255), border_width=3)
    panel1_focus2 = draw_focus_box(panel1_focus, (250, 330, 780, 540), label="Clip Seleccionado: jump_land.wav (CC0)", color=(230, 57, 70, 255), border_width=3)
    panel1_final = add_technical_frame(panel1_focus2)
    panel1_final.save(os.path.join(media_dir, "fig1_freesound_licenses.png"))

    # --- FIGURA 2: Importación de Clips en Assets/Audio ---
    print("Generando Figura 2: Unity Assets Audio...")
    f2_raw = extract_frame(405, "raw_fig2.png")
    img2 = Image.open(f2_raw)
    panel2 = crop_image(img2, (0, 735, 800, 990))
    panel2_focus = draw_focus_box(panel2, (380, 55, 500, 235), label="Clips Importados: footstep & Jump", color=(27, 54, 93, 255), border_width=3)
    draw2 = ImageDraw.Draw(panel2_focus)
    draw_arrow(draw2, start=(600, 140), end=(505, 140), color=(27, 54, 93, 255), width=4, arrowhead_len=18)
    panel2_final = add_technical_frame(panel2_focus)
    panel2_final.save(os.path.join(media_dir, "fig2_unity_assets_audio.png"))

    # --- FIGURA 3: Asignación de Audio Source al GameObject Mango ---
    print("Generando Figura 3: Audio Source Component...")
    f3_raw = extract_frame(515, "raw_fig3.png")
    img3 = Image.open(f3_raw)
    panel3 = crop_image(img3, (1440, 460, 1918, 980))
    panel3_focus = draw_focus_box(panel3, (10, 40, 465, 500), label="Componente Audio Source Incorporado", color=(27, 54, 93, 255), border_width=3)
    panel3_final = add_technical_frame(panel3_focus)
    panel3_final.save(os.path.join(media_dir, "fig3_audiosource_component.png"))

    # --- FIGURA 4: Configuración de Parámetros de Audio Source ---
    print("Generando Figura 4: Parámetros Audio Source (Play On Awake & Spatial Blend)...")
    f4_raw = extract_frame(575, "raw_fig4.png")
    img4 = Image.open(f4_raw)
    panel4 = crop_image(img4, (1440, 620, 1918, 980))
    panel4_focus = draw_focus_box(panel4, (12, 40, 465, 280), label="Play On Awake Desmarcado & Spatial Blend 2D", color=(230, 57, 70, 255), border_width=3)
    draw4 = ImageDraw.Draw(panel4_focus)
    # Flecha apuntando a la casilla de verificación de Play On Awake (x ≈ 405, y ≈ 70)
    draw_arrow(draw4, start=(330, 70), end=(395, 70), color=(230, 57, 70, 255), width=4, arrowhead_len=18)
    panel4_final = add_technical_frame(panel4_focus)
    panel4_final.save(os.path.join(media_dir, "fig4_audiosource_parameters.png"))

    # --- FIGURA 5: Declaración de Variables y Captura en Start() ---
    print("Generando Figura 5: Variables C# y Start()...")
    f5_raw = extract_frame(990, "raw_fig5.png")
    img5 = Image.open(f5_raw)
    panel5 = crop_image(img5, (35, 210, 1400, 710))
    panel5_focus = draw_focus_box(panel5, (50, 40, 760, 130), label="Variables AudioClip y AudioSource", color=(27, 54, 93, 255), border_width=3)
    panel5_focus2 = draw_focus_box(panel5_focus, (50, 180, 800, 480), label="Captura y Configuración Defensiva en Start()", color=(40, 167, 69, 255), border_width=3)
    panel5_final = add_technical_frame(panel5_focus2)
    panel5_final.save(os.path.join(media_dir, "fig5_code_variables_start.png"))

    # --- FIGURA 6: Asignación de Clips en CatControl (Inspector) ---
    print("Generando Figura 6: Clips Asignados en Inspector...")
    f6_raw = extract_frame(1056, "raw_fig6.png")
    img6 = Image.open(f6_raw)
    panel6 = crop_image(img6, (1440, 500, 1918, 740))
    panel6_focus = draw_focus_box(panel6, (12, 135, 465, 225), label="Clips Enlazados: Jump Clip & Walk Clip", color=(27, 54, 93, 255), border_width=3)
    draw6 = ImageDraw.Draw(panel6_focus)
    draw_arrow(draw6, start=(420, 100), end=(455, 150), color=(27, 54, 93, 255), width=4, arrowhead_len=18)
    panel6_final = add_technical_frame(panel6_focus)
    panel6_final.save(os.path.join(media_dir, "fig6_inspector_clips_assigned.png"))

    # --- FIGURA 7: Implementación de Audio de Salto (PlayOneShot) ---
    print("Generando Figura 7: Código PlayOneShot Salto...")
    f7_raw = extract_frame(1190, "raw_fig7.png")
    img7 = Image.open(f7_raw)
    panel7 = crop_image(img7, (35, 520, 1400, 830))
    panel7_focus = draw_focus_box(panel7, (50, 50, 800, 270), label="Disparo de Salto: audioSource.PlayOneShot(jumpClip)", color=(27, 54, 93, 255), border_width=3)
    panel7_final = add_technical_frame(panel7_focus)
    panel7_final.save(os.path.join(media_dir, "fig7_code_jump_oneshot.png"))

    # --- FIGURA 8 (GIF): Prueba en Modo Play de Salto ---
    print("Generando Figura 8 (GIF): Salto en Modo Play...")
    fig8_gif = os.path.join(media_dir, "fig8_jump_play_mode.gif")
    generate_gif(video, start=1218.0, duration=5.0, output_path=fig8_gif, crop_filter="crop=1240:660:195:68", cfg=DEFAULT_CONFIG)

    # --- FIGURA 9: Implementación de ManageAudioSteps() ---
    print("Generando Figura 9: Código ManageAudioSteps()...")
    f9_raw = extract_frame(1550, "raw_fig9.png")
    img9 = Image.open(f9_raw)
    panel9 = crop_image(img9, (35, 680, 1400, 990))
    panel9_focus = draw_focus_box(panel9, (50, 20, 940, 290), label="Bucle de Pasos de Caminata (loop = true & Play())", color=(27, 54, 93, 255), border_width=3)
    panel9_final = add_technical_frame(panel9_focus)
    panel9_final.save(os.path.join(media_dir, "fig9_code_manage_audio_steps.png"))

    # --- FIGURA 10 (GIF): Prueba en Modo Play de Pasos ---
    print("Generando Figura 10 (GIF): Pasos en Modo Play...")
    fig10_gif = os.path.join(media_dir, "fig10_walk_play_mode.gif")
    generate_gif(video, start=1598.0, duration=5.0, output_path=fig10_gif, crop_filter="crop=1240:660:195:68", cfg=DEFAULT_CONFIG)

    # --- FIGURA 11: Detección de Anomalía (Consola Limpia pero Audio en Conflicto) ---
    print("Generando Figura 11: Anomalía de Audio y Consola...")
    f11_raw = extract_frame(1635, "raw_fig11.png")
    img11 = Image.open(f11_raw)
    panel11 = crop_image(img11, (0, 735, 1440, 990))
    panel11_focus = draw_focus_box(panel11, (960, 25, 1420, 65), label="Consola (0 Errores) - Conflicto Lógico en AudioSource", color=(230, 57, 70, 255), border_width=3)
    draw11 = ImageDraw.Draw(panel11_focus)
    draw_arrow(draw11, start=(920, 45), end=(955, 45), color=(230, 57, 70, 255), width=4, arrowhead_len=18)
    panel11_final = add_technical_frame(panel11_focus)
    panel11_final.save(os.path.join(media_dir, "fig11_anomaly_audio_conflict.png"))

    # --- FIGURA 12: Solución Defensiva de Limpieza y Reseteo ---
    print("Generando Figura 12: Código de Limpieza Defensiva...")
    f12_raw = extract_frame(1835, "raw_fig12.png")
    img12 = Image.open(f12_raw)
    panel12 = crop_image(img12, (35, 520, 1400, 870))
    panel12_focus = draw_focus_box(panel12, (50, 60, 940, 270), label="Limpieza Defensiva: audioSource.Stop() & clip = null", color=(40, 167, 69, 255), border_width=3)
    draw12 = ImageDraw.Draw(panel12_focus)
    draw_arrow(draw12, start=(1080, 160), end=(945, 160), color=(40, 167, 69, 255), width=4, arrowhead_len=18)
    panel12_final = add_technical_frame(panel12_focus)
    panel12_final.save(os.path.join(media_dir, "fig12_code_defensive_cleanup.png"))

    # --- FIGURA 13 (GIF): Demostración Final Armónica (Caminar + Saltar) ---
    print("Generando Figura 13 (GIF): Armonía Final en Modo Play...")
    fig13_gif = os.path.join(media_dir, "fig13_final_harmony.gif")
    generate_gif(video, start=1874.0, duration=5.5, output_path=fig13_gif, crop_filter="crop=1240:660:195:68", cfg=DEFAULT_CONFIG)

    # --- FIGURA 14: Arquitectura Final en el Inspector ---
    print("Generando Figura 14: Inspector Final de Mango...")
    f14_raw = extract_frame(1876, "raw_fig14.png")
    img14 = Image.open(f14_raw)
    panel14 = crop_image(img14, (1440, 40, 1918, 970))
    panel14_focus = draw_focus_box(panel14, (12, 230, 465, 920), label="Arquitectura de Componentes Consolidada", color=(27, 54, 93, 255), border_width=3)
    panel14_final = add_technical_frame(panel14_focus)
    panel14_final.save(os.path.join(media_dir, "fig14_inspector_final_architecture.png"))

    print("✓ Todas las 14 figuras (estáticas anotadas y GIFs optimizados) fueron generadas con éxito!")

if __name__ == "__main__":
    generate_enhanced_images()
