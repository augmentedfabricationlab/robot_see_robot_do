from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from compas_fab.robots import Robot

from compas.geometry import Frame
from compas.geometry import Vector, Point
from compas.geometry import Transformation
from compas.geometry import Rotation
from compas.geometry import Translation

import math

class Robot(Robot):
    """Represents a robot, which can be moved in the world coordinate system.
    """

    def __init__(self, model, artist=None, semantics=None, client=None):

        super(Robot, self).__init__(model, artist, semantics, client)

        self._scale_factor = 1.
        self.model = model
        self.attached_tool = None
        self.artist = artist
        self.semantics = semantics
        self.client = client
        self.attributes = {}
        self._current_ik = {
            'request_id': None,
            'solutions': None
        }

        self.origin_frame = Frame.worldXY() # robot's origin in world

        self.base_geometry = [] #robot's base geometry
        self.picking_frame = Frame.worldXY() #pick up frame at robot's base

    def get_origin_frame(self):
        """Get the robot's origin frame.
        :class:`compas.geometry.Frame`
        """
        return self.origin_frame
    
    def set_origin_frame(self, robot_coordinate_frame):
        """Move the origin frame of the robot to the robot_coordinate_frame.
        """
        self.origin_frame = robot_coordinate_frame

    def transformation_OCF_WCF(self):
        """Get the transformation from the robot's origin frame (OCF) to the world coordinate frame (WCF).
        -------
        :class:`compas.geometry.Transformation`
        """
        origin_frame = self.origin_frame
        return Transformation.from_change_of_basis(origin_frame, Frame.worldXY())

    def transformation_WCF_OCF(self):
        """Get the transformation from the world coordinate frame (WCF) to the robot's origin frame (OCF).
        -------
        :class:`compas.geometry.Transformation`
        """
        origin_frame = self.origin_frame
        return Transformation.from_change_of_basis(Frame.worldXY(), origin_frame)

    def to_local_coordinates_origin(self, frame_WCF):
        """Represent a frame from the world coordinate system (WCF) in the robot's origin coordinate system (OCF).
        Parameters
        ----------
        frame_WCF : :class:`compas.geometry.Frame`
            A frame in the world coordinate frame.
        Returns
        -------
        :class:`compas.geometry.Frame`
            A frame in the robot's coordinate frame.
        """
        frame_OCF = frame_WCF.transformed(self.transformation_WCF_OCF())
        return frame_OCF

    def to_world_coordinates_origin(self, frame_OCF):
        """Represent a frame from the robot's origin coordinate system (OCF) in the world coordinate system (WCF).
        Parameters
        ----------
        frame_OCF : :class:`compas.geometry.Frame`
            A frame in the robot's coordinate frame.
        Returns
        -------
        :class:`compas.geometry.Frame`
            A frame in the world coordinate frame.
        """
        frame_WCF = frame_OCF.transformed(self.transformation_OCF_WCF())
        return frame_WCF

    def get_base_geometry(self):
        return self.base_geometry
    def set_base_geometry(self, base_geometry):
        self.base_geometry = base_geometry
    
    def get_picking_frame(self):
        return self.picking_frame
    def set_picking_frame(self, picking_frame):
        self.picking_frame = picking_frame