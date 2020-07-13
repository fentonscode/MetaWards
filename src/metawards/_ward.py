
from ._wardinfo import WardInfo

from typing import Union as _Union

__all__ = ["Ward"]


def _as_positive_integer(number: int, zero_allowed: bool = True):
    try:
        number = int(number)
    except Exception:
        raise ValueError(f"{number} is not an integer")

    if number < 0:
        raise ValueError(f"{number} is negative - it must be positive")

    if number == 0 and not zero_allowed:
        raise ValueError("This value cannot be equal to zero")

    return number


def _as_positive_float(number: float):
    try:
        number = float(number)
    except Exception:
        raise ValueError(f"{number} is not a floating point number")

    if number < 0:
        raise ValueError(f"{number} is not greater or equal to zero")

    return number


class Ward:
    """This class holds all of the information about a Ward. It is used
       to create and edit Networks
    """

    def __init__(self, id: int = None, name: str = None, code: str = None,
                 authority: str = None, region: str = None,
                 info: WardInfo = None,
                 auto_assign_players: bool = True):
        """Construct a new Ward, optionally supplying information about
           the ward

           Parameters
           ----------
           id: int
             The identifier for the ward. This must be an integer that
             is greater or equal to 1. Every ward in a network must have
             a unique ID. Typically the IDs should be contiguous, as this
             ID is used as the index into the Network array
           name: str
             The name of this ward. This can be used to find the ward.
           code: str
             The code of this ward. This is used when wards are identified
             by codes, rather than names
           authority: str
             The local authority name for this node
           region: str
             The name of the region containing this ward
           info: WardInfo
             The complete WardInfo used to identify this ward.
           auto_assign_players: bool
             Whether or not to automatically ensure that all remaining
             player weight is assigned to players who play in their home
             ward
        """
        if id is None:
            self._id = None
        else:
            self._id = _as_positive_integer(id, zero_allowed=False)

        if info is not None:
            if not isinstance(info, WardInfo):
                raise TypeError(
                    f"The passed WardInfo {info} must be of type WardInfo")
            from copy import deepcopy
            self._info = deepcopy(info)
        else:
            self._info = WardInfo()

        if name is not None:
            self._info.name = str(name)

        if code is not None:
            self._info.code = str(code)

        if authority is not None:
            self._info.authority = str(authority)

        if region is not None:
            self._info.region = str(region)

        if self._id is None and self._info.is_null():
            return

        self._workers = {}
        self._players = {}

        self._player_total = 1.0

        self._num_workers = 0
        self._num_players = 0

        self._pos = {}

        # use this nomenclature to ensure this is a True/False data type
        self._auto_assign_players = True if auto_assign_players else False

    def __str__(self):
        if self.is_null():
            return "Ward::null"
        else:
            idstr = []

            if not self._info.is_null():
                idstr.append("info=" + self._info.summary())

            if self._id is not None:
                idstr.append("id=" + str(self._id))

            idstr = ", ".join(idstr)

            return f"Ward( {idstr}, " \
                f"num_workers={self.num_workers()}, " \
                f"num_players={self.num_players()} )"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.__class__ == other.__class__ and \
            self.__dict__ == other.__dict__

    def is_null(self):
        return self._id is None and self._info.is_null()

    def id(self):
        """Return the ID of this ward"""
        return self._id

    def auto_assign_players(self) -> bool:
        """Return whether or not the remaining player weight is automatically
           added to the home-ward player weight
        """
        return self._auto_assign_players

    def set_auto_assign_players(self, auto_assign_players: bool = True):
        """Return whether or not the remaining player weight is automatically
           assigned to the home-ward player weight
        """
        # use this syntax to ensure True or False type
        self._auto_assign_players = True if auto_assign_players else False

    def name(self):
        """Return the name of this ward"""
        return self._info.name

    def code(self):
        """Return the code of this ward"""
        return self._info.code

    def authority(self):
        """Return the local authority of this ward"""
        return self._info.authority

    def region(self):
        """Return the region containing this ward"""
        return self._info.region

    def info(self):
        """Return (a copy of) the WardInfo containing all ward
           identifying metadata
        """
        from copy import deepcopy
        return deepcopy(self._info)

    def assert_sane(self):
        """Assert that the data in this ward is sane"""
        assert self._id is not None and self._id > 0

        t = sum(self._players.values()) + self._player_total

        if abs(t - 1.0) > 1e-6:
            raise AssertionError(f"Player sum should equal 1.0, not {t}")

        t = sum(self._workers.values())

        if abs(t - self._num_workers) > 1e-6:
            raise AssertionError(
                f"Worker sum should be {self._num_workers}, not {t}")

    def set_name(self, name: str):
        """Set the name of this ward"""
        self._info.name = str(name)

    def set_id(self, id: int):
        """Set the ID of this ward"""
        try:
            id = int(id)
        except Exception:
            raise TypeError(f"The ID {id} must be an integer")

        if id < 1:
            raise ValueError(
                f"The passed ID {id} must be greater or equal to 1")

        if id == self._id:
            # nothing to do
            return

        if id in self._workers or id in self._players:
            raise ValueError(
                f"You cannot change the ID {id} to match an ID of an "
                f"existing link!")

        old_id = self._id

        self._id = id

        if old_id is not None:
            for key in list(self._workers.keys()):
                if key == old_id:
                    self._workers[id] = self._workers[old_id]
                    del self._workers[old_id]

            for key in list(self._players.keys()):
                if key == old_id:
                    self._players[id] = self._players[old_id]
                    del self._players[old_id]

        if id not in self._workers:
            for key in list(self._workers.keys()):
                if key == self._info:
                    self._workers[id] = self._workers[self._info]
                    del self._workers[self._info]

        if id not in self._players:
            for key in list(self._players.keys()):
                if key == self._info:
                    self._players[id] = self._players[self._info]
                    del self._players[self._info]

    def set_code(self, code: str):
        """Set the code of this ward"""
        self._info.code = str(code)

    def set_authority(self, authority: str):
        """Set the local authority of this ward"""
        self._info.authority = str(authority)

    def set_region(self, region: str):
        """Set the region of this ward"""
        self._info.region = str(region)

    def set_info(self, info: WardInfo):
        """Set the info of this ward"""
        if not isinstance(info, WardInfo):
            raise TypeError(f"The ward info {info} must be a WardInfo object")

        from copy import deepcopy
        self._info = deepcopy(info)

    def _resolve_destination(self, destination: _Union[int, WardInfo] = None):
        """Resolve the passed destination into either an ID or a
           WardInfo object
        """
        if destination is None:
            if self._id is None:
                if self._info.is_null():
                    raise ValueError("You cannot add to a null destination")

                destination = self._info
            else:
                destination = self._id

        elif isinstance(destination, Ward):
            if destination.id() is None:
                destination = destination._info

                if self._id is not None and destination == self._info:
                    # this is this ward
                    destination = self._id
            else:
                if destination.id() == self._id:
                    if self._info != destination._info:
                        raise ValueError(
                            f"Disagreement in info for Ward {self}: "
                            f"{self._info} versus {destination._info}.")

                destination = destination.id()

        if not isinstance(destination, WardInfo):
            destination = _as_positive_integer(destination, zero_allowed=False)

        return destination

    def resolve(self, wards) -> None:
        """Resolve any unresolved links using the passed Wards object
           'wards'
        """
        from ._wards import Wards

        if not isinstance(wards, Wards):
            raise TypeError(
                f"You can only resolve links using a valid Wards object!")

        for key in list(self._workers.keys()):
            if not isinstance(key, int):
                if key in wards:
                    idx = wards.index(key)

                    if idx in self._workers:
                        raise KeyError(f"Duplicate keys? {idx} and {key}")

                    self._workers[idx] = self._workers[key]
                    del self._workers[key]

        for key in list(self._players.keys()):
            if not isinstance(key, int):
                if key in wards:
                    idx = wards.index(key)

                    if idx in self._players:
                        raise KeyError(f"Duplicate keys? {idx} and {key}")

                    self._players[idx] = self._players[key]
                    del self._players[key]

    def is_resolved(self):
        """Return whether or not any of the worker or player links in
           this ward are unresolved, or whether the ID of this ward is None
        """
        if self._id is None:
            return False

        for key in self._workers.keys():
            if not isinstance(key, int):
                return False

        for key in self._players.keys():
            if not isinstance(key, int):
                return False

        return True

    def add_workers(self, number: int,
                    destination: _Union[int, WardInfo] = None):
        """Add some workers to this ward, specifying their destination
           if they work out of ward
        """
        destination = self._resolve_destination(destination)
        number = _as_positive_integer(number)

        if destination not in self._workers:
            self._workers[destination] = 0

        self._workers[destination] += number
        self._num_workers += number

    def subtract_workers(self, number: int, destination: int = None):
        """Remove some workers from this ward, specifying their destination
           if they work out of ward
        """
        destination = self._resolve_destination(destination)
        number = _as_positive_integer(number)

        if destination not in self._workers:
            return

        if number >= self._workers[destination]:
            self._num_workers -= self._workers[destination]
            del self._workers[destination]
        else:
            self._workers -= number
            self._num_workers -= number

    def add_player_weight(self, weight: float, destination: int = None):
        """Add the weight for players who will randomly move to
           the specified destination to play(or to play in the home
           ward if destination is not set). Note that the sum of
           player weights cannot be greater than 1.0.
        """
        tiny = 1e-10

        weight = _as_positive_float(weight)
        destination = self._resolve_destination(destination)

        if weight < tiny:
            return

        if abs(weight - self._player_total) < tiny:
            weight = self._player_total

        if weight > self._player_total:
            raise ValueError(
                f"You cannot add {weight} to {destination} as the sum of "
                f"weights must be <= 1.0, and this is greater "
                f"than the remaining weight available {self._player_total}. "
                f"You can only add a weight that is less than this value")

        if destination not in self._players:
            self._players[destination] = 0

        self._players[destination] += weight
        self._player_total -= weight

        if self._player_total < tiny:
            self._player_total = 0

    def subtract_player_weight(self, weight: float, destination: int = None):
        """Subtract the weight for players who will randomly move to
           the specified destination to play (or to play in the home
           ward if destination is not set).
        """
        tiny = 1e-10

        weight = _as_positive_float(weight)
        destination = self._resolve_destination(destination)

        if weight < tiny:
            return

        if destination not in self._players:
            return

        if weight > self._players[destination]:
            weight = self._players[destination]

        self._player_total += weight
        del self._players[destination]

        if abs(self._player_total - 1.0) < tiny:
            self._player_total = 1.0

    def get_workers(self, destination: int = None):
        """Return the number of workers who commute to the specified
           destination ward (or who commute to their home ward if
           destination is not set)
        """
        destination = self._resolve_destination(destination)
        return self._workers.get(destination, 0)

    def get_players(self, destination: int = None):
        """Return the fraction of players who will play in the
           specified destination ward (or who play in their home
           ward if destination is not set)
        """
        destination = self._resolve_destination(destination)

        p = self._players.get(destination, 0.0)

        if self._auto_assign_players and destination == self._id:
            p += self._player_total

        return p

    def num_work_links(self):
        """Return the total number of work links"""
        return len(self._workers)

    def num_play_links(self):
        """Return the total number of play links"""
        return len(self._players)

    def num_workers(self):
        """Return the total number of workers who make their home
           in this ward
        """
        return self._num_workers

    def num_players(self):
        """Return the total number of players who make their home
           in this ward
        """
        return self._num_players

    def population(self):
        """Return the total population of this ward"""
        return self._num_workers + self._num_players

    def set_num_players(self, number: int):
        """Set the number of players in this ward"""
        self._num_players = _as_positive_integer(number)

    def set_num_workers(self, number: int):
        """Set the number of workers in this ward."""
        number = _as_positive_integer(number)

        delta = number - self._num_workers

        if delta > 0:
            # add the workers as individuals who commute to their home ward
            self.add_workers(delta)

        elif delta < 0:
            # can we remove just the workers who commute to their home ward?
            if delta <= self.get_workers():
                self.subtract_workers(delta)
            else:
                raise ValueError(
                    f"Cannot set the number of workers to {number} as there "
                    f"are not enough home workers to subtract")

    def get_worker_lists(self):
        """Return a pair of arrays, containing the destination wards
           and worker populations for this ward
        """
        from .utils._array import create_int_array

        keys = list(self._workers.keys())
        keys.sort()

        wards = create_int_array(len(keys))
        pops = create_int_array(len(keys))

        for i, key in enumerate(keys):
            if not isinstance(key, int):
                raise KeyError(
                    f"Cannot create worker list as link to {key} is "
                    f"unresolved")

            wards[i] = key
            pops[i] = self._workers[key]

        return (wards, pops)

    def get_player_lists(self, no_auto_assign: bool = False):
        """Return a pair of arrays, containing the destination wards
           and player weights for this ward.

           If 'no_auto_assign' is set then do not include any
           auto-assigned weights. This normally should be false,
           as it is only used when serialising
        """
        from .utils._array import create_double_array, create_int_array

        keys = list(self._players.keys())

        auto_assign = (not no_auto_assign) and self._auto_assign_players

        if auto_assign and self._id not in keys:
            keys.append(self._id)

        keys.sort()

        wards = create_int_array(len(keys))
        weights = create_double_array(len(keys))

        for i, key in enumerate(keys):
            if not isinstance(key, int):
                raise KeyError(
                    f"Cannot create worker list as link to {key} is "
                    f"unresolved")

            wards[i] = key
            weights[i] = self._players.get(key, 0.0)

            if auto_assign and key == self._id:
                weights[i] += self._player_total

        return (wards, weights)

    def set_position(self, x: float = None, y: float = None,
                     lat: float = None, long: float = None,
                     units: str = "m"):
        """Set the position of the centre of this ward. This can
           be set either as x/y coordinates or latitude/longitude
           coordinates.

           Parameters
           ----------
           x: float
             The x coordinates if x/y are used. The units are set
             via the 'units' argument
           y: float
             The y coordinates if x/y are used. The units are set
             via the 'units' argument
           units: str
             The units for x/y coordinates. This should be "m" for
             meters or "km" for kilometers
           lat: float
             The latitude if lat/long coordinates are used
           long: float
             The longitude if lat/long coordinates are used
        """
        if x is not None:
            if y is None or lat is not None or long is not None:
                raise ValueError(
                    f"You must set either x/y or lat/long, but not both!")

            if units is None:
                units = "m"

            units = str(units).strip().lower()

            if units in ["m", "meter", "meters"]:
                units = 0.001
            elif units in ["km", "kilometer", "kilometers"]:
                units = 1.0
            else:
                raise ValueError(
                    f"Unrecognised units {units}. This should be either "
                    f"'m' or 'km'")

            self._pos = {"x": units * float(x),
                         "y": units * float(y)}

        elif lat is not None:
            if long is None or x is not None or y is not None:
                raise ValueError(
                    f"You must set either x/y or lat/long, but not both!")

            self._pos = {"lat": float(lat),
                         "long": float(long)}

        else:
            # nothing is being set - ignore
            if y is not None or long is not None:
                raise ValueError(
                    "Confused inputs. Either set x and y, or lat and long")

    def position(self):
        """Return the position of the center of this ward. This will
           return a dictionary containing either the {"x", "y"}
           coordinates (in kilometers) or containing the
           {"lat", "long"} coordinates, or an empty dictionary
           if cooordinates have not been set.
        """
        from copy import deepcopy
        return deepcopy(self._pos)

    def work_connections(self):
        """Return the full list of work connections for this ward"""
        c = list(self._workers.keys())

        try:
            c.sort()
        except Exception:
            pass

        return c

    def play_connections(self):
        """Return the full list of play connections for this ward"""
        c = list(self._players.keys())

        try:
            c.sort()
        except Exception:
            pass

        return c

    def to_data(self):
        """Return a dictionary that can be serialised to JSON"""
        data = {}

        data["id"] = self._id

        if len(self._pos) > 0:
            data["position"] = self.position()

        data["info"] = self._info.to_data()

        if not self._auto_assign_players:
            data["auto_assign_players"] = False

        data["num_workers"] = self.num_workers()
        data["num_players"] = self.num_players()

        workers = self.get_worker_lists()

        if len(workers[0]) > 0:
            data["workers"] = {"destination": workers[0].tolist(),
                               "population": workers[1].tolist()}

        players = self.get_player_lists(no_auto_assign=True)

        if len(players[0]) > 0:
            data["players"] = {"destination": players[0].tolist(),
                               "weights": players[1].tolist()}

        return data

    @staticmethod
    def from_data(data):
        """Return a Ward that has been created from the passed dictionary
           (e.g. which has been deserialised from JSON)
        """

        if data is None or len(data) == 0:
            return Ward()

        ward = Ward(id=data.get("id", None),
                    info=WardInfo.from_data(data.get("info", {})),
                    auto_assign_players=True)

        pos = data.get("position", {})

        ward.set_position(x=pos.get("x", None), y=pos.get("y", None),
                          lat=pos.get("lat", None), long=pos.get("long", None),
                          units="km")

        ward.set_auto_assign_players(data.get("auto_assign_players", True))

        ward.set_num_players(data.get("num_players", 0))

        workers = data.get("workers", {})

        for d, p in zip(workers.get("destination", []),
                        workers.get("population", [])):
            d = _as_positive_integer(d, zero_allowed=False)
            p = _as_positive_integer(p)

            ward._workers[d] = p

        ward._num_workers = sum(ward._workers.values())

        if data.get("num_workers", 0) > 0:
            if ward.num_workers() != data["num_workers"]:
                raise AssertionError(
                    f"Disagreement in number of workers: {ward.num_workers()} "
                    f"versus {data['num_workers']}")

        players = data.get("players", {})

        for d, w in zip(players.get("destination", []),
                        players.get("weights", [])):
            d = _as_positive_integer(d, zero_allowed=False)
            w = _as_positive_float(w)

            ward._players[d] = w

        ward._player_total = 1.0 - sum(ward._players.values())

        if abs(ward._player_total) < 1e-10:
            ward._player_total = 0

        elif ward._player_total < 0:
            raise AssertionError(
                f"The sum of player weights cannot be greater than zero")

        ward.assert_sane()

        return ward
