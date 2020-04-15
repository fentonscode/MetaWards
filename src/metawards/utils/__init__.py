"""
.. currentmodule:: metawards.utils

Functions
=========

.. autosummary::
    :toctree: generated/

    add_wards_network_distance
    allocate_vaccination
    assert_sane_network
    build_play_matrix
    build_wards_network
    clear_all_infections
    create_int_array
    create_double_array
    create_string_array
    create_thread_generators
    delete_ran_binomial
    extract_data
    extract_data_for_graphics
    fill_in_gaps
    get_available_num_threads
    get_min_max_distances
    get_number_of_processes
    how_many_vaccinated
    initialise_infections
    initialise_play_infections
    iterate
    move_population_from_work_to_play
    move_population_from_play_to_work
    open_files
    prepare_worker
    ran_binomial
    ran_int
    ran_uniform
    read_done_file
    recalculate_work_denominator_day
    recalculate_play_denominator_day
    redirect_output
    rescale_play_matrix
    resize_array
    reset_everything
    reset_play_matrix
    reset_play_susceptibles
    reset_work_matrix
    run_model
    run_models
    run_worker
    seed_ran_binomial
    string_to_ints
    vaccinate_same_id

Classes
=======

.. autosummary::
    :toctree: generated/

    Profiler
    NullProfiler
    Workspace

"""

# make top-level objects also available in utils, e.g. network
from .. import _network

from ._initialise_infections import *
from ._read_done_file import *
from ._string_to_ints import *
from ._profiler import *
from ._run_model import *
from ._runner import *
from ._iterate import *
from ._worker import *

# pyx imports
from ._build_wards_network import *
from ._add_wards_network_distance import *
from ._get_min_max_distances import *
from ._reset_everything import *
from ._rescale_matrix import *
from ._recalculate_denominators import *
from ._move_population import *
from ._fill_in_gaps import *
from ._build_play_matrix import *
from ._workspace import *
from ._array import *
from ._ran_binomial import *
from ._parallel import *
from ._assert_sane_network import *
from ._extract_data import *
from ._vaccination import *
from ._clear_all_infections import *
