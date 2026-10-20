# Qdrant Full-Replica Replication

Cloning an entire Qdrant memory store to another machine so each node runs its **own**
Qdrant with a complete copy. Used for the hydra mesh (see `hydra-protocol`): one node is
the source, targets get a full replica.

## Why full replica, not delta sync

**Vectors don't conflict.** A memory embedding is an immutable fact, so merging two
Qdrants is the **union of points**, keyed by ID. Full replica therefore removes the need
for conflict resolution entirely. That is why "clone it all" is the right default for a
vector store even though it is the wrong default for a document store.

## Size reality — measure the DATA, not the container

`docker system df` reports the container's *writable layer*, which can be wildly larger
than the data. On this VM it reported **14 GB** while the actual store was **380 MB**.

Measure the real thing:
```bash
docker inspect <container> --format '{{range .Mounts}}{{.Source}} => {{.Destination}}{{println}}{{end}}'
du -sh /path/to/qdrant_storage        # the bind-mounted data dir
```
A 20-collection / 42,919-point store is ~380 MB of data — a full clone fits on a laptop
or a phone. Do not let the container number scare you off a full replica.

## Inventory the store before cloning

The inventory + clone scripts ship with this skill in `scripts/`:
```bash
python3 scripts/qdrant_report.py                   # points + vector config per collection
python3 scripts/qdrant_peek.py <collection> -n 6   # several points from one collection
python3 scripts/qdrant_snapshot.py --out DIR       # snapshot every collection
python3 scripts/qdrant_restore.py --dir DIR        # restore into a local Qdrant
bash    scripts/qcounts.sh                         # verify point counts per collection
```

**Pitfall — never characterize a collection from a single scroll point.** The first point
of a collection can be a stray test entry (`{"text": "test", "id": 12345}`). Sampling only
the first point once led to a 107 MB collection of real session memories being written off
as "test junk". Sample several points, and check whether the count is in the thousands
before calling anything junk.

**Pitfall — a collection named after another daemon may still be yours.**
Framework-prefixed collections (e.g. `intelligent_gould_*`) look like third-party data but
are the daemon's own history from an earlier frontend. Ask before excluding.

**Pitfall — do not trim a user's memory to save space on your own initiative.** Proposing
to skip "the archive" or "the junk" is a judgment call about someone's history. Present
what each collection actually holds and let the user decide; if they say clone it all,
clone it all.

## The pipeline

### 1. Snapshot (on the source)

Qdrant has native snapshots — consistent, compressed, one file per collection.

```bash
python3 scripts/qdrant_snapshot.py --out /mnt/data/qdrant-snapshots
python3 scripts/qdrant_snapshot.py --out DIR --only coll_a,coll_b   # subset
```

`POST /collections/{name}/snapshots` creates it; `GET .../snapshots/{file}` downloads it.
**Delete the server-side copy right after download** (`DELETE .../snapshots/{file}`) or the
source disk fills. Write to a large partition, never a nearly-full `/`.

### 2. Transfer

```bash
tar cf qdrant-snapshots.tar qdrant-snapshots/
scp -i ~/.hydra/hydra_ed25519 -q qdrant-snapshots.tar user@host:/target/dir/
```
395 MB moved in ~17 s over Tailscale.

### 3. Restore (on the target)

`POST /collections/{name}/snapshots/upload?priority=snapshot` with multipart field
`snapshot` creates or replaces the collection from the file.

```bash
python3 scripts/qdrant_restore.py --dir ./qdrant-snapshots --url http://127.0.0.1:6333
```

### 4. Verify — exact point counts, per collection

```bash
bash scripts/qcounts.sh http://127.0.0.1:6333
```
Compare against the source's counts collection by collection. A clean restore is an
**exact match** (e.g. 20/20 collections, 42,919/42,919 points). Point counts, not
"it returned 200", are the proof.

## Running Qdrant on a Windows host

**Docker Desktop cannot be started from an SSH session.** Its engine needs the interactive
desktop session; launching `Docker Desktop.exe` over SSH leaves the `docker-desktop` WSL
distro and `com.docker.service` stopped and the CLI hanging. `Start-Service
com.docker.service` succeeds from an elevated session, but the engine still never comes
up. Do not burn time on it — go around it.

**Go around it: Qdrant natively inside a WSL distro.**

```powershell
wsl --install -d Debian --no-launch      # WSL2 already exists if Docker Desktop is installed
```
Then inside Debian (runs as root):
```bash
mkdir -p /opt/qdrant && cd /opt/qdrant
curl -sL -o q.tgz https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-unknown-linux-gnu.tar.gz
tar xzf q.tgz && rm q.tgz
```

**Make it survive WSL idling out.** A WSL distro shuts down when idle and takes any
foreground process with it — Qdrant dies within minutes. Install it as a systemd service
(systemd is on by default in modern WSL distros; confirm `ps -p 1 -o comm=` says
`systemd`):

```bash
printf '%s\n' \
  "[Unit]" "Description=Qdrant vector database" "After=network.target" "" \
  "[Service]" "Type=simple" "WorkingDirectory=/opt/qdrant" "ExecStart=/opt/qdrant/qdrant" \
  "Restart=always" "RestartSec=5" "" \
  "[Install]" "WantedBy=multi-user.target" > /etc/systemd/system/qdrant.service
systemctl daemon-reload && systemctl enable --now qdrant
```
`Restart=always` + `enable` means it returns after both idleness and reboot.

### Windows/WSL remote-command quoting

When driving WSL over SSH, **put pipes and redirects INSIDE the WSL command**:
```bash
ssh host 'wsl -d Debian -- bash -c "curl -s http://127.0.0.1:6333/collections | head -c 200"'
```
A pipe in the outer ssh string is evaluated by **cmd.exe** on the Windows side, which has
no `head`/`grep`/`sort` — you get `'head' is not recognized...` and no output. Scripts are
the clean answer: write the script, `scp` it, then
`wsl -d Debian -- bash /mnt/c/.../script.sh` with all logic inside the script.

**Expect a startup race.** A script that curls Qdrant immediately after starting the
distro can get an empty body while a direct curl a moment later succeeds — WSL cold-starts
the service asynchronously. Re-run the script rather than concluding the restore failed.
