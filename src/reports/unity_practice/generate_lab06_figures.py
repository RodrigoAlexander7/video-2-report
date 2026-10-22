import os
import subprocess
from PIL import Image, ImageDraw
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.append(os.path.join(project_root, ".agents/skills/figure-enhancer/scripts"))
from enhance_image import crop_image, draw_focus_box, draw_arrow, add_technical_frame

def generate_enhanced_images():
    media_dir = os.path.join(project_root, "output/IDSE/lab06/figures")
    os.makedirs(media_dir, exist_ok=True)
    video = os.path.join(project_root, "inputs/IDSE/lab06/video_lab_unity.mp4")

    # Helper para extraer frame en segundos específicos
    def extract_frame(ss_time, out_name):
        out_path = os.path.join(media_dir, out_name)
        subprocess.run([
            "ffmpeg", "-y", "-ss", str(ss_time), "-i", video, "-vframes", "1", out_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return out_path

    # --- FIGURA 1: Estado inicial sin rotación orientada ---
    print("Generando Figura 1...")
    f1_raw = extract_frame(15, "raw_fig1.png")
    img1 = Image.open(f1_raw)
    panel1 = crop_image(img1, (195, 68, 1435, 703))
    panel1 = add_technical_frame(panel1)
    panel1.save(os.path.join(media_dir, "fig1_prev_state.png"))

    # --- FIGURA 2: Declaración de variables y Start() ---
    print("Generando Figura 2...")
    f2_raw = extract_frame(105, "raw_fig2.png")
    img2 = Image.open(f2_raw)
    panel2 = crop_image(img2, (35, 70, 1400, 480))
    # Focus box en variables de control
    panel2_focus = draw_focus_box(panel2, (50, 40, 680, 130), label="Variables de Control y Rigidbody", color=(27, 54, 93, 255), border_width=3)
    panel2_final = add_technical_frame(panel2_focus)
    panel2_final.save(os.path.join(media_dir, "fig2_code_variables.png"))

    # --- FIGURA 3: transform.Rotate sin Time.deltaTime ---
    print("Generando Figura 3...")
    f3_raw = extract_frame(105, "raw_fig3.png")
    img3 = Image.open(f3_raw)
    panel3 = crop_image(img3, (35, 380, 1400, 780))
    panel3_focus = draw_focus_box(panel3, (50, 140, 850, 310), label="transform.Rotate() directo (Sin Time.deltaTime)", color=(230, 57, 70, 255), border_width=3)
    draw3 = ImageDraw.Draw(panel3_focus)
    draw_arrow(draw3, start=(980, 160), end=(860, 200), color=(230, 57, 70, 255), width=4, arrowhead_len=18)
    panel3_final = add_technical_frame(panel3_focus)
    panel3_final.save(os.path.join(media_dir, "fig3_code_rotate.png"))

    # --- FIGURA 5: Ventana Stats con 229.9 FPS ---
    print("Generando Figura 5...")
    f5_raw = extract_frame(345, "raw_fig5.png")
    img5 = Image.open(f5_raw)
    panel5 = crop_image(img5, (750, 40, 1435, 430))
    # En el recorte, la ventana Statistics está aproximadamente en x: 130..680, y: 30..380
    panel5_focus = draw_focus_box(panel5, (130, 70, 670, 170), label="229.9 FPS (Falta de Independencia de Frames)", color=(230, 57, 70, 255), border_width=4)
    draw5 = ImageDraw.Draw(panel5_focus)
    draw_arrow(draw5, start=(80, 115), end=(125, 115), color=(230, 57, 70, 255), width=4, arrowhead_len=18)
    panel5_final = add_technical_frame(panel5_focus)
    panel5_final.save(os.path.join(media_dir, "fig5_stats_panel.png"))

    # --- FIGURA 6: Código con Time.deltaTime ---
    print("Generando Figura 6...")
    f6_raw = extract_frame(415, "raw_fig6.png")
    img6 = Image.open(f6_raw)
    panel6 = crop_image(img6, (35, 380, 1400, 780))
    panel6_focus = draw_focus_box(panel6, (50, 140, 1050, 310), label="Solución: Factor * Time.deltaTime", color=(40, 167, 69, 255), border_width=3)
    draw6 = ImageDraw.Draw(panel6_focus)
    draw_arrow(draw6, start=(1180, 180), end=(1060, 205), color=(40, 167, 69, 255), width=4, arrowhead_len=18)
    panel6_final = add_technical_frame(panel6_focus)
    panel6_final.save(os.path.join(media_dir, "fig6_code_deltatime.png"))

    # --- FIGURA 9: Código AddRelativeForce ---
    print("Generando Figura 9...")
    f9_raw = extract_frame(685, "raw_fig9.png")
    img9 = Image.open(f9_raw)
    panel9 = crop_image(img9, (35, 420, 1400, 880))
    panel9_focus = draw_focus_box(panel9, (50, 190, 880, 380), label="Fuerza Física Local: rb.AddRelativeForce", color=(27, 54, 93, 255), border_width=3)
    panel9_final = add_technical_frame(panel9_focus)
    panel9_final.save(os.path.join(media_dir, "fig9_code_addrelativeforce.png"))

    # --- FIGURA 10: Gizmo Eje Z Invertido en Scene View ---
    print("Generando Figura 10...")
    f10_raw = extract_frame(888, "raw_fig10.png")
    img10 = Image.open(f10_raw)
    panel10 = crop_image(img10, (200, 80, 1300, 720))
    # Mango en el centro. El Gizmo con flecha azul está en el torso apuntando a la derecha
    panel10_focus = draw_focus_box(panel10, (280, 260, 580, 480), label="Gizmo Z (Azul) Invertido hacia la Cola", color=(230, 57, 70, 255), border_width=3)
    draw10 = ImageDraw.Draw(panel10_focus)
    # Flecha apuntando a la flecha azul del gizmo
    draw_arrow(draw10, start=(680, 370), end=(585, 370), color=(230, 57, 70, 255), width=4, arrowhead_len=18)
    panel10_final = add_technical_frame(panel10_focus)
    panel10_final.save(os.path.join(media_dir, "fig10_z_axis_gizmo.png"))

    # --- FIGURA 11: Código final con vectores invertidos ---
    print("Generando Figura 11...")
    f11_raw = extract_frame(875, "raw_fig11.png")
    img11 = Image.open(f11_raw)
    panel11 = crop_image(img11, (35, 460, 1400, 920))
    panel11_focus = draw_focus_box(panel11, (50, 210, 880, 410), label="Ajuste Defensivo: W -> Vector3.back / S -> Vector3.forward", color=(27, 54, 93, 255), border_width=3)
    panel11_final = add_technical_frame(panel11_focus)
    panel11_final.save(os.path.join(media_dir, "fig11_code_final_inverted.png"))

    # --- FIGURA 13: Configuración completa en el Inspector ---
    print("Generando Figura 13...")
    f13_raw = extract_frame(805, "raw_fig13.png")
    img13 = Image.open(f13_raw)
    panel13 = crop_image(img13, (1440, 40, 1918, 970))
    panel13_focus = draw_focus_box(panel13, (15, 330, 465, 890), label="Componentes: Rigidbody, Freeze Rotation, CatControl", color=(27, 54, 93, 255), border_width=3)
    panel13_final = add_technical_frame(panel13_focus)
    panel13_final.save(os.path.join(media_dir, "fig13_inspector_setup.png"))

    print("✓ Todas las 9 figuras estáticas mejoradas generadas con éxito!")

if __name__ == "__main__":
    generate_enhanced_images()
