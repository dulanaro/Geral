---
name: dfmed
description: >-
  Gerencia o prontuário eletrônico DFMed (dfmed.app.br / dfMed Cloud) do próprio
  usuário: consultar a agenda do dia e horários, buscar pacientes e ver fichas,
  ler o prontuário/histórico e baixar PDFs, e lançar/editar registros de
  atendimento. Use sempre que o pedido envolver DFMed, dfmed.app.br, "meu
  prontuário", "minha agenda de pacientes", consultas/horários de pacientes,
  ou dados de um paciente do consultório. Requer um token de sessão do DFMed.
---

# DFMed — prontuário eletrônico

Skill para operar o prontuário eletrônico **DFMed** (app Angular "dfMed Cloud")
pela sua API REST interna (`https://dfmed.app.br/backend/api/`), em nome do
próprio usuário logado. Tudo passa pelo script `scripts/dfmed.py` (Python 3,
só biblioteca padrão).

## Dados sensíveis (leia primeiro)

Isto manipula **dados de saúde de pacientes reais** (LGPD). Portanto:

- Nunca cole conteúdo de prontuário, nomes ou CPFs de pacientes em serviços
  externos, logs públicos, commits ou PRs. Mantenha tudo na conversa.
- Operações de **escrita** (`prontuario-save`, `horario-desmarca`,
  `horario-status`) alteram o sistema real. **Confirme com o usuário** antes de
  executar e mostre exatamente o que será enviado. O script também pede
  confirmação interativa, exceto com `--yes`.
- Esta é uma API **não oficial** reconstruída do app; pode mudar sem aviso.

## Pré-requisito: token de sessão

As chamadas usam o **token** da sessão do próprio usuário (a senha nunca é
usada nem guardada). Se nenhuma chamada autenticada funcionar, peça ao usuário
para obter o token:

1. Logar em https://dfmed.app.br/ no navegador.
2. DevTools (F12) → aba **Application/Aplicativo** → **Session Storage** →
   `https://dfmed.app.br` → copiar o **valor** da chave `token`.
3. Guardar esse valor em **um** destes locais:
   - variável de ambiente `DFMED_TOKEN`
   - arquivo `~/.config/dfmed/token.json`
   - arquivo `.claude/skills/dfmed/.token.json` (já ignorado pelo git)

O token **expira**. Quando aparecer "token inválido ou expirado", peça um token
novo (ou tente `renova`).

## Como usar

Rode sempre a partir da raiz do repo:

```bash
python3 .claude/skills/dfmed/scripts/dfmed.py <comando> [opções]
```

Toda saída é JSON — interprete e responda ao usuário em português, de forma
resumida, sem despejar JSON cru a menos que ele peça.

### Leitura

| Objetivo | Comando |
|---|---|
| Quem sou eu + clínicas | `whoami` |
| Listar minhas agendas | `agenda-list` |
| Horários de uma agenda num dia | `agenda-dia --ag <agID> --ini 2026-11-17 [--fim 2026-11-18]` |
| Aniversariantes | `aniversariantes --data 2026-11-17` |
| Detalhe de um horário | `horario-get --agh <aghID>` |
| Buscar paciente | `paciente-busca --nome "Maria" [--celular ... --dtnasc ...]` |
| Ficha do paciente | `paciente --id <pacID>` |
| Telefones do paciente | `paciente-telefones --id <pacID>` |
| Registros do prontuário | `prontuario-list --pac <pacID> [--ordem desc]` |
| Um registro específico | `prontuario-get --id <pacfID>` |
| Baixar PDF de um registro | `prontuario-pdf --pacf <pacfID> --out /caminho/arquivo.pdf` |

### Escrita (confirmar antes!)

| Objetivo | Comando |
|---|---|
| Mudar status de horário | `horario-status --agh <aghID> --status <status>` |
| Desmarcar horário | `horario-desmarca --agh <aghID>` |
| Gravar/editar registro | `prontuario-save --file registro.json` |

Para `prontuario-save`, **nunca** monte o JSON do zero. O fluxo seguro é:
1. `prontuario-get --id <pacfID>` para pegar o registro atual (ou crie um novo
   com `id:0` e o `pacID` correto — campos conhecidos: `id`, `pacID`, `texto`,
   `isHtml`).
2. Edite apenas o necessário, salve o JSON num arquivo.
3. Mostre o conteúdo ao usuário, peça OK, e então rode `prontuario-save`.

### Fluxo típico "agenda do dia"

```bash
python3 .claude/skills/dfmed/scripts/dfmed.py agenda-list          # descobre o agID
python3 .claude/skills/dfmed/scripts/dfmed.py agenda-dia --ag 123 --ini 2026-11-17
```
Depois, para abrir o prontuário de um paciente da agenda, use o `pacID` do
horário em `prontuario-list --pac <pacID>`.

### Endpoint cru (para algo não coberto acima)

```bash
python3 .claude/skills/dfmed/scripts/dfmed.py raw Session/Environment
python3 .claude/skills/dfmed/scripts/dfmed.py raw --method POST CadPac/BuscaPaciente --body '{"nome":"Ana","limite":50}'
```

O mapa completo de endpoints está em `reference/endpoints.md`.
