import random

import simpy


class Component:

    def __init__(self, name: str):
        """
        Constructor for component
        :param name: of the component
        """
        self.name = name


class Product:

    def __init__(self, name: str, required_components: list):
        """
        Constructor for product
        :param name: of the product
        :param required_components: components required to build the product
        """
        self.name = name
        self.required_components = required_components


class Workstation:

    def __init__(self, env: simpy.Environment, name: str, product: Product, processing_times: list):
        """
        Constructor for workstation
        :param env: the environment the workstation will be
        :param name:  of the workstation
        :param product:  the product that the workstation is building
        :param processing_times: the processing times generated in the .dat file
        """
        self.name = name
        self.product = product
        self.buffers = {}
        for i in product.required_components:
            self.buffers[i] = simpy.Container(env, 2)
        self.env = env
        self.processing_times = processing_times
        self.products_made = 0
        env.process(self.workstation_process())
        self.wait_time = 0

    def workstation_process(self):
        """
        Process to be run by SimPy environment
        :return: None
        """
        while True:
            before_time = self.env.now
            for i in self.buffers.keys():
                yield self.buffers[i].get(1)  # try to get one component from each of the buffers

            self.wait_time += (self.env.now - before_time)

            process_time = self.processing_times.pop(0)
            yield self.env.timeout(process_time)
            print(self.name, " created ", self.product.name, " at ", round(self.env.now, 2),
                  " minutes")
            self.products_made += 1


class Inspector:

    def __init__(self, env: simpy.Environment, name: str, components: list, processing_times: list,
                 workstations: list):
        """
        Constructor for an inspector
        :param env: the environment the inspector will be
        :param name: of the inspector
        :param components: the components the inspector will build
        :param processing_times: the processing times generated in the .dat file
        :param workstations: the workstations that the inspector can send components to
        """
        self.name = name
        self.components = components
        self.env = env
        self.processing_times = {}

        count = 0
        for i in components:
            self.processing_times[i] = processing_times[count]
            count += 1

        self.workstations = workstations
        self.env.process(self.inspector_process())
        self.blocked_time = 0

    def send_component(self, component: Component) -> Workstation:
        """
        Used to find the workstation with the minimal buffer

        :param component: sends component to an available workstation
        :return: the workstation where it is sent
        """
        min_buffer = 2

        for workstation in self.workstations:  # find buffer with minimal components
            if component in workstation.buffers.keys() and workstation.buffers[component].level < min_buffer:
                min_buffer = workstation.buffers[component].level
        for workstation in self.workstations:  # find first workstation with minimal buffer
            if component in workstation.buffers.keys() and workstation.buffers[component].level == min_buffer:
                return workstation

    def choose_random_component(self) -> Component:
        """
        Returns a randomly chosen component for the inspector
        :return: a component
        """
        return self.components[random.randint(0, len(self.components) - 1)]

    def inspector_process(self):
        """
        Process to be run by SimPy environment
        :return: None
        """
        while True:
            component = self.choose_random_component()
            delay = self.processing_times[component].pop(0)
            yield self.env.timeout(delay)  # allow delay for processing times

            before_time = self.env.now

            destination = self.send_component(component)
            yield destination.buffers[component].put(1)  # try to put component inside buffer
            self.blocked_time += (self.env.now - before_time)

            print(self.name, " sent ", component.name, " to ", destination.name, " at ", round(self.env.now, 2),
                  " minutes")
