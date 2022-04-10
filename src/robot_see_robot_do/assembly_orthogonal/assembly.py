from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import os
import math
import compas

from copy import deepcopy
from compas.geometry import Frame
from compas.geometry import Transformation, Translation, Rotation
from compas.geometry import distance_point_point
from compas.datastructures import Network, network, mesh_offset
from compas_ghpython.artists import MeshArtist

import rhinoscriptsyntax as rs

from .element import Element

from .utilities import FromToData
from .utilities import FromToJson

__all__ = ['Assembly']


class Assembly(FromToData, FromToJson):
    """A data structure for discrete element assemblies.

    An assembly is essentially a network of assembly elements.
    Each element is represented by a node of the network.
    Each interface or connection between elements is represented by an edge of the network.

    Attributes
    ----------
    network : :class:`compas.Network`, optional
    elements : list of :class:`Element`, optional
        A list of assembly elements.
    attributes : dict, optional
        User-defined attributes of the assembly.
        Built-in attributes are:
        * name (str) : ``'Assembly'``
    default_element_attribute : dict, optional
        User-defined default attributes of the elements of the assembly.
        The built-in attributes are:
        * is_planned (bool) : ``False``
        * is_placed (bool) : ``False``
    default_connection_attributes : dict, optional
        User-defined default attributes of the connections of the assembly.

    Examples
    --------
    >>> assembly = Assembly()
    >>> for i in range(2):
    >>>     element = Element.from_box(Box(Frame.worldXY(), 10, 5, 2))
    >>>     assembly.add_element(element)
    """

    def __init__(self,
                 elements=None,
                 attributes=None,
                 default_element_attributes=None,
                 default_connection_attributes=None):

        self.network = Network()
        self.network.attributes.update({'name': 'Assembly'})

        if attributes is not None:
            self.network.attributes.update(attributes)

        self.network.default_node_attributes.update({
            'is_planned': False,
            'is_placed': False
        })

        if default_element_attributes is not None:
            self.network.default_node_attributes.update(default_element_attributes)

        if default_connection_attributes is not None:
            self.network.default_edge_attributes.update(default_connection_attributes)

        if elements:
            for element in elements:
                self.add_element(element)

    @property
    def name(self):
        """str : The name of the assembly."""
        return self.network.attributes.get('name', None)

    @name.setter
    def name(self, value):
        self.network.attributes['name'] = value

    def number_of_elements(self):
        """Compute the number of elements of the assembly.

        Returns
        -------
        int
            The number of elements.

        """
        return self.network.number_of_nodes()

    def number_of_connections(self):
        """Compute the number of connections of the assembly.

        Returns
        -------
        int
            the number of connections.

        """
        return self.network.number_of_edges()

    @property
    def data(self):
        """Return a data dictionary of the assembly.
        """
        # Network data does not recursively serialize to data...
        d = self.network.data

        # so we need to trigger that for elements stored in nodes
        node = {}
        for vkey, vdata in d['node'].items():
            node[vkey] = {key: vdata[key] for key in vdata.keys() if key != 'element'}
            node[vkey]['element'] = vdata['element'].to_data()

            if 'frame_est' in vdata:
                if node[vkey]['frame_est']:
                    node[vkey]['frame_est'] = node[vkey]['frame_est'].to_data()

        d['node'] = node

        return d

    @data.setter
    def data(self, data):
        # Deserialize elements from node dictionary
        for _vkey, vdata in data['node'].items():
            vdata['element'] = Element.from_data(vdata['element'])

            if 'frame_est' in vdata:
                if vdata['frame_est']:
                    vdata['frame_est'] = Frame.from_data(vdata['frame_est']) #node[vkey]['frame_est'].to_data()

        self.network = Network.from_data(data)

    def clear(self):
        """Clear all the assembly data."""
        self.network.clear()

    def add_element(self, element, key=None, attr_dict={}, **kwattr):
        """Add an element to the assembly.

        Parameters
        ----------
        element : Element
            The element to add.
        attr_dict : dict, optional
            A dictionary of element attributes. Default is ``None``.

        Returns
        -------
        hashable
            The identifier of the element.
        """
        attr_dict.update(kwattr)
        x, y, z = element.frame.point
        key = self.network.add_node(key=key, attr_dict=attr_dict,
                                    x=x, y=y, z=z, element=element)
        return key


    def add_unit_element(self, current_key, flip='AA', shift_value=0, angle=90, placed_by='human', on_ground=False, unit_index=0, frame_id=None, frame_est=None):
        """Add an element to the assembly.
        """
        radius = self.globals['radius']
        height = self.globals['height']
        shift_value = self.globals['shift_value']

        N = self.network.number_of_nodes()

        current_elem = self.network.node[current_key]['element']

        # Find the open connector of the current element
        if current_elem.connector_1_state:
            current_connector_frame = current_elem.connector_frame_1
        else:
            current_connector_frame = current_elem.connector_frame_2

        if flip == 'AA':
            a = b = 1
        if flip == 'AB':
            a = 1
            b = -1
        if flip == 'BA':
            a = -1
            b = 1
        if flip == 'BB':
            a = b = -1

        if placed_by == 'robot':
            R = Rotation.from_axis_and_angle(current_elem.frame.zaxis, math.radians(angle*a), current_connector_frame.point)

        else:
            R = Rotation.from_axis_and_angle(current_elem.frame.yaxis, math.radians(angle*b), current_connector_frame.point)

        new_elem = current_elem.transformed(R)

        if unit_index == 0:
            T = Translation.from_vector(new_elem.frame.zaxis*radius*a*b*2.)
        if unit_index == 1:
            T = Translation.from_vector(new_elem.frame.yaxis*radius*-a*2.+ new_elem.frame.zaxis*-radius*a*2.)
        T_shift = Translation.from_vector(current_connector_frame.xaxis*shift_value)
        new_elem.transform(T*T_shift)

        #if self.collision_check(new_elem, tolerance = -0.001) == False:
        if True:
            self.add_element(new_elem, placed_by=placed_by, on_ground=on_ground, frame_id=frame_id, frame_est=frame_est)

            if unit_index == 0:
                self.network.add_edge(current_key, N, edge_to='neighbour')
            else:
                self.network.add_edge(N-1, N, edge_to='parent')
                self.network.add_edge(current_key, N, edge_to='parent')

            self.update_connectors_states(current_key, new_elem, unit_index)

        return new_elem

    def add_connection(self, u, v, attr_dict=None, **kwattr):
        """Add a connection between two elements and specify its attributes.

        Parameters
        ----------
        u : hashable
            The identifier of the first element of the connection.
        v : hashable
            The identifier of the second element of the connection.
        attr_dict : dict, optional
            A dictionary of connection attributes.
        kwattr
            Other connection attributes as additional keyword arguments.

        Returns
        -------
        tuple
            The identifiers of the elements.
        """
        return self.network.add_edge(u, v, attr_dict, **kwattr)

    def add_joint(self, edge, joint):
        """
        """
        u, v = edge
        return self.add_edge(u, v, joint=joint)

    def transform(self, transformation):
        """Transforms this assembly.

        Parameters
        ----------
        transformation : :class:`Transformation`

        Returns
        -------
        None
        """
        for _k, element in self.elements(data=False):
            element.transform(transformation)

    def transformed(self, transformation):
        """Returns a transformed copy of this assembly.

        Parameters
        ----------
        transformation : :class:`Transformation`

        Returns
        -------
        Assembly
        """
        assembly = self.copy()
        assembly.transform(transformation)
        assembly.network.transform(transformation)
        return assembly

    def copy(self):
        """Returns a copy of this assembly.
        """
        cls = type(self)
        return cls.from_data(deepcopy(self.data))

    def element(self, key, data=False):
        """Get an element by its key."""
        if data:
            return self.network.node[key]['element'], self.network.node[key]
        else:
            return self.network.node[key]['element']

    def elements(self, data=False):
        """Iterate over the elements of the assembly.

        Parameters
        ----------
        data : bool, optional
            If ``True``, yield both the identifier and the attributes.

        Yields
        ------
        2-tuple
            The next element as a (key, element) tuple, if ``data`` is ``False``.
        3-tuple
            The next element as a (key, element, attr) tuple, if ``data`` is ``True``.

        """
        if data:
            for vkey, vattr in self.network.nodes(True):
                yield vkey, vattr['element'], vattr
        else:
            for vkey in self.network.nodes(data):
                yield vkey, self.network.node[vkey]['element']

    def connections(self, data=False):
        """Iterate over the connections of the network.

        Parameters
        ----------
        data : bool, optional
            If ``True``, yield both the identifier and the attributes.

        Yields
        ------
        2-tuple
            The next connection identifier (u, v), if ``data`` is ``False``.
        3-tuple
            The next connection as a (u, v, attr) tuple, if ``data`` is ``True``.

        """
        return self.network.edges(data)

    def direction(self, current_key, current_connector_key):
        """Compute direction of growth.
        """
        current_elem = self.network.node[current_key]['element']
        current_elem_type = current_elem._type
        current_connectors = current_elem.connectors(state='open')

        orient_map = {'X': 0, 'Y': 1, 'Z': 2}
        axis = orient_map[current_elem_type]

        current_location = current_elem.tool_frame.point[axis]

        if current_connectors:
            next_location = current_connectors[current_connector_key].point[axis]
            if current_location > next_location:
                direction = 0
            else:
                direction = 1
            return direction

    def direction_rf(self, current_key, current_connector_key):
        """Compute direction of growth.
        """
        current_elem = self.network.node[current_key]['element']
        current_elem_type = current_elem._type
        current_connectors = current_elem.connectors(state='open')

        orient_map = {'X': 0, 'Y': 1, 'Z': 2}
        axis = orient_map[current_elem_type]

        current_location = current_elem.tool_frame.point[axis]

        if current_connectors:
            next_location = current_connectors[current_connector_key].point[axis]
            if current_location > next_location:
                direction = 0
            else:
                direction = 1
            return direction

    def sequence(self, start_type, on_ground=False):
        """Compute the sequence for element placement.
        """
        sequence = []

        if start_type == 'X':
            sequence = ['X', 'Y', 'Z']
        if start_type == 'Y' and on_ground:
            sequence = ['X', 'Y', 'Z']
        else:
            sequence = ['X', 'Y', 'Z']  # should be Y,X,Z when on ground=False
        if start_type == 'Z':
            sequence = ['Z', 'X', 'Y']

        return sequence

    def sequence_rf(self, start_type, on_ground=False):
        """Compute the sequence for element placement.
        """
        sequence = []

        if start_type == 'X':
            sequence = ['Y', 'Z']
        #if start_type == 'Y' and on_ground:
        elif start_type == 'Y':
            sequence = ['X', 'Z']
        else:
            sequence = ['X', 'Y']

        return sequence

    def collision_check(self, elem, tolerance):
        """Check for collisions with assembly elements.
        """

        #key_index = self.network.key_index()
        #keys = [key_index[key] for key in self.network.nodes()]
        keys = [key for key, element in self.elements()]
        elements = [self.element(key) for key in keys]

        collision = False

        for element in elements:
            elem_mesh_offset = mesh_offset(elem.mesh, distance=tolerance, cls=None)

            artist1 = MeshArtist(elem_mesh_offset)
            elem_rmesh = artist1.draw_mesh()

            artist2 = MeshArtist(element.mesh)
            assembly_rmesh = artist2.draw_mesh()

            results = rs.MeshMeshIntersection(elem_rmesh, assembly_rmesh)
            if results:
                collision = True

        return collision

    def close_unit(self, current_key, flip=0, shift_value=0, angle=90, on_ground=False, added_frame_id=None, frame_est=None):
        """Add a module to the assembly.
        """

        keys_robot = []

        for i in range(2):
            if i == 0:
                placed_by = 'robot'
                frame_id = None
                my_new_elem = self.add_unit_element(current_key, flip=flip, shift_value=shift_value, angle=angle, placed_by=placed_by, on_ground=False, unit_index=i, frame_id=frame_id, frame_est=None)
                keys_robot += list(self.network.nodes_where({'element': my_new_elem}))
            else:
                placed_by = 'human'
                frame_id = added_frame_id
                my_new_elem = self.add_unit_element(current_key, flip=flip, shift_value=shift_value, angle=angle, placed_by=placed_by, on_ground=False, unit_index=i, frame_id=frame_id, frame_est=frame_est)
                keys_human = list((self.network.nodes_where({'element': my_new_elem})))

        keys_dict = {'keys_human': keys_human, 'keys_robot':keys_robot}

        return keys_dict


    def parent_key(self, point, within_dist):
        """Return the parent key of a tracked object.
        """
        parent_key = None

        for key, element in self.elements():
            connectors = element.connectors(state='open')
            for connector in connectors:
                dist = distance_point_point(point, connector.point)
                if dist < within_dist:
                    parent_key = key

        return parent_key


    def update_connectors_states(self, current_key, my_new_elem, unit_index):

        key_index = self.network.key_index()
        current_elem = self.network.node[current_key]['element']
        keys = [key_index[key] for key in self.network.nodes()]
        previous_elem = self.network.node[keys[-2]]['element']

        if unit_index == 1:
            if current_elem.connector_1_state:
                previous_elem.connector_1_state = False
                current_elem.connector_1_state = False
                my_new_elem.connector_1_state = False
            if current_elem.connector_2_state:
                previous_elem.connector_2_state = False
                current_elem.connector_2_state = False
                my_new_elem.connector_2_state = False


    def keys_within_radius(self, current_key):

        for key, element in self.elements(data=True):
            pass

    def keys_within_radius_xy(self, current_key):
        pass

    def keys_within_radius_domain(self, current_key):
        pass

    def range_filter(self, base_frame):
        """Disable connectors outside of a given range, e.g. robot reach.
        """
        ur_range_max = 1.3
        ur_range_min = 0.75

        for key, element in self.elements():
            if element.connector_1_state == True:
                distance = distance_point_point(element.connector_frame_1.point, base_frame.point)
                if not ur_range_min <= distance <= ur_range_max:
                    element.connector_1_state = False
            elif element.connector_2_state == True:
                distance = distance_point_point(element.connector_frame_2.point, base_frame.point)
                if not ur_range_min <= distance <= ur_range_max:
                    element.connector_2_state = False
            else:
                pass

    def options_elements(self, elem_x, elem_y, elem_z):
        """Returns a list of elements.
        """
        keys = [key for key, element in self.elements()]
        return [self.element(key).options_elements(elem_x=elem_x, elem_y=elem_y, elem_z=elem_z) for key in keys]


    def options_vectors(self):
        """Returns a list of vectors.
        """
        keys = [key for key, element in self.elements()]
        return [self.element(key).options_vectors() for key in keys]


    def connectors(self, state='all'):
        """ Get assembly's connectors.

        Parameters
        ----------
        state : string
            A string indentifying the connectors' state.

        'all' : return all connectors.
        'open' : return all open connectors.
        'closed' : return all closed connectors.

        Returns
        -------
        list
            A list of frames.

        """
        #key_index = self.network.key_index()
        #keys = [key_index[key] for key in self.network.nodes()]
        keys = [key for key, element in self.elements()]
        return [self.element(key).connectors(state) for key in keys]


    def export_building_plan(self):
        """
        exports the building plan by using the following protocol:

        the first lines are the description of the global markers (fixed in the world frame):
        type [string], element pose [6]
        = "GM", x, y, z, qw, qx, qy, qz

        the next lines contain the wall information:
        type [string], element pose [6], string_message [string]
        = type, x, y, z, qw, qx, qy, qz, string_message
        """

        print("exporting")
        building_plan = []

        for key, element, data in self.elements(data=True):
            line = []

            t = element._type
            line.append(t) #type
            line += element.get_pose_quaternion() #element pose
            string_message = "This is the element with the key index %i" %key
            line.append(string_message)
            building_plan.append(line)

        print(building_plan)
        exporter = Exporter()
        exporter.delete_file()
        exporter.export_building_plan(building_plan)

    def export_to_json_for_xr(self, path, is_built=False):

        self.network.update_default_node_attributes({"is_built":False,"idx_v":None,"custom_attr_1":None,"custom_attr_2":None,"custom_attr_3":None})

        for key, element in self.elements():
            idx_v = self.network.node_attribute(key, "course")
            self.network.node_attribute(key, "idx_v", idx_v)
            self.network.node_attribute(key, "is_built", is_built)

        self.to_json(path)

    def export_to_json_incon(self, qr_code, path, is_built=True, pretty=True):
        buildingplan = {"id":"iaac_plan",'name':"iaac_plan", "description":"iaac_plan", "building_steps":[]}
        building_steps = []

        for key, element, data in self.elements(data=True):
            x,y,z,w,qx,qy,qz = element.get_pose_quaternion()
            line = {
                "id":element.message,
                'type':element.objecttype,
                "object_type":"cylinder_for_iaac_workshop.obj",
                "is_tag": False,
                "pos.x": x,
                "pos.y": y,
                "pos.z": z,
                "quat.w": w,
                "quat.x": qx,
                "quat.y": qy,
                "quat.z": qz,
                "is_already_built": is_built,
                "color_rgb": [1.0, 0.0, 0.0],
                "build_instructions": []
                }
            building_steps.append(line)

        placeholder = {"type":"object",'object_type':"cylinder_for_iaac_workshop.obj", "is_tag": False, "is_already_built": False, "color_rgb": [1.0, 0.0, 0.0],"instances": 200,"build_instructions" : []}
        building_steps.append(placeholder)

        for tag in qr_code:
            w,qx,qy,qz = tag.quaternion
            tags = {
                "id" : "tag_",
                "type": "tag",
                "tag_id": 0,
                "tag_size" : 0.096,
                "pos.x" : tag.point.x,
                "pos.y" : tag.point.y,
                "pos.z" : tag.point.z,
                "quat.w" : w,
                "quat.x" : qx,
                "quat.y" : qy,
                "quat.z" : qz,
                "is_already_built" : True,
                "build_instructions" : []
            }
            building_steps.append(tags)

        buildingplan['building_steps'] = building_steps
        compas.json_dump(buildingplan, path, pretty)

