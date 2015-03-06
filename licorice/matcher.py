
import re

from collections import defaultdict
from fuzzywuzzy import fuzz

class LicenceMatcher(object):
    '''
    Class matching licences, snippets, copyright notices etc. in files
    '''

    def __init__(self, licences, keywords):
        self.licences = licences
        self.keywords = keywords

    def get_licences(self, mappedfile, threshold=95):
        '''
        Get all licences from a given file with a given threshold

        mappedfile: a model.MappedFile instance to be analyzed
        threshold: a threshold for licences to be recognized
        '''
        found_licences = defaultdict(lambda: 0)
        for kw in self.keywords:
            m_occurrences = mappedfile.occurrences(kw)
            for m_occurrence in m_occurrences:
                for licence in (l for l in self.licences if l.contains(kw)):
                    match = 0
                    for l_occurrence in licence.positions(kw):
                        if m_occurrence - l_occurrence < 0: # License's prefix is longer than file's prefix
                            continue

                        end = len(licence.contents) - l_occurrence
                        if end > mappedfile.length: # License's suffix is longer than the file's length
                            continue

                        bad = False
                        for offset in [10, 50, 200, end]:
                            if bad:
                                break
                            temp_start = max(l_occurrence - offset, 0)
                            temp_end = min(l_occurrence + offset, len(licence.contents))
                            lic_str = re.sub('[\W]+', ' ', licence.contents[temp_start:temp_end])
                            try:
                                matched_str = re.sub('[\W]+', ' ', mappedfile.get(m_occurrence - l_occurrence, m_occurrence + temp_end))
                            except UnicodeDecodeError:
                                raise exceptions.RunTimeError('Error reading {}'.format(mappedfile.path))

                            match = fuzz.token_set_ratio(lic_str, matched_str)
                            if match < 95:
                                bad = True
                                match = 0
                                continue

                        if match > found_licences[licence]:
                            found_licences[licence] = match

        return dict([(l, score) for l, score in found_licences.items() if score > 0])