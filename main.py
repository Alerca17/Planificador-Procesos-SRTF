import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class SRTFApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador SRTF Pro - Sistemas Operativos")
        self.root.geometry("500x650")
        
        # --- Configuración Inicial ---
        self.frame_input = ttk.LabelFrame(root, text=" Configuración ", padding="10")
        self.frame_input.pack(pady=10, fill="x", padx=10)

        ttk.Label(self.frame_input, text="N° de procesos:").grid(row=0, column=0)
        self.num_proc_entry = ttk.Entry(self.frame_input, width=10)
        self.num_proc_entry.grid(row=0, column=1, padx=5)
        
        self.btn_generar = ttk.Button(self.frame_input, text="Generar Tabla", command=self.crear_campos_procesos)
        self.btn_generar.grid(row=0, column=2)

        self.canvas_scroll = tk.Canvas(root)
        self.scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.canvas_scroll.yview)
        self.frame_procesos = ttk.Frame(self.canvas_scroll, padding="10")

        self.canvas_scroll.create_window((0, 0), window=self.frame_procesos, anchor="nw")
        self.canvas_scroll.configure(yscrollcommand=self.scrollbar.set)
        self.canvas_scroll.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.entradas_datos = []

    def crear_campos_procesos(self):
        for widget in self.frame_procesos.winfo_children():
            widget.destroy()
        self.entradas_datos = []

        try:
            n = int(self.num_proc_entry.get())
            headers = ["ID", "T. Llegada", "NCPU (Ráfaga)"]
            for col, text in enumerate(headers):
                ttk.Label(self.frame_procesos, text=text, font=('Arial', 10, 'bold')).grid(row=0, column=col, padx=5)

            for i in range(n):
                ttk.Label(self.frame_procesos, text=f"P{i}", font=('Arial', 10, 'bold')).grid(row=i+1, column=0)
                llegada = ttk.Entry(self.frame_procesos, width=10)
                llegada.grid(row=i+1, column=1, padx=5, pady=2)
                rafaga = ttk.Entry(self.frame_procesos, width=10)
                rafaga.grid(row=i+1, column=2, padx=5, pady=2)
                self.entradas_datos.append({'llegada': llegada, 'rafaga': rafaga, 'id': f"P{i}"})

            ttk.Button(self.frame_procesos, text="CALCULAR Y GRAFICAR", command=self.ejecutar_planificacion).grid(row=n+1, column=0, columnspan=3, pady=20)
            self.frame_procesos.update_idletasks()
            self.canvas_scroll.config(scrollregion=self.canvas_scroll.bbox("all"))
        except ValueError:
            messagebox.showerror("Error", "Ingresa un número entero")

    def ejecutar_planificacion(self):
        try:
            procs = []
            for item in self.entradas_datos:
                l = int(item['llegada'].get())
                r = int(item['rafaga'].get())
                procs.append({'id': item['id'], 'llegada': l, 'rafaga': r, 'restante': r})

            tiempo = 0
            completados = 0
            n = len(procs)
            gantt_raw = []
            resultados_finales = {}

            while completados < n:
                disponibles = [p for p in procs if p['llegada'] <= tiempo and p['restante'] > 0]
                if disponibles:
                    actual = min(disponibles, key=lambda x: x['restante'])
                    gantt_raw.append((actual['id'], tiempo))
                    actual['restante'] -= 1
                    if actual['restante'] == 0:
                        completados += 1
                        tf = tiempo + 1
                        tv = tf - actual['llegada']
                        te = tv - actual['rafaga']
                        resultados_finales[actual['id']] = {'fin': tf, 'vuelta': tv, 'espera': te}
                tiempo += 1
            
            self.mostrar_ventana_resultados(resultados_finales, gantt_raw, tiempo, procs)
        except Exception:
            messagebox.showerror("Error", "Revisa los datos ingresados")

    def mostrar_ventana_resultados(self, resultados, raw, total_t, original_procs):
        res_win = tk.Toplevel(self.root)
        res_win.title("Resultados Detallados SRTF")
        res_win.geometry("900x750")

        # Tabla de cálculos
        frame_tabla = ttk.LabelFrame(res_win, text=" Cuadro de Resultados ", padding="10")
        frame_tabla.pack(pady=10, fill="x", padx=10)

        tree = ttk.Treeview(frame_tabla, columns=("ID", "Llegada", "NCPU", "Fin", "Vuelta", "Espera"), show='headings', height=6)
        cols = [("ID", "Proceso"), ("Llegada", "T. Llegada"), ("NCPU", "NCPU"), ("Fin", "T. Final"), ("Vuelta", "T. Vuelta"), ("Espera", "T. Espera")]
        for cid, head in cols:
            tree.heading(cid, text=head)
            tree.column(cid, width=100, anchor="center")

        sum_v, sum_e = 0, 0
        for p in original_procs:
            r = resultados[p['id']]
            tree.insert("", "end", values=(p['id'], p['llegada'], p['rafaga'], r['fin'], r['vuelta'], r['espera']))
            sum_v += r['vuelta']; sum_e += r['espera']

        tree.pack(fill="x")
        ttk.Label(res_win, text=f"Promedios -> Vuelta: {sum_v/len(original_procs):.2f} | Espera: {sum_e/len(original_procs):.2f}", 
                  font=('Arial', 11, 'bold'), foreground="darkgreen").pack(pady=5)

        # Diagrama de Gantt Mejorado
        gantt = []
        if raw:
            curr_p, start = raw[0]
            for i in range(1, len(raw)):
                if raw[i][0] != curr_p:
                    gantt.append((curr_p, start, raw[i][1]))
                    curr_p, start = raw[i]
            gantt.append((curr_p, start, total_t))

        fig, ax = plt.subplots(figsize=(10, 4))
        cmap = plt.get_cmap('Pastel1')
        
        for i, (pid, s, e) in enumerate(gantt):
            duracion = e - s
            color_idx = int(pid.replace("P", "")) % 9
            ax.broken_barh([(s, duracion)], (10, 8), facecolors=cmap(color_idx), edgecolor='black')
            
            # Texto central (Proceso)
            ax.text(s + duracion/2, 14, pid, ha='center', va='center', fontweight='bold')
            # Texto abajo (Cuánto se le dio)
            ax.text(s + duracion/2, 9, f"Δ:{duracion}", ha='center', va='top', fontsize=8, color='gray')
            # Marcadores de tiempo en las esquinas (Línea de tiempo)
            ax.text(s, 18.5, str(s), ha='center', va='bottom', fontsize=9, fontweight='bold', color='red')
            if i == len(gantt) - 1: # Solo poner el final en el último bloque
                ax.text(e, 18.5, str(e), ha='center', va='bottom', fontsize=9, fontweight='bold', color='red')

        ax.set_ylim(5, 22)
        ax.set_xlabel("Eje de Tiempo (Quantum)")
        ax.set_yticks([])
        ax.set_title("Diagrama de Gantt (Marcas Rojas = Tiempo acumulado | Δ = Tiempo otorgado)")
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=res_win)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=10, fill="both", expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = SRTFApp(root)
    root.mainloop()