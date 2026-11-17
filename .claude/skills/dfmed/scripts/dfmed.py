#!/usr/bin/env python3
"""Cliente de linha de comando para o prontuário eletrônico DFMed (dfmed.app.br).

Usa a API REST interna do app dfMed Cloud (https://dfmed.app.br/backend/api/),
autenticando pelo TOKEN de sessão do próprio usuário — a senha nunca é
armazenada. Apenas biblioteca padrão do Python 3.

Como obter o token:
  1. Faça login em https://dfmed.app.br/ no navegador.
  2. Abra o DevTools (F12) -> aba Application/Aplicativo.
  3. Em Session Storage -> https://dfmed.app.br, copie o VALOR da chave `token`.
  4. Guarde esse valor (um JSON) em um dos lugares abaixo:
       - variável de ambiente  DFMED_TOKEN='<valor>'
       - arquivo               ~/.config/dfmed/token.json
       - arquivo               .claude/skills/dfmed/.token.json   (ignorado pelo git)

O token expira; quando as chamadas falharem com "token inválido ou expirado",
repita os passos acima (ou rode `renova` para tentar renovar).
"""

import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = os.environ.get("DFMED_API", "https://dfmed.app.br/backend/api/")
TOKEN_FILES = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".token.json"),
    os.path.expanduser("~/.config/dfmed/token.json"),
]


# --------------------------------------------------------------------------- #
# token + HTTP
# --------------------------------------------------------------------------- #
def load_token():
    """Retorna o token como STRING JSON, exatamente como o app o envia no header."""
    raw = os.environ.get("DFMED_TOKEN")
    if not raw:
        for path in TOKEN_FILES:
            if os.path.isfile(path):
                with open(path, encoding="utf-8") as fh:
                    raw = fh.read().strip()
                break
    if not raw:
        die(
            "Nenhum token encontrado.\n"
            "Defina DFMED_TOKEN ou crie "
            + TOKEN_FILES[0]
            + " com o valor da chave `token` do sessionStorage do dfmed.app.br.\n"
            "Veja o cabeçalho de dfmed.py para o passo a passo."
        )
    raw = raw.strip()
    # Aceita tanto o JSON puro quanto algo já entre aspas; normaliza para a
    # mesma string que o navegador guarda em sessionStorage.
    try:
        obj = json.loads(raw)
        # Se o usuário colou um objeto, reserializa compacto (como JSON.stringify).
        if isinstance(obj, (dict, list)):
            return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
    except json.JSONDecodeError:
        pass
    return raw


def _ssl_context():
    ctx = ssl.create_default_context()
    bundle = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
    if bundle and os.path.isfile(bundle):
        ctx.load_verify_locations(bundle)
    return ctx


def request(method, path, body=None):
    url = BASE_URL + path
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json",
        "token": load_token(),
    }
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=_ssl_context(), timeout=60) as resp:
            payload = resp.read()
            ctype = resp.headers.get("Content-Type", "")
            return payload, ctype
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:500]
        if exc.code in (401, 403):
            die("token inválido ou expirado (HTTP %d). Reobtenha o token." % exc.code)
        die("Erro HTTP %d em %s\n%s" % (exc.code, path, detail))
    except urllib.error.URLError as exc:
        die("Falha de conexão com %s: %s" % (url, exc.reason))


def get_json(path):
    payload, _ = request("GET", path)
    return _parse(payload, path)


def post_json(path, body):
    payload, _ = request("POST", path, body)
    return _parse(payload, path)


def _parse(payload, path):
    text = payload.decode("utf-8", "replace").strip()
    if text == "" or text.lower() in ("null", "false"):
        die(
            "Resposta vazia/negada em %s — token inválido/expirado ou sem permissão."
            % path
        )
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


# --------------------------------------------------------------------------- #
# util
# --------------------------------------------------------------------------- #
def die(msg):
    print("erro: " + msg, file=sys.stderr)
    sys.exit(1)


def out(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def q(params):
    return urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})


def token_obj():
    try:
        return json.loads(load_token())
    except (json.JSONDecodeError, TypeError):
        return {}


def resolve_usr(arg):
    if arg:
        return arg
    uid = token_obj().get("usrID")
    if not uid:
        die("--usr não informado e não foi possível lê-lo do token.")
    return uid


# --------------------------------------------------------------------------- #
# comandos
# --------------------------------------------------------------------------- #
def cmd_whoami(a):
    out(get_json("Usuarios/GetUsuarioLogado?" + q({"usrID": resolve_usr(a.usr)})))


def cmd_clinicas(a):
    out(get_json("Usuarios/TemClinicas?" + q({"usrID": resolve_usr(a.usr)})))


def cmd_renova(a):
    out(get_json("Session/RenovaToken"))


def cmd_agenda_list(a):
    out(get_json("Agenda/ListaAgendas?" + q({"usrID": resolve_usr(a.usr)})))


def cmd_agenda_dia(a):
    out(
        get_json(
            "Agenda/HorariosList?"
            + q({"agID": a.ag, "dataIniStr": a.ini, "dataFimStr": a.fim or a.ini})
        )
    )


def cmd_aniversariantes(a):
    out(get_json("CadPac/ListAniversariantes?" + q({"data": a.data})))


def cmd_horario_get(a):
    out(get_json("Agenda/GetHorario?" + q({"aghID": a.agh})))


def cmd_horario_status(a):
    out(get_json("Agenda/HorarioMudaStatus?" + q({"aghID": a.agh, "status": a.status})))


def cmd_horario_desmarca(a):
    confirm(a, "Desmarcar o horário %s" % a.agh)
    out(get_json("Agenda/HorarioDesmarca?" + q({"aghID": a.agh})))


def cmd_paciente_busca(a):
    filtro = {
        "nome": a.nome or "",
        "celular": a.celular or "",
        "dtNasc": a.dtnasc or "",
        "limite": a.limite,
    }
    out(post_json("CadPac/BuscaPaciente", filtro))


def cmd_paciente(a):
    out(get_json("CadPac/GetGui?" + q({"pacID": a.id})))


def cmd_paciente_telefones(a):
    out(get_json("CadPac/TelefoneList?" + q({"pacID": a.id})))


def cmd_prontuario_list(a):
    out(get_json("Prontuario/List?" + q({"pacID": a.pac, "ordem": a.ordem})))


def cmd_prontuario_get(a):
    out(get_json("Prontuario/Get?" + q({"id": a.id})))


def cmd_prontuario_pdf(a):
    payload, _ = request("GET", "Prontuario/Pdf?" + q({"pacfID": a.pacf}))
    # a API pode devolver bytes de PDF ou base64; grava o que vier.
    data = payload
    text = payload.decode("utf-8", "replace").strip()
    if text.startswith('"') and text.endswith('"'):
        import base64

        try:
            data = base64.b64decode(json.loads(text))
        except Exception:
            pass
    with open(a.out, "wb") as fh:
        fh.write(data)
    print("PDF gravado em %s (%d bytes)" % (a.out, len(data)))


def cmd_prontuario_save(a):
    with open(a.file, encoding="utf-8") as fh:
        body = json.load(fh)
    confirm(
        a,
        "Gravar registro no prontuário (pacID=%s, id=%s)"
        % (body.get("pacID"), body.get("id")),
    )
    out(post_json("Prontuario/Save", body))


def cmd_raw(a):
    body = json.loads(a.body) if a.body else None
    if body is None and a.method == "GET":
        out(get_json(a.path))
    else:
        out(post_json(a.path, body or {}))


def confirm(a, action):
    if getattr(a, "yes", False):
        return
    ans = input("%s? Isto ALTERA dados no DFMed. [s/N] " % action).strip().lower()
    if ans not in ("s", "sim", "y", "yes"):
        die("cancelado pelo usuário.")


# --------------------------------------------------------------------------- #
# parser
# --------------------------------------------------------------------------- #
def build_parser():
    p = argparse.ArgumentParser(description="Cliente do prontuário DFMed.")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(name, fn, help=""):
        sp = sub.add_parser(name, help=help)
        sp.set_defaults(func=fn)
        return sp

    add("whoami", cmd_whoami, "Dados do usuário logado e suas clínicas").add_argument("--usr")
    add("clinicas", cmd_clinicas, "Clínicas do usuário").add_argument("--usr")
    add("renova", cmd_renova, "Tenta renovar o token de sessão")

    sp = add("agenda-list", cmd_agenda_list, "Lista as agendas do usuário")
    sp.add_argument("--usr")

    sp = add("agenda-dia", cmd_agenda_dia, "Horários de uma agenda num intervalo")
    sp.add_argument("--ag", required=True, help="agID (id da agenda)")
    sp.add_argument("--ini", required=True, help="data inicial (ex.: 2026-11-17)")
    sp.add_argument("--fim", help="data final (padrão = inicial)")

    sp = add("aniversariantes", cmd_aniversariantes, "Pacientes aniversariantes")
    sp.add_argument("--data", required=True, help="data (ex.: 2026-11-17)")

    sp = add("horario-get", cmd_horario_get, "Detalhe de um horário")
    sp.add_argument("--agh", required=True)

    sp = add("horario-status", cmd_horario_status, "Muda status de um horário")
    sp.add_argument("--agh", required=True)
    sp.add_argument("--status", required=True)

    sp = add("horario-desmarca", cmd_horario_desmarca, "Desmarca um horário")
    sp.add_argument("--agh", required=True)
    sp.add_argument("--yes", action="store_true")

    sp = add("paciente-busca", cmd_paciente_busca, "Busca pacientes por filtro")
    sp.add_argument("--nome")
    sp.add_argument("--celular")
    sp.add_argument("--dtnasc", help="data de nascimento")
    sp.add_argument("--limite", type=int, default=50)

    sp = add("paciente", cmd_paciente, "Ficha (GUI) de um paciente")
    sp.add_argument("--id", required=True, help="pacID")

    sp = add("paciente-telefones", cmd_paciente_telefones, "Telefones de um paciente")
    sp.add_argument("--id", required=True, help="pacID")

    sp = add("prontuario-list", cmd_prontuario_list, "Registros do prontuário de um paciente")
    sp.add_argument("--pac", required=True, help="pacID")
    sp.add_argument("--ordem", default="desc")

    sp = add("prontuario-get", cmd_prontuario_get, "Um registro do prontuário")
    sp.add_argument("--id", required=True, help="id do registro (pacfID)")

    sp = add("prontuario-pdf", cmd_prontuario_pdf, "Baixa o PDF de um registro")
    sp.add_argument("--pacf", required=True, help="pacfID")
    sp.add_argument("--out", required=True, help="arquivo de saída .pdf")

    sp = add("prontuario-save", cmd_prontuario_save, "Grava/edita um registro (ESCRITA)")
    sp.add_argument("--file", required=True, help="JSON do registro")
    sp.add_argument("--yes", action="store_true")

    sp = add("raw", cmd_raw, "Chamada crua a um endpoint")
    sp.add_argument("--method", default="GET", choices=["GET", "POST"])
    sp.add_argument("path", help="ex.: Session/Environment")
    sp.add_argument("--body", help="corpo JSON para POST")

    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
