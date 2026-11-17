# API DFMed — referência de endpoints

Base: `https://dfmed.app.br/backend/api/`
Autenticação: header `token: <JSON do sessionStorage>`
Content-Type: `application/json; charset=utf-8`

Reconstruído do bundle Angular do app "dfMed Cloud". **Não é oficial** e pode
mudar. Nem todos os endpoints estão cobertos pelo `dfmed.py` — os extras podem
ser chamados via `raw`.

## Session/
| Método | Caminho | Uso |
|---|---|---|
| POST | `Session/Autentica` | login (payload `{id, pw}` ofuscados pelo app) — **não** implementado aqui; usamos token |
| GET | `Session/Logout` | encerra sessão |
| GET | `Session/RenovaToken` | renova o token |
| GET | `Session/IsAlive` | ping (público) |
| GET | `Session/Environment` | ambiente (público) |
| GET | `Session/EnviaSenha?para=<email>` | envia recuperação de senha |
| POST | `Session/TrocaSenha` | troca senha `{token, novaSenha}` |
| GET | `Session/AtualizaClinicaUnidade?clinica=<>&unidade=<>` | troca clínica/unidade ativa |
| GET | `Session/QtdeSessoes` / `Session/QtdeSessoesClinica` | sessões ativas |

## Usuarios/
| Método | Caminho | Uso |
|---|---|---|
| GET | `Usuarios/GetUsuarioLogado?usrID=<>` | dados do usuário + `clinicas` |
| GET | `Usuarios/TemClinicas?usrID=<>` | clínicas do usuário |
| GET | `Usuarios/ModulosAcesso?usrID=<>&clinUnID=<>` | permissões |
| GET | `Usuarios/GetByEmail?email=<>` / `GetByCelular?celular=<>` | busca usuário |
| GET | `Usuarios/Lista` | lista usuários |
| GET | `Usuarios/ConviteEnvia?conviteID=<>` / `ConvitePega?conviteID=<>&token=<>` | convites |
| POST | `Usuarios/ConviteSalva` | salva convite |
| GET/POST | `Usuarios/GuiGet?usrID=<>` / `Usuarios/GuiSave` | ficha do usuário |

## CadPac/ (pacientes)
| Método | Caminho | Uso |
|---|---|---|
| POST | `CadPac/BuscaPaciente` | busca `{nome, celular, dtNasc, limite}` |
| POST | `CadPac/ListByFiltro` | lista por filtro |
| GET | `CadPac/ListAniversariantes?data=<>` | aniversariantes |
| GET | `CadPac/GetGui?pacID=<>` | ficha completa do paciente |
| POST | `CadPac/SaveGui` | salva ficha do paciente |
| GET | `CadPac/TelefoneList?pacID=<>` | telefones |
| GET | `CadPac/Exclui?pacID=<>` | exclui paciente |

## Prontuario/
| Método | Caminho | Uso |
|---|---|---|
| GET | `Prontuario/List?pacID=<>&ordem=<asc\|desc>` | registros do paciente |
| GET | `Prontuario/Get?id=<pacfID>` | um registro |
| POST | `Prontuario/Save` | grava/edita registro (`{id, pacID, texto, isHtml}`) |
| GET | `Prontuario/Delete?pacfID=<>` | exclui registro |
| GET | `Prontuario/Pdf?pacfID=<>` | PDF do registro (blob) |
| GET | `Prontuario/PdfByToken?token=<>` | PDF por token de compartilhamento |
| GET | `Prontuario/DadosByToken?token=<>` | dados por token |

## Agenda/
| Método | Caminho | Uso |
|---|---|---|
| GET | `Agenda/ListaAgendas?usrID=<>` | agendas do usuário |
| GET | `Agenda/HorariosList?agID=<>&dataIniStr=<>&dataFimStr=<>` | horários no período |
| GET | `Agenda/AgendaDias?agID=<>&dataIniStr=<>&dataFimStr=<>` | dias com atendimento |
| GET | `Agenda/GetHorario?aghID=<>` | detalhe do horário |
| POST | `Agenda/SaveHorario` | cria/edita horário |
| GET | `Agenda/HorarioDesmarca?aghID=<>` | desmarca |
| GET | `Agenda/HorarioMudaStatus?aghID=<>&status=<>` | muda status |
| POST | `Agenda/HorarioReplica?id=<>` | replica horário |
| GET | `Agenda/NovoParaExistente?aghID=<>&pacID=<>` | vincula horário a paciente existente |
| GET | `Agenda/GetAgenda?agID=<>` / `SaveAgenda` (POST) / `DeleteAgenda?id=<>` | CRUD de agenda |
| GET | `Agenda/AgendaDiaPdf?agID=<>&data=<>` | PDF do dia (blob) |

## Outros
| Grupo | Endpoints |
|---|---|
| Clinica/ | `GetGui?clinID=<>`, `SaveGui` (POST) |
| Unidade/ | `GetGui?clinUnID=<>`, `SaveGui` (POST) |
| Convenios/ | `Get?id=<>`, `Save` (POST), `Delete?id=<>` |
| Whatsapp/ | `Get?id=<>`, `Save` (POST), `Delete?id=<>` |
| Memed/ (receita) | `Token?usrID=<>`, `UsuarioCria` (POST), `UsuarioExclui?id=<>` |
| TabGeneric/ | `Especialidades`, `CBOS`, `Conselhos`, `Modulos`, `NiveisAcesso`, `CabecRodape` |

## Observações
- O header `token` é a **string JSON** inteira guardada no `sessionStorage`
  (objeto com `ok`, `usrID`, etc.), enviada como veio.
- Muitas operações dependem da clínica/unidade ativa — ver `whoami` para os IDs
  (`clinUnID`).
- Endpoints `*Pdf*` devolvem binário (ou base64); o script grava em arquivo.
