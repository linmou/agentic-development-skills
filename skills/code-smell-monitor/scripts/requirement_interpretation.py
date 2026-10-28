"""Associate structural evidence with explicitly sourced requirements, without inferring violations."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any


def interpret(repo: Path, architecture: dict[str, Any], manifest: Path | None) -> dict[str, Any]:
    if manifest is None:
        return {'status': 'not_provided', 'requirements': [], 'associations': [],
                'unmapped_findings': [f['id'] for f in architecture['findings']],
                'limitations': ['No requirements supplied; business impact is unknown.']}
    data = json.loads(manifest.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('version') != 1 or not isinstance(data.get('requirements'), list):
        raise ValueError('requirements manifest needs version 1 and a requirements array')
    requirements, associations, ids = [], [], set()
    repo = repo.resolve()
    for item in data['requirements']:
        if not isinstance(item, dict):
            raise ValueError('requirement must be an object')
        identity, kind = item.get('id'), item.get('kind')
        if not isinstance(identity, str) or not identity.strip() or identity in ids:
            raise ValueError('requirement IDs must be unique nonempty strings')
        ids.add(identity)
        if kind not in ('functional', 'quality'):
            raise ValueError('requirement kind must be functional or quality')
        for field in ('rationale', 'uncertainty'):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError(f'{identity}: {field} is required')
        modules = item.get('modules')
        if not isinstance(modules, list) or not modules:
            raise ValueError(f'{identity}: explicit module paths are required')
        for module in modules:
            if (not isinstance(module, str) or not module or '\\' in module
                or PurePosixPath(module).is_absolute() or '..' in PurePosixPath(module).parts
                or not (repo / module).resolve().is_relative_to(repo)
                or not (repo / module).is_file()):
                raise ValueError(f'{identity}: module must be an existing repository-relative file')
        source = item.get('source')
        if not isinstance(source, dict) or not isinstance(source.get('path'), str):
            raise ValueError(f'{identity}: precise source is required')
        path = (repo / source['path']).resolve()
        if Path(source['path']).is_absolute() or not path.is_relative_to(repo):
            raise ValueError(f'{identity}: source must stay inside repository')
        raw = path.read_bytes()
        lines = raw.decode('utf-8').splitlines()
        start, end, quote = source.get('line_start'), source.get('line_end'), source.get('quote')
        if (type(start) is not int or type(end) is not int or not 1 <= start <= end <= len(lines)
            or not isinstance(quote, str) or not quote.strip()
            or quote != '\n'.join(lines[start - 1:end])):
            raise ValueError(f'{identity}: source quote must match the exact line range')
        requirement = {**item, 'source': {**source, 'sha256': hashlib.sha256(raw).hexdigest()},
                       'validation': 'source_quote_verified_mapping_user_supplied'}
        requirements.append(requirement)
        for finding in architecture['findings']:
            involved = {finding['source'], finding.get('target')}
            involved.update(finding.get('evidence', {}).get('members', []))
            matching = sorted(set(modules) & involved)
            if matching:
                associations.append({'finding_id': finding['id'], 'requirement_id': identity,
                                     'matched_modules': matching, 'classification': 'impact_hypothesis',
                                     'confidence': 'association_only', 'rationale': item['rationale'],
                                     'uncertainty': item['uncertainty'],
                                     'evidence': finding['evidence'], 'source': requirement['source']})
    mapped = {a['finding_id'] for a in associations}
    return {'status': 'covered', 'manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(),
            'requirements': requirements, 'associations': associations,
            'unmapped_findings': [f['id'] for f in architecture['findings'] if f['id'] not in mapped],
            'limitations': ['Exact quotations are verified; requirement authority, currency and module '
                            'mapping require human review. Associations do not prove impact, '
                            'requirement satisfaction or violation and never change CI enforcement.']}
