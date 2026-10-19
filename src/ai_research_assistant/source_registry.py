"""Run-local source identity and dates, owned by the application, not agents."""
from datetime import date
import re
from urllib.parse import urlsplit

from pydantic import HttpUrl

SOURCE_ID = re.compile(r"S[1-9][0-9]*")
REFERENCE = re.compile(r"\[(S[1-9][0-9]*(?:\s*[,;]\s*S[1-9][0-9]*)*)\](?!\()")


def iso_date(value):
    """Accept explicit ISO dates only; never interpret 'today' as publication."""
    if not isinstance(value, str) or not re.match(r"^\d{4}-\d{2}-\d{2}(?:$|T)", value):
        return None
    try:
        return date.fromisoformat(value[:10]).isoformat()
    except ValueError:
        return None


def register_sources(sources):
    used = {s.get('source_id') for s in sources.values() if SOURCE_ID.fullmatch(s.get('source_id', ''))}
    number = max((int(value[1:]) for value in used), default=0)
    seen = set()
    for url, source in sources.items():
        sid = source.get('source_id')
        if sid not in used or sid in seen:
            number += 1
            sid = f'S{number}'
            source['source_id'] = sid
        seen.add(sid)
        source['url'] = url
        source.setdefault('retrieved_at', source.get('retrieved'))
        if 'published_at' not in source:
            # A dated article path is metadata, not the observation's period.
            match = re.search(r'/(\d{4})/(\d{2})/(\d{2})(?:/|$)', urlsplit(url).path)
            path_date = iso_date('-'.join(match.groups())) if match else None
            source['published_at'] = iso_date(source.get('published')) or path_date
            source['publication_date_basis'] = ('search_metadata' if iso_date(source.get('published'))
                                                 else 'url_path' if path_date else None)
    return sources


def resolve_source(reference, sources):
    register_sources(sources)
    for url, source in sources.items():
        if reference == source['source_id']:
            return url
    # Legacy checkpoints and existing reports retain exact URL compatibility.
    try:
        normalized = str(HttpUrl(reference))
    except ValueError:
        return None
    return next((url for url in sources if str(HttpUrl(url)) == normalized), None)


def render_references(text, sources, language='suomi'):
    """Resolve registered [S1] tokens; never guess a mistyped URL or source ID."""
    register_sources(sources)
    # A structured analysis cites observations. Resolve those through their
    # registered provenance rather than asking the writer to renumber them.
    finding_sources = {
        finding['finding_id']: source['source_id']
        for source in sources.values()
        for kind in ('research_findings', 'trend_findings')
        for finding in source.get(kind, [])
        if finding.get('finding_id')
    }
    def observation_reference(match):
        ids = [value.strip() for value in match[1].split(',')]
        if not all(value in finding_sources for value in ids):
            return match[0]
        return ' '.join(f'[{sid}]' for sid in dict.fromkeys(finding_sources[value] for value in ids))
    text = re.sub(r'\[([^\[\]\n]+)\](?!\()', observation_reference, text)
    by_id = {s['source_id']: url for url, s in sources.items()}
    unknown = {sid for group in REFERENCE.findall(text) for sid in SOURCE_ID.findall(group)} - by_id.keys()
    if unknown:
        raise ValueError('Unknown source IDs: ' + ', '.join(sorted(unknown)))
    # Old stage text can contain bare URLs. Check those as well so a typo
    # cannot slip past the Markdown-only validator into accepted evidence.
    without_links = re.sub(r'\[[^\]\n]+\]\(<?https?://[^\s<>]+?>?\)', '', text)
    for url in re.findall(r'https?://[^\s<>\[\]()]+', without_links):
        if resolve_source(url.rstrip('.,;'), sources) is None:
            raise ValueError('Unregistered source URL')
    label = 'Lähde' if language != 'english' else 'Source'
    return REFERENCE.sub(lambda m: ' '.join(f'[{label} {sid}]({by_id[sid]})'
                         for sid in dict.fromkeys(SOURCE_ID.findall(m[1]))), text)


def unsupported_years(finding):
    """A claimed year must occur in the selected evidence, not a page footer."""
    if not finding.source_id:
        return set()  # Legacy records did not store a specific supporting passage.
    years = lambda text: set(re.findall(r'\b(?:19|20)\d{2}\b', text or ''))
    claims = ' '.join((finding.title, finding.summary, finding.period or '', finding.local_relevance))
    return years(claims) - years(finding.supporting_text + ' ' + finding.period_support)
