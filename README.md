# 🎓 Chat Ismart – Simulador de Bancas de Projeto de Vida

Este projeto é um **agente de IA** que ajuda jovens do **Ismart** a ensaiar suas apresentações de **Projeto de Vida** diante de bancas avaliadoras simuladas.  

O sistema foi desenvolvido em **Flask** e se conecta ao **Azure AI Foundry** e ao **Azure Speech** para gerar feedback em tempo real, com diferentes perfis de banca, suporte a voz e registro das conversas.

## ✨ Funcionalidades
- **Perfis de banca simulada**:  
  - **Rigor Acadêmico** – criteriosa e técnica  
  - **Acolhedora** – empática e encorajadora  
  - **Desafiadora** – firme e provocadora  
- **Interface web** com Bootstrap + logo do Ismart.  
- **Suporte a voz**:  
  - O aluno pode falar → Speech-to-Text (STT).  
  - A banca responde em áudio → Text-to-Speech (TTS).  
- **Registro automático das conversas** (`conversas.csv`), incluindo aluno, perfil, pergunta e resposta.

---

## 🚀 Como rodar localmente

### 1. Clonar o repositório
```bash
git clone https://github.com/SEU-USUARIO/chat-ismart.git
cd chat-ismart
