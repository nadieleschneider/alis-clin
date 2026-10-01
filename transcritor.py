import threading
import os
import gc
from datetime import datetime
from tkinter import filedialog, messagebox
import tkinter as tk
import customtkinter as ctk
import whisper
import ollama
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
from docx import Document

# Configuração do tema da interface
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class AppProntuario(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Alis Clin - Assistente de Prontuário por Voz")
        self.geometry("1060, 800")

        # Variáveis de controle de áudio, gravação e cache de sugestões
        self.caminho_audio = ""
        self.amostragem = 10000
        self.canais = 1
        self.gravando = False
        self.pausado = False
        self.dados_gravacao = []
        self.stream = None
        self.sugestoes_cache = "Nenhuma sugestão gerada para esta consulta ainda."

        # Cria pasta local de histórico se não existir
        self.pasta_historico = "prontuarios_salvos"
        if not os.path.exists(self.pasta_historico):
            os.makedirs(self.pasta_historico)

        # LAYOUT DA INTERFACE (GRID PRINCIPAL)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)

        # 1. LATERAL ESQUERDA (CHECKLIST)
        self.frame_checklist = ctk.CTkFrame(self, width=280)
        self.frame_checklist.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")
        self.frame_checklist.grid_propagate(False)

        # Título da Marca (Alis Clin)
        self.label_marca = ctk.CTkLabel(self.frame_checklist, text="Alis Clin", font=ctk.CTkFont(size=24, weight="bold"), text_color="#3498db")
        self.label_marca.grid(row=0, column=0, padx=15, pady=(15, 0), sticky="w")

        self.label_sub = ctk.CTkLabel(self.frame_checklist, text="Inteligência Clínica Local & Privada", font=ctk.CTkFont(size=12))
        self.label_sub.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="w")

        # PAINEL LATERAL: CHECKLIST TÓPICOS CLÍNICOS
        self.lbl_chk_titulo = ctk.CTkLabel(self.frame_checklist, text="Tópicos do Prontuário:", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_chk_titulo.grid(row=2, column=0, padx=(15, 15), pady=10, sticky="w")

        check_itens = [
            ("Queixa Principal (QP)", "Motivo principal da consulta e tempo de evolução."),
            ("História da Doença Atual (HDA)", "Detalhes dos sintomas e fatores de melhora/piora."),
            ("História da Doença Pregressa (HDP)", "Histórico médico prévio e comorbidades."),
            ("Medicamentos / Suplementação", "Uso atual de fármacos ou suplementos."),
            ("Antecedentes Familiares", "Histórico de saúde na família."),
            ("Hábitos de Vida", "Estilo de vida, atividade física e rotina."),
            ("Avaliação / Exame Físico", "Achados clínicos e testes específicos."),
            ("Conduta / Plano Terapêutico", "Previsão, orientações e exames solicitados."),
        ]
        for i, (titulo, desc) in enumerate(check_itens):
            lbl_t = ctk.CTkLabel(self.frame_checklist, text=titulo, font=ctk.CTkFont(size=12, weight="bold"), text_color="#2ecc71")
            lbl_t.grid(row=3 + (i * 2), column=0, padx=15, pady=(5, 0), sticky="w")
            lbl_d = ctk.CTkLabel(self.frame_checklist, text=desc, font=ctk.CTkFont(size=11), text_color="gray", wraplength=240, justify="left")
            lbl_d.grid(row=4 + (i * 2), column=0, padx=15, pady=(0, 8), sticky="w")

        # 2. PAINEL DIREITO: CONTROLES E RESULTADO
        self.frame_direito = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_direito.grid(row=0, column=2, padx=(5, 10), pady=10, sticky="nsew")
        self.frame_direito.grid_rowconfigure(1, weight=1)
        self.frame_direito.grid_columnconfigure(0, weight=1)

        # Frame de Gravação
        self.frame_entrada = ctk.CTkFrame(self.frame_direito)
        self.frame_entrada.grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.btn_gravar = ctk.CTkButton(self.frame_entrada, text="Gravar", fg_color="#2ecc71", hover_color="#27ae60", width=100, command=self.alternar_gravacao)
        self.btn_gravar.pack(side="left", padx=5, pady=8)

        self.btn_pausa = ctk.CTkButton(self.frame_entrada, text="Pausar", fg_color="#e67e22", hover_color="#d35400", width=90, command=self.alternar_pausa, state="disabled")
        self.btn_pausa.pack(side="left", padx=5, pady=12)

        self.label_ou = ctk.CTkLabel(self.frame_entrada, text="OU", text_color="gray")
        self.label_ou.pack(side="left", padx=5)

        self.btn_selecionar = ctk.CTkButton(self.frame_entrada, text="Arquivo", width=90, command=self.selecionar_arquivo)
        self.btn_selecionar.pack(side="left", padx=5, pady=12)

        # Botão independente para abrir a janela pop-up de Sugestões de Conduta e Exercícios
        self.btn_sugestoes = ctk.CTkButton(self.frame_entrada, text="Sugestões de Conduta", fg_color="#2980b9", hover_color="#2471a3", width=140, command=self.abrir_janela_sugestoes, state="disabled")
        self.label_status_audio.grid(row=1, column=0, sticky="w", pady=9)

        self.label_status_audio = ctk.CTkLabel(self.frame_direito, text="Status: Pronto para gravar ou selecionar áudio.", text_color="gray", font=ctk.CTkFont(size=11))
        self.label_status_audio.grid(row=1, column=0, sticky="w", pady=9)
        
        # Botão principal de execução
        self.btn_executar = ctk.CTkButton(self.frame_direito, text="Processar e Estruturar Prontuário", fg_color="green", hover_color="darkgreen", height=38, command=self.iniciar_processamento, state="disabled")
        self.btn_executar.grid(row=2, column=0, sticky="ew", pady=(0, 5))

        # Caixa de Texto
        self.label_resultado = ctk.CTkLabel(self.frame_direito, text="Prontuário Estruturado:", font=ctk.CTkFont(size=14, weight="bold"))
        self.label_resultado.grid(row=3, column=0, sticky="w", pady=(5, 4))

        self.texto_saida = ctk.CTkTextbox(self.frame_direito, font=ctk.CTkFont(size=13))
        self.texto_saida.grid(row=4, column=0, sticky="nsew", pady=5)

        # Rodapé com Salvar e Monitor de Sistema
        self.frame_rodapé = ctk.CTkFrame(self.frame_direito, fg_color="transparent")
        self.frame_rodapé.grid(row=5, column=0, sticky="ew", pady=5)

        self.btn_salvar_word = ctk.CTkButton(self.frame_rodapé, text="Salvar Prontuário em Word (.docx)", command=self.salvar_word, state="disabled")
        self.btn_salvar_word.grid(row=0, column=0, sticky="ew", pady=5)

        self.frame_rodape = ctk.CTkFrame(self.frame_rodapé, fg_color="transparent")
        self.frame_rodape.grid(row=6, column=0, sticky="ew", pady=5)

        self.label_lgpd = ctk.CTkLabel(self.frame_rodape, text="🔒 100% Local | LGPD Compliant", text_color="gray", font=ctk.CTkFont(size=10))
        self.label_lgpd.pack(side="left")

        # Label do Monitor de Hardware
        self.label_hardware = ctk.CTkLabel(self.frame_rodape, text="CPU: 0% | RAM: 0%", text_color="#3498db", font=ctk.CTkFont(size=10, weight="bold"))
        self.label_hardware.pack(side="right")

        # Inicia a atualização do monitor de hardware em tempo real
        self.atualizar_monitor_hardware()

    def atualizar_monitor_hardware(self):
        try:
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
            self.label_hardware.configure(text=f"CPU: {cpu}% | RAM: {ram}%")
        except:
            pass
        self.after(3000, self.atualizar_monitor_hardware)

    def alternar_gravacao(self):
        if not self.gravando:
            self.gravando = True
            self.pausado = False
            self.dados_gravacao = []
            self.btn_gravar.configure(text="Parar", fg_color="#d63031")
            self.btn_pausa.configure(state="normal", fg_color="#f1c40f")
            self.btn_selecionar.configure(state="disabled")
            self.label_status_audio.configure(text="Gravando áudio da consulta...", text_color="#00ff76")

            self.stream = sd.InputStream(samplerate=self.amostragem, channels=self.canais, callback=self.callback_gravacao)
            self.stream.start()
        else:
            self.gravando = False
            self.pausado = False
            if self.stream:
                self.stream.stop()
                self.stream.close()

            if self.dados_gravacao:
                self.caminho_audio = "audio_consulta.wav"
                audio_np = np.concatenate(self.dados_gravacao, axis=0)
                write(self.caminho_audio, self.amostragem, audio_np)
                self.label_status_audio.configure(text="Áudio gravado com sucesso! Pronto para processar.", text_color="#00ff76")
                self.btn_executar.configure(state="normal")
            else:
                self.label_status_audio.configure(text="Nenhum áudio capturado.", text_color="gray")

            self.btn_gravar.configure(text="Gravar", fg_color="#2ecc71")
            self.btn_pausa.configure(state="disabled", text="Pausar")
            self.btn_selecionar.configure(state="normal")

    def alternar_pausa(self):
        if not self.pausado:
            self.pausado = True
            self.btn_pausa.configure(text="Retomar", fg_color="#f1c40f")
            self.label_status_audio.configure(text="Gravação pausada.", text_color="#f1c402")
        else:
            self.pausado = False
            self.btn_pausa.configure(text="Pausar", fg_color="#f1c40f")
            self.label_status_audio.configure(text="Gravando áudio da consulta...", text_color="#00ff76")

    def callback_gravacao(self, indata, frames, time, status):
        if self.gravando and not self.pausado:
            self.dados_gravacao.append(indata.copy())

    def selecionar_arquivo(self):
        arquivo = filedialog.askopenfilename(filetypes=[("Arquivos de áudio", "*.ogg *.mp3 *.wav")])
        if arquivo:
            self.caminho_audio = arquivo
            nome_curto = arquivo.split("/")[-1]
            self.label_status_audio.configure(text=f"Arquivo selecionado: {nome_curto}", text_color="white")
            self.btn_executar.configure(state="normal")

    def iniciar_processamento(self):
        self.btn_executar.configure(state="disabled", text="Processando prontuário...")
        self.btn_gravar.configure(state="disabled")
        self.btn_pausa.configure(state="disabled")
        self.btn_selecionar.configure(state="disabled")
        self.btn_sugestoes.configure(state="disabled")
        self.texto_saida.delete("1.0", tk.END)
        self.texto_saida.insert("1.0", "Carregando modelo Whisper e transcrevendo áudio...\n")

        threading.Thread(target=self.processar_pipeline).start()

    def processar_pipeline(self):
        try:
            # 1. Transcrição com Whisper otimizada para Ryzen/GPU
            modelo_whisper = whisper.load_model("tiny")
            resultado_audio = modelo_whisper.transcribe(self.caminho_audio, language="portuguese", fp16=False)
            texto_bruto = resultado_audio["text"]

            del modelo_whisper
            gc.collect()

            self.texto_saida.delete("1.0", tk.END)
            self.texto_saida.insert("1.0", "Estruturando com inteligência local (Llama 3.2 3B)...\n")

            # 2. Estruturação do Prontuário com Ollama
            prompt_prontuario = f"""
            Você é um assistente clínico especialista em estruturação de prontuários.
            Abaixo está a transcrição bruta de uma consulta.
            Organize este texto estritamente nos seguintes tópicos profissionais:
            - Queixa Principal (QP)
            - História da Doença Atual (HDA)
            - História da Doença Pregressa (HDP)
            - Medicamentos em uso / Suplementação
            - Antecedentes Familiares
            - Hábitos de Vida / Estilo de Vida
            - Avaliação / Exame Físico
            - Conduta / Plano Terapêutico

            Texto bruto:
            "{texto_bruto}"
            """

            resp_prontuario = ollama.chat(model='llama3.2:3b', messages=[
                {'role': 'user', 'content': prompt_prontuario},
            ])
            prontuario_final = resp_prontuario['message']['content']

            # 3. Geração de Sugestões Focadas em Exercícios Específicos e Condutas
            prompt_sugestoes = f"""
            Com base estritamente na transcrição da consulta abaixo, atue como um especialista em raciocínio clínico. Apunte sugestões de condutas práticas e exercícios terapêuticos específicos (incluindo objetivos ou parâmetros aplicáveis) para o tratamento exato do problema relatado pelo paciente, servindo de base analítica para o profissional:

            Transcrição:
            "{texto_bruto}"
            """

            resp_sugestoes = ollama.chat(model='llama3.2:3b', messages=[
                {'role': 'user', 'content': prompt_sugestoes},
            ])
            self.sugestoes_cache = resp_sugestoes['message']['content']

            # Exibe o prontuário na tela principal
            self.texto_saida.delete("1.0", tk.END)
            self.texto_saida.insert("1.0", prontuario_final)

            # Salva histórico local em texto
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            caminho_txt_local = os.path.join(self.pasta_historico, f"prontuario_{timestamp}.txt")
            with open(caminho_txt_local, "w", encoding="utf-8") as f:
                f.write(prontuario_final)

            # Libera botões
            self.btn_executar.configure(state="normal")
            self.btn_sugestoes.configure(state="normal")
            self.btn_salvar_word.configure(state="normal")
            self.btn_executar.configure(text="Processar e Estruturar Prontuário")
            self.btn_gravar.configure(state="normal")
            self.btn_selecionar.configure(state="normal")

        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")
            self.btn_executar.configure(state="normal", text="Processar e Estruturar Prontuário")
            self.btn_gravar.configure(state="normal")
            self.btn_selecionar.configure(state="normal")

    def abrir_janela_sugestoes(self):
        # Criação de uma janela pop-up secundária (Toplevel) focada em condutas e exercícios
        janela_pop = ctk.CTkToplevel(self)
        janela_pop.title("Alis Clin - Sugestões de Conduta e Exercícios Terapêuticos")
        janela_pop.geometry("650, 550")
        janela_pop.grab_set() # Foco exclusivo na janela

        lbl_titulo = ctk.CTkLabel(janela_pop, text="💡 Sugestões de Conduta e Condutas Específicas (IA)", font=ctk.CTkFont(size=15, weight="bold"), text_color="#3498db")
        lbl_titulo.pack(pady=(15, 10), padx=20, anchor="w")

        txt_sugestoes = ctk.CTkTextbox(janela_pop, font=("Arial", 13))
        txt_sugestoes.pack(fill="both", expand=True, padx=20, pady=10)
        txt_sugestoes.insert("1.0", self.sugestoes_cache)

        btn_fechar = ctk.CTkButton(janela_pop, text="Fechar Janela", fg_color="#c0392b", hover_color="#962d22", command=janela_pop.destroy)
        btn_fechar.pack(pady=15)

    def salvar_word(self):
        conteudo = self.texto_saida.get("1.0", tk.END).strip()
        if not conteudo:
            return
        
        caminho_salvar = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Documento Word", "*.docx")])
        if caminho_salvar:
            doc = Document()
            doc.add_heading("Prontuário Clínico - Alis Clin", level=1)
            doc.add_paragraph(conteudo)
            doc.save(caminho_salvar)
            messagebox.showinfo("Sucesso", "Prontuário salvo em Word com sucesso!")

if __name__ == "__main__":
    app = AppProntuario()
    app.mainloop()