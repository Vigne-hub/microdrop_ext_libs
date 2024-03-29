"""Schemas for structured data."""
from __future__ import absolute_import
from flatland.exc import AdaptationError
from flatland.schema import Array, Boolean, Compound, Constrained, Container,\
        Date, DateTime, DateYYYYMMDD, Decimal, Dict, Element, Enum, Float, Form,\
        Integer, JoinedString, List, Mapping, MultiValue, Number,\
        Properties, Ref, Scalar, Sequence, Skip, SkipAll, SkipAllFalse,\
        SparseDict, String, Time, Unevaluated, Unset

'''
from flatland.util.deferred import deferred_module


deferred_module.shadow(
    'flatland',
    {'exc': ('AdaptationError',),
     'schema': ('Array',
                'Boolean',
                'Compound',
                'Constrained',
                'Container',
                'Date',
                'DateTime',
                'DateYYYYMMDD',
                'Decimal',
                'Dict',
                'Element',
                'Enum',
                'Float',
                'Form',
                'Integer',
                'JoinedString',
                'List',
                'Mapping',
                'MultiValue',
                'Number',
                'Properties',
                'Ref',
                'Scalar',
                'Sequence',
                'Skip',
                'SkipAll',
                'SkipAllFalse',
                'SparseDict',
                'String',
                'Time',
                'Unevaluated',
                'Unset',
                ),
     'signals': (),
     'util': ('Unspecified', 'class_cloner',),
     'validation': (),
     },
    __version__='dev')
'''
__version__='fix-imports'
