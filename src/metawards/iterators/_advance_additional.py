
from typing import Union as _Union

from .._network import Network
from .._networks import Networks
from .._population import Population
from ..utils._profiler import Profiler
from .._infections import Infections

__all__ = ["advance_additional"]


def _get_ward(s, network, rng):
    if s is None:
        return 1

    if isinstance(network, Networks):
        raise TypeError("This should be a Network object...")

    try:
        from .._interpret import Interpret
        index = Interpret.integer(s, rng=rng, minval=1, maxval=network.nnodes)
        return network.get_node_index(index)
    except Exception:
        pass

    return network.get_node_index(s)


def _get_demographic(s, network):
    if s is None:
        return s
    elif isinstance(network, Network):
        return None
    elif s == "overall":
        return None

    return network.demographics.get_index(s)


def _load_additional_seeds(network: _Union[Network, Networks],
                           filename: str, rng):
    """Load additional seeds from the passed filename. This returns
       the added seeds. Note that the filename can be interpreted
       as the actual contents of the file, meaning that for short
       content, it is quicker to pass this than the filename
    """
    import os as _os
    from ..utils._console import Console, Table

    if _os.path.exists(filename):
        Console.print(f"Loading additional seeds from {filename}")
        with open(filename, "r") as FILE:
            lines = FILE.readlines()
    else:
        Console.print(f"Loading additional seeds from the command line")
        lines = filename.split("\\n")

    seeds = []

    table = Table()
    table.add_column("Day")
    table.add_column("Demographic")
    table.add_column("Ward")
    table.add_column("Number seeded")

    import csv

    try:
        dialect = csv.Sniffer().sniff(lines[0], delimiters=[" ", ","])
    except Exception:
        Console.warning(
            f"Could not identify what sort of separator to use to "
            f"read the additional seeds, so will assume commas. If this is "
            f"wrong then could you add commas to separate the "
            f"fields?")
        dialect = csv.excel  #  default comma-separated file

    for line in csv.reader(lines, dialect=dialect,
                           quoting=csv.QUOTE_ALL,
                           skipinitialspace=True):

        words = []

        # yes, the original files really do mix tabe and spaces... need
        # to extract these separately!
        for l in line:
            for p in l.split("\t"):
                words.append(p)

        if len(words) == 0:
            continue

        if len(words) < 3:
            raise ValueError(
                f"Can not interpret additional seeds from the line '{line}'")

        row = []

        from .._interpret import Interpret

        # yes, this is really the order of the seeds - "t num loc"
        # is in the file as "t loc num"
        day = Interpret.day_or_date(words[0], rng=rng)

        row.append(str(day))

        if len(words) == 4:
            demographic = _get_demographic(words[3], network=network)

            if demographic is not None:
                # we need the right network to get the ward below
                network = network.subnets[demographic]
        else:
            demographic = None

        row.append(str(demographic))

        ward = _get_ward(words[2], network=network, rng=rng)

        try:
            row.append(f"{ward} : {network.info[ward]}")
        except Exception:
            row.append(str(ward))

        seed = Interpret.integer(words[1], rng=rng, minval=0)
        row.append(str(seed))
        table.add_row(row)

        seeds.append((day, ward, seed, demographic))

    Console.print(table.to_string())

    return seeds


def setup_additional_seeds(network: _Union[Network, Networks],
                           profiler: Profiler,
                           rng,
                           **kwargs):
    """Setup function that reads in the additional seeds held
       in `params.additional_seeds` and puts them ready to
       be used by `advance_additional` to import additional
       infections at specified times in specified wards
       during the outbreak

       Parameters
       ----------
       network: Network or Networks
         The network to be seeded
       profiler: Profiler
         Profiler used to profile this function
       rng:
         Random number generator used to generate any random seeding
       kwargs
         Arguments that are not used by this setup function
    """
    params = network.params

    p = profiler.start("load_additional_seeds")
    additional_seeds = []

    if params.additional_seeds is not None:
        for additional in params.additional_seeds:
            additional_seeds += _load_additional_seeds(network=network,
                                                       filename=additional,
                                                       rng=rng)
    p = p.stop()

    return additional_seeds


def advance_additional(network: _Union[Network, Networks],
                       population: Population,
                       infections: Infections,
                       profiler: Profiler,
                       rngs,
                       **kwargs):
    """Advance the infection by infecting additional wards based
       on a pre-determined pattern based on the additional seeds

       Parameters
       ----------
       network: Network or Networks
         The network being modelled
       population: Population
         The population experiencing the outbreak - also contains the day
         of the outbreak
       infections: Infections
         Space to hold the infections
       rngs:
         The list of thread-safe random number generators, one per thread
       profiler: Profiler
         Used to profile this function
       kwargs
         Arguments that aren't used by this advancer
    """

    if not hasattr(network, "_advance_additional_seeds"):
        network._advance_additional_seeds = \
            setup_additional_seeds(network=network, profiler=profiler,
                                   rng=rngs[0])

    from ..utils._console import Console

    additional_seeds = network._advance_additional_seeds

    p = profiler.start("additional_seeds")
    for seed in additional_seeds:
        if seed[0] == population.day:
            ward = seed[1]
            num = seed[2]

            if isinstance(network, Networks):
                demographic = seed[3]

                if demographic is None:
                    # not specified, so seed the first demographic
                    demographic = 0
                else:
                    demographic = network.demographics.get_index(demographic)

                network = network.subnets[demographic]
                wards = network.nodes
                play_infections = infections.subinfs[demographic].play
            else:
                demographic = None
                wards = network.nodes
                play_infections = infections.play

            try:
                ward = network.get_node_index(ward)

                if wards.play_suscept[ward] < num:
                    Console.warning(
                        f"Not enough susceptibles in ward for seeding")
                else:
                    wards.play_suscept[ward] -= num
                    if demographic is not None:
                        Console.print(
                            f"seeding demographic {demographic} "
                            f"play_infections[0][{ward}] += {num}")
                    else:
                        Console.print(
                            f"seeding play_infections[0][{ward}] += {num}")

                    play_infections[0][ward] += num

            except Exception as e:
                Console.error(
                    f"Unable to seed the infection using {seed}. The "
                    f"error was {e.__class__}: {e}. Please double-check "
                    f"that you are trying to seed a node that exists "
                    f"in this network.")
                raise e

    p.stop()
