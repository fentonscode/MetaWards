
from dataclasses import dataclass as _dataclass
from dataclasses import field as _field
from typing import List as _List

from ._network import Network
from ._parameters import Parameters
from ._demographics import Demographics
from ._population import Population
from ._outputfiles import OutputFiles

__all__ = ["Networks"]


@_dataclass
class Networks:
    """This is a combination of Network objects which together represent
       an entire diverse population. Each individual Network is used to
       model the disease outbreak within a single demographic of the
       population. Multiple demographics are modelled by combining
       multiple networks. Special merge functions enable joint
       FOIs to be calculated, through which an outbreak in one
       network can cross-infect a demographic in another network.

       The Networks can be very independent, and don't necessarily
       need to have the same links. However, it is assumed (and checked)
       that each network will have the same nodes.
    """

    #: The overall Network, which contains a combination of all of the
    #: sub-networks. This is used for summary analysis and also as
    #: a means of merging and distributing data between sub-networks
    overall: Network = None

    #: The list of Networks, one for each demographic, ordered in the
    #: same order as the "Demographics" object. This is empty if
    #: only a single demographic is modelled
    subnets: _List[Network] = _field(default_factory=list)

    #: Metadata about each of the demographics being modelled. This is
    #: None if only a single demographic is modelled
    demographics: Demographics = None

    @property
    def params(self) -> int:
        """The overall parameters that are then specialised for the
           different demographics
        """
        if self.overall is not None:
            return self.overall.params
        else:
            return None

    def assert_sane(self, profiler: None):
        """Assert that the networks is sane. This checks that the
           networks and all of the demographic sub-networks are
           laid out correctly in memory and that they don't have
           anything unexpected. Checking here will prevent us from having
           to check every time the networks are accessed
        """
        if self.overall:
            self.overall.assert_sane(profiler=profiler)

        for subnet in self.subnets:
            subnet.assert_sane(profiler=profiler)

        # SHOULD ASSERT HERE THAT THE POPULATIONS OF ALL OF THE SUBNETS
        # IN EACH WARD SUM UP TO THE POPULATION IN THE OVERALL NETWORK
        # WARDS

    @staticmethod
    def build(network: Network, demographics: Demographics):
        """Build the set of networks that will model the passed
           demographics based on the overall population model
           in the passed network

           Parameters
           ----------
           network: Network
             The overall population model - this contains the base
             parameters, wards, work and play links that define
             the model outbreak

           demographics: Demographics
             Information about each of the demographics to be modelled.
             Note that the sum of the "work" and "play" populations
             across all demographics must be 1.0 in all wards in
             the model

           Returns
           -------
           networks: Networks
             The set of Networks that represent the model run over the
             full set of different demographics
        """
        if demographics is None or len(demographics) < 2:
            raise ValueError(f"You can only create a Networks object "
                             f"with a valid Demographics that contains "
                             f"more than one demographic")

        networks = []

        # specialise the network for each demographic
        for i in range(0, len(demographics)):
            networks.append(network.specialise(demographics[i]))

        # now verify that the sum of the populations in each ward across
        # all demographics equals the sum of the overall population in
        # each ward

        result = Networks()
        result.overall = network
        result.subnets = networks
        result.demographics = demographics

        return result

    def run(self, population: Population,
            output_dir: OutputFiles,
            seed: int = None,
            nsteps: int = None,
            profile: bool = True,
            s: int = None,
            nthreads: int = None,
            iterator=None,
            extractor=None,
            mover=None,
            mixer=None,
            profiler=None):
        """Run the model simulation for the passed population.
           The random number seed is given in 'seed'. If this
           is None, then a random seed is used.

           All output files are written to 'output_dir'

           The simulation will continue until the infection has
           died out or until 'nsteps' has passed (keep as 'None'
           to prevent exiting early).

           s is used to select the 'to_seed' entry to seed
           the nodes

           Parameters
           ----------
           population: Population
             The initial population at the start of the model outbreak.
             This is also used to set start date and day of the model
             outbreak
           output_dir: OutputFiles
             The directory to write all of the output into
           seed: int
             The random number seed used for this model run. If this is
             None then a very random random number seed will be used
           nsteps: int
             The maximum number of steps to run in the outbreak. If None
             then run until the outbreak has finished
           profile: bool
             Whether or not to profile the model run and print out the
             results
           profiler: Profiler
             The profiler to use - a new one is created if one isn't passed
           s: int
             Index of the seeding parameter to use
           nthreads: int
             Number of threads over which to parallelise this model run
           iterator: function
             Function that is called at each iteration to get the functions
             that are used to advance the model
           extractor: function
             Function that is called at each iteration to get the functions
             that are used to extract data for analysis or writing to files
           mixer: function
             Function that is called to mix the data calculated for each
             of the sub-networks for the different demographics and
             merge it together so that this is shared
           mover: function
             Function that is called to move the population between
             different demographics
        """
        # Create the random number generator
        from .utils._ran_binomial import seed_ran_binomial, ran_binomial

        if seed == 0:
            # this is a special mode that a developer can use to force
            # all jobs to use the same random number seed (15324) that
            # is used for comparing outputs. This should NEVER be used
            # for production code
            print("** WARNING: Using special mode to fix all random number")
            print("** WARNING: seeds to 15324. DO NOT USE IN PRODUCTION!!!")
            rng = seed_ran_binomial(seed=15324)
        else:
            rng = seed_ran_binomial(seed=seed)

        # Print the first five random numbers so that we can
        # compare to other codes/runs, and be sure that we are
        # generating the same random sequence
        randnums = []
        for i in range(0, 5):
            randnums.append(str(ran_binomial(rng, 0.5, 100)))

        print(f"First five random numbers equal {', '.join(randnums)}")
        randnums = None

        if nthreads is None:
            from .utils._parallel import get_available_num_threads
            nthreads = get_available_num_threads()

        print(f"Number of threads used equals {nthreads}")

        from .utils._parallel import create_thread_generators
        rngs = create_thread_generators(rng, nthreads)

        # Create space to hold the results of the simulation
        print("Initialise infections...")
        infections = self.initialise_infections()

        from .utils import run_model
        population = run_model(network=self,
                               population=population,
                               infections=infections,
                               rngs=rngs, s=s, output_dir=output_dir,
                               nsteps=nsteps,
                               profile=profile, nthreads=nthreads,
                               profiler=profiler,
                               iterator=iterator, extractor=extractor,
                               mixer=mixer, mover=mover)

        return population

    def reset_everything(self, nthreads: int = 1, profiler=None):
        """Resets the networks ready for a new run of the model"""
        if self.overall:
            self.overall.reset_everything(nthreads=nthreads, profiler=profiler)

        for subnet in self.subnets:
            subnet.reset_everything(nthreads=nthreads, profiler=profiler)

    def update(self, params: Parameters,
               nthreads: int = 1, profile: bool = False,
               profiler=None):
        """Update the networks with a new set of parameters.
           This is used to update the parameters for the networks
           for a new run. The networks will be reset
           and ready for a new run.
        """
        if profile:
            if profiler:
                p = profiler
            else:
                from .utils import Profiler
                p = Profiler()
        else:
            from .utils import NullProfiler
            p = NullProfiler()

        p = p.start("overall.update")
        self.overall.update(params, profiler=p)
        p = p.stop()

        for i in range(0, len(self.demographics)):
            demographic = self.demographics[i]

            # TODO::: RESET THE SUSCEPTIBLE POPULATIONS BACK TO
            #         WHERE THEY SHOULD BE AT THE START OF THE RUN

            p = p.start(f"{demographic.name}.update")
            if demographic.adjustment:
                subnet_params = params.set_variables(demographic.adjustment)
            else:
                subnet_params = params

            self.subnets[i].update(subnet_params, profiler=p)
            p = p.stop()

        if profile and (profiler is None):
            print(p)

    def initialise_infections(self, nthreads: int = 1):
        """Initialise and return the space that will be used
           to track infections
        """
        from ._infections import Infections
        return Infections.build(networks=self)

    def rescale_play_matrix(self, nthreads: int = 1, profiler=None):
        """Rescale the play matrix"""
        if self.overall:
            self.overall.reset_everything(nthreads=nthreads, profiler=profiler)

        for subnet in self.subnets:
            subnet.rescale_play_matrix(nthreads=nthreads, profiler=profiler)

    def move_from_play_to_work(self, nthreads: int = 1, profiler=None):
        """Move the population from play to work"""
        if self.overall:
            self.overall.move_from_play_to_work(nthreads=nthreads,
                                                profiler=profiler)

        for subnet in self.subnets:
            subnet.move_from_play_to_work(nthreads=nthreads,
                                          profiler=profiler)