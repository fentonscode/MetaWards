
from dataclasses import dataclass as _dataclass

from ._network import Network
from ._networks import Networks

__all__ = ["Infections"]


@_dataclass
class Infections:
    """This class holds the arrays that record the infections as they
       are occuring during the outbreak
    """

    #: The infections caused by fixed (work) movements. This is a list
    #: of int arrays, size work[N_INF_CLASSES][nlinks+1]
    work = None

    #: The infections caused by random (play) movements. This is a list
    #: of int arrays, size play[N_INF_CLASSES][nnodes+1]
    play = None

    #: The work infections for each of the subnets of a Networks that
    #: models multiple demographics
    sub_works = None

    #: The play infections for each of the subnets of a Networks that
    #: models multiple demographics
    sub_plays = None

    @staticmethod
    def build(network: Network = None, networks: Networks = None):
        """Construct and return the Infections object that will track
           infections during a model run on the passed Network (or Networks)

           Parameters
           ----------
           network: Network
             A single network that will be run
           networks: Networks
             The full set of networks with multiple demographics

           Returns
           -------
           infections: Infections
             The space for the work and play infections for the network
             (including space for all of the demographics)
        """
        from .utils import initialise_infections, initialise_play_infections

        if network is None:
            network = networks
        elif networks is not None:
            raise ValueError(f"Pass one of network or networks - not both!")

        if isinstance(network, Network):
            inf = Infections()
            inf.work = initialise_infections(network=network)
            inf.play = initialise_play_infections(network=network)

            return inf
        else:
            if networks is None:
                networks = network

            inf = Infections()
            inf.work = initialise_infections(network=networks.overall)
            inf.play = initialise_play_infections(network=networks.overall)

            works = []
            plays = []

            for subnet in networks.subnets:
                works.append(initialise_infections(network=subnet))
                plays.append(initialise_play_infections(network=subnet))

            inf.sub_works = works
            inf.sub_plays = plays

            return inf

    def clear(self, nthreads: int = 1):
        """Clear all of the infections (resets all to zero)

           Parameters
           ----------
           nthreads: int
             Optionally parallelise this reset by specifying the number
             of threads to use
        """
        from .utils import clear_all_infections
        clear_all_infections(infections=self.work,
                             play_infections=self.play,
                             nthreads=nthreads)

        if self.sub_works:
            for i in range(0, len(self.sub_works)):
                clear_all_infections(infections=self.sub_works[i],
                                     play_infections=self.sub_plays[i],
                                     nthreads=nthreads)