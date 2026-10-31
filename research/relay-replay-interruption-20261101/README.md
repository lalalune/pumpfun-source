# Relay replay interruption cleanup

The public replay supervisor starts its command in a separate POSIX session.
At base `9120883a957d7d9b2cab6140f66fb5bc9e6774d5`, Ctrl-C interrupts the
supervisor but bypasses its normal timeout/disk cleanup. The command and its
descendants continue after the supervisor returns. A failure writing the
process record after `Popen` has the same effect.

`probe.py` executes the exact base or current `monitored()` with authored Python
processes. It sends a real SIGINT to the supervisor, waits for its exit, then
releases a file barrier that surviving child/grandchild processes can observe.
Both processes write markers after the base supervisor exits. Neither writes
after the correction. The probe removes its owned processes after observation,
including when testing the defective base.

| Actual scenario | Base child / grandchild write after return | Fixed |
| --- | --- | --- |
| SIGINT, ordinary child and grandchild | yes / yes | no / no |
| SIGINT, both ignore SIGTERM | yes / yes | no / no |
| SIGINT, only grandchild ignores SIGTERM | yes / yes | no / no |
| Process-record creation raises `FileExistsError` | yes / yes | no / no |

The correction sends SIGTERM on exceptional exits, retains the existing
three-second grace period, and sends SIGKILL to any remaining owned group
before reaping the leader and propagating the original exception. Checking the
group after the leader exits covers descendants that ignore SIGTERM. Partial
logs and the existing process record remain available.

```sh
python -B research/relay-replay-interruption-20261101/probe.py . \
  --revision 9120883a957d7d9b2cab6140f66fb5bc9e6774d5
python -B research/relay-replay-interruption-20261101/probe.py .
python -B tests/test_relay_replay_process_cleanup.py -v
python -B reconstruction/donation-relay/native-linux-v148-20261030/test_replay.py --repo . -v
```

`results.json` records actual before/after observations on macOS arm64 with
CPython 3.12.13. The five new tests pass, including ordinary successful command
output and exception/diagnostic preservation. Existing timeout, disk-floor,
packet and admission tests pass (9 passed, one second-filesystem skip).
The required tooling suite passes 250 tests and evidence verification passes
all nine captures. Existing `contract-tests` discovery runs the new regression.

This extends the public launcher's existing host-process qualification; it is
not another Donation Relay compiler build, a new program result, or a runtime
equivalence claim. Cleanup is for the owned process group. It does not cover
descendants that deliberately leave the group, killing the supervisor with
SIGKILL, or repeated interruption during cleanup. Historical measured inputs,
compiler outputs, recipes and seals are unchanged.
