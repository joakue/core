#!/usr/bin/env python3
from typing import TypedDict, Any
import jq

from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.generic.json.config import JsonBatSetup


class KwargsDict(TypedDict):
    device_id: int


class JsonBat(AbstractBat):
    def __init__(self, component_config: JsonBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, response) -> None:
        config = self.component_config.configuration

        currents = [0] * 3
        for i, c in enumerate(config.jq_currents):
            if c is not None:
                currents[i] = float(jq.compile(c).input(response).first())

        power = float(jq.compile(config.jq_power).input(response).first())
        if config.jq_soc != "":
            soc = float(jq.compile(config.jq_soc).input(response).first())
        else:
            soc = 0

        if config.jq_imported is not None and config.jq_exported is not None:
            imported = float(jq.compile(config.jq_imported).input(response).first())
            exported = float(jq.compile(config.jq_exported).input(response).first())
        else:
            imported, exported = self.sim_counter.sim_count(power)

        bat_state = BatState(
            currents=currents,
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=JsonBatSetup)
