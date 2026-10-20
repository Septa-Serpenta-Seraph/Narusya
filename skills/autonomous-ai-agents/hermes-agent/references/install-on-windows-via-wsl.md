# Installing Hermes on a Windows Host via WSL

Hermes runs natively on Windows, but a Windows box can also host a full Hermes
**inside a WSL distro** — a real Linux environment where the installer, PM, and
tool binaries behave as they do on a server. This is the path for a *second,
independent* Hermes instance on a Windows machine (a parallel node, not a client).

Reach for it when Docker Desktop is unavailable (its engine needs the interactive
desktop session and will not start from an SSH session), or whenever you need a
Linux toolchain on a Windows box.

## 0. Work carefully — the operator's machine is not a sandbox

Installing onto someone's personal computer changes their machine. Before running
anything:

1. **Read the installer first.** Fetch it and skim it.
   `bash install.sh --manifest` prints the stage list as JSON without installing.
2. **Install the build prerequisites first** so the installer's prerequisite stage
   does not fail halfway through.
3. **Run `--non-interactive`.** The `setup` and `gateway` stages need user input;
   non-interactive skips them. That is the point — it yields an **inert** install:
   no API keys, no service, no bot, nothing listening.
4. **Do not touch the host's native config.** Install into the WSL distro's own
   home; leave the Windows-side `%USERPROFILE%\.hermes` alone.
5. **Report what you did AND what you deliberately did not do**, so the operator
   knows the instance is installed-but-not-running and can be lit later.

## 1. Install the distro

```powershell
wsl --install -d Debian --no-launch
wsl -l -v                      # confirm the distro is listed
```

WSL2 is already present if Docker Desktop is installed. A `--no-launch` distro
starts as **root** on first use — fine for a service-style install; create a normal
user if it will be driven interactively.

## 2. Build prerequisites

```bash
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq \
  git curl ca-certificates build-essential tar unzip xz-utils \
  python3 python3-venv python3-dev pkg-config libssl-dev
```

Verify with `for t in git curl tar unzip sha256sum python3; do command -v $t; done`.
Node is **not** needed up front — the installer's `products` stage brings its own.

## 3. Run the installer, non-interactively

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh -o /tmp/hermes-install.sh
bash /tmp/hermes-install.sh --non-interactive >/tmp/hermes-install.log 2>&1
tail -40 /tmp/hermes-install.log
```

Stage protocol (from `--manifest`):

| Stage | Needs input |
|---|---|
| prerequisites, repository, venv, python-deps, config, products, complete | no |
| setup (API keys), gateway (service) | **yes** — skipped by `--non-interactive` |

Success prints `✓ Hermes Agent install complete. Run: hermes`. It lands in
`$HOME/.hermes` inside the distro and appends `~/.local/bin` to `.bashrc`/`.profile`.

## 4. Post-install fixes

**`hermes` not on PATH in a non-login shell.** The installer edits `.bashrc`
(interactive) and `.profile` (login); `wsl -d Debian -- hermes` gets neither.
Prefix the path: `export PATH="$HOME/.local/bin:$PATH"; hermes --version`.

**`cua-driver` fails to stage** with `error while loading shared libraries:
libXi.so.6` (then `libxkbcommon.so.0`). The optional computer-use driver links
against X11/GL libs a minimal distro omits. Install them and retry — the rest of
the install is unaffected:

```bash
apt-get install -y libxi6 libxtst6 libxrandr2 libxfixes3 libxext6 libx11-6 \
                   libxkbcommon0 libxkbcommon-x11-0 libwayland-client0 libgl1 libegl1
ldconfig
export PATH="$HOME/.local/bin:$PATH"; hermes pm install cua-driver
```

A missing optional tool is not an install failure — `hermes pm doctor` lists what
is still unavailable.

## 5. Driving the WSL instance over SSH

**Put pipes and redirects INSIDE the WSL command**, and prefer shipping a script
over inline quoting:

```bash
ssh host 'wsl -d Debian -- bash -c "export PATH=\$HOME/.local/bin:\$PATH; hermes --version"'

# cleanest — all logic inside the script:
scp script.sh host:C:/Users/<user>/.hermes-agent/
ssh host 'wsl -d Debian -- bash /mnt/c/Users/<user>/.hermes-agent/script.sh'
```

An outer pipe (`... | head`) is evaluated by **cmd.exe**, which has no Unix text
tools — you get `'head' is not recognized` and no output.
