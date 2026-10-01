# Alis Clin - Assistente de Prontuário por Voz 🎙️🏥

O **Alis Clin** é uma aplicação desktop desenvolvida em Python com **CustomTkinter**, projetada para automatizar e otimizar a estruturação de prontuários médicos e fisioterapêuticos através de **Inteligência Artificial 100% local e privada**. 

O sistema realiza a transcrição de áudios de consultas (via microfone em tempo real ou arquivos) e utiliza modelos de linguagem locais para estruturar automaticamente os dados clínicos de acordo com a LGPD (Lei Geral de Proteção de Dados).

---

## 📋 Sumário
1. [Principais Funcionalidades](#principais-funcionalidades)
2. [Tecnologias Utilizadas](#tecnologias-utilizadas)
3. [Arquitetura e Segurança de Dados (LGPD)](#arquitetura-e-segurança-de-dados-lgpd)
4. [Pré-requisitos e Instalação](#pré-requisitos-e-instalação)
5. [Como Executar](#como-executar)

---

## 🚀 Principais Funcionalidades

* **Gravação e Gestão de Áudio em Tempo Real:** Captura de áudio de alta precisão via `sounddevice` com controles de Gravação, Pausa/Retomada e suporte à importação de arquivos (`.wav`, `.mp3`, `.ogg`).
* **Transcrição Inteligente Local:** Utiliza o modelo **OpenAI Whisper (`tiny`)** para converter a fala do paciente e do profissional em texto com alta fidelidade em português.
* **Estruturação Automática de Prontuário:** Integração com **Ollama (`Llama 3.2 3B`)** para organizar o texto bruto nos tópicos clínicos essenciais (Queixa Principal, HDA, HDP, Medicamentos, Hábitos, Exame Físico e Conduta).
* **Sugestões de Conduta e Exercícios:** Janela secundária dedicada gerada por IA com propostas de condutas e exercícios específicos para o caso do paciente.
* **Exportação para Word (`.docx`):** Geração automática de documentos formatados prontos para impressão ou arquivo.
* **Monitor de Hardware Integrado:** Acompanhamento em tempo real do uso de CPU e Memória RAM diretamente na interface.

---

## 🧰 Tecnologias Utilizadas

* **Linguagem:** Python 3.10+
* **Interface Gráfica (GUI):** `CustomTkinter` e `Tkinter`
* **Transcrição de Áudio:** `Whisper` (OpenAI)
* **Inteligência Artificial Local:** `Ollama` (`llama3.2:3b`)
* **Processamento de Áudio e Matemática:** `sounddevice`, `scipy`, `NumPy`
* **Manipulação de Documentos:** `python-docx`
* **Monitoramento de Sistema:** `psutil`

---

## 🔒 Arquitetura e Segurança de Dados (LGPD)

Por processar dados sensíveis de saúde, o **Alis Clin** foi arquitetado para rodar **100% localmente** na máquina do profissional. Nenhuma informação de paciente, áudio ou prontuário é enviada para servidores em nuvem de terceiros, garantindo total conformidade com as diretrizes da **LGPD**.

---

## ⚙️ Pré-requisitos e Instalação

1. **Instalar o Ollama:** Certifique-se de ter o [Ollama](https://ollama.com/) instalado e o modelo Llama 3.2 baixado na sua máquina:
   ```bash
   ollama pull llama3.2:3b
