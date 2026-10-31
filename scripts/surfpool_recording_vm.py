"""Record offline VM fixture inputs for signed Surfpool replay.

The recording behavior is retained from the former localnet helper; this module
contains only the VM wrapper used by the on-chain differential runners.
"""


def require_aligned_runs(prepared, left, right):
    """Refuse to compare prepared fixtures against runs of a different length.

    The differentials compare the prepared fixtures to the original and
    candidate runs positionally with zip. zip stops at the shortest sequence, so
    a run that returned fewer rows than it was given would compare only a
    prefix and could still report no mismatches.
    """
    lengths = {'prepared': len(prepared), 'original': len(left), 'candidate': len(right)}
    if len(set(lengths.values())) != 1:
        raise ValueError(f'surfpool runs do not cover the same cases: {lengths}')


class RecordingVM:
    def __init__(self,vm): self.vm=vm;self.accounts={};self.transaction=None
    def with_transaction_history(self,n):self.vm.with_transaction_history(n);return self
    def __getattr__(self,name): return getattr(self.vm,name)
    def set_account(self,key,account):
        self.accounts[str(key)]={'lamports':account.lamports,'data':account.data.hex(),'owner':str(account.owner),'executable':account.executable}
        return self.vm.set_account(key,account)
    def send_transaction(self,transaction):
        self.transaction=transaction
        return self.vm.send_transaction(transaction)
