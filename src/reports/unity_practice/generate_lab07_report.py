import os
import sys
import argparse
import docx
from docx.shared import Pt, Inches

if not __package__:
    # Ejecución directa: exponer la raíz del proyecto para resolver config y src.*
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from config import ReportConfig
from src.docx_engine.cell_helpers import (
    apply_cell_margins,
    add_cell_heading_1,
    add_cell_heading_2,
    add_cell_body_paragraph,
    add_cell_bullet_point,
    add_cell_code_block,
    add_cell_image_with_caption,
)

def build_lab07_report(
    template_path: str,
    output_path: str,
    media_dir: str,
    cfg: ReportConfig = ReportConfig()
):
    print(f"Cargando plantilla desde: {template_path}")
    doc = docx.Document(template_path)
    table = doc.tables[0]

    # --- 1. ENCABEZADO Y METADATOS DE LA PRÁCTICA ---
    # Título de la práctica
    cell_tit = table.rows[2].cells[1]
    cell_tit.text = "Trabajo con Audio Source y Sonidos"
    p_tit = cell_tit.paragraphs[0]
    p_tit.runs[0].font.name = cfg.font_family_body
    p_tit.runs[0].font.size = Pt(cfg.font_size_body_pt)
    p_tit.runs[0].bold = True

    # Número de práctica
    cell_num = table.rows[3].cells[1]
    cell_num.text = "07"
    p_num = cell_num.paragraphs[0]
    p_num.runs[0].font.name = cfg.font_family_body
    p_num.runs[0].font.size = Pt(cfg.font_size_body_pt)
    p_num.runs[0].bold = True

    # Fecha de presentación
    cell_fec = table.rows[4].cells[1]
    cell_fec.text = "16/10/2026"
    p_fec = cell_fec.paragraphs[0]
    p_fec.runs[0].font.name = cfg.font_family_body
    p_fec.runs[0].font.size = Pt(cfg.font_size_body_pt)

    # --- 2. SECCIÓN: RESULTADOS Y PRUEBAS (TUTORIAL PROGRESIVO POR ETAPAS) ---
    cell_ej = table.rows[9].cells[0]
    cell_ej.text = ""
    apply_cell_margins(cell_ej)

    add_cell_heading_1(cell_ej, "EJERCICIOS RESUELTOS: TUTORIAL DE AUDIO SOURCE Y SONIDOS (CatControl)", cfg)

    add_cell_body_paragraph(cell_ej, 
        "El presente tutorial describe detalladamente la investigación, implementación técnica y validación experimental "
        "del sistema acústico y efectos sonoros interactivos para el personaje tridimensional ('Mango') en Unity 6. "
        "El flujo de trabajo comprende desde el estudio de licenciamiento libre de recursos de audio en repositorios comunitarios (Freesound.org), "
        "la integración y parametrización rigurosa del componente nativo AudioSource en el Inspector, hasta la programación modular en C# "
        "del disparo instantáneo de sonido de salto mediante PlayOneShot, la reproducción continua en bucle de pasos de locomoción mediante bucles "
        "condicionales en Update(), y la resolución técnica defensiva de un conflicto de concurrencia al reutilizar un único AudioSource. "
        "La guía se organiza en 5 etapas secuenciales, con fragmentos de código incrementales y evidencia visual anotada en cada fase.",
        cfg
    )

    # =========================================================================
    # ETAPA 1
    # =========================================================================
    add_cell_heading_2(cell_ej, "Etapa 1: Investigación de Licencias y Adquisición de Efectos de Sonido (Freesound.org)", cfg)
    add_cell_body_paragraph(cell_ej, 
        "En esta etapa inicial se investigan las fuentes de recursos sonoros comunitarios, se evalúan los diferentes marcos de licencias libres "
        "para desarrollo de software interactivo y se obtienen los archivos de audio requeridos para el personaje.",
        cfg
    )

    # Subpaso 1.1
    add_cell_bullet_point(cell_ej, "Paso 1.1: Exploración y Evaluación de Licencias Libres en Freesound.org. ", 
        "Para dotar de dinamismo sonoro al personaje (un gato samurái), se recurre a la plataforma comunitaria Freesound.org. "
        "Durante la búsqueda de efectos de salto y pasos, se examinan rigurosamente las opciones del panel de licencias del repositorio: "
        "Creative Commons 0 (CC0, dominio público sin requisitos de atribución), Attribution (CC BY, uso comercial permitido con crédito obligatorio), "
        "Attribution NonCommercial (CC BY-NC, restringido exclusivamente a proyectos no monetizados), Sampling Plus (permite remezcla y transformación, "
        "pero prohíbe la redistribución intacta comercial) y el distintivo 'Approved for Free Cultural Works'. Para este laboratorio se seleccionan clips bajo "
        "licencia Creative Commons 0 (como 'jump_land.wav'), lo que garantiza libertad total de uso, modificación y distribución sin riesgos legales.", 
        cfg, level=1)
    
    add_cell_image_with_caption(cell_ej,
        os.path.join(media_dir, "fig1_freesound_licenses.png"),
        "Figura 1: Interfaz de Freesound.org con filtrado de licencias libres (CC0, CC BY, Sampling+) y selección del clip 'jump_land.wav'.",
        cfg)

    # Subpaso 1.2
    add_cell_bullet_point(cell_ej, "Paso 1.2: Descarga e Importación de Clips en la Estructura del Proyecto (Assets/Audio). ", 
        "Tras descargar los archivos en formato de audio de alta fidelidad (.wav), se renombran de manera estandarizada y descriptiva como "
        "'Jump' (para el impulso vertical) y 'footstep' (para las pisadas de caminata). Posteriormente, se arrastran hacia la carpeta de proyecto "
        "'Assets/Audio' en Unity 6. Al inspeccionar los assets en el panel Project, Unity genera automáticamente sus ondas sonoras (waveforms) "
        "y los expone como recursos nativos de tipo AudioClip listos para ser reproducidos o configurados con bucles de preescucha.", 
        cfg, level=1)

    add_cell_image_with_caption(cell_ej,
        os.path.join(media_dir, "fig2_unity_assets_audio.png"),
        "Figura 2: Explorador de proyecto de Unity mostrando los recursos AudioClip ('footstep' y 'Jump') importados dentro de Assets/Audio.",
        cfg)

    # =========================================================================
    # ETAPA 2
    # =========================================================================
    add_cell_heading_2(cell_ej, "Etapa 2: Incorporación y Parametrización del Componente AudioSource en el Inspector", cfg)
    add_cell_body_paragraph(cell_ej, 
        "En esta etapa se vincula la fuente emisora de sonido al GameObject del personaje en la escena y se calibran sus propiedades acústicas básicas.",
        cfg
    )

    # Subpaso 2.1
    add_cell_bullet_point(cell_ej, "Paso 2.1: Asignación del Componente AudioSource al GameObject Mango. ", 
        "En la jerarquía de Unity, se selecciona el GameObject raíz del personaje ('Mango'). En la ventana Inspector, se presiona el botón "
        "'Add Component', se navega a la categoría 'Audio' y se selecciona 'Audio Source'. Esta acción adhiere la entidad emisora del motor de audio "
        "de Unity al personaje, permitiendo que transmita vibraciones acústicas al Audio Listener presente en la escena.", 
        cfg, level=1)

    add_cell_image_with_caption(cell_ej,
        os.path.join(media_dir, "fig3_audiosource_component.png"),
        "Figura 3: Adición del componente Audio Source al GameObject 'Mango' desde el menú de componentes de Unity.",
        cfg)

    # Subpaso 2.2
    add_cell_bullet_point(cell_ej, "Paso 2.2: Configuración de Parámetros Operativos (Play On Awake, Spatial Blend 2D y Prioridad). ", 
        "Al inspeccionar las propiedades de Audio Source, se realiza un ajuste crítico: se desmarca la casilla 'Play On Awake'. "
        "Si esta propiedad permaneciera activa, el audio sonaría automáticamente en cuanto el objeto despierte o se instancie en la escena, "
        "lo cual es indeseable para efectos de juego que deben responder estrictamente a eventos del usuario (como presionar Space o teclas de dirección). "
        "Asimismo, se ajusta el control deslizante 'Spatial Blend' completamente a la izquierda en 0.0f (sonido 2D). Dado que la cámara principal "
        "seguirá rígidamente al gato manteniendo una distancia relativa constante, no se requiere atenuación volumétrica tridimensional por distancia (3D Sound), "
        "evitando pérdidas de inteligibilidad auditiva o cálculos de atenuación innecesarios.", 
        cfg, level=1)

    add_cell_image_with_caption(cell_ej,
        os.path.join(media_dir, "fig4_audiosource_parameters.png"),
        "Figura 4: Calibración de parámetros en el Inspector: casilla 'Play On Awake' desmarcada y 'Spatial Blend' fijado en 0.0 (Audio 2D).",
        cfg)

    # =========================================================================
    # ETAPA 3
    # =========================================================================
    add_cell_heading_2(cell_ej, "Etapa 3: Integración en C#: Declaración de Variables, Enlace de Referencias y Sonido de Salto (PlayOneShot)", cfg)
    add_cell_body_paragraph(cell_ej, 
        "En esta etapa se conecta la arquitectura lógica del script C# 'CatControl.cs' con el subsistema de audio, configurando el disparo acústico de salto.",
        cfg
    )

    # Subpaso 3.1
    add_cell_bullet_point(cell_ej, "Paso 3.1: Declaración de Variables Públicas de AudioClip y Configuración en Start(). ", 
        "Se abre el archivo 'CatControl.cs' en el editor de código. Para gestionar de forma desacoplada los efectos sonoros, se declaran dos campos públicos: "
        "'public AudioClip jumpClip;' y 'public AudioClip walkClip;'. Además, se declara la referencia privada 'private AudioSource audioSource;'. "
        "En el método Start(), se captura la instancia del componente mediante 'GetComponent<AudioSource>()'. Como medida de programación defensiva "
        "y para asegurar la trazabilidad del código sin depender exclusivamente del Inspector, se inicializan por código sus banderas fundamentales: "
        "'playOnAwake = false', 'loop = false' y 'spatialBlend = 0.0f':", 
        cfg, level=1)

    code_step3_1 = """// CatControl.cs - Fragmento Incremental: Variables de Audio y Captura en Start()
using UnityEngine;

public class CatControl : MonoBehaviour
{
    // Variables previas de física y locomoción...
    public float thrust = 20f;
    public float rotationSpeed = 100f;
    public float moveSpeed = 10f; 
    public bool isGrounded = true;

    // Declaración de variables de audio
    public AudioClip jumpClip;
    public AudioClip walkClip;

    private AudioSource audioSource;

    void Start()
    {
        rb = GetComponent<Rigidbody>();
        rb.freezeRotation = true;

        // Captura e inicialización defensiva del componente AudioSource
        audioSource = GetComponent<AudioSource>();
        audioSource.playOnAwake = false;
        audioSource.loop = false;
        audioSource.spatialBlend = 0.0f; // Sonido estéreo 2D directo
    }
}"""
    add_cell_code_block(cell_ej, code_step3_1, cfg)

    add_cell_image_with_caption(cell_ej,
        os.path.join(media_dir, "fig5_code_variables_start.png"),
        "Figura 5: Código C# en Visual Studio Code declarando los campos de audio y asegurando la configuración en Start().",
        cfg)

    # Subpaso 3.2
    add_cell_bullet_point(cell_ej, "Paso 3.2: Enlace de Referencias de AudioClip en el Inspector de Unity. ", 
        "Al guardar el script y volver a Unity, el componente 'Cat Control (Script)' expone dos nuevas ranuras serializadas en el Inspector: "
        "'Jump Clip' y 'Walk Clip'. Se arrastra el recurso 'Jump' desde Assets/Audio hacia 'Jump Clip' y el recurso 'footstep' hacia 'Walk Clip', "
        "estableciendo el puente directo entre los assets binarios y el controlador lógico:", 
        cfg, level=1)

    add_cell_image_with_caption(cell_ej,
        os.path.join(media_dir, "fig6_inspector_clips_assigned.png"),
        "Figura 6: Ranuras 'Jump Clip' y 'Walk Clip' enlazadas con los assets de audio correspondientes en el Inspector de Unity.",
        cfg)

    # Subpaso 3.3
    add_cell_bullet_point(cell_ej, "Paso 3.3: Implementación del Disparo de Audio de Salto mediante AudioSource.PlayOneShot(). ", 
        "En el método Update(), dentro del bloque condicional que evalúa la pulsación de la barra espaciadora ('Input.GetKey(KeyCode.Space) && isGrounded'), "
        "se añade la instrucción de reproducción acústica. Se verifica que 'jumpClip' no sea nulo y se invoca el método 'audioSource.PlayOneShot(jumpClip)'. "
        "El método PlayOneShot es la función especializada de Unity para reproducir un efecto no acumulativo y de duración finita sin alterar el clip asignado "
        "por defecto ni interrumpir bruscamente otras fuentes sonoras en curso:", 
        cfg, level=1)

    code_step3_3 = """// CatControl.cs - Fragmento Incremental: Audio de Salto en Update()
    void Update()
    {
        if (Input.GetKey(KeyCode.Space) && isGrounded)
        {
            rb.AddForce(Vector3.up * thrust, ForceMode.Impulse);
            isGrounded = false;

            // Reproducción instantánea del audio de salto mediante PlayOneShot
            if (jumpClip != null)
            {
                audioSource.PlayOneShot(jumpClip);
            }
        }
        // Resto de controles de rotación y traslación...
    }"""
    add_cell_code_block(cell_ej, code_step3_3, cfg)

    add_cell_image_with_caption(cell_ej,
        os.path.join(media_dir, "fig7_code_jump_oneshot.png"),
        "Figura 7: Implementación de la instrucción audioSource.PlayOneShot(jumpClip) en el bloque de salto dentro de Update().",
        cfg)

    # Subpaso 3.4
    add_cell_bullet_point(cell_ej, "Paso 3.4: Validación Experimental del Salto con Audio en Modo Play. ", 
        "Se ejecuta la escena en modo Play en Unity. Al presionar la barra espaciadora, el gato 'Mango' se impulsa verticalmente mediante el vector "
        "de fuerza impulsiva 'Vector3.up * thrust' y, de forma simultánea e inmediata, se reproduce con total nitidez el clip de audio de salto. "
        "El sonido reproduce el impacto ágil y el sonido de su equipamiento, culminando de manera natural al alcanzar el aire:", 
        cfg, level=1)

    add_cell_image_with_caption(cell_ej,
        os.path.join(media_dir, "fig8_jump_play_mode.gif"),
        "Figura 8 (GIF Animado): Verificación en modo Play del personaje saltando con reproducción exitosa del efecto sonoro.",
        cfg)

    # =========================================================================
    # ETAPA 4
    # =========================================================================
    add_cell_heading_2(cell_ej, "Etapa 4: Implementación del Bucle de Pasos (Footsteps Loop) para la Locomoción Continua", cfg)
    add_cell_body_paragraph(cell_ej, 
        "En esta etapa se programa el bucle sonoro continuo de pisadas que acompaña el avance y retroceso del personaje sobre el terreno.",
        cfg
    )

    # Subpaso 4.1
    add_cell_bullet_point(cell_ej, "Paso 4.1: Programación del Método ManageAudioSteps() y Control de Bucle de Caminata. ", 
        "A diferencia del salto (evento puntual), la locomoción requiere un sonido sostenido en bucle mientras el jugador mantenga presionada la tecla 'W' o 'S' "
        "y el personaje esté efectivamente en contacto con el suelo. Para modularizar la arquitectura, se crea el método privado 'ManageAudioSteps()' invocado "
        "al final de Update(). En este método: "
        "1. Se aplica una cláusula de guarda inicial: si 'audioSource == null' o 'walkClip == null', la función retorna inmediatamente. "
        "2. Se evalúa la condición de movimiento: 'verticalInput != 0f && isGrounded'. Si se cumple y el audio no está sonando ('!audioSource.isPlaying'), "
        "se asigna 'audioSource.clip = walkClip', se activa 'audioSource.loop = true' y se ejecuta 'audioSource.Play()'. "
        "3. En la rama 'else' (si el jugador suelta las teclas o salta perdiendo contacto con el piso), se evalúa si el audio en reproducción coincide "
        "con 'walkClip', invocando 'audioSource.Stop()' para cesar las pisadas instantáneamente:", 
        cfg, level=1)

    code_step4_1 = """// CatControl.cs - Fragmento Incremental: Gestión Modular de Pasos en Bucle
    void Update()
    {
        // ... Lectura de rotación y verticalInput ...

        ManageAudioSteps();
    }

    private void ManageAudioSteps()
    {
        if (audioSource == null || walkClip == null) return;

        // Si hay entrada de traslación y el personaje está en el suelo
        if (verticalInput != 0f && isGrounded)
        {
            if (!audioSource.isPlaying)
            {
                audioSource.clip = walkClip;
                audioSource.loop = true;
                audioSource.Play();
            }
        }
        else
        {
            // Detener el bucle de pasos si el gato se detiene o está en el aire
            if (audioSource.isPlaying && audioSource.clip == walkClip)
            {
                audioSource.Stop();
            }
        }
    }"""
    add_cell_code_block(cell_ej, code_step4_1, cfg)

    add_cell_image_with_caption(cell_ej,
        os.path.join(media_dir, "fig9_code_manage_audio_steps.png"),
        "Figura 9: Método ManageAudioSteps() controlando el bucle condicional de pisadas según verticalInput y el estado isGrounded.",
        cfg)

    # Subpaso 4.2
    add_cell_bullet_point(cell_ej, "Paso 4.2: Verificación de Locomoción y Pasos Rítmicos en Modo Play. ", 
        "Se recompila el script y se prueba en Unity. Al avanzar ('W') o retroceder ('S'), el efecto de pasos 'footstep' se reproduce rítmicamente en bucle "
        "mientras el personaje se desplaza por el terreno de pasto. Al soltar las teclas, el sonido cesa inmediatamente, transmitiendo una sensación cinemática "
        "sólida y reactiva:", 
        cfg, level=1)

    add_cell_image_with_caption(cell_ej,
        os.path.join(media_dir, "fig10_walk_play_mode.gif"),
        "Figura 10 (GIF Animado): Prueba en modo Play de la caminata del personaje con reproducción fluida del bucle de pasos.",
        cfg)

    # =========================================================================
    # ETAPA 5
    # =========================================================================
    add_cell_heading_2(cell_ej, "Etapa 5: Diagnóstico del Conflicto de Concurrencia de Audio, Solución Defensiva y Consolidación Final", cfg)
    add_cell_body_paragraph(cell_ej, 
        "En esta etapa final se detecta una anomalía de concurrencia al reutilizar el componente AudioSource, se implementa una rutina de reseteo "
        "defensivo y se consolida el código de producción completo.",
        cfg
    )

    # Subpaso 5.1
    add_cell_bullet_point(cell_ej, "Paso 5.1: Detección y Análisis de la Anomalía (Conflicto de Estado en AudioSource Único). ", 
        "Durante las pruebas combinadas de juego, se descubrió un fallo sutil pero crítico: si el usuario camina (activando el bucle de pasos) "
        "y acto seguido presiona la barra espaciadora para saltar en carrera, el personaje ejecuta el salto físico en el aire, ¡pero el efecto de sonido "
        "de salto deja de escucharse por completo! Al abrir la ventana Console de Unity, no se registra ningún error ni excepción (0 errores, 0 advertencias). "
        "Causa raíz: Dado que ambos sonidos comparten la misma instancia de AudioSource para economizar recursos, el método 'ManageAudioSteps()' asignó "
        "'audioSource.clip = walkClip' con 'loop = true'. Al ingresar a la condición de salto, la instrucción 'PlayOneShot(jumpClip)' colisiona con el canal "
        "ocupado por el clip de pasos que no fue liberado ni reseteado limpiamente en su estado interno, provocando que el disparo de salto sea sofocado:", 
        cfg, level=1)

    add_cell_image_with_caption(cell_ej,
        os.path.join(media_dir, "fig11_anomaly_audio_conflict.png"),
        "Figura 11: Vista de Unity y consola de depuración limpia (0 errores) durante la manifestación del conflicto de concurrencia de audio.",
        cfg)

    # Subpaso 5.2
    add_cell_bullet_point(cell_ej, "Paso 5.2: Implementación de la Rutina Defensiva de Limpieza y Reseteo (Stop() y clip = null). ", 
        "Para solucionar este conflicto de manera robusta sin incurrir en el costo de instanciar múltiples componentes AudioSource, se refactoriza "
        "el bloque de salto en Update(). Se introduce una doble validación de nulidad ('jumpClip != null && audioSource != null') y se ejecutan dos órdenes "
        "de saneamiento previas al disparo: "
        "1. 'audioSource.Stop()': Detiene de inmediato cualquier reproducción o bucle en curso (evitando que el sonido de pasos siga ejecutándose en el aire). "
        "2. 'audioSource.clip = null;': Desvincula el clip previo del búfer del canal de audio. "
        "Tras esta purga defensiva, se invoca 'audioSource.PlayOneShot(jumpClip)', garantizando que el canal esté 100% limpio y disponible para emitir el salto:", 
        cfg, level=1)

    code_step5_2 = """// CatControl.cs - Fragmento Incremental: Rutina Defensiva de Limpieza de Audio
        if (Input.GetKey(KeyCode.Space) && isGrounded)
        {
            rb.AddForce(Vector3.up * thrust, ForceMode.Impulse);
            isGrounded = false;

            if (jumpClip != null && audioSource != null)
            {
                audioSource.Stop();          // Detener bucles de pasos activos
                audioSource.clip = null;     // Limpiar canal para evitar colisión de clips
                if (jumpClip != null)
                {
                    audioSource.PlayOneShot(jumpClip); // Disparo garantizado
                }
            }
        }"""
    add_cell_code_block(cell_ej, code_step5_2, cfg)

    add_cell_image_with_caption(cell_ej,
        os.path.join(media_dir, "fig12_code_defensive_cleanup.png"),
        "Figura 12: Implementación de la rutina defensiva con audioSource.Stop() y audioSource.clip = null antes del disparo de salto.",
        cfg)

    # Subpaso 5.3
    add_cell_bullet_point(cell_ej, "Paso 5.3: Demostración Final de Convivencia Sonora en Modo Play (Armonía entre Pasos y Salto). ", 
        "Con la corrección integrada, se valida la escena completa. El jugador puede avanzar de forma continua con pasos rítmicos, saltar en cualquier instante "
        "(donde los pasos se silencian y el salto se reproduce con impecable potencia acústica) y, al volver a aterrizar en el terreno y seguir avanzando, "
        "los pasos se reanudan fluidamente sin ninguna desincronización ni latencia:", 
        cfg, level=1)

    add_cell_image_with_caption(cell_ej,
        os.path.join(media_dir, "fig13_final_harmony.gif"),
        "Figura 13 (GIF Animado): Validación final en modo Play con perfecta coexistencia y armonía acústica entre la locomoción y el salto.",
        cfg)

    # Subpaso 5.4
    add_cell_bullet_point(cell_ej, "Paso 5.4: Arquitectura de Componentes en el Inspector y Código Consolidado. ", 
        "La arquitectura final de 'Mango' integra un Rigidbody (con masa = 3, Freeze Rotation X, Y, Z activado para estabilidad contra torque parásito), "
        "un CapsuleCollider ajustado al cuerpo del gato, el componente nativo AudioSource (Play On Awake = false, Spatial Blend = 0) y el controlador 'CatControl' "
        "con sus clips y parámetros físicos calibrados (Thrust = 20, Rotation Speed = 100, Move Speed = 10, Jump Clip = jump, Walk Clip = footstep):", 
        cfg, level=1)

    add_cell_image_with_caption(cell_ej,
        os.path.join(media_dir, "fig14_inspector_final_architecture.png"),
        "Figura 14: Vista integral del Inspector de Unity mostrando la pila de componentes configurada (Rigidbody, Collider, CatControl y AudioSource).",
        cfg)

    add_cell_body_paragraph(cell_ej, "A continuación se presenta el código fuente completo, consolidado y documentado de la práctica ('CatControl.cs'):", cfg)

    full_code = """using UnityEngine;

public class CatControl : MonoBehaviour
{
    [Header("Parámetros de Física y Locomoción")]
    public float thrust = 20f;             // Fuerza de impulso vertical para el salto
    public float rotationSpeed = 100f;     // Velocidad angular de rotación en grados/segundo
    public float moveSpeed = 10f;          // Velocidad lineal de traslación
    public bool isGrounded = true;         // Bandera de contacto con el suelo

    Rigidbody rb;
    float verticalInput;
    float horizontalInput;

    [Header("Efectos de Audio (Clips)")]
    public AudioClip jumpClip;             // Clip de sonido para el salto puntual
    public AudioClip walkClip;             // Clip de sonido para las pisadas continuas

    private AudioSource audioSource;       // Fuente de emisión acústica única compartida

    void Start()
    {
        rb = GetComponent<Rigidbody>();
        rb.freezeRotation = true;          // Bloqueo de rotación física para control cinemático estable

        // Captura y configuración defensiva de AudioSource por código
        audioSource = GetComponent<AudioSource>();
        audioSource.playOnAwake = false;   // Desactivar reproducción automática al iniciar la escena
        audioSource.loop = false;          // Loop gestionado dinámicamente por lógica de juego
        audioSource.spatialBlend = 0.0f;   // Modo 2D directo (sin atenuación por distancia relativa)
    }

    void Update()
    {
        // 1. Detección y ejecución de salto con audio defensivo
        if (Input.GetKey(KeyCode.Space) && isGrounded)
        {
            rb.AddForce(Vector3.up * thrust, ForceMode.Impulse);
            isGrounded = false;

            if (jumpClip != null && audioSource != null)
            {
                audioSource.Stop();        // Detener cualquier bucle previo (ej. pasos)
                audioSource.clip = null;   // Limpiar canal para garantizar la prioridad del salto
                if (jumpClip != null)
                {
                    audioSource.PlayOneShot(jumpClip);
                }
            }
        }

        // 2. Rotación angular horizontal escalada por Time.deltaTime
        if (Input.GetKey(KeyCode.D))
        {
            transform.Rotate(Vector3.up * rotationSpeed * Time.deltaTime);
        }
        else if (Input.GetKey(KeyCode.A))
        {
            transform.Rotate(Vector3.down * rotationSpeed * Time.deltaTime);
        }

        // 3. Lectura de entrada longitudinal (W = +1 hacia adelante, S = -1 hacia atrás)
        verticalInput = 0f;
        if (Input.GetKey(KeyCode.W)) verticalInput = 1f;
        else if (Input.GetKey(KeyCode.S)) verticalInput = -1f;

        // 4. Gestión dinámica del bucle de pasos
        ManageAudioSteps();
    }

    void FixedUpdate()
    {
        // Cálculo de velocidad física orientada en coordenadas locales hacia donde mira el personaje
        Vector3 forwardVelocity = transform.forward * (verticalInput * moveSpeed);

        // Mantenemos la velocidad vertical (Y) intacta para preservar el efecto de la gravedad y salto
        rb.linearVelocity = new Vector3(forwardVelocity.x, rb.linearVelocity.y, forwardVelocity.z);
    }

    private void ManageAudioSteps()
    {
        if (audioSource == null || walkClip == null) return;

        // Reproducir bucle continuo si el gato se desplaza y está pisando el suelo
        if (verticalInput != 0f && isGrounded)
        {
            if (!audioSource.isPlaying)
            {
                audioSource.clip = walkClip;
                audioSource.loop = true;
                audioSource.Play();
            }
        }
        else
        {
            // Detener las pisadas si el jugador frena o el personaje se encuentra en el aire
            if (audioSource.isPlaying && audioSource.clip == walkClip)
            {
                audioSource.Stop();
            }
        }
    }

    private void OnCollisionEnter(Collision collision)
    {
        // Detección de superficie transitable evaluando la normal del punto de contacto
        foreach (ContactPoint contact in collision.contacts)
        {
            if (contact.normal.y > 0.6f)
            {
                isGrounded = true;
                break;
            }
        }
    }

    private void OnCollisionExit(Collision collision)
    {
        isGrounded = false;
    }
}"""
    add_cell_code_block(cell_ej, full_code, cfg)

    # --- 3. SECCIÓN: CUESTIONARIO TÉCNICO ---
    cell_cue = table.rows[10].cells[0]
    cell_cue.text = ""
    apply_cell_margins(cell_cue)

    add_cell_heading_1(cell_cue, "CUESTIONARIO TÉCNICO", cfg)

    # Pregunta 1
    add_cell_body_paragraph(cell_cue, 
        "¿Qué función realiza el componente Audio Listener de la Cámara principal en Unity?",
        cfg, bold_prefix="Pregunta 1: "
    )
    add_cell_body_paragraph(cell_cue, 
        "El componente Audio Listener actúa como los 'oídos virtuales' del jugador dentro del mundo simulado en Unity. "
        "Su función arquitectónica primordial es servir de receptor e interfaz central entre el subsistema de audio espacial 3D/2D "
        "(alimentado por el backend nativo FMOD de Unity) y los dispositivos de salida de hardware físico del usuario (altavoces, auriculares o sistemas multicanal).",
        cfg
    )
    add_cell_body_paragraph(cell_cue, 
        "En una escena interactiva, todas las fuentes acústicas (Audio Source) emiten señales que viajan por el espacio virtual. "
        "El Audio Listener recopila estas señales y calcula matemáticamente las transformaciones perceptivas en función de su posición relativa, "
        "orientación tridimensional y velocidad (mediante el efecto Doppler): balance estéreo (panning), atenuación por distancia y atenuación direccional. "
        "Por convención estándar, se adhiere a la Cámara Principal (Main Camera) para que el punto de escucha coincida exactamente con la perspectiva "
        "visual del espectador. Cabe destacar que, por diseño del motor, solo puede existir un único Audio Listener activo simultáneamente por escena; "
        "la presencia de múltiples componentes activos genera advertencias en la consola y comportamientos erráticos en la mezcla general.",
        cfg
    )

    # Pregunta 2
    add_cell_body_paragraph(cell_cue, 
        "¿Qué función realiza el componente Audio Source?",
        cfg, bold_prefix="Pregunta 2: "
    )
    add_cell_body_paragraph(cell_cue, 
        "El componente Audio Source cumple el rol de 'altavoz o emisor acústico virtual' en la escena de Unity. "
        "Su responsabilidad técnica es tomar un recurso de audio digital (AudioClip) y reproducirlo en el entorno virtual, "
        "controlando de forma exhaustiva sus parámetros de emisión y modulando su señal antes de que sea percibida por el Audio Listener.",
        cfg
    )
    add_cell_body_paragraph(cell_cue, 
        "Entre las principales capacidades y responsabilidades del Audio Source destacan: "
        "1. Ciclo de Vida de Reproducción: Expone métodos de control por código como Play(), Pause(), Stop() y PlayOneShot(), permitiendo reproducir pistas individuales o disparos rápidos superpuestos. "
        "2. Espacialización Sonora (Spatial Blend): Modula la señal entre sonido puramente 2D (Spatial Blend = 0, donde el volumen es homogéneo y constante sin importar la posición en el mundo) "
        "y sonido posicional 3D (Spatial Blend = 1, donde el motor aplica curvas logarítmicas/lineales de atenuación por distancia física al listener). "
        "3. Enrutamiento y Mezcla (Output Routing): Permite direccionar el flujo de audio hacia canales o grupos específicos de un AudioMixer para aplicar ecualización, reverberación y balance dinámico. "
        "4. Modulación Paramétrica: Gestiona volumen (amplitud), tono (pitch/frecuencia), paneo estéreo, repetición continua (loop) y prioridad de desalojo en caso de saturación de canales de voz en la CPU.",
        cfg
    )

    # Pregunta 3
    add_cell_body_paragraph(cell_cue, 
        "¿En qué situaciones debemos mantener Play On Awake seleccionado?",
        cfg, bold_prefix="Pregunta 3: "
    )
    add_cell_body_paragraph(cell_cue, 
        "La propiedad 'Play On Awake' debe mantenerse seleccionada exclusivamente en aquellas situaciones donde el sonido deba comenzar "
        "a reproducirse de manera automática e inmediata en el instante en que el GameObject se activa o se inicializa en la escena (durante las fases Awake/OnEnable), "
        "sin requerir la invocación previa de ninguna lógica programática o evento interactivo.",
        cfg
    )
    add_cell_body_paragraph(cell_cue, 
        "Los escenarios típicos donde es correcto y conveniente mantener Play On Awake activo incluyen: "
        "a) Música de Fondo (BGM): Bandas sonoras de menús principales, temas ambientales de niveles o música cinemática continua. "
        "b) Audio Ambiental Sostenido (Ambience SFX): Efectos de entorno de la naturaleza o la locación como el viento en la pradera, el oleaje del mar, "
        "el fluir de un río, el crepitar de antorchas, el zumbido de maquinaria industrial pesada o lluvia constante. "
        "c) Fanfarrias de Inicio o Introducción: Sonidos de entrada triunfal o campanas introductorias que marcan el arranque automático del nivel. "
        "Por el contrario, para efectos de sonido reactivos (SFX interactivos como pasos, disparos, impactos de daño, recolección de monedas o salto), "
        "Play On Awake DEBE mantenerse desmarcado obligatoriamente, ya que de lo contrario el clip sonaría de forma caótica y errónea al cargar la escena.",
        cfg
    )

    # Pregunta 4
    add_cell_body_paragraph(cell_cue, 
        "Investiga las diferentes licencias libres que existen y cuáles son los requisitos para el uso de archivos de sonido e imagen.",
        cfg, bold_prefix="Pregunta 4: "
    )
    add_cell_body_paragraph(cell_cue, 
        "En la industria del software, videojuegos y producción multimedia, el uso de recursos abiertos de audio e imagen está regido "
        "por diversos marcos jurídicos y modelos de licenciamiento libre. Conocer sus especificaciones es mandatorio para garantizar la legalidad del proyecto "
        "y evitar contingencias por infracción de derechos patrimoniales de autor:",
        cfg
    )
    add_cell_bullet_point(cell_cue, 
        "Familia Creative Commons (CC): ", 
        "Es el estándar mundial más extendido para activos artísticos, audio e imagen. Se articula a partir de 4 condiciones fundamentales combinables:", 
        cfg, level=1)
    add_cell_bullet_point(cell_cue, 
        "• Creative Commons Zero (CC0 1.0 Universal - Dominio Público): ", 
        "El autor renuncia a todos sus derechos de autor a nivel global. Permite usar, copiar, modificar, remezclar, distribuir y comercializar el archivo "
        "sin necesidad de solicitar permiso ni otorgar créditos o atribución (máxima libertad para producción comercial).", 
        cfg, level=2)
    add_cell_bullet_point(cell_cue, 
        "• CC BY (Atribución): ", 
        "Permite cualquier uso (incluyendo explotación comercial y modificaciones profundas). Requisito indispensable: Dar crédito adecuado al autor original, "
        "proporcionar un enlace a la licencia e indicar si se realizaron cambios sobre el archivo.", 
        cfg, level=2)
    add_cell_bullet_point(cell_cue, 
        "• CC BY-SA (Atribución - CompartirIgual / Copyleft): ", 
        "Permite uso comercial y obras derivadas siempre que se otorgue atribución y cualquier obra derivada o remix se distribuya estrictamente bajo la misma licencia idéntica.", 
        cfg, level=2)
    add_cell_bullet_point(cell_cue, 
        "• CC BY-NC (Atribución - NoComercial): ", 
        "Permite copiar, adaptar y distribuir el asset dando créditos, pero prohíbe terminantemente su utilización en obras monetizadas, videojuegos con precio o productos comerciales.", 
        cfg, level=2)
    add_cell_bullet_point(cell_cue, 
        "• CC BY-ND (Atribución - SinDerivadas): ", 
        "Permite la redistribución comercial y no comercial, pero el archivo debe permanecer inalterado en su forma original (prohíbe recortes, remezclas o edición visual/acústica).", 
        cfg, level=2)
    
    add_cell_bullet_point(cell_cue, 
        "Licencias Específicas de Audio y Definiciones Culturales: ", 
        "En repositorios de sonido como Freesound.org existen licencias complementarias:", 
        cfg, level=1)
    add_cell_bullet_point(cell_cue, 
        "• Sampling Plus 1.0 (Creative Commons): ", 
        "Autoriza a extraer muestras (samples), recortar y transformar partes del audio para integrarlas en una nueva creación artística, "
        "pero prohíbe revender o redistribuir copias intactas del archivo original, y exige que la obra derivada sea sin fines comerciales.", 
        cfg, level=2)
    add_cell_bullet_point(cell_cue, 
        "• Approved for Free Cultural Works (Obras Culturales Libres): ", 
        "Sello o estándar de libertad cultural promovido por Freedom Defined que certifica que una licencia cumple cuatro libertades inviolables: "
        "libertad de usar y ejecutar la obra, libertad de estudiarla, libertad de redistribuir copias y libertad de mejorarla y publicar derivados (abarca CC0, CC BY y CC BY-SA).", 
        cfg, level=2)

    add_cell_bullet_point(cell_cue, 
        "Licencias de Código Abierto Aplicadas a Assets: ", 
        "Licencias como MIT, Apache 2.0 y BSD se emplean comúnmente en paquetes de recursos técnicos o shaders, requiriendo preservar el aviso de copyright "
        "y el texto de exención de responsabilidad. Para fuentes tipográficas e iconografía, la SIL Open Font License (OFL) es el estándar libre predominante.", 
        cfg, level=1)

    add_cell_body_paragraph(cell_cue, 
        "Requisitos Prácticos para Desarrolladores de Videojuegos: Al integrar archivos de imagen o sonido libre en un proyecto, el equipo de desarrollo debe: "
        "1. Crear y mantener una bitácora de activos ('CREDITS.txt' o 'ATTRIBUTION.md') consignando: Nombre del asset, autor original, URL de procedencia y tipo de licencia. "
        "2. Incluir una pantalla o sección accesible de 'Créditos / Licencias de Terceros' en el menú de opciones del videojuego. "
        "3. Validar de forma preventiva que ningún activo integrado en un producto con micropagos o venta contenga cláusulas restrictivas '-NC' (NonCommercial).",
        cfg
    )

    # --- 4. SECCIÓN: CONCLUSIONES ---
    cell_concl = table.rows[13].cells[0]
    cell_concl.text = ""
    apply_cell_margins(cell_concl)

    add_cell_heading_1(cell_concl, "CONCLUSIONES", cfg)

    add_cell_bullet_point(cell_concl, 
        "Determinismo y Trazabilidad mediante Configuración por Código: ", 
        "La inicialización defensiva de las propiedades de AudioSource en el método Start() (fijando playOnAwake = false, loop = false y spatialBlend = 0.0f) "
        "establece una arquitectura confiable que elimina la dependencia de configuraciones manuales propensas a errores en el Inspector de Unity, "
        "garantizando que la fuente sonora mantenga un comportamiento predecible en cualquier escenario o plataforma de despliegue.", 
        cfg, level=1)

    add_cell_bullet_point(cell_concl, 
        "Diferenciación entre Disparos Puntuales (PlayOneShot) y Bucles Continuos (Loop Play): ", 
        "Se comprobó experimentalmente la idoneidad técnica de 'AudioSource.PlayOneShot()' para efectos transitorios no acumulativos como el salto, "
        "frente al control explícito de 'clip', 'loop = true' y 'Play()' en Update() para la locomoción sostenida. Esta separación funcional permite sincronizar "
        "el audio con la cinemática física del personaje de manera reactiva y sin latencia perceptible.", 
        cfg, level=1)

    add_cell_bullet_point(cell_concl, 
        "Resolución Defensiva de Conflictos de Concurrencia en AudioSource Único: ", 
        "La investigación y depuración del silenciamiento anómalo del salto tras caminar reveló que compartir una única fuente de audio exige una "
        "rutina de desahogo y reseteo previo. La invocación secuencial de 'audioSource.Stop()' y 'audioSource.clip = null' antes de ejecutar el salto "
        "desaloja el búfer ocupado por las pisadas, garantizando una transición sonora limpia y armoniosa sin saturar la memoria con múltiples componentes innecesarios.", 
        cfg, level=1)

    add_cell_bullet_point(cell_concl, 
        "Eficiencia del Audio Estéreo 2D en Cámaras de Seguimiento: ", 
        "La calibración del Spatial Blend en 0.0f (sonido 2D) demostró ser la decisión óptima para personajes con cámara de seguimiento rígida, "
        "asegurando máxima inteligibilidad auditiva sin pérdidas de volumen por atenuación de distancia ni consumo superfluo de ciclos de procesamiento "
        "en cálculos de espacialización 3D en el motor FMOD.", 
        cfg, level=1)

    add_cell_bullet_point(cell_concl, 
        "Gobernanza y Cumplimiento Normativo de Recursos Multimedia Libres: ", 
        "El análisis riguroso de las licencias comunitarias en Freesound.org (CC0, CC BY, CC BY-NC, Sampling+) constató que la selección de assets "
        "debe alinearse estrictamente con el modelo de distribución del videojuego. La priorización de activos en dominio público (CC0) o con atribución formal "
        "constituye un pilar ético y profesional indispensable en el desarrollo formal de software de entretenimiento.", 
        cfg, level=1)

    # --- 5. SECCIÓN: REFERENCIAS Y BIBLIOGRAFÍA ---
    cell_ref = table.rows[17].cells[0]
    cell_ref.text = ""
    apply_cell_margins(cell_ref)

    add_cell_heading_1(cell_ref, "REFERENCIAS Y BIBLIOGRAFÍA", cfg)

    add_cell_bullet_point(cell_ref, 
        "Unity Technologies. (2024). ", 
        "AudioSource - Unity Scripting API Reference (v6000.0). San Francisco, CA: Unity Documentation. Recuperado de https://docs.unity.com/ScriptReference/AudioSource.html", 
        cfg, level=1)

    add_cell_bullet_point(cell_ref, 
        "Unity Technologies. (2024). ", 
        "AudioListener - Unity Scripting API Reference (v6000.0). San Francisco, CA: Unity Documentation. Recuperado de https://docs.unity.com/ScriptReference/AudioListener.html", 
        cfg, level=1)

    add_cell_bullet_point(cell_ref, 
        "Unity Technologies. (2024). ", 
        "Audio Overview and Sound Spatialization in Unity. San Francisco, CA: Unity Documentation. Recuperado de https://docs.unity.com/Manual/AudioOverview.html", 
        cfg, level=1)

    add_cell_bullet_point(cell_ref, 
        "Gregory, J. (2018). ", 
        "Game Engine Architecture: Audio Systems and DSP Pipelines (3.ª ed.). Boca Raton, FL: CRC Press / Taylor & Francis Group.", 
        cfg, level=1)

    add_cell_bullet_point(cell_ref, 
        "Creative Commons Foundation. (2024). ", 
        "About the Licenses: Recommended Practices for Attribution and Legal Code. Mountain View, CA: Creative Commons. Recuperado de https://creativecommons.org/licenses/", 
        cfg, level=1)

    add_cell_bullet_point(cell_ref, 
        "Freesound. (2024). ", 
        "Freesound Help & Licensing Guidelines: Sampling Plus, CC0 and Cultural Heritage. Universitat Pompeu Fabra. Recuperado de https://freesound.org/help/faq/#licenses", 
        cfg, level=1)

    # Guardar documento
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    print(f"✓ Reporte de Laboratorio 07 compilado exitosamente en: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generador de reporte de Laboratorio 07 de IDSE")
    parser.add_argument("--template", default="inputs/IDSE/IDSE-Lab05/input-template.docx")
    parser.add_argument("--output", default="output/IDSE/lab07/Reporte_Practica_07_Unity.docx")
    parser.add_argument("--media", default="output/IDSE/lab07/figures")
    args = parser.parse_args()

    build_lab07_report(
        template_path=args.template,
        output_path=args.output,
        media_dir=args.media
    )
