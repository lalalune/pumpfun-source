"""Validation shared by append admission and offline attempt-ledger audits."""
import datetime as dt
import json


def validate_row(row, statuses):
    if not isinstance(row, dict) or row.get('schema') != 'main-pump-attempt-v1':
        raise ValueError('expected a main-pump-attempt-v1 object')
    for field in ('attempt_id', 'timestamp_utc', 'lane', 'approach', 'target', 'dedupe_key', 'hypothesis'):
        if not isinstance(row.get(field), str) or not row[field].strip():
            raise ValueError(f'{field} must be a nonempty string')
    if row.get('status') not in statuses:
        raise ValueError('unknown attempt status')
    if not isinstance(row.get('data'), dict):
        raise ValueError('data must be an object')
    timestamp = dt.datetime.fromisoformat(row['timestamp_utc'].replace('Z', '+00:00'))
    if timestamp.utcoffset() != dt.timedelta(0):
        raise ValueError('timestamp_utc must include a UTC offset')
    json.dumps(row, allow_nan=False)


def inspect_ledger(text, statuses):
    rows, errors = [], []
    ids, keys = {}, {}

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'duplicate JSON property: {key}')
            result[key] = value
        return result

    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line, object_pairs_hook=unique_object)
            validate_row(row, statuses)
            for field, seen in [('attempt_id', ids), ('dedupe_key', keys)]:
                if row[field] in seen:
                    raise ValueError(f'duplicate {field} (first seen on line {seen[row[field]]})')
            ids[row['attempt_id']] = number
            keys[row['dedupe_key']] = number
            rows.append(row)
        except (ValueError, TypeError, OverflowError) as error:
            errors.append({'line': number, 'message': str(error)})
    return rows, errors
