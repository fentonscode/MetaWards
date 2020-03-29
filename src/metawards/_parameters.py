
from dataclasses import dataclass
from typing import List
from copy import deepcopy
import pathlib
import os

from ._inputfiles import InputFiles
from ._disease import Disease

__all__ = ["Parameters"]

_default_parameters_path = os.path.join(pathlib.Path.home(),
                                        "GitHub", "MetaWardsData",
                                        "parameters")


@dataclass
class Parameters:
    def __init__(self):
        """Allow creation of a null Parameters object"""
        pass

    input_files: InputFiles = None
    uv_filename: str = None
    disease_params: Disease = None

    length_day: float = 0.7
    plength_day: float = 0.5
    initial_inf: int = 5

    static_play_at_home: float = 0.0
    dyn_play_at_home: float = 0.0

    data_dist_cutoff: float = 10000000.0
    dyn_dist_cutoff: float = 10000000.0

    play_to_work: float = 0.0
    work_to_play: float = 0.0

    local_vaccination_thresh: int = 4
    global_detection_thresh: int = 4
    daily_ward_vaccination_capacity: int = 5
    neighbour_weight_threshold: float = 0.0

    daily_imports: float = 0.0 # proportion of daily imports
    UV: float = 0.0

    _name: str = None
    _version: str = None
    _authors: str = None
    _contacts: str = None
    _references: str = None
    _parameters_path: str = None

    def __str__(self):
        return f"Parameters {self._name}\n" \
               f"loaded from {self._parameters_path}\n" \
               f"version: {self._version}\n" \
               f"author(s): {self._authors}\n" \
               f"contact(s): {self._contacts}\n" \
               f"references(s): {self._references}\n\n" \
    length_day: float = 0.7
    plength_day: float = 0.5
    initial_inf: int = 5

    static_play_at_home: float = 0.0
    dyn_play_at_home: float = 0.0

    data_dist_cutoff: float = 10000000.0
    dyn_dist_cutoff: float = 10000000.0

    play_to_work: float = 0.0
    work_to_play: float = 0.0

    local_vaccination_thresh: int = 4
    global_detection_thresh: int = 4
    daily_ward_vaccination_capacity: int = 5
    neighbour_weight_threshold: float = 0.0

    daily_imports: float = 0.0 # proportion of daily imports
    UV: float = 0.0

    @staticmethod
    def load(parameters: str = "march29",
             parameters_path: str = _default_parameters_path):
        """ This will return a Parameters object containing all of the
            parameters loaded from the parameters found in file
            f"{parameters_path}/{parameters}.json"

            By default this will load the march29 parameters from
           $HOME/GitHub/model_data/2011Data/parameters/march29.json
        """
        json_file = os.path.join(parameters_path, f"{parameters}.json")

        try:
            with open(json_file, "r") as FILE:
                import json
                data = json.load(FILE)

        except Exception as e:
            print(f"Could not find the parameters file {json_file}")
            print(f"Either it does not exist of was corrupted.")
            print(f"Error was {e.__class__} {e}")
            print(f"To download the parameters type the command:")
            print(f"  git clone https://github.com/chryswoods/MetaWardsData")
            print(f"and then re-run this function passing in the full")
            print(f"path to where you downloaded this directory")
            raise FileNotFoundError(f"Could not find or read {json_file}: "
                                    f"{e.__class__} {e}")


        par = Parameters(length_day=data["length_day"],
                         plength_day=data["plength_day"],
                         initial_inf=data["initial_inf"],
                         static_play_at_home=data["static_play_at_home"],
                         dyn_play_at_home=data["dyn_play_at_home"],
                         data_dist_cutoff=data["data_dist_cutoff"],
                         dyn_dist_cutoff=data["dyn_dist_cutoff"],
                         play_to_work=data["play_to_work"],
                         work_to_play=data["work_to_play"],
                         local_vaccination_thresh=data["local_vaccination_threshold"],
                         global_detection_thresh=data["global_detection_threshold"],
                         daily_ward_vaccination_capacity=data["daily_ward_vaccination_capacity"],
                         neighbour_weight_threshold=data["neighbour_weight_threshold"],
                         daily_imports=data["daily_imports"],
                         UV=data["UV"],
                         _name=data["name"],
                         _authors=data["author(s)"],
                         _version=data["version"],
                         _contacts=data["contact(s)"],
                         _references=data["reference(s)"],
                         _parameters_path=parameters_path
                         )

        print("Using parameters:")
        print(self)

        return par

    def set_input_files(self, input_files: InputFiles):
        """Set the input files that are used to initialise the
           simulation
        """
        print("Using input files:")
        print(input_files)

        self.input_files = deepcopy(input_files)

    def set_disease(self, disease: Disease):
        '""Set the disease that will be modelled"""
        print("Using disease")
        print(disease)

        self.disease = deepcopy(disease)

    def read_file(self, filename: str, line_number: int):
        """Read in extra parameters from the specified line number
           of the specified file
        """
        print(f"Reading in parameters from line {line_number} of {filename}")

        i = 0
        with open(filename, "r") as FILE:
            line = FILE.readline()

            if i == line_number:
                words = line.split(",")

                if len(words) != 5:
                    raise ValueError(
                        f"Corrupted input file. Expecting 5 values. "
                        f"Received {line}")

                vals = []

                try:
                    for word in words:
                        vals.append(float(word))
                except Exception:
                    raise ValueError(
                            f"Corrupted input file. Expected 5 numbers. "
                            f"Received {line}")

                self.disease_params.beta[2] = vals[0]
                self.disease_params.beta[3] = vals[1]
                self.disease_params.progress[1] = vals[2]
                self.disease_params.progress[2] = vals[3]
                self.disease_params.progress[3] = vals[4]

                print(f"Updated beta = {self.disease_params.beta}")
                print(f"Updated progress = {self.disease_params.progress}")

                return
            else:
                i += 1

        # get here if we can't find this line in the file
        raise ValueError(f"Cannot read parameters from line {line_number} "
                         f"as the file contains just {i} lines")
