# Migracao para Raspberry Pi OS Trixie

Documento de operacao. Ler inteiro antes de comecar: a instalacao limpa apaga o
cartao, e ha dados no Pi que nao existem em nenhum outro lugar.

## Por que migrar

Duas travas do Bookworm caem de uma vez:

| Trava | Bookworm | Trixie |
| --- | --- | --- |
| PySide6 | 6.8.0.2 (ultima `manylinux_2_31`, glibc 2.36) | 6.11, wheels `manylinux_2_39` |
| OpenGL ES | 3.1 sem suporte pleno no driver do Pi 5 | 3.x completo, exigido pelo LIVI |
| Python | 3.11 | 3.13 |

O LIVI - central de CarPlay e Android Auto - so roda no Pi 5 com Trixie. Sem a
migracao, a projecao fica fora do projeto.

## Antes de reinstalar

Estes itens vivem apenas no Pi e somem com a formatacao:

- [ ] **Codigo**: `git push origin main` (GitHub) e conferir que o commit apareceu
- [ ] **Repositorio bare** `~/picockpit.git`: e o remote de deploy; sera recriado
- [ ] **Banco de viagens**: `scripts/backup.sh` e copiar o `.tar.gz` para o PC

```bash
# no Pi
cd ~/picockpit
./scripts/backup.sh
ls -lt ~/picockpit-backups | head -3

# no PC (WSL)
scp <usuario>@<ip-do-pi>:~/picockpit-backups/picockpit-*.tar.gz ~/
```

- [ ] Anotar a configuracao de rede (Wi-Fi, IP fixo se houver)
- [ ] Lembrar que o Raspberry Pi Connect precisara ser vinculado de novo

## Instalacao

1. Gravar o **Raspberry Pi OS 13 (Trixie), 64 bits, com desktop** pelo Raspberry
   Pi Imager, em outro cartao se possivel - o cartao antigo vira backup fisico
2. No Imager, pre-configurar: nome do host, usuario, Wi-Fi e **SSH habilitado**
3. Primeiro boot, e entao:

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y git rpi-connect
rpi-connect on
rpi-connect signin      # vincula o dispositivo de novo
```

## Restaurar o PiCockpit

```bash
# 1. Repositorio bare de deploy
git init --bare ~/picockpit.git

# 2. Codigo
git clone https://github.com/<seu-usuario>/picockpit.git ~/picockpit
# ou, do PC:  git push pi HEAD:refs/heads/main  e depois clonar do bare

# 3. Ambiente
~/picockpit/scripts/setup_pi.sh

# 4. Banco de viagens
~/picockpit/scripts/restore.sh ~/picockpit-<data>.tar.gz

# 5. Servico
~/picockpit/scripts/install_service.sh
systemctl --user start picockpit
```

## Verificar depois

```bash
grep PRETTY /etc/os-release          # Debian 13 (trixie)
ldd --version | head -1              # glibc 2.41 ou superior
python3 -V                           # 3.13
~/picockpit-venv/bin/python -c "import PySide6; print(PySide6.__version__)"
QT_QPA_PLATFORM=offscreen ~/picockpit-venv/bin/python -m pytest -q
~/picockpit/scripts/lint_qml.sh
```

## O que provavelmente vai quebrar

**PySide6 6.11 nao e 6.8.** A trava do `pyproject.toml` precisa sair, e a API de
`QtQuick.Shapes` mudou entre as versoes - os mostradores sao o ponto a conferir
primeiro. O teste de fumaca da interface existe justamente para isso: ele
transforma qualquer aviso do QML em falha.

**O compositor pode nao ser mais o labwc.** Conferir com
`echo $XDG_CURRENT_DESKTOP`; as regras de posicionamento de janela para a
projecao dependem disso.

**Python 3.13 no lugar do 3.11.** O container de desenvolvimento precisa passar
para `python:3.13-trixie` para as duas trilhas voltarem a espelhar uma a outra.
