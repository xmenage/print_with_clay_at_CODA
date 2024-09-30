import numpy as np
import fullcontrol as fc
from fullcontrol.visualize import bounding_box
from fullcontrol.geometry import move
from math import tau, ceil
from dataclasses import dataclass

@dataclass
class ShapeParameters:
    vertical_scale: float  # actual height of the object
    horizontal_scale: float  # use to size width of object
    layer_height: float  # needed to calculate number of layers
    first_layer_height: float  # should be less than layer_height to compensate for nozzle that does not touch the stand
    extrusion_width: float  # needed for filling and when printing several layers


@dataclass
class GenerativeShape(ShapeParameters):

    def polar_curve(self, layer_index, h):
        points_per_layer = 500
        theta = np.linspace(0, tau, points_per_layer)
        rho = np.full(theta.shape, self.horizontal_scale)
        return rho, theta

    def print_polar(self):
        self.layer_count = ceil(self.vertical_scale / self.layer_height)
        hsteps = np.linspace(0, 1, self.layer_count)
        self.steps = []

        self.steps.append(fc.ManualGcode(text=f';WIDTH:{self.extrusion_width}'))

        for layer_index, h in enumerate(hsteps):
            z = h * self.vertical_scale + self.first_layer_height
            center_point = fc.Point(x=0.0, y=0.0, z=z)
            self.steps.append(fc.ManualGcode(text=';LAYER_CHANGE'))
            self.steps.append(fc.ManualGcode(text=f";Z:{z:.1f}"))
            self.steps.append(fc.ManualGcode(text=f";HEIGHT:{self.layer_height:.1f}"))
            self.steps.append(fc.ManualGcode(text=f';TYPE:External perimeter'))
            self.steps.append(fc.Extruder(relative_gcode=False))  # only there to reset E parameter
            (rho, theta) = self.polar_curve(layer_index, h)
            self.steps.append(fc.Extruder(on=False))
            self.steps.append(fc.polar_to_point(center_point, rho[0], theta[0]))
            self.steps.append(fc.Extruder(on=True))
            for r, t in zip(rho, theta):
                self.steps.append(fc.polar_to_point(center_point, r, t))

        return self.steps

    def move_to_positive_quadrant(self):
        bb = bounding_box.BoundingBox()
        bb.calc_bounds(self.steps)
        print(f"width: {bb.maxx - bb.minx:.0f}, depth: {bb.maxy - bb.miny:.0f}")
        vector_to_positive_quadrant = fc.Vector(x=-bb.minx + 10.0, y=-bb.miny + 10.0, z=0.0)
        self.steps = move(self.steps, vector_to_positive_quadrant, copy=False)
        return self.steps

