#!/usr/bin/env python3
"""Conservative available-storage budgets for reconstruction operations.

The guard measures filesystem-reported bytes available to the current user.
It does not estimate reclaimable cache bytes or APFS clone extents and never
removes data.  Measurements are observations, not reservations.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
import time
from typing import Callable, Iterable


SCHEMA = 'reconstruction-resource-receipt-v1'
IDENTITY_SCHEMA = 'reconstruction-resource-budget-v1'
IMPLEMENTATION_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


class ResourceBudgetError(RuntimeError):
    """Base class for unavailable measurements and crossed floors."""


class DiskMeasurementError(ResourceBudgetError):
    """The selected filesystem cannot be measured conservatively."""


class DiskBudgetExceeded(ResourceBudgetError):
    """At least one selected filesystem crossed its configured floor."""

    def __init__(self, observation):
        self.observation = observation
        crossed = [row for row in observation['filesystems'] if row['below_floor']]
        detail = ', '.join(f"{row['probe_path']}={row['available_bytes']}"
                           for row in crossed)
        super().__init__(f'disk safety floor crossed ({detail})')


def validate_floor(value):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError('minimum free bytes must be a positive integer')
    return value


def validate_interval(value):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value <= 0 or value > 3600):
        raise ValueError('disk check interval must be positive, finite, and at most one hour')
    return float(value)


def _absolute(path):
    value = Path(path).expanduser()
    if not value.is_absolute():
        value = Path.cwd() / value
    return value.resolve(strict=False)


def existing_probe(path):
    """Return the closest existing ancestor without creating the target."""
    candidate = _absolute(path)
    while True:
        try:
            candidate.stat()
            return candidate
        except FileNotFoundError:
            parent = candidate.parent
            if parent == candidate:
                raise DiskMeasurementError(f'no existing ancestor for filesystem path: {path}')
            candidate = parent
        except OSError as error:
            raise DiskMeasurementError(f'cannot inspect filesystem path {path}: {error}') from error


def available_bytes(path):
    """Measure bytes available to this user on the filesystem containing path."""
    if not hasattr(os, 'statvfs'):
        raise DiskMeasurementError('os.statvfs is unavailable on this platform')
    probe = existing_probe(path)
    try:
        values = os.statvfs(probe)
        blocks, fragment = values.f_bavail, values.f_frsize
    except (AttributeError, OSError) as error:
        raise DiskMeasurementError(f'cannot measure available storage at {probe}: {error}') from error
    if (isinstance(blocks, bool) or isinstance(fragment, bool)
            or not isinstance(blocks, int) or not isinstance(fragment, int)
            or blocks < 0 or fragment <= 0):
        raise DiskMeasurementError(f'invalid statvfs values at {probe}')
    return blocks * fragment


def filesystem_identity(paths: Iterable[os.PathLike | str]):
    requested = sorted({_absolute(path) for path in paths}, key=lambda path: str(path))
    if not requested:
        raise ValueError('at least one filesystem path is required')
    grouped = {}
    for path in requested:
        probe = existing_probe(path)
        try:
            device = probe.stat().st_dev
        except OSError as error:
            raise DiskMeasurementError(f'cannot identify filesystem at {probe}: {error}') from error
        if isinstance(device, bool) or not isinstance(device, int):
            raise DiskMeasurementError(f'invalid filesystem device identity at {probe}')
        row = grouped.setdefault(device, {'device': device, 'probe_path': str(probe),
                                          'monitored_paths': []})
        row['probe_path'] = min(row['probe_path'], str(probe))
        row['monitored_paths'].append(str(path))
    return [dict(row, monitored_paths=sorted(row['monitored_paths']))
            for _, row in sorted(grouped.items())]


@dataclass(frozen=True)
class DiskBudgetConfig:
    floor_bytes: int
    paths: tuple[str, ...] = ()
    check_interval: float = 1.0

    def __post_init__(self):
        validate_floor(self.floor_bytes)
        validate_interval(self.check_interval)
        object.__setattr__(self, 'paths', tuple(str(_absolute(path)) for path in self.paths))
        if len(set(self.paths)) != len(self.paths):
            raise ValueError('disk paths must be unique')

    def monitor(self, paths=()):
        selected = tuple(self.paths) + tuple(str(_absolute(path)) for path in paths)
        return DiskBudget(self.floor_bytes, selected, self.check_interval)

    def as_dict(self):
        return {'floor_bytes': self.floor_bytes, 'paths': list(self.paths),
                'check_interval_seconds': self.check_interval}


class DiskBudget:
    """One operation's measurements and fail-closed receipt state."""

    def __init__(self, floor_bytes, paths, check_interval=1.0,
                 measure: Callable[[os.PathLike | str], int] = available_bytes):
        self.floor_bytes = validate_floor(floor_bytes)
        self.check_interval = validate_interval(check_interval)
        self.filesystems = filesystem_identity(paths)
        self.measure = measure
        self.observations = []
        self.guard_fired = None

    @property
    def identity(self):
        return {'schema': IDENTITY_SCHEMA, 'floor_bytes': self.floor_bytes,
                'check_interval_seconds': self.check_interval,
                'filesystems': self.filesystems,
                'implementation_sha256': IMPLEMENTATION_SHA256}

    def sample(self, phase, *, enforce=True):
        if not isinstance(phase, str) or not phase:
            raise ValueError('resource phase must be a nonempty string')
        rows = []
        for filesystem in self.filesystems:
            probe = Path(filesystem['probe_path'])
            current_probe = existing_probe(probe)
            try:
                device = current_probe.stat().st_dev
            except OSError as error:
                raise DiskMeasurementError(f'cannot recheck filesystem at {probe}: {error}') from error
            if device != filesystem['device']:
                raise DiskMeasurementError(f'filesystem identity changed at {probe}')
            try:
                available = self.measure(probe)
            except ResourceBudgetError:
                raise
            except Exception as error:
                raise DiskMeasurementError(f'available-byte measurement failed at {probe}: {error}') from error
            if isinstance(available, bool) or not isinstance(available, int) or available < 0:
                raise DiskMeasurementError(f'invalid available-byte measurement at {probe}')
            rows.append({'device': filesystem['device'], 'probe_path': str(probe),
                         'available_bytes': available,
                         'below_floor': available < self.floor_bytes})
        observation = {'sequence': len(self.observations), 'phase': phase,
                       'observed_ns': time.time_ns(), 'filesystems': rows}
        self.observations.append(observation)
        if enforce and any(row['below_floor'] for row in rows):
            if self.guard_fired is None:
                self.guard_fired = {'sequence': observation['sequence'], 'phase': phase,
                                    'classification': 'resource_budget_exceeded'}
            raise DiskBudgetExceeded(observation)
        return observation

    def monitor(self, phase='runtime_monitor'):
        """Compiler callback: return a stop reason instead of raising."""
        try:
            self.sample(phase)
        except DiskBudgetExceeded as error:
            return {'classification': 'resource_budget_exceeded',
                    'observation_sequence': error.observation['sequence']}
        return None

    def receipt(self, *, operation, outcome, failure_classification=None,
                candidate_published=False, build_identity=None, retained_logs=()):
        if not self.observations:
            raise ValueError('resource receipt requires at least one observation')
        minima = {}
        for observation in self.observations:
            for row in observation['filesystems']:
                key = str(row['device'])
                minima[key] = min(minima.get(key, row['available_bytes']), row['available_bytes'])
        return {
            'schema': SCHEMA,
            'budget': self.identity,
            'operation': operation,
            'outcome': outcome,
            'failure_classification': failure_classification,
            'candidate_published': bool(candidate_published),
            'guard_fired': self.guard_fired,
            'minimum_observed_free_bytes': minima,
            'observations': self.observations,
            'build_identity': build_identity or {},
            'retained_logs': [str(path) for path in retained_logs],
            'limitations': [
                'available bytes are measured, not reserved',
                'sudden external consumption and whole-system crashes remain possible',
                'no logical file size is treated as recoverable physical storage',
            ],
        }


def atomic_write_receipt(path, receipt):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.resource-receipt-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(receipt, stream, indent=2, sort_keys=True)
            stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return path


def verify_receipt(value, *, expected_budget=None):
    """Independently recompute internal receipt acceptance."""
    if isinstance(value, (str, os.PathLike)):
        value = json.loads(Path(value).read_text(encoding='utf-8'))
    if not isinstance(value, dict) or value.get('schema') != SCHEMA:
        raise ValueError('invalid resource receipt schema')
    budget = value.get('budget')
    if not isinstance(budget, dict) or budget.get('schema') != IDENTITY_SCHEMA:
        raise ValueError('invalid resource budget identity')
    validate_floor(budget.get('floor_bytes'))
    validate_interval(budget.get('check_interval_seconds'))
    if budget.get('implementation_sha256') != IMPLEMENTATION_SHA256:
        raise ValueError('resource budget implementation identity mismatch')
    if expected_budget is not None and budget != expected_budget:
        raise ValueError('stale or unexpected resource budget identity')
    filesystems = budget.get('filesystems')
    if not isinstance(filesystems, list) or not filesystems:
        raise ValueError('resource budget has no filesystems')
    expected_devices = []
    for row in filesystems:
        if (not isinstance(row, dict) or type(row.get('device')) is not int
                or not isinstance(row.get('probe_path'), str)
                or not isinstance(row.get('monitored_paths'), list)):
            raise ValueError('invalid filesystem identity')
        expected_devices.append(row['device'])
    if len(set(expected_devices)) != len(expected_devices):
        raise ValueError('duplicate filesystem identity')
    observations = value.get('observations')
    if not isinstance(observations, list) or not observations:
        raise ValueError('resource receipt has no observations')
    minima = {}
    crossed = set()
    for sequence, observation in enumerate(observations):
        if (not isinstance(observation, dict) or observation.get('sequence') != sequence
                or not isinstance(observation.get('phase'), str)
                or type(observation.get('observed_ns')) is not int):
            raise ValueError('invalid resource observation')
        rows = observation.get('filesystems')
        if not isinstance(rows, list) or [row.get('device') for row in rows] != expected_devices:
            raise ValueError('resource observation filesystem mismatch')
        for row in rows:
            available = row.get('available_bytes')
            below = row.get('below_floor')
            if type(available) is not int or available < 0 or type(below) is not bool:
                raise ValueError('invalid available-byte observation')
            if below != (available < budget['floor_bytes']):
                raise ValueError('resource floor classification mismatch')
            key = str(row['device'])
            minima[key] = min(minima.get(key, available), available)
            if below:
                crossed.add(sequence)
    if value.get('minimum_observed_free_bytes') != minima:
        raise ValueError('resource minimum does not match observations')
    guard = value.get('guard_fired')
    if guard is not None:
        if (not isinstance(guard, dict) or guard.get('sequence') not in crossed
                or guard.get('classification') != 'resource_budget_exceeded'
                or guard.get('phase') != observations[guard['sequence']]['phase']):
            raise ValueError('resource guard evidence is inconsistent')
    if value.get('failure_classification') == 'resource_budget_exceeded' and guard is None:
        raise ValueError('resource failure is missing guard evidence')
    if type(value.get('candidate_published')) is not bool:
        raise ValueError('candidate publication state must be boolean')
    if not isinstance(value.get('build_identity'), dict):
        raise ValueError('resource receipt build identity must be an object')
    if not isinstance(value.get('retained_logs'), list):
        raise ValueError('resource receipt retained logs must be an array')
    return {'accepted': True, 'observation_count': len(observations),
            'guard_fired': guard is not None, 'minimum_observed_free_bytes': minima}


def _main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('receipt', type=Path)
    args = parser.parse_args(argv)
    try:
        result = verify_receipt(args.receipt)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.exit(1, f'invalid resource receipt: {error}\n')
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(_main())
