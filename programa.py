import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import whisper
import os
import threading
import datetime
from pathlib import Path
from deep_translator import GoogleTranslator

class WhisperAppPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Transcriptor Whisper Pro (CPU)")
        # Resolución solicitada
        self.root.geometry("1024x768")
        
        # Variables
        self.source_dir = tk.StringVar()
        self.status_general = tk.StringVar(value="Esperando directorio...")
        self.status_current_file = tk.StringVar(value="...")
        self.model_size = "base" 
        
        # Configuración de estilos
        self.configure_styles()
        
        self.languages = {
            "Detectar Automáticamente": None,
            "Inglés": "en", "Español": "es", "Francés": "fr", 
            "Alemán": "de", "Italiano": "it", "Portugués": "pt", 
            "Japonés": "ja", "Chino": "zh"
        }
        
        self.create_widgets()

    def configure_styles(self):
        style = ttk.Style()
        style.configure(".", font=("Segoe UI", 12)) 
        style.configure("TLabelframe.Label", font=("Segoe UI", 14, "bold"))
        style.configure("Bold.TLabel", font=("Segoe UI", 12, "bold"))
        style.configure("Big.TButton", font=("Segoe UI", 14, "bold"), padding=10)

    def create_widgets(self):
        # Contenedor principal
        main_container = ttk.Frame(self.root, padding=20)
        main_container.pack(fill="both", expand=True)

        # --- SECCIÓN 1: SELECCIÓN ---
        frame_top = ttk.LabelFrame(main_container, text=" 1. Selección de Archivos ", padding=15)
        frame_top.pack(side="top", fill="x", pady=(0, 15))

        ttk.Entry(frame_top, textvariable=self.source_dir, state="readonly", font=("Segoe UI", 12)).pack(side="left", fill="x", expand=True, padx=(0, 15))
        ttk.Button(frame_top, text="📂 Examinar Carpeta", command=self.select_directory).pack(side="right")

        # --- SECCIÓN 2: CONFIGURACIÓN ---
        frame_config = ttk.LabelFrame(main_container, text=" 2. Configuración ", padding=15)
        frame_config.pack(side="top", fill="x", pady=(0, 15))

        frame_config.columnconfigure(1, weight=1)
        frame_config.columnconfigure(3, weight=1)

        ttk.Label(frame_config, text="Idioma Origen:", style="Bold.TLabel").grid(row=0, column=0, sticky="w", padx=5, pady=10)
        self.combo_source = ttk.Combobox(frame_config, values=list(self.languages.keys()), state="readonly", font=("Segoe UI", 12))
        self.combo_source.current(0)
        self.combo_source.grid(row=0, column=1, sticky="ew", padx=10)

        ttk.Label(frame_config, text="Acción / Destino:", style="Bold.TLabel").grid(row=0, column=2, sticky="w", padx=5)
        self.target_options = [
            "Transcribir (Mantener idioma original)", 
            "Traducir a Inglés (Nativo Whisper)",
            "Traducir a Español (Vía Traductor)"
        ]
        self.combo_target = ttk.Combobox(frame_config, values=self.target_options, state="readonly", font=("Segoe UI", 12))
        self.combo_target.current(0)
        self.combo_target.grid(row=0, column=3, sticky="ew", padx=10)

        # --- SECCIÓN 3: PROGRESO ---
        frame_prog = ttk.LabelFrame(main_container, text=" 3. Estado del Proceso ", padding=15)
        frame_prog.pack(side="top", fill="x", pady=(0, 15))

        ttk.Label(frame_prog, text="Progreso Total:", style="Bold.TLabel").pack(anchor="w")
        self.pb_total = ttk.Progressbar(frame_prog, orient="horizontal", mode="determinate")
        self.pb_total.pack(fill="x", pady=(5, 15))
        
        ttk.Label(frame_prog, textvariable=self.status_current_file, foreground="#0055aa").pack(anchor="w")
        self.pb_current = ttk.Progressbar(frame_prog, orient="horizontal", mode="indeterminate")
        self.pb_current.pack(fill="x", pady=(5, 5))

        # --- CORRECCIÓN AQUÍ: EL BOTÓN SE EMPAQUETA AHORA, ANCLADO AL FONDO ---
        # Al usar side="bottom", reservamos el espacio para el botón antes de que el Log ocupe el resto
        self.btn_run = ttk.Button(main_container, text="▶ INICIAR PROCESAMIENTO", style="Big.TButton", command=self.start_thread)
        self.btn_run.pack(side="bottom", fill="x", pady=(10, 0))

        # --- SECCIÓN 4: LOG (Ocupa el espacio restante) ---
        frame_log = ttk.LabelFrame(main_container, text=" Registro de Eventos ", padding=10)
        # Se empaqueta después del botón, pero ocupa todo el espacio SOBRANTE entre el progreso y el botón
        frame_log.pack(side="top", fill="both", expand=True)

        scroll = ttk.Scrollbar(frame_log)
        scroll.pack(side="right", fill="y")
        
        self.log_text = tk.Text(
            frame_log, 
            state="disabled", 
            font=("Consolas", 16), 
            yscrollcommand=scroll.set,
            bg="#f0f0f0",
            wrap="word"
        )
        self.log_text.pack(fill="both", expand=True)
        scroll.config(command=self.log_text.yview)

    def log(self, message):
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def select_directory(self):
        path = filedialog.askdirectory()
        if path:
            self.source_dir.set(path)
            self.log(f"Directorio cargado: {path}")

    def format_timestamp(self, seconds):
        td = datetime.timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        millis = int((seconds - total_seconds) * 1000)
        return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

    def start_thread(self):
        directory = self.source_dir.get()
        if not directory or not os.path.isdir(directory):
            messagebox.showerror("Error", "Directorio inválido o no seleccionado.")
            return

        self.btn_run.config(state="disabled")
        threading.Thread(target=self.run_process, args=(directory,), daemon=True).start()

    def run_process(self, root_directory):
        try:
            self.status_current_file.set("Iniciando motor Whisper...")
            self.pb_current.start(10)
            self.log("Cargando modelo Whisper (CPU). Esto puede tardar...")
            
            # --- PREPARACIÓN DE RECURSOS ---
            model = whisper.load_model(self.model_size, device="cpu")
            self.log("Modelo cargado.")

            valid_ext = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.wma', '.mp4', '.mkv', '.avi'}
            
            # --- RECOLECCIÓN RECURSIVA DE ARCHIVOS ---
            all_files_to_process = []
            self.log("Buscando archivos multimedia en subdirectorios...")
            for dirpath, dirnames, filenames in os.walk(root_directory):
                for filename in filenames:
                    if Path(filename).suffix.lower() in valid_ext:
                        # Guardamos la ruta completa y su directorio
                        all_files_to_process.append((os.path.join(dirpath, filename), dirpath))
            
            total_files = len(all_files_to_process)
            
            if not all_files_to_process:
                self.pb_current.stop()
                self.status_current_file.set("Sin archivos.")
                messagebox.showwarning("Vacío", "No se encontraron archivos multimedia compatibles en el directorio ni sus subdirectorios.")
                self.btn_run.config(state="normal")
                return

            self.pb_total["maximum"] = total_files
            self.pb_total["value"] = 0

            src_lang = self.languages[self.combo_source.get()]
            action = self.combo_target.get()
            
            task_type = "translate" if action == "Traducir a Inglés (Nativo Whisper)" else "transcribe"
            do_spanish_trans = (action == "Traducir a Español (Vía Traductor)")

            self.log(f"Modo: {task_type}. Traducir a ES (vía Google): {do_spanish_trans}. Archivos totales: {total_files}")

            # --- PROCESAMIENTO ---
            for i, (filepath, current_directory) in enumerate(all_files_to_process):
                filename = Path(filepath).name
                relative_path = os.path.relpath(filepath, root_directory)
                
                self.status_current_file.set(f"Analizando archivo {i+1}/{total_files}: {relative_path}")
                self.log(f"Procesando: {relative_path}...")
                
                try:
                    opts = {"task": task_type, "fp16": False}
                    if src_lang: opts["language"] = src_lang

                    result = model.transcribe(filepath, **opts)
                    segments = result["segments"]

                    if do_spanish_trans:
                        self.log(" -> Traduciendo texto a Español (Google Translator)...")
                        translator = GoogleTranslator(source='auto', target='es')
                        for seg in segments:
                            try:
                                # Pre-procesamiento de la traducción
                                seg["text"] = translator.translate(seg["text"])
                            except Exception as trans_e: 
                                self.log(f"   Advertencia: Fallo al traducir segmento: {trans_e}")
                                pass

                    base = Path(filepath).stem
                    
                    # Los archivos de salida se guardan en el mismo directorio del archivo fuente.
                    
                    # SRT
                    srt_path = os.path.join(current_directory, f"{base}.srt")
                    with open(srt_path, "w", encoding="utf-8") as f:
                        for idx, seg in enumerate(segments, 1):
                            start = self.format_timestamp(seg["start"])
                            end = self.format_timestamp(seg["end"])
                            f.write(f"{idx}\n{start} --> {end}\n{seg['text'].strip()}\n\n")

                    # TXT
                    full_text = " ".join([s["text"].strip() for s in segments])
                    txt_path = os.path.join(current_directory, f"{base}_completo.txt")
                    with open(txt_path, "w", encoding="utf-8") as f:
                        f.write(full_text)

                    self.log(f" -> OK. Guardado en: {current_directory}")

                except Exception as e:
                    self.log(f"ERROR en {relative_path}: {e}")

                self.pb_total["value"] = i + 1

            # --- FINALIZACIÓN ---
            self.pb_current.stop()
            self.status_current_file.set("Proceso finalizado.")
            self.log("¡Tarea completada en todos los directorios!")
            messagebox.showinfo("Éxito", "Todos los archivos y subdirectorios han sido procesados.")

        except Exception as e:
            self.pb_current.stop()
            self.log(f"ERROR CRÍTICO: {e}")
            messagebox.showerror("Error", str(e))
        
        finally:
            self.btn_run.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = WhisperAppPro(root)
    root.mainloop()
